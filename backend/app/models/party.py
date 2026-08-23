import enum
import uuid
from typing import Optional
from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import PortableJSON, TimeStampedUUIDModel


class PartyRoleEnum(str, enum.Enum):
    PLAINTIFF = "PLAINTIFF"
    DEFENDANT = "DEFENDANT"
    WITNESS = "WITNESS"
    EXPERT = "EXPERT"
    COUNSEL = "COUNSEL"


class Party(TimeStampedUUIDModel):
    __tablename__ = "parties"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[PartyRoleEnum] = mapped_column(
        Enum(PartyRoleEnum), default=PartyRoleEnum.PLAINTIFF, nullable=False
    )
    contact_info: Mapped[dict] = mapped_column(PortableJSON, default=dict)
    statement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    case = relationship("Case", back_populates="parties")
