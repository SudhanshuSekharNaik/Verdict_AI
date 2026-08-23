from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agents.research_agent import LegalResearchAgent
from app.database.session import get_db
from app.schemas.response import APIResponse
from rag.citation_validator import CitationValidator
from rag.retrieval import HybridRetriever

router = APIRouter()


class SearchQueryRequest(BaseModel):
    query: str = Field(..., example="security deposit deduction damages burden of proof")
    jurisdiction: Optional[str] = Field(None, example="India")
    court: Optional[str] = Field(None)
    top_k: int = Field(5, ge=1, le=20)


class CitationValidationRequest(BaseModel):
    citation: str = Field(..., example="2018 SCC OnLine Del 11234")
    proposition: str = Field(..., example="Landlord cannot make deductions without itemized bills and move-out inspection.")


class ResearchQueryRequest(BaseModel):
    issue: str = Field(..., example="Unilateral deduction of tenancy deposit without joint inspection report")
    case_facts: str = Field(..., example="Tenant claims full refund, landlord produced delayed repair invoice.")
    jurisdiction: str = Field("India")


@router.post("/search", response_model=APIResponse[List[Dict[str, Any]]])
async def search_legal_knowledge(req: SearchQueryRequest, db: AsyncSession = Depends(get_db)):
    results = await HybridRetriever.retrieve(
        db=db,
        query=req.query,
        top_k=req.top_k,
        jurisdiction=req.jurisdiction,
        court=req.court,
    )
    return APIResponse(success=True, data=results)


@router.post("/validate-citation", response_model=APIResponse[Dict[str, Any]])
async def validate_citation(req: CitationValidationRequest, db: AsyncSession = Depends(get_db)):
    val_result = await CitationValidator.validate_citation(
        db=db, citation_str=req.citation, proposition=req.proposition
    )
    return APIResponse(success=True, data=val_result)


@router.post("/agent-query", response_model=APIResponse[Dict[str, Any]])
async def query_research_agent(req: ResearchQueryRequest, db: AsyncSession = Depends(get_db)):
    res_data = await LegalResearchAgent.research_issue(
        db=db, issue=req.issue, case_facts=req.case_facts, jurisdiction=req.jurisdiction
    )
    return APIResponse(success=True, data=res_data)
