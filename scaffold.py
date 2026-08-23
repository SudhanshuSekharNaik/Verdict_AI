import os
from pathlib import Path

def create_aadalat_structure():
    # List of all directories to create
    directories = [
        Path("backend/app/api/v1/endpoints"),
        Path("backend/app/database"),
        Path("backend/app/models"),
        Path("backend/app/schemas"),
        Path("backend/app/services"),
        Path("backend/app/security"),
        Path("backend/app/workers"),
        Path("backend/alembic"),
        Path("backend/tests"),
        Path("agents"),
        Path("rag"),
        Path("ml/ner"),
        Path("ml/classification"),
        Path("ml/nli"),
        Path("ml/similarity"),
        Path("ml/training"),
        Path("ml/evaluation"),
        Path("document_ai"),
        Path("court_data/connectors"),
        Path("courtroom"),
        Path("evaluation"),
        Path("frontend/app/dashboard"),
        Path("frontend/app/court-intelligence"),
        Path("frontend/app/agents"),
        Path("frontend/app/evaluation"),
        Path("frontend/app/cases/[id]/evidence"),
        Path("frontend/app/cases/[id]/timeline"),
        Path("frontend/app/cases/[id]/research"),
        Path("frontend/app/cases/[id]/analysis"),
        Path("frontend/app/cases/[id]/courtroom"),
        Path("frontend/app/cases/[id]/judgment"),
        Path("frontend/app/cases/[id]/report"),
        Path("frontend/components/ui"),
        Path("frontend/components/courtroom"),
        Path("frontend/components/evidence"),
        Path("frontend/components/judge"),
        Path("frontend/hooks"),
        Path("frontend/lib"),
        Path("frontend/types"),
        Path("frontend/tests"),
        Path("data/raw"),
        Path("data/processed"),
        Path("docs"),
        Path("scripts"),
        Path("docker"),
    ]

    # Create directories
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        # Create __init__.py for Python packages
        if any(pkg in str(directory) for pkg in ["backend/app", "agents", "rag", "ml", "document_ai", "court_data", "courtroom", "evaluation"]):
            (directory / "__init__.py").touch(exist_ok=True)

    # 5 Demo cases setup
    demo_cases = [
        "case_001_security_deposit",
        "case_002_used_car",
        "case_003_employment",
        "case_004_online_product",
        "case_005_payment",
    ]
    for case in demo_cases:
        case_dir = Path(f"cases/{case}")
        (case_dir / "plaintiff/evidence").mkdir(parents=True, exist_ok=True)
        (case_dir / "defence/evidence").mkdir(parents=True, exist_ok=True)
        (case_dir / "legal_context").mkdir(parents=True, exist_ok=True)
        (case_dir / "case_metadata.json").touch(exist_ok=True)
        (case_dir / "ground_truth.json").touch(exist_ok=True)
        (case_dir / "plaintiff/statement.md").touch(exist_ok=True)
        (case_dir / "defence/statement.md").touch(exist_ok=True)

    # Key project files
    files = [
        Path("backend/Dockerfile"),
        Path("backend/requirements.txt"),
        Path("frontend/Dockerfile"),
        Path("frontend/package.json"),
        Path(".env.example"),
        Path(".gitignore"),
        Path("docker-compose.yml"),
        Path("README.md"),
        Path("docs/ARCHITECTURE.md"),
        Path("docs/API.md"),
        Path("docs/DATABASE.md"),
        Path("docs/AGENTS.md"),
        Path("docs/RAG.md"),
        Path("docs/ML.md"),
        Path("docs/COURT_DATA.md"),
        Path("docs/DEPLOYMENT.md"),
    ]
    for file in files:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.touch(exist_ok=True)

    print("✅ Successfully scaffolded AADALAT AI workspace!")

if __name__ == "__main__":
    create_aadalat_structure()