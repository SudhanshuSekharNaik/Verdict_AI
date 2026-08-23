import enum
import uuid
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import PortableJSON, TimeStampedUUIDModel


class VerdictEnum(str, enum.Enum):
    PLAINTIFF_SUCCEEDS = "PLAINTIFF_SUCCEEDS"
    DEFENDANT_SUCCEEDS = "DEFENDANT_SUCCEEDS"
    PARTIALLY_SUCCEEDS = "PARTIALLY_SUCCEEDS"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class Judgment(TimeStampedUUIDModel):
    __tablename__ = "judgments"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    judge_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verdict: Mapped[VerdictEnum] = mapped_column(
        Enum(VerdictEnum), default=VerdictEnum.PLAINTIFF_SUCCEEDS, nullable=False
    )
    relief_awarded: Mapped[str] = mapped_column(Text, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_relied_on: Mapped[list] = mapped_column(PortableJSON, default=list)
    authorities_relied_on: Mapped[list] = mapped_column(PortableJSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(PortableJSON, default=dict)

    case = relationship("Case", back_populates="judgment")
