from fastapi import APIRouter

from app.api.v1.endpoints import (
    agents,
    auth,
    cases,
    court,
    courtroom,
    evidence,
    hearing,
    ml,
    research,
    evaluation,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Security"])
api_router.include_router(cases.router, prefix="/cases", tags=["Case Management"])
api_router.include_router(evidence.router, tags=["Evidence Vault & Timeline"])
api_router.include_router(ml.router, prefix="/ml", tags=["Hugging Face ML"])
api_router.include_router(research.router, prefix="/research", tags=["Legal RAG & Research"])
api_router.include_router(court.router, prefix="/court", tags=["Court Intelligence"])
api_router.include_router(agents.router, prefix="/agents", tags=["AI Agents"])
api_router.include_router(courtroom.router, prefix="/courtroom", tags=["Courtroom Orchestration"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["Evaluation & Benchmarks"])
api_router.include_router(hearing.router, prefix="/hearing", tags=["Adversarial Hearing"])
