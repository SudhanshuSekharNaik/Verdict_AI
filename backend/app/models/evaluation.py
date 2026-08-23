import uuid
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import PortableJSON, TimeStampedUUIDModel


class EvaluationResult(TimeStampedUUIDModel):
    __tablename__ = "evaluation_results"

    case_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("cases.id", ondelete="SET NULL"), nullable=True
    )
    metric_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    metric_category: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # NER, CLASSIFICATION, NLI, RETRIEVAL, GROUNDING, FAITHFULNESS
    score: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[dict] = mapped_column(PortableJSON, default=dict)
    model_version: Mapped[str] = mapped_column(String(128), default="1.0.0", nullable=False)


class AgentRunLog(TimeStampedUUIDModel):
    __tablename__ = "agent_runs"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), default="v1", nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, default=1)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    token_usage: Mapped[int] = mapped_column(Integer, default=0)
    tool_calls: Mapped[list] = mapped_column(PortableJSON, default=list)
    output: Mapped[str] = mapped_column(Text, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
