from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from services import law_service

router = APIRouter(prefix="/api/law", tags=["law"])


@router.get("/search")
def search_indian_laws(
    q: Optional[str] = Query("", description="Search term for section, offence, article or legal concept"),
    source: Optional[str] = Query(None, description="Filter by source: BNS, BNSS, BSA, Constitution, IPC"),
    type: Optional[str] = Query(None, description="Filter by type: Section, Article, Chapter"),
):
    """Searches official Indian legal source database with source and type filtering."""
    results = law_service.search_laws(query=q or "", source_filter=source, type_filter=type)
    return {
        "count": len(results),
        "query": q,
        "source_filter": source,
        "results": results,
    }


@router.get("/provision/{provision_id}")
def get_provision(provision_id: str):
    """Fetches full statutory text, plain explanation, and official source metadata for a provision."""
    prov = law_service.get_provision_by_id(provision_id)
    if not prov:
        raise HTTPException(status_code=404, detail=f"Legal provision '{provision_id}' not found.")
    return prov
