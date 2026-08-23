import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agents.defence_agent import DefenceAgent
from agents.orchestrator import CourtroomOrchestrator
from agents.plaintiff_agent import PlaintiffAgent
from app.database.session import get_db
from app.models.case import Case, CaseStatusEnum
from app.models.courtroom import CourtroomEvent, CourtroomRound, CourtroomStageEnum
from app.models.evidence import Evidence
from app.models.judgment import VerdictEnum
from app.models.user import User
from app.schemas.response import APIResponse
from app.security.dependencies import get_current_user_optional
from courtroom.judgment import JudgmentService
from courtroom.report_generator import CourtroomReportGenerator

router = APIRouter()

STAGE_PROGRESSION = [
    CourtroomStageEnum.CASE_OPENED,
    CourtroomStageEnum.CASE_PREPARATION,
    CourtroomStageEnum.EVIDENCE_SUBMISSION,
    CourtroomStageEnum.OPENING_ARGUMENTS,
    CourtroomStageEnum.PLAINTIFF_ARGUMENT,
    CourtroomStageEnum.DEFENCE_ARGUMENT,
    CourtroomStageEnum.CROSS_EXAMINATION,
    CourtroomStageEnum.PLAINTIFF_REBUTTAL,
    CourtroomStageEnum.DEFENCE_REBUTTAL,
    CourtroomStageEnum.FINAL_SUBMISSIONS,
    CourtroomStageEnum.JUDGE_QUESTIONS,
    CourtroomStageEnum.JUDGE_DELIBERATION,
    CourtroomStageEnum.VERDICT,
    CourtroomStageEnum.CASE_CLOSED,
]


class StepRequest(BaseModel):
    target_stage: Optional[str] = Field(None, example="PLAINTIFF_ARGUMENT")


class JudgeQuestionRequest(BaseModel):
    target_agent: str = Field(..., example="PLAINTIFF_AI")
    question: str = Field(..., example="Can you explain why the damage report was dated after the tenant moved out?")


class JudgmentCreateRequest(BaseModel):
    verdict: VerdictEnum = Field(..., example=VerdictEnum.PLAINTIFF_SUCCEEDS)
    relief_awarded: str = Field(..., example="Respondent is directed to refund ₹50,000 security deposit with 6% interest.")
    reasoning: str = Field(..., example="Respondent failed to establish verifiable damages.")
    evidence_relied_on: List[str] = Field(default_factory=list)
    authorities_relied_on: List[str] = Field(default_factory=list)


async def _get_evidence_labels(db: AsyncSession, case_id: uuid.UUID) -> Dict[str, str]:
    result = await db.execute(
        select(Evidence).where(Evidence.case_id == case_id).order_by(Evidence.created_at)
    )
    ev_list = result.scalars().all()
    labels = {}
    p_idx, d_idx = 1, 1
    for ev in ev_list:
        eid = str(ev.id)
        if ev.party.value == "PLAINTIFF":
            labels[eid] = f"P-{p_idx:03d}"
            p_idx += 1
        elif ev.party.value == "DEFENDANT":
            labels[eid] = f"D-{d_idx:03d}"
            d_idx += 1
    return labels


async def _get_citation_labels(db: AsyncSession) -> Dict[str, str]:
    from app.models.legal_source import LegalSource
    result = await db.execute(select(LegalSource).order_by(LegalSource.created_at))
    sources = result.scalars().all()
    labels = {}
    for i, src in enumerate(sources, 1):
        labels[str(src.id)] = f"A-{i:03d}"
    return labels


