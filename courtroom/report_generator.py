import uuid
from typing import Any, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case import Case
from app.models.judgment import Judgment


class CourtroomReportGenerator:
    """Generates comprehensive post-judgment certified case reports."""

    @staticmethod
    async def generate_post_judgment_report(db: AsyncSession, case_id: uuid.UUID) -> Dict[str, Any]:
        result = await db.execute(
            select(Case)
            .where(Case.id == case_id)
            .options(
                selectinload(Case.parties),
                selectinload(Case.evidence_list),
                selectinload(Case.events),
                selectinload(Case.claims),
                selectinload(Case.arguments),
                selectinload(Case.judgment),
            )
        )
        case = result.scalars().first()
        if not case:
            return {"error": "Case not found"}

        judgment = case.judgment
        if not judgment:
            return {
                "case_number": case.case_number,
                "title": case.title,
                "status": "JUDGMENT_PENDING",
                "message": "Hearing in progress or awaiting deliberation by My Lord (Human Judge).",
            }

        # Format sections
        plaintiff_args = [
            {"claim": a.claim, "reasoning": a.reasoning, "attack_type": a.attack_type.value}
            for a in case.arguments if a.agent.value == "PLAINTIFF_AGENT"
        ]
        defence_args = [
            {"claim": a.claim, "reasoning": a.reasoning, "attack_type": a.attack_type.value}
            for a in case.arguments if a.agent.value == "DEFENCE_AGENT"
        ]

        timeline_summary = [
            {
                "date": e.date_raw_str,
                "event": e.title,
                "party": e.party,
                "conflict": e.conflict_flag,
                "notes": e.conflict_notes,
            }
            for e in case.events
        ]

        evidence_catalog = [
            {
                "id": str(ev.id),
                "title": ev.title,
                "party": ev.party.value,
                "type": ev.document_type,
                "hash": ev.file_hash,
                "status": ev.verification_status.value,
            }
            for ev in case.evidence_list
        ]

        return {
            "certified_report_id": f"REP-{case.case_number}-{str(judgment.id)[:6]}",
            "case_number": case.case_number,
            "case_title": case.title,
            "case_type": case.case_type,
            "jurisdiction": case.jurisdiction,
            "date_of_judgment": judgment.created_at.strftime("%d %B %Y"),
            "parties": [
                {"name": p.name, "role": p.role.value} for p in case.parties
            ],
            "factual_matrix": case.description,
            "timeline": timeline_summary,
            "admitted_evidence": evidence_catalog,
            "plaintiff_submissions": plaintiff_args,
            "defence_submissions": defence_args,
            "human_judge_decision": {
                "verdict": judgment.verdict.value,
                "operative_relief": judgment.relief_awarded,
                "judicial_reasoning": judgment.reasoning,
                "evidence_relied_upon": judgment.evidence_relied_on,
                "authorities_relied_upon": judgment.authorities_relied_on,
            },
            "disclaimer": "OFFICIAL AADALAT AI CERTIFIED SIMULATION RECORD — AI ARGUED, EVIDENCE SPOKE, MY LORD DECIDED.",
        }
