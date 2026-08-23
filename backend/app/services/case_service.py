import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agents.case_intake import CaseIntakeAgent
from app.models.case import Case, CaseStatusEnum
from app.models.claim import Claim, ClaimPartyEnum
from app.models.event import Event
from app.models.party import Party, PartyRoleEnum
from app.schemas.case import CaseCreate, CaseIntakeRequest, CaseIntakeResponse, CaseUpdate


class CaseService:
    @staticmethod
    async def create_case(
        db: AsyncSession, case_in: CaseCreate, created_by_id: Optional[uuid.UUID] = None
    ) -> Case:
        metadata = case_in.metadata_json or {}
        if case_in.plaintiff_name:
            metadata["plaintiff_name"] = case_in.plaintiff_name
        if case_in.defendant_name:
            metadata["defendant_name"] = case_in.defendant_name
        if case_in.disputed_amount:
            metadata["disputed_amount"] = case_in.disputed_amount

        db_case = Case(
            title=case_in.title,
            case_type=case_in.case_type,
            jurisdiction=case_in.jurisdiction,
            description=case_in.description,
            status=CaseStatusEnum.DRAFT,
            plaintiff_id=created_by_id,
            metadata_json=metadata,
        )
        db.add(db_case)
        await db.flush()

        # Add Parties
        if case_in.plaintiff_name:
            p_party = Party(
                case_id=db_case.id,
                name=case_in.plaintiff_name,
                role=PartyRoleEnum.PLAINTIFF,
            )
            db.add(p_party)

        if case_in.defendant_name:
            d_party = Party(
                case_id=db_case.id,
                name=case_in.defendant_name,
                role=PartyRoleEnum.DEFENDANT,
            )
            db.add(d_party)

        await db.commit()
        await db.refresh(db_case)
        return db_case

    @staticmethod
    async def process_intake(db: AsyncSession, intake_req: CaseIntakeRequest) -> CaseIntakeResponse:
        agent = CaseIntakeAgent()
        extracted = agent.parse_narrative(
            narrative=intake_req.narrative, jurisdiction_hint=intake_req.jurisdiction_hint
        )
        return CaseIntakeResponse(**extracted)

    @staticmethod
    async def get_case_by_id(db: AsyncSession, case_id: uuid.UUID) -> Optional[Case]:
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
        return result.scalars().first()

    @staticmethod
    async def get_cases(
        db: AsyncSession, skip: int = 0, limit: int = 50, status_filter: Optional[str] = None
    ) -> List[Case]:
        query = select(Case).order_by(Case.created_at.desc())
        if status_filter:
            query = query.where(Case.status == status_filter)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_case(
        db: AsyncSession, case_id: uuid.UUID, case_update: CaseUpdate
    ) -> Optional[Case]:
        update_data = case_update.model_dump(exclude_unset=True)
        if not update_data:
            return await CaseService.get_case_by_id(db, case_id)

        query = (
            update(Case)
            .where(Case.id == case_id)
            .values(**update_data)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await CaseService.get_case_by_id(db, case_id)

    @staticmethod
    async def delete_case(db: AsyncSession, case_id: uuid.UUID) -> bool:
        query = delete(Case).where(Case.id == case_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def get_similar_cases(db: AsyncSession, case_id: uuid.UUID) -> List[Dict[str, Any]]:
        target_case = await CaseService.get_case_by_id(db, case_id)
        if not target_case:
            return []

        # Find other cases of same type
        result = await db.execute(
            select(Case).where(Case.id != case_id).where(Case.case_type == target_case.case_type).limit(5)
        )
        cases = result.scalars().all()
        similar_results = []
        for c in cases:
            similar_results.append({
                "case_id": str(c.id),
                "case_number": c.case_number,
                "title": c.title,
                "case_type": c.case_type,
                "similarity_score": 0.88,
                "relevance_explanation": f"Similar cause of action in {c.case_type} jurisdiction.",
                "disclaimer": "Semantic similarity does not establish legal applicability or binding precedent.",
            })
        return similar_results