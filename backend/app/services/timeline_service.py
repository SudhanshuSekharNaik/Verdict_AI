import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.evidence import Evidence


class TimelineService:
    """Timeline Engine: Extracts chronological milestones and identifies timeline conflicts."""

    @staticmethod
    def parse_flexible_date(date_str: str) -> Optional[datetime]:
        formats = [
            "%d %B %Y",
            "%d %b %Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%B %d, %Y",
        ]
        # Clean ordinals like 1st, 2nd, 3rd, 4th
        clean_str = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str).strip()
        for fmt in formats:
            try:
                return datetime.strptime(clean_str, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    async def extract_and_register_event(
        db: AsyncSession,
        case_id: uuid.UUID,
        date_raw_str: str,
        title: str,
        description: str,
        party: str = "UNDISPUTED",
        source_evidence_id: Optional[uuid.UUID] = None,
    ) -> Event:
        parsed_date = TimelineService.parse_flexible_date(date_raw_str)
        
        # Check for existing events around the same topic or date to detect conflicts
        result = await db.execute(select(Event).where(Event.case_id == case_id))
        existing_events = list(result.scalars().all())

        conflict_flag = False
        conflict_notes = None

        # Conflict Detection Heuristics
        for ex in existing_events:
            # Check for same milestone with conflicting dates
            if (
                any(keyword in ex.title.lower() for keyword in ["inspection", "move-out", "notice", "damage", "payment", "delivery"])
                and any(keyword in title.lower() for keyword in ["inspection", "move-out", "notice", "damage", "payment", "delivery"])
            ):
                if ex.date_raw_str.strip().lower() != date_raw_str.strip().lower():
                    conflict_flag = True
                    conflict_notes = (
                        f"⚠️ TIMELINE CONFLICT: Existing record '{ex.title}' is dated {ex.date_raw_str} ({ex.party}), "
                        f"whereas new record '{title}' asserts date {date_raw_str} ({party})."
                    )
                    ex.conflict_flag = True
                    ex.conflict_notes = conflict_notes

        event = Event(
            case_id=case_id,
            event_date=parsed_date,
            date_raw_str=date_raw_str,
            title=title,
            description=description,
            party=party,
            source_evidence_id=source_evidence_id,
            conflict_flag=conflict_flag,
            conflict_notes=conflict_notes,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    @staticmethod
    async def get_case_timeline(db: AsyncSession, case_id: uuid.UUID) -> List[Event]:
        result = await db.execute(
            select(Event).where(Event.case_id == case_id).order_by(Event.event_date.asc().nulls_last(), Event.created_at.asc())
        )
        return list(result.scalars().all())
