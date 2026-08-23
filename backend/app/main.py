import logging
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import settings
from app.database.session import engine
from app.models.base import Base
from app.schemas.response import APIResponse, ErrorDetail

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler — replaces deprecated @app.on_event."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified successfully.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("DB init warning (non-fatal): %s", exc)
    yield
    # Shutdown: dispose engine connections
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Evidence-Grounded Multi-Agent Courtroom Simulation & Legal Intelligence Platform",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — allow all origins if "*" is present, otherwise use the list
_cors_origins = settings.BACKEND_CORS_ORIGINS
_allow_all = "*" in _cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all else _cors_origins,
    allow_credentials=not _allow_all,  # credentials can't be used with wildcard origin
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health", response_model=APIResponse)
async def health_check():
    return APIResponse(
        success=True,
        data={
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": "1.0.0",
            "tagline": "AI argues. Evidence speaks. My Lord decides.",
        },
    )


@app.get("/api/version", response_model=APIResponse)
async def api_version():
    return APIResponse(
        success=True,
        data={
            "version": "1.0.0",
            "capabilities": [
                "Multi-Agent Courtroom Simulation (LangGraph)",
                "Structure-Aware Legal RAG (Hybrid BM25 + Vector)",
                "Hugging Face ML Registry (NER, BART, RoBERTa-MNLI)",
                "Evidence Vault & NetworkX Knowledge Graph",
                "Chronological Timeline with Conflict Detection",
                "Court Intelligence & Permitted Ingestion",
                "Human Judge Deliberation & Verdict Entry",
            ],
        },
    )


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            error=ErrorDetail(code="INTERNAL_SERVER_ERROR", message=str(exc)),
            request_id=getattr(request.state, "request_id", None),
        ).model_dump(),
    )
