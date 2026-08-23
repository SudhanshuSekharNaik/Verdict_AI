import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case import Case, CaseStatusEnum
from app.models.judgment import Judgment, VerdictEnum


class JudgmentService:
    """Handles Human Judge verdict registration and enforcement."""

    @staticmethod
    async def enter_judgment(
        db: AsyncSession,
        case_id: uuid.UUID,
        verdict: VerdictEnum,
        relief_awarded: str,
        reasoning: str,
        evidence_relied_on: List[str],
        authorities_relied_on: List[str],
        judge_id: Optional[uuid.UUID] = None,
    ) -> Judgment:
        # 1. Check if judgment already exists
        result = await db.execute(select(Judgment).where(Judgment.case_id == case_id))
        existing = result.scalars().first()
        if existing:
            existing.verdict = verdict
            existing.relief_awarded = relief_awarded
            existing.reasoning = reasoning
            existing.evidence_relied_on = evidence_relied_on
            existing.authorities_relied_on = authorities_relied_on
            await db.commit()
            await db.refresh(existing)
            return existing

        judgment = Judgment(
            case_id=case_id,
            judge_id=judge_id,
            verdict=verdict,
            relief_awarded=relief_awarded,
            reasoning=reasoning,
            evidence_relied_on=evidence_relied_on,
            authorities_relied_on=authorities_relied_on,
            metadata_json={"entered_by": "HUMAN_JUDGE", "certified_at": datetime.utcnow().isoformat()},
        )
        db.add(judgment)

        # Update Case status to CLOSED
        case_res = await db.execute(select(Case).where(Case.id == case_id))
        case = case_res.scalars().first()
        if case:
            case.status = CaseStatusEnum.CLOSED

        await db.commit()
        await db.refresh(judgment)
        return judgment
