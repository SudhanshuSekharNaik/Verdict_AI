import enum
import random
import string
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import PortableJSON, TimeStampedUUIDModel


def generate_case_number() -> str:
    """Generates unique court case numbers (e.g., AAD-2026-X89K)."""
    random_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"AAD-{datetime.utcnow().year}-{random_str}"


class CaseStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    FILED = "FILED"
    PREPARATION = "PREPARATION"
    READY_FOR_HEARING = "READY_FOR_HEARING"
    HEARING = "HEARING"
    JUDGMENT_PENDING = "JUDGMENT_PENDING"
    CLOSED = "CLOSED"


class CaseTypeEnum(str, enum.Enum):
    CIVIL = "CIVIL"
    CRIMINAL = "CRIMINAL"
    CONSUMER = "CONSUMER"
    EMPLOYMENT = "EMPLOYMENT"
    PROPERTY = "PROPERTY"
    CONTRACT = "CONTRACT"
    FAMILY = "FAMILY"
    FINANCIAL = "FINANCIAL"
    TECHNOLOGY = "TECHNOLOGY"
    OTHER = "OTHER"


class Case(TimeStampedUUIDModel):
    __tablename__ = "cases"

    case_number: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, default=generate_case_number, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    case_type: Mapped[str] = mapped_column(String(64), default="CIVIL", index=True, nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CaseStatusEnum] = mapped_column(
        Enum(CaseStatusEnum), default=CaseStatusEnum.DRAFT, nullable=False, index=True
    )
    
    plaintiff_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    defendant_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(PortableJSON, default=dict)

    # Relationships
    parties = relationship("Party", back_populates="case", cascade="all, delete-orphan")
    evidence_list = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="case", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="case", cascade="all, delete-orphan")
    arguments = relationship("Argument", back_populates="case", cascade="all, delete-orphan")
    courtroom_rounds = relationship("CourtroomRound", back_populates="case", cascade="all, delete-orphan")
    judgment = relationship("Judgment", back_populates="case", uselist=False, cascade="all, delete-orphan")