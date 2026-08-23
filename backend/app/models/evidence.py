import enum
import uuid
from typing import List, Optional

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import PortableJSON, TimeStampedUUIDModel


class EvidenceStatusEnum(str, enum.Enum):
    INDEXED = "INDEXED"
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    CONFLICTING = "CONFLICTING"
    FLAGGED = "FLAGGED"


class EvidencePartyEnum(str, enum.Enum):
    PLAINTIFF = "PLAINTIFF"
    DEFENDANT = "DEFENDANT"
    COURT = "COURT"


class Evidence(TimeStampedUUIDModel):
    __tablename__ = "evidence"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False
    )
    party: Mapped[EvidencePartyEnum] = mapped_column(
        Enum(EvidencePartyEnum), default=EvidencePartyEnum.PLAINTIFF, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(128), default="UPLOAD", nullable=False)
    verification_status: Mapped[EvidenceStatusEnum] = mapped_column(
        Enum(EvidenceStatusEnum), default=EvidenceStatusEnum.INDEXED, nullable=False
    )
    file_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    extraction_metadata: Mapped[dict] = mapped_column(PortableJSON, default=dict)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    case = relationship("Case", back_populates="evidence_list")
    chunks = relationship("EvidenceChunk", back_populates="evidence", cascade="all, delete-orphan")
