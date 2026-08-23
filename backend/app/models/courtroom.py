import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import PortableJSON, TimeStampedUUIDModel


class CourtroomStageEnum(str, enum.Enum):
    CASE_OPENED = "CASE_OPENED"
    CASE_PREPARATION = "CASE_PREPARATION"
    EVIDENCE_SUBMISSION = "EVIDENCE_SUBMISSION"
    OPENING_ARGUMENTS = "OPENING_ARGUMENTS"
    PLAINTIFF_ARGUMENT = "PLAINTIFF_ARGUMENT"
    DEFENCE_ARGUMENT = "DEFENCE_ARGUMENT"
    CROSS_EXAMINATION = "CROSS_EXAMINATION"
    PLAINTIFF_REBUTTAL = "PLAINTIFF_REBUTTAL"
    DEFENCE_REBUTTAL = "DEFENCE_REBUTTAL"
    FINAL_SUBMISSIONS = "FINAL_SUBMISSIONS"
    JUDGE_QUESTIONS = "JUDGE_QUESTIONS"
    JUDGE_DELIBERATION = "JUDGE_DELIBERATION"
    VERDICT = "VERDICT"
    CASE_CLOSED = "CASE_CLOSED"


class CourtroomRound(TimeStampedUUIDModel):
    __tablename__ = "courtroom_rounds"
    __table_args__ = (
        {"extend_existing": True},
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False
    )
    round_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    stage: Mapped[CourtroomStageEnum] = mapped_column(
        Enum(CourtroomStageEnum), default=CourtroomStageEnum.CASE_OPENED, nullable=False
    )
    active_speaker: Mapped[str] = mapped_column(String(64), default="PLAINTIFF_AI", nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(PortableJSON, default=dict)

    case = relationship("Case", back_populates="courtroom_rounds")
    events = relationship("CourtroomEvent", back_populates="round", cascade="all, delete-orphan")


class CourtroomEvent(TimeStampedUUIDModel):
    __tablename__ = "courtroom_events"

    round_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courtroom_rounds.id", ondelete="CASCADE"), index=True, nullable=False
    )
    speaker: Mapped[str] = mapped_column(String(64), nullable=False)  # PLAINTIFF_AI, DEFENCE_AI, MY_LORD, JUDGE_ASSISTANT
    event_type: Mapped[str] = mapped_column(String(64), default="ARGUMENT", nullable=False)  # ARGUMENT, ATTACK, REBUTTAL, QUESTION, ANSWER, RULING
    content: Mapped[str] = mapped_column(Text, nullable=False)
    references: Mapped[list] = mapped_column(PortableJSON, default=list)  # evidence_ids, citation_ids
    metadata_json: Mapped[dict] = mapped_column(PortableJSON, default=dict)

    round = relationship("CourtroomRound", back_populates="events")


class JudgeNote(TimeStampedUUIDModel):
    __tablename__ = "judge_notes"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False
    )
    judge_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    note_type: Mapped[str] = mapped_column(String(64), default="OBSERVATION", nullable=False)  # OBSERVATION, DOUBT, CONTRADICTION_FLAG, QUESTION_DRAFT
    content: Mapped[str] = mapped_column(Text, nullable=False)
    linked_evidence_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True
    )
