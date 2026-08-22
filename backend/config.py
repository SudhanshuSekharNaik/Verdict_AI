import os
from pathlib import Path
from dotenv import load_dotenv

# Load from backend/.env or root .env
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
ARGUMENT_ROUNDS = int(os.getenv("ARGUMENT_ROUNDS", "2"))

if not GROQ_API_KEY:
    print(
        "[WARN] GROQ_API_KEY is not set. Copy .env.example to .env and add your key "
        "from https://console.groq.com/keys before running a case."
    )
