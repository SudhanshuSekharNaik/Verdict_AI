"""
Root-level main.py — Render entry point.

Render dashboard runs: uvicorn main:app --host 0.0.0.0 --port $PORT
from the repo root (this file). We load backend/main.py by its absolute
file path to avoid the circular import that happens with 'import main'.
"""
import importlib.util
import os
import sys

_root = os.path.dirname(os.path.abspath(__file__))
_backend = os.path.join(_root, "backend")

# Add backend/ to sys.path so all relative imports inside backend resolve
if _backend not in sys.path:
    sys.path.insert(0, _backend)

# Load backend/main.py by file path, registered as "backend_main"
# This avoids any name collision with THIS file (also called "main")
_spec = importlib.util.spec_from_file_location(
    "backend_main",
    os.path.join(_backend, "main.py"),
)
_module = importlib.util.module_from_spec(_spec)
sys.modules["backend_main"] = _module
_spec.loader.exec_module(_module)

# Re-export the FastAPI app so uvicorn finds main:app
app = _module.app