@router.post("/cases/{case_id}/session/start", response_model=APIResponse[Dict[str, Any]])
async def start_courtroom_session(case_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    case_res = await db.execute(select(Case).where(Case.id == case_id))
    case = case_res.scalars().first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    existing_rounds = await db.execute(
        select(CourtroomRound).where(CourtroomRound.case_id == case_id)
    )
    if existing_rounds.scalars().first():
        return APIResponse(success=True, data={"session_status": "ACTIVE", "message": "Session already started"})

    case.status = CaseStatusEnum.HEARING
    await db.commit()

    return APIResponse(success=True, data={"session_status": "ACTIVE", "message": "Hearing started. Click Advance to generate opening arguments."})


@router.get("/cases/{case_id}/state", response_model=APIResponse[Dict[str, Any]])
async def get_courtroom_state(case_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Case)
        .where(Case.id == case_id)
        .options(
            selectinload(Case.courtroom_rounds).selectinload(CourtroomRound.events),
            selectinload(Case.judgment),
        )
    )
    case = result.scalars().first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    ev_labels = await _get_evidence_labels(db, case_id)
    cit_labels = await _get_citation_labels(db)

    rounds_data = []
    for r in case.courtroom_rounds:
        events = []
        for e in r.events:
            labeled_refs = []
            for ref in (e.references or []):
                label = ev_labels.get(ref, ref)
                labeled_refs.append({"id": ref, "label": label})

            meta_labels = (e.metadata_json or {}).get("evidence_labels", [])
            ev_chips = meta_labels if meta_labels else [r_item["label"] for r_item in labeled_refs if isinstance(r_item, dict)]

            events.append({
                "id": str(e.id),
                "speaker": e.speaker,
                "event_type": e.event_type,
                "content": e.content,
                "references": [r_item["id"] if isinstance(r_item, dict) else r_item for r_item in labeled_refs],
                "evidence_chips": ev_chips,
            })
        rounds_data.append({
            "round_id": str(r.id),
            "round_number": r.round_number,
            "stage": r.stage.value,
            "active_speaker": r.active_speaker,
            "events": events,
            "metadata": r.metadata_json or {},
        })

    current_stage = rounds_data[-1]["stage"] if rounds_data else "CASE_OPENED"
    next_idx = STAGE_PROGRESSION.index(CourtroomStageEnum(current_stage)) + 1 if current_stage in [s.value for s in STAGE_PROGRESSION] else -1
    next_stage = STAGE_PROGRESSION[next_idx].value if next_idx < len(STAGE_PROGRESSION) else None

    return APIResponse(
        success=True,
        data={
            "case_id": str(case.id),
            "case_number": case.case_number,
            "title": case.title,
            "status": case.status.value,
            "current_stage": current_stage,
            "next_stage": next_stage,
            "rounds": rounds_data,
            "has_judgment": case.judgment is not None,
            "evidence_labels": ev_labels,
            "citation_labels": cit_labels,
        },
    )


@router.post("/cases/{case_id}/step", response_model=APIResponse[Dict[str, Any]])
async def step_courtroom_turn(
    case_id: uuid.UUID, req: StepRequest, db: AsyncSession = Depends(get_db)
):
    case_res = await db.execute(select(Case).where(Case.id == case_id))
    case = case_res.scalars().first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    if req.target_stage:
        try:
            target = CourtroomStageEnum(req.target_stage)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid stage: {req.target_stage}")

        if target in (CourtroomStageEnum.CASE_OPENED, CourtroomStageEnum.CASE_PREPARATION,
                       CourtroomStageEnum.EVIDENCE_SUBMISSION):
            raise HTTPException(status_code=400, detail=f"Cannot manually advance to {target.value}")

        round_res = await db.execute(
            select(CourtroomRound)
            .where(CourtroomRound.case_id == case_id)
            .order_by(CourtroomRound.created_at.desc())
        )
        last_round = round_res.scalars().first()
        if last_round:
            last_idx = STAGE_PROGRESSION.index(last_round.stage) if last_round.stage in STAGE_PROGRESSION else -1
            target_idx = STAGE_PROGRESSION.index(target) if target in STAGE_PROGRESSION else -1
            if target_idx <= last_idx and last_round.stage != target:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot skip backwards from {last_round.stage.value} to {target.value}"
                )

    step_result = await CourtroomOrchestrator.run_courtroom_step(
        db=db, case_id=case_id, target_stage=req.target_stage
    )
    return APIResponse(success=True, data=step_result)


