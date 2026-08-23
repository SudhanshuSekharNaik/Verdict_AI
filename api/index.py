# Vercel entrypoint — re-exports the FastAPI app from its actual location.
# Vercel's Python runtime always looks here first (api/index.py → variable: app).
# PYTHONPATH is set to the repo root via vercel.json so the import resolves.
import sys
from pathlib import Path

# Ensure repo root is on sys.path so `backend.app.main` resolves
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.app.main import app  # noqa: E402 — re-export for Vercel

__all__ = ["app"]
