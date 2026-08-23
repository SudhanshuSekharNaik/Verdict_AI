import enum
import uuid
from typing import Optional

from sqlalchemy import Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import PortableJSON, TimeStampedUUIDModel


class GroundingStatusEnum(str, enum.Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONFLICTING = "CONFLICTING"


class ClaimPartyEnum(str, enum.Enum):
    PLAINTIFF = "PLAINTIFF"
    DEFENDANT = "DEFENDANT"


class Claim(TimeStampedUUIDModel):
    __tablename__ = "claims"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False
    )
    party: Mapped[ClaimPartyEnum] = mapped_column(
        Enum(ClaimPartyEnum), default=ClaimPartyEnum.PLAINTIFF, nullable=False
    )
    claim_type: Mapped[str] = mapped_column(String(64), default="FACTUAL", nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grounding_status: Mapped[GroundingStatusEnum] = mapped_column(
        Enum(GroundingStatusEnum), default=GroundingStatusEnum.UNSUPPORTED, nullable=False
    )
    grounding_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    supporting_evidence_ids: Mapped[list] = mapped_column(PortableJSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(PortableJSON, default=dict)

    case = relationship("Case", back_populates="claims")
