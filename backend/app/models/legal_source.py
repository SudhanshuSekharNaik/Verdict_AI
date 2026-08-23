import uuid
from typing import List, Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import PortableJSON, TimeStampedUUIDModel


class LegalSource(TimeStampedUUIDModel):
    __tablename__ = "legal_sources"

    citation: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    court: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    jurisdiction: Mapped[str] = mapped_column(String(128), default="India", nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), default="PRECEDENT", nullable=False)  # PRECEDENT, STATUTE, REGULATION
    statute_section: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provenance_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(PortableJSON, default=dict)

    chunks = relationship("LegalChunk", back_populates="source", cascade="all, delete-orphan")


class LegalChunk(TimeStampedUUIDModel):
    __tablename__ = "legal_chunks"

    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("legal_sources.id", ondelete="CASCADE"), index=True, nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    section_type: Mapped[str] = mapped_column(String(64), default="BODY", nullable=False)  # FACTS, ISSUES, RATIO, ORDER
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list] = mapped_column(PortableJSON, default=list, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(PortableJSON, default=dict)

    source = relationship("LegalSource", back_populates="chunks")
