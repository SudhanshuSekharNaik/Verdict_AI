import enum
import uuid
from typing import List, Optional

from sqlalchemy import Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import PortableJSON, TimeStampedUUIDModel


class AttackTypeEnum(str, enum.Enum):
    DIRECT_ARGUMENT = "DIRECT_ARGUMENT"
    FACTUAL_CONTRADICTION = "FACTUAL_CONTRADICTION"
    EVIDENCE_WEAKNESS = "EVIDENCE_WEAKNESS"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    LEGAL_DISTINCTION = "LEGAL_DISTINCTION"
    TIMELINE_CONFLICT = "TIMELINE_CONFLICT"
    ALTERNATIVE_INTERPRETATION = "ALTERNATIVE_INTERPRETATION"
    SOURCE_RELIABILITY = "SOURCE_RELIABILITY"
    CAUSATION_CHALLENGE = "CAUSATION_CHALLENGE"
    QUANTUM_CHALLENGE = "QUANTUM_CHALLENGE"


class AgentRoleEnum(str, enum.Enum):
    PLAINTIFF_AGENT = "PLAINTIFF_AGENT"
    DEFENCE_AGENT = "DEFENCE_AGENT"
    JUDGE_ASSISTANT = "JUDGE_ASSISTANT"
    HUMAN_JUDGE = "HUMAN_JUDGE"


class Argument(TimeStampedUUIDModel):
    __tablename__ = "arguments"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False
    )
    round_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("courtroom_rounds.id", ondelete="SET NULL"), nullable=True
    )
    agent: Mapped[AgentRoleEnum] = mapped_column(
        Enum(AgentRoleEnum), default=AgentRoleEnum.PLAINTIFF_AGENT, nullable=False
    )
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    target_argument_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("arguments.id", ondelete="SET NULL"), nullable=True
    )
    attack_type: Mapped[AttackTypeEnum] = mapped_column(
        Enum(AttackTypeEnum), default=AttackTypeEnum.DIRECT_ARGUMENT, nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    evidence_ids: Mapped[list] = mapped_column(PortableJSON, default=list)
    citation_ids: Mapped[list] = mapped_column(PortableJSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(PortableJSON, default=dict)

    # Relationships
    case = relationship("Case", back_populates="arguments")
    target_argument = relationship("Argument", remote_side="Argument.id")
