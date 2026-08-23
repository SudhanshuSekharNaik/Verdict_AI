import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.user import User
from app.schemas.case import CaseCreate, CaseIntakeRequest, CaseIntakeResponse, CaseResponse, CaseUpdate
from app.schemas.response import APIResponse
from app.security.dependencies import get_current_user_optional
from app.services.case_service import CaseService

router = APIRouter()


@router.post("/intake", response_model=APIResponse[CaseIntakeResponse])
async def process_case_intake(
    intake_req: CaseIntakeRequest, db: AsyncSession = Depends(get_db)
):
    """Parses natural language case descriptions into structured parties, claims, and timeline facts."""
    intake_result = await CaseService.process_intake(db=db, intake_req=intake_req)
    return APIResponse(success=True, data=intake_result)


@router.post("/", response_model=APIResponse[CaseResponse], status_code=status.HTTP_201_CREATED)
async def create_new_case(
    case_in: CaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    user_id = current_user.id if current_user else None
    case = await CaseService.create_case(db=db, case_in=case_in, created_by_id=user_id)
    return APIResponse(success=True, data=CaseResponse.model_validate(case))


@router.get("/", response_model=APIResponse[List[CaseResponse]])
async def list_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    cases = await CaseService.get_cases(
        db=db, skip=skip, limit=limit, status_filter=status_filter
    )
    return APIResponse(
        success=True, data=[CaseResponse.model_validate(c) for c in cases]
    )


@router.get("/{case_id}", response_model=APIResponse[CaseResponse])
async def get_case(case_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    case = await CaseService.get_case_by_id(db=db, case_id=case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {case_id} not found",
        )
    return APIResponse(success=True, data=CaseResponse.model_validate(case))


@router.get("/{case_id}/similar", response_model=APIResponse[List[Dict[str, Any]]])
async def get_similar_cases(case_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    similar = await CaseService.get_similar_cases(db=db, case_id=case_id)
    return APIResponse(success=True, data=similar)


@router.patch("/{case_id}", response_model=APIResponse[CaseResponse])
async def update_case_details(
    case_id: uuid.UUID,
    case_update: CaseUpdate,
    db: AsyncSession = Depends(get_db),
):
    updated_case = await CaseService.update_case(
        db=db, case_id=case_id, case_update=case_update
    )
    if not updated_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {case_id} not found",
        )
    return APIResponse(success=True, data=CaseResponse.model_validate(updated_case))


@router.delete("/{case_id}", response_model=APIResponse[dict])
async def remove_case(case_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    deleted = await CaseService.delete_case(db=db, case_id=case_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {case_id} not found",
        )
    return APIResponse(success=True, data={"message": "Case deleted successfully"})
