import enum
import uuid
from typing import List, Optional

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import PortableJSON, TimeStampedUUIDModel


class HearingSideEnum(str, enum.Enum):
    PLAINTIFF = "PLAINTIFF"
    DEFENCE = "DEFENCE"
    JUDGE = "JUDGE"
    SYSTEM = "SYSTEM"


class HearingMessageTypeEnum(str, enum.Enum):
    ARGUMENT = "ARGUMENT"
    QUESTION = "QUESTION"
    ANSWER = "ANSWER"
    REBUTTAL = "REBUTTAL"
    RULING = "RULING"
    NOTE = "NOTE"
    OPENING = "OPENING"
    CROSS_EXAM = "CROSS_EXAM"


class HearingMessage(TimeStampedUUIDModel):
    __tablename__ = "hearing_messages"
    __table_args__ = (
        UniqueConstraint("turn_id", name="uq_hearing_message_turn_id"),
        {"extend_existing": True},
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False
    )
    stage: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    turn_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    side: Mapped[HearingSideEnum] = mapped_column(
        Enum(HearingSideEnum), nullable=False
    )
    message_type: Mapped[HearingMessageTypeEnum] = mapped_column(
        Enum(HearingMessageTypeEnum), default=HearingMessageTypeEnum.ARGUMENT, nullable=False
    )
    content_json: Mapped[dict] = mapped_column(PortableJSON, default=dict)
    evidence_refs: Mapped[list] = mapped_column(PortableJSON, default=list)
    authority_refs: Mapped[list] = mapped_column(PortableJSON, default=list)
    parent_turn_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
