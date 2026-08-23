from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.legal_source import LegalSource
from app.schemas.response import APIResponse
from court_data.connectors.public_archive import PublicArchiveConnector
from court_data.ingestion import CourtDataIngestionService
from court_data.parser import CourtDocumentParser

router = APIRouter()


class CourtSearchRequest(BaseModel):
    query: str = Field(..., example="tenancy security deposit damage")
    court: Optional[str] = None
    year: Optional[int] = None


class CourtImportRequest(BaseModel):
    title: str = Field(..., example="Anil Verma v. Sunita Rathi")
    citation: str = Field(..., example="2019 SCC OnLine Del 7891")
    court: str = Field(..., example="Delhi High Court")
    year: int = Field(2019)
    full_text: str = Field(..., example="RATIO: A landlord withholding tenant security deposit on ground of property degradation must demonstrate verifiable receipts.")
    provenance_url: str = Field(..., example="https://delhihighcourt.nic.in/judgments/7891")


class AnalyzeDocRequest(BaseModel):
    text: str = Field(..., example="IN THE HIGH COURT OF DELHI AT NEW DELHI...")


@router.post("/search", response_model=APIResponse[List[Dict[str, Any]]])
async def search_court_records(req: CourtSearchRequest):
    connector = PublicArchiveConnector()
    results = await connector.fetch_documents(search_query=req.query)
    return APIResponse(success=True, data=results)


@router.post("/documents/analyze", response_model=APIResponse[Dict[str, Any]])
async def analyze_court_text(req: AnalyzeDocRequest):
    analysis = CourtDocumentParser.analyze_court_document(req.text)
    return APIResponse(success=True, data=analysis)


@router.post("/documents/import", response_model=APIResponse[Dict[str, Any]], status_code=status.HTTP_201_CREATED)
async def import_court_document(req: CourtImportRequest, db: AsyncSession = Depends(get_db)):
    source = await CourtDataIngestionService.import_court_document(
        db=db,
        title=req.title,
        citation=req.citation,
        court=req.court,
        year=req.year,
        full_text=req.full_text,
        provenance_url=req.provenance_url,
    )
    return APIResponse(success=True, data={
        "id": str(source.id),
        "citation": source.citation,
        "title": source.title,
        "court": source.court,
        "message": "Court document successfully ingested and vector-indexed.",
    })
