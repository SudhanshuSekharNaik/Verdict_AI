import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.evidence import Evidence, EvidencePartyEnum
from app.models.user import User
from app.schemas.evidence import (
    EvidenceCreate,
    EvidenceGraphResponse,
    EvidenceResponse,
    TimelineEventResponse,
)
from app.schemas.response import APIResponse
from app.security.dependencies import get_current_user_optional
from app.services.evidence_service import EvidenceService
from app.services.graph_service import GraphService
from app.services.timeline_service import TimelineService

router = APIRouter()


@router.post("/cases/{case_id}/evidence", response_model=APIResponse[EvidenceResponse], status_code=status.HTTP_201_CREATED)
async def upload_evidence_to_case(
    case_id: uuid.UUID,
    file: UploadFile,
    title: str = Form(...),
    party: EvidencePartyEnum = Form(EvidencePartyEnum.PLAINTIFF),
    document_type: str = Form("CONTRACT"),
    source: str = Form("UPLOAD"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    metadata = EvidenceCreate(title=title, party=party, document_type=document_type, source=source)
    user_id = current_user.id if current_user else None
    evidence = await EvidenceService.process_and_store_evidence(
        db=db, case_id=case_id, metadata=metadata, file=file, uploaded_by_id=user_id
    )
    return APIResponse(success=True, data=EvidenceResponse.model_validate(evidence))


@router.get("/cases/{case_id}/evidence", response_model=APIResponse[List[EvidenceResponse]])
async def list_case_evidence(case_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    evidences = await EvidenceService.get_case_evidence(db=db, case_id=case_id)
    return APIResponse(
        success=True, data=[EvidenceResponse.model_validate(e) for e in evidences]
    )


@router.get("/evidence/{evidence_id}", response_model=APIResponse[EvidenceResponse])
async def get_single_evidence(evidence_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    evidence = await EvidenceService.get_evidence_by_id(db=db, evidence_id=evidence_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence with ID {evidence_id} not found",
        )
    return APIResponse(success=True, data=EvidenceResponse.model_validate(evidence))


@router.post(
    "/cases/{case_id}/evidence/{evidence_id}/admit",
    response_model=APIResponse[EvidenceResponse],
)
async def admit_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Mark evidence as admitted to the court record."""
    result = await db.execute(
        select(Evidence).where(
            Evidence.id == evidence_id,
            Evidence.case_id == case_id,
        )
    )
    evidence = result.scalars().first()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence {evidence_id} not found in case {case_id}",
        )
    # Update verification status to ADMITTED
    evidence.verification_status = "ADMITTED"  # type: ignore[assignment]
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)
    return APIResponse(success=True, data=EvidenceResponse.model_validate(evidence))


@router.delete(
    "/cases/{case_id}/evidence/{evidence_id}",
    response_model=APIResponse[dict],
)
async def delete_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove an evidence item from a case."""
    result = await db.execute(
        select(Evidence).where(
            Evidence.id == evidence_id,
            Evidence.case_id == case_id,
        )
    )
    evidence = result.scalars().first()
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence {evidence_id} not found in case {case_id}",
        )
    await db.delete(evidence)
    await db.commit()
    return APIResponse(success=True, data={"message": "Evidence deleted successfully"})


@router.get("/cases/{case_id}/timeline", response_model=APIResponse[List[TimelineEventResponse]])
async def get_case_timeline(case_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    events = await TimelineService.get_case_timeline(db=db, case_id=case_id)
    return APIResponse(
        success=True, data=[TimelineEventResponse.model_validate(e) for e in events]
    )


@router.get("/cases/{case_id}/evidence-graph", response_model=APIResponse[EvidenceGraphResponse])
async def get_case_evidence_graph(case_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    graph_data = await GraphService.build_case_graph(db=db, case_id=case_id)
    return APIResponse(success=True, data=graph_data)
