import json
import os
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Aadalat AI"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "aadalat-ai-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database: Supports async SQLite for local/test and PostgreSQL + pgvector
    # Default uses a path relative to the project root so it works on any OS
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{(Path(__file__).resolve().parents[2] / 'aadalat.db').as_posix()}"
    )

    # ML & RAG Configuration
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    NER_MODEL_NAME: str = "dslim/bert-base-NER"
    CLASSIFIER_MODEL_NAME: str = "facebook/bart-large-mnli"
    NLI_MODEL_NAME: str = "roberta-large-mnli"

    # Storage paths
    BASE_DIR: Path = Path(__file__).resolve().parents[2]
    UPLOAD_DIR: Path = BASE_DIR / "data" / "raw"
    PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    CASES_DIR: Path = BASE_DIR / "cases"

    # CORS — accepts a JSON array string, a comma-separated string, or a plain "*"
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if v == "*":
                return ["*"]
            # Try JSON array first: ["http://...","http://..."]
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Comma-separated fallback
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()

# Ensure directories exist (skip on read-only filesystems like Render)
try:
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    pass
