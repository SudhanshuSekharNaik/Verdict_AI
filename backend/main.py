import os
import sys

# Ensure backend directory is in sys.path for direct or module execution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import cases, law
from services.database import init_db

app = FastAPI(
    title="Nyay Manch / Courtroom Arena API",
    description="Turn-based multi-agent legal courtroom simulator and Indian Law reasoning platform — "
    "prosecution & defense agents argue sequentially turn-by-turn with strict fact-grounding, "
    "Indian Law statutory intelligence (BNS/BNSS/BSA), RAG knowledge grounding, "
    "and an impartial presiding judge agent.",
    version="2.5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router)
app.include_router(law.router)


@app.on_event("startup")
def on_startup():
    init_db()


# Mount frontend static files
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    # Also mount at root if no conflicting API route
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static_root")
else:
    @app.get("/")
    def root():
        return {
            "status": "ok",
            "system": "Nyay Manch Courtroom Simulator",
            "version": "2.5.0",
            "message": "API is running. See /docs for the interactive API explorer.",
        }

