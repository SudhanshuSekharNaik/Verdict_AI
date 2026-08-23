import uuid
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case import Case
from app.models.claim import Claim
from app.models.event import Event
from app.models.evidence import Evidence


class JudgeAssistantAgent:
    """👨‍⚖️ Judge Assistant Agent: Organizes facts, synthesizes contradictions, and drafts question briefs for the Human Judge."""

    @staticmethod
    async def prepare_bench_brief(db: AsyncSession, case_id: uuid.UUID) -> Dict[str, Any]:
        result = await db.execute(
            select(Case)
            .where(Case.id == case_id)
            .options(
                selectinload(Case.parties),
                selectinload(Case.evidence_list),
                selectinload(Case.events),
                selectinload(Case.claims),
            )
        )
        case = result.scalars().first()
        if not case:
            return {"error": "Case not found"}

        # 1. Facts Breakdown
        plaintiff_claims = [c.statement for c in case.claims if c.party.value == "PLAINTIFF"]
        defence_claims = [c.statement for c in case.claims if c.party.value == "DEFENDANT"]

        # 2. Timeline Contradictions
        timeline_conflicts = [
            {
                "event_title": e.title,
                "date": e.date_raw_str,
                "party": e.party,
                "notes": e.conflict_notes,
            }
            for e in case.events if e.conflict_flag
        ]

        # 3. Evidence Status Summary
        evidence_summary = {
            "total_exhibits": len(case.evidence_list),
            "plaintiff_exhibits": len([e for e in case.evidence_list if e.party.value == "PLAINTIFF"]),
            "defence_exhibits": len([e for e in case.evidence_list if e.party.value == "DEFENDANT"]),
        }

        # 4. Bench Question Suggestions for Human Judge
        suggested_questions = [
            "To Plaintiff AI: Can you point to the exact timestamp or record verifying the condition when you vacated?",
            "To Defence AI: Where is the itemized breakdown showing that the alleged damages exceeded normal wear and tear?",
            "To Both Parties: How do you explain the discrepancy in the timeline between the inspection notice and move-out date?",
        ]

        return {
            "case_number": case.case_number,
            "title": case.title,
            "case_type": case.case_type,
            "jurisdiction": case.jurisdiction,
            "plaintiff_claims": plaintiff_claims,
            "defence_claims": defence_claims,
            "timeline_conflicts": timeline_conflicts,
            "evidence_summary": evidence_summary,
            "suggested_questions_for_my_lord": suggested_questions,
            "core_issue": f"Whether the contested deductions or liability in {case.title} are legally substantiated by verifiable evidence.",
            "disclaimer": "AI PREPARES & ORGANIZES. THE FINAL JUDICIAL DECISION IS MADE EXCLUSIVELY BY MY LORD (HUMAN JUDGE).",
        }
