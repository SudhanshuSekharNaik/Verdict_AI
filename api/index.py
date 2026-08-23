"""
Vercel Python entrypoint.

Vercel scans `api/index.py` for a top-level `app` variable.
This module adds the repo root to sys.path then assigns `app`
as a direct local name so both static analysis and runtime resolve it.
"""
import sys
from pathlib import Path

# /var/task is the repo root inside Vercel's Lambda sandbox
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.main import app as app  # explicit `app = ...` pattern for static scanners  # noqa: F401, E402
