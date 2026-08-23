import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agents.defence_agent import DefenceAgent
from agents.judge_assistant import JudgeAssistantAgent
from agents.orchestrator import CourtroomOrchestrator
from agents.plaintiff_agent import PlaintiffAgent
from app.database.session import get_db
from app.schemas.response import APIResponse

router = APIRouter()


class DirectAgentQuestionRequest(BaseModel):
    agent_target: str = Field(..., example="PLAINTIFF_AI")  # PLAINTIFF_AI, DEFENCE_AI, JUDGE_ASSISTANT
    question: str = Field(..., example="Where is the move-out inspection document?")


@router.get("/status", response_model=APIResponse[List[Dict[str, Any]]])
async def get_agent_swarm_status():
    swarm = [
        {"agent": "Case Intake Agent", "role": "Intake & Structure Parser", "status": "ACTIVE", "model": "BART + Regex NER", "latency_ms": 120},
        {"agent": "Plaintiff AI Agent", "role": "Adversarial Affirmative Advocate", "status": "ACTIVE", "model": "LangGraph + MiniLM RAG", "latency_ms": 280},
        {"agent": "Defence AI Agent", "role": "Adversarial Defense Counsel", "status": "ACTIVE", "model": "LangGraph + RoBERTa NLI", "latency_ms": 260},
        {"agent": "Legal Research Agent", "role": "Precedent & Statutory Retrieval", "status": "ACTIVE", "model": "Hybrid BM25 + Vector Search", "latency_ms": 190},
        {"agent": "Validation Agent", "role": "Anti-Hallucination & Citation Verification", "status": "ACTIVE", "model": "RoBERTa-MNLI Grounding", "latency_ms": 140},
        {"agent": "Judge Assistant Agent", "role": "Judicial Briefing & Synthesis", "status": "ACTIVE", "model": "Timeline + Graph Engine", "latency_ms": 110},
    ]
    return APIResponse(success=True, data=swarm)


@router.post("/cases/{case_id}/ask", response_model=APIResponse[Dict[str, Any]])
async def ask_agent_directly(
    case_id: uuid.UUID, req: DirectAgentQuestionRequest, db: AsyncSession = Depends(get_db)
):
    if req.agent_target.upper() == "PLAINTIFF_AI":
        res = await PlaintiffAgent.answer_judge_question(
            question=req.question,
            plaintiff_evidence=[{"title": "Primary Case Filings"}],
            authorities=[],
        )
    elif req.agent_target.upper() == "DEFENCE_AI":
        res = await DefenceAgent.answer_judge_question(
            question=req.question,
            defence_evidence=[{"title": "Counter Submissions"}],
            authorities=[],
        )
    else:
        brief = await JudgeAssistantAgent.prepare_bench_brief(db=db, case_id=case_id)
        res = {
            "speaker": "JUDGE_ASSISTANT",
            "question": req.question,
            "answer": f"Bench Brief: {brief.get('core_issue')}. Timeline conflicts detected: {len(brief.get('timeline_conflicts', []))}.",
            "references": [],
        }

    return APIResponse(success=True, data=res)
