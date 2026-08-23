import hashlib
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.case import Case, CaseStatusEnum
from app.models.hearing_message import (
    HearingMessage,
    HearingMessageTypeEnum,
    HearingSideEnum,
)
from app.schemas.response import APIResponse
from app.services.context_builder import build_case_context, build_judge_context
from app.services.groq_service import generate_judge_analysis, generate_legal_argument

router = APIRouter()

HEARING_STAGES = [
    "OPENING_ARGUMENTS",
    "PLAINTIFF_ARGUMENT",
    "DEFENCE_ARGUMENT",
    "CROSS_EXAMINATION",
    "PLAINTIFF_REBUTTAL",
    "DEFENCE_REBUTTAL",
    "FINAL_SUBMISSIONS",
    "JUDGE_QUESTIONS",
    "JUDGE_DELIBERATION",
    "VERDICT",
]


class GenerateRequest(BaseModel):
    side: str = Field(..., pattern="^(PLAINTIFF|DEFENCE)$")
    stage: str = Field(default="PLAINTIFF_ARGUMENT")
    instruction: str = Field(default="")
    opposing_turn_id: Optional[str] = Field(default=None)


class JudgeAnalysisRequest(BaseModel):
    pass


def _make_turn_id(case_id: uuid.UUID, side: str, stage: str) -> str:
    raw = f"{case_id}:{side}:{stage}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


