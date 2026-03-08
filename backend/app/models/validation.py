import uuid
from sqlalchemy import ForeignKey, Integer, String, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from sqlalchemy import DateTime, func

from app.database import Base


class Validation(Base):
    """Immutable validation record — re-validation creates a new row."""
    __tablename__ = "validations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    extraction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("extractions.id"), nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    field_results: Mapped[dict] = mapped_column(JSONB, nullable=False)
    overall_status: Mapped[str] = mapped_column(
        SAEnum("pass", "fail", "warn", name="validation_status_enum"), nullable=False
    )
    warnings_count: Mapped[int] = mapped_column(Integer, default=0)
    errors_count: Mapped[int] = mapped_column(Integer, default=0)
    validated_by: Mapped[str] = mapped_column(String(50), default="bedrock")
    ai_suggestions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document = relationship("Document", back_populates="validations")
    extraction = relationship("Extraction")
