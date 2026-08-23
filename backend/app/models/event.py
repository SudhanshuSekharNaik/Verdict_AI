import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import PortableJSON, TimeStampedUUIDModel


class Event(TimeStampedUUIDModel):
    __tablename__ = "events"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False
    )
    event_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    date_raw_str: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    party: Mapped[str] = mapped_column(String(64), default="UNDISPUTED", nullable=False)
    source_evidence_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True
    )
    conflict_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    conflict_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(PortableJSON, default=dict)

    case = relationship("Case", back_populates="events")
    source_evidence = relationship("Evidence")