@router.post(
    "/cases/{case_id}/hearing/messages",
    response_model=APIResponse[Dict[str, Any]],
)
async def list_hearing_messages(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    case_res = await db.execute(select(Case).where(Case.id == case_id))
    case = case_res.scalars().first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    msg_res = await db.execute(
        select(HearingMessage)
        .where(HearingMessage.case_id == case_id)
        .order_by(HearingMessage.created_at)
    )
    messages = msg_res.scalars().all()

    items = []
    for msg in messages:
        items.append({
            "id": str(msg.id),
            "turn_id": msg.turn_id,
            "stage": msg.stage,
            "side": msg.side.value,
            "message_type": msg.message_type.value,
            "content_json": msg.content_json,
            "evidence_refs": msg.evidence_refs,
            "authority_refs": msg.authority_refs,
            "parent_turn_id": msg.parent_turn_id,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
        })

    return APIResponse(success=True, data={"messages": items})


@router.post(
    "/cases/{case_id}/hearing/generate",
    response_model=APIResponse[Dict[str, Any]],
)
async def generate_hearing_message(
    case_id: uuid.UUID,
    req: GenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    case_res = await db.execute(select(Case).where(Case.id == case_id))
    case = case_res.scalars().first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case.status not in (CaseStatusEnum.HEARING, CaseStatusEnum.READY_FOR_HEARING):
        case.status = CaseStatusEnum.HEARING
        await db.commit()

    side_upper = req.side.upper()
    if side_upper not in ("PLAINTIFF", "DEFENCE"):
        raise HTTPException(status_code=400, detail="side must be PLAINTIFF or DEFENCE")

    stage = req.stage
    if side_upper == "PLAINTIFF" and stage not in (
        "OPENING_ARGUMENTS", "PLAINTIFF_ARGUMENT", "PLAINTIFF_REBUTTAL",
        "CROSS_EXAMINATION", "FINAL_SUBMISSIONS",
    ):
        stage = "PLAINTIFF_ARGUMENT"
    elif side_upper == "DEFENCE" and stage not in (
        "DEFENCE_ARGUMENT", "DEFENCE_REBUTTAL", "CROSS_EXAMINATION",
        "FINAL_SUBMISSIONS",
    ):
        stage = "DEFENCE_ARGUMENT"

    turn_id = _make_turn_id(case_id, side_upper, stage)

    existing = await db.execute(
        select(HearingMessage).where(
            HearingMessage.case_id == case_id,
            HearingMessage.turn_id == turn_id,
        )
    )
    existing_msg = existing.scalars().first()
    if existing_msg:
        return APIResponse(
            success=True,
            data={
                "id": str(existing_msg.id),
                "turn_id": existing_msg.turn_id,
                "stage": existing_msg.stage,
                "side": existing_msg.side.value,
                "message_type": existing_msg.message_type.value,
                "content_json": existing_msg.content_json,
                "evidence_refs": existing_msg.evidence_refs,
                "authority_refs": existing_msg.authority_refs,
                "authority_verification": existing_msg.content_json.get("authority_verification", {}),
                "deduplicated": True,
            },
        )

    context = await build_case_context(
        db=db,
        case_id=case_id,
        stage=stage,
        side=side_upper,
        instruction=req.instruction,
        opposing_turn_id=req.opposing_turn_id,
    )

    # Extract verified authorities and verification report
    verified_authorities = context.get("verified_authorities", [])
    authority_verification = context.get("authority_verification", {})
    actual_evidence_count = len(context.get("evidence", []))

    try:
        result = await generate_legal_argument(
            side=side_upper,
            context=context,
            verified_authorities=verified_authorities,
            actual_evidence_count=actual_evidence_count,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    # Inject authority verification report into the result
    result["authority_verification"] = authority_verification

    # Enrich authority_references with metadata from verified authorities
    auth_lookup = {a.get("citation", ""): a for a in verified_authorities}
    for ref in result.get("authority_references", []):
        cit = ref.get("citation", "")
        if cit in auth_lookup:
            v = auth_lookup[cit]
            ref.setdefault("case_name", v.get("case_name", ""))
            ref.setdefault("court", v.get("court", ""))
            ref.setdefault("year", v.get("year"))
            ref.setdefault("verification_status", v.get("verification_status", "VERIFIED"))
        elif not ref.get("verification_status"):
            ref["verification_status"] = "UNVERIFIED"

    if side_upper == "PLAINTIFF":
        msg_type = HearingMessageTypeEnum.ARGUMENT
        if "REBUTTAL" in stage.upper():
            msg_type = HearingMessageTypeEnum.REBUTTAL
        elif "CROSS" in stage.upper():
            msg_type = HearingMessageTypeEnum.CROSS_EXAM
        elif "OPENING" in stage.upper():
            msg_type = HearingMessageTypeEnum.OPENING
    else:
        msg_type = HearingMessageTypeEnum.ARGUMENT
        if "REBUTTAL" in stage.upper():
            msg_type = HearingMessageTypeEnum.REBUTTAL
        elif "CROSS" in stage.upper():
            msg_type = HearingMessageTypeEnum.CROSS_EXAM

    evidence_refs = [er.get("id", "") for er in result.get("evidence_references", []) if er.get("id")]
    authority_refs = [ar.get("citation", "") for ar in result.get("authority_references", []) if ar.get("citation")]

    db_msg = HearingMessage(
        case_id=case_id,
        stage=stage,
        turn_id=turn_id,
        side=HearingSideEnum(side_upper),
        message_type=msg_type,
        content_json=result,
        evidence_refs=evidence_refs,
        authority_refs=authority_refs,
        parent_turn_id=req.opposing_turn_id,
    )
    db.add(db_msg)
    await db.commit()
    await db.refresh(db_msg)

    return APIResponse(
        success=True,
        data={
            "id": str(db_msg.id),
            "turn_id": db_msg.turn_id,
            "stage": db_msg.stage,
            "side": db_msg.side.value,
            "message_type": db_msg.message_type.value,
            "content_json": db_msg.content_json,
            "evidence_refs": db_msg.evidence_refs,
            "authority_refs": db_msg.authority_refs,
            "authority_verification": authority_verification,
            "deduplicated": False,
        },
    )


@router.post(
    "/cases/{case_id}/hearing/judge-analysis",
    response_model=APIResponse[Dict[str, Any]],
)
async def judge_analysis(
    case_id: uuid.UUID,
    req: JudgeAnalysisRequest,
    db: AsyncSession = Depends(get_db),
):
    case_res = await db.execute(select(Case).where(Case.id == case_id))
    case = case_res.scalars().first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    turn_id = _make_turn_id(case_id, "JUDGE", "JUDGE_DELIBERATION")

    existing = await db.execute(
        select(HearingMessage).where(
            HearingMessage.case_id == case_id,
            HearingMessage.turn_id == turn_id,
        )
    )
    existing_msg = existing.scalars().first()
    if existing_msg:
        return APIResponse(
            success=True,
            data={
                "id": str(existing_msg.id),
                "turn_id": existing_msg.turn_id,
                "stage": existing_msg.stage,
                "side": "JUDGE",
                "content_json": existing_msg.content_json,
                "deduplicated": True,
            },
        )

    context = await build_judge_context(db=db, case_id=case_id)
    verified_authorities = context.get("verified_authorities", [])

    try:
        result = await generate_judge_analysis(
            context=context,
            verified_authorities=verified_authorities,
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Judge analysis failed: {str(e)}")

    db_msg = HearingMessage(
        case_id=case_id,
        stage="JUDGE_DELIBERATION",
        turn_id=turn_id,
        side=HearingSideEnum.JUDGE,
        message_type=HearingMessageTypeEnum.RULING,
        content_json=result,
        evidence_refs=[],
        authority_refs=[],
    )
    db.add(db_msg)
    await db.commit()
    await db.refresh(db_msg)

    return APIResponse(
        success=True,
        data={
            "id": str(db_msg.id),
            "turn_id": db_msg.turn_id,
            "stage": db_msg.stage,
            "side": "JUDGE",
            "content_json": db_msg.content_json,
            "deduplicated": False,
        },
    )
