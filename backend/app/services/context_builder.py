import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case import Case
from app.models.claim import Claim
from app.models.evidence import Evidence, EvidencePartyEnum
from app.models.hearing_message import HearingMessage, HearingSideEnum
from app.models.legal_source import LegalSource
from app.services.authority_verification import AuthorityVerificationService


async def build_case_context(
    db: AsyncSession,
    case_id: uuid.UUID,
    stage: str = "OPENING_ARGUMENTS",
    side: str = "PLAINTIFF",
    instruction: str = "",
    opposing_turn_id: Optional[str] = None,
) -> Dict[str, Any]:
    case_res = await db.execute(
        select(Case)
        .where(Case.id == case_id)
        .options(
            selectinload(Case.parties),
            selectinload(Case.claims),
        )
    )
    case = case_res.scalars().first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    case_info = {
        "id": str(case.id),
        "title": case.title,
        "case_type": case.case_type,
        "jurisdiction": case.jurisdiction,
        "description": case.description,
        "case_number": case.case_number,
    }

    parties = {"plaintiff": "", "defendant": ""}
    for p in (case.parties or []):
        if hasattr(p, "role"):
            role_str = p.role.value if hasattr(p.role, "value") else str(p.role)
            name = p.name if hasattr(p, "name") else str(p.id)
            if "PLAINTIFF" in role_str.upper():
                parties["plaintiff"] = name
            elif "DEFENDANT" in role_str.upper():
                parties["defendant"] = name
    case_info["parties"] = parties

    evidence_items = []
    p_ev_res = await db.execute(
        select(Evidence)
        .where(Evidence.case_id == case_id, Evidence.party == EvidencePartyEnum.PLAINTIFF)
        .order_by(Evidence.created_at)
    )
    p_ev_list = p_ev_res.scalars().all()
    p_idx = 1
    for ev in p_ev_list:
        label = f"P-{p_idx:03d}"
        evidence_items.append({
            "label": label,
            "id": str(ev.id),
            "title": ev.title,
            "document_type": ev.document_type,
            "extracted_text": (ev.extracted_text or "")[:500],
            "summary": ev.title,
            "party": "PLAINTIFF",
        })
        p_idx += 1

    d_ev_res = await db.execute(
        select(Evidence)
        .where(Evidence.case_id == case_id, Evidence.party == EvidencePartyEnum.DEFENDANT)
        .order_by(Evidence.created_at)
    )
    d_ev_list = d_ev_res.scalars().all()
    d_idx = 1
    for ev in d_ev_list:
        label = f"D-{d_idx:03d}"
        evidence_items.append({
            "label": label,
            "id": str(ev.id),
            "title": ev.title,
            "document_type": ev.document_type,
            "extracted_text": (ev.extracted_text or "")[:500],
            "summary": ev.title,
            "party": "DEFENDANT",
        })
        d_idx += 1

    claim_items = []
    for claim in (case.claims or []):
        claim_items.append({
            "party": claim.party.value if hasattr(claim.party, "value") else str(claim.party),
            "statement": claim.statement,
            "claim_type": claim.claim_type,
        })

    issues = []
    for claim in claim_items:
        if claim["statement"]:
            issues.append(claim["statement"][:200])

    facts = []
    for ev in evidence_items[:5]:
        if ev.get("extracted_text"):
            facts.append(f"[{ev['label']}] {ev['title']}: {ev['extracted_text'][:150]}")

    # 1. Retrieve candidate authorities from DB
    candidate_authorities = []
    auth_res = await db.execute(select(LegalSource).order_by(LegalSource.created_at))
    auth_list = auth_res.scalars().all()
    for src in auth_list[:10]:
        candidate_authorities.append({
            "citation": src.citation,
            "title": src.title,
            "court": src.court,
            "year": src.year,
            "proposition": (src.summary or src.full_text or "")[:300],
            "source_type": src.source_type,
            "statute_section": src.statute_section,
        })

    # 2. Verify all authorities against DB + NLI (pass case facts for real verification)
    case_facts_text = "\n".join(facts[:5])
    legal_issues_text = "\n".join(issues[:5])
    verification_result = await AuthorityVerificationService.verify_all_authorities(
        db=db,
        candidate_authorities=candidate_authorities,
        case_facts=case_facts_text,
        legal_issues=legal_issues_text,
    )

    # 3. Format verified authorities for Groq (VERIFIED ONLY)
    verified_for_groq = AuthorityVerificationService.format_for_groq(
        verification_result["verified"]
    )

    previous_arguments = []
    opposing_arguments = []

    if side.upper() == "PLAINTIFF":
        msg_res = await db.execute(
            select(HearingMessage)
            .where(
                HearingMessage.case_id == case_id,
                HearingMessage.side == HearingSideEnum.PLAINTIFF,
            )
            .order_by(HearingMessage.created_at)
        )
        for msg in msg_res.scalars().all():
            previous_arguments.append(msg.content_json)

        opp_res = await db.execute(
            select(HearingMessage)
            .where(
                HearingMessage.case_id == case_id,
                HearingMessage.side == HearingSideEnum.DEFENCE,
            )
            .order_by(HearingMessage.created_at)
        )
        for msg in opp_res.scalars().all():
            opposing_arguments.append(msg.content_json)
    else:
        msg_res = await db.execute(
            select(HearingMessage)
            .where(
                HearingMessage.case_id == case_id,
                HearingMessage.side == HearingSideEnum.DEFENCE,
            )
            .order_by(HearingMessage.created_at)
        )
        for msg in msg_res.scalars().all():
            previous_arguments.append(msg.content_json)

        opp_res = await db.execute(
            select(HearingMessage)
            .where(
                HearingMessage.case_id == case_id,
                HearingMessage.side == HearingSideEnum.PLAINTIFF,
            )
            .order_by(HearingMessage.created_at)
        )
        for msg in opp_res.scalars().all():
            opposing_arguments.append(msg.content_json)

    return {
        "case": case_info,
        "stage": stage,
        "issues": issues,
        "facts": facts,
        "evidence": evidence_items,
        "claims": claim_items,
        "legal_authorities": candidate_authorities,
        "verified_authorities": verified_for_groq,
        "authority_verification": {
            "total_candidate": verification_result["total_candidate"],
            "verified_count": verification_result["verified_count"],
            "rejected_count": verification_result["rejected_count"],
            "rejected": [
                {
                    "citation": r.get("citation", ""),
                    "reason": r.get("verification", {}).get("reason", ""),
                }
                for r in verification_result["rejected"]
            ],
        },
        "previous_arguments": previous_arguments,
        "opposing_arguments": opposing_arguments,
        "instruction": instruction,
    }


async def build_judge_context(
    db: AsyncSession,
    case_id: uuid.UUID,
) -> Dict[str, Any]:
    base_context = await build_case_context(db, case_id, stage="JUDGE_DELIBERATION", side="JUDGE")

    p_args = []
    d_args = []
    msg_res = await db.execute(
        select(HearingMessage)
        .where(HearingMessage.case_id == case_id)
        .order_by(HearingMessage.created_at)
    )
    for msg in msg_res.scalars().all():
        if msg.side == HearingSideEnum.PLAINTIFF:
            p_args.append(msg.content_json)
        elif msg.side == HearingSideEnum.DEFENCE:
            d_args.append(msg.content_json)

    return {
        **base_context,
        "plaintiff_arguments": p_args,
        "defence_arguments": d_args,
    }
