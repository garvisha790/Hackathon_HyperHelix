import uuid
from sqlalchemy import String, Integer, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base, TimestampMixin


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    gstin: Mapped[str | None] = mapped_column(String(15), nullable=True)
    pan: Mapped[str | None] = mapped_column(String(10), nullable=True)
    state_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    business_type: Mapped[str | None] = mapped_column(
        SAEnum("service", "retail", "manufacturing", "trading", "professional", name="business_type_enum"),
        nullable=True,
    )
    return_frequency: Mapped[str] = mapped_column(
        SAEnum("monthly", "quarterly", name="return_frequency_enum"), default="quarterly"
    )
    fy_start_month: Mapped[int] = mapped_column(Integer, default=4)
    tax_regime: Mapped[str] = mapped_column(
        SAEnum("new", "old", name="tax_regime_enum"), default="new"
    )
    retention_days: Mapped[int] = mapped_column(Integer, default=2555)

    users = relationship("User", back_populates="tenant", lazy="selectin")
    documents = relationship("Document", back_populates="tenant", lazy="noload")