@router.post("/cases/{case_id}/judge/question", response_model=APIResponse[Dict[str, Any]])
async def ask_judge_question(
    case_id: uuid.UUID, req: JudgeQuestionRequest, db: AsyncSession = Depends(get_db)
):
    case_res = await db.execute(select(Case).where(Case.id == case_id))
    case = case_res.scalars().first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    round_count_res = await db.execute(
        select(CourtroomRound).where(CourtroomRound.case_id == case_id)
    )
    all_rounds = round_count_res.scalars().all()

    existing_judge_rounds = [r for r in all_rounds if r.stage == CourtroomStageEnum.JUDGE_QUESTIONS]
    if existing_judge_rounds:
        round_obj = existing_judge_rounds[-1]
    else:
        round_obj = CourtroomRound(
            case_id=case_id,
            round_number=len(all_rounds) + 1,
            stage=CourtroomStageEnum.JUDGE_QUESTIONS,
            active_speaker="MY_LORD",
            is_completed=True,
        )
        db.add(round_obj)
        await db.flush()

    ev_q = CourtroomEvent(
        round_id=round_obj.id,
        speaker="MY_LORD",
        event_type="QUESTION",
        content=f"QUESTION FROM MY LORD (TO {req.target_agent}):\n\n\"{req.question}\"",
        metadata_json={"target_agent": req.target_agent},
    )
    db.add(ev_q)

    ev_labels = await _get_evidence_labels(db, case_id)
    all_ev_labels = list(ev_labels.values())

    if req.target_agent.upper() == "PLAINTIFF_AI":
        p_ev = await _get_evidence_records(db, case_id, "PLAINTIFF")
        ans_data = await PlaintiffAgent.answer_judge_question(
            question=req.question,
            plaintiff_evidence=[{"title": e.title, "id": str(e.id)} for e in p_ev],
            authorities=[],
        )
    else:
        d_ev = await _get_evidence_records(db, case_id, "DEFENDANT")
        ans_data = await DefenceAgent.answer_judge_question(
            question=req.question,
            defence_evidence=[{"title": e.title, "id": str(e.id)} for e in d_ev],
            authorities=[],
        )

    ev_ans = CourtroomEvent(
        round_id=round_obj.id,
        speaker=req.target_agent,
        event_type="ANSWER",
        content=f"RESPONSE TO BENCH:\n\n{ans_data['answer']}",
        references=ans_data.get("references", []),
    )
    db.add(ev_ans)
    await db.commit()

    return APIResponse(success=True, data={
        "question": ev_q.content,
        "answer": ev_ans.content,
        "round_id": str(round_obj.id),
    })


async def _get_evidence_records(db, case_id, party_str):
    from app.models.evidence import EvidencePartyEnum
    party_enum = EvidencePartyEnum.PLAINTIFF if party_str == "PLAINTIFF" else EvidencePartyEnum.DEFENDANT
    result = await db.execute(
        select(Evidence).where(Evidence.case_id == case_id, Evidence.party == party_enum)
    )
    return result.scalars().all()


@router.post("/cases/{case_id}/judgment", response_model=APIResponse[Dict[str, Any]])
async def enter_human_judgment(
    case_id: uuid.UUID,
    req: JudgmentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    judge_id = current_user.id if current_user else None
    judgment = await JudgmentService.enter_judgment(
        db=db, case_id=case_id, verdict=req.verdict,
        relief_awarded=req.relief_awarded, reasoning=req.reasoning,
        evidence_relied_on=req.evidence_relied_on,
        authorities_relied_on=req.authorities_relied_on,
        judge_id=judge_id,
    )
    return APIResponse(success=True, data={"judgment_id": str(judgment.id), "verdict": judgment.verdict.value})


@router.get("/cases/{case_id}/report", response_model=APIResponse[Dict[str, Any]])
async def get_courtroom_report(case_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    report = await CourtroomReportGenerator.generate_post_judgment_report(db=db, case_id=case_id)
    return APIResponse(success=True, data=report)
