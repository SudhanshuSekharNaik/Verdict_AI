import uuid
from typing import List, Optional

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import PortableJSON, TimeStampedUUIDModel


class EvidenceChunk(TimeStampedUUIDModel):
    __tablename__ = "evidence_chunks"

    evidence_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence.id", ondelete="CASCADE"), index=True, nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list] = mapped_column(PortableJSON, default=list, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(PortableJSON, default=dict)

    evidence = relationship("Evidence", back_populates="chunks")
