import uuid
from sqlalchemy import String, ForeignKey, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base, TimestampMixin, SoftDeleteMixin

DOCUMENT_STATUSES = ("UPLOADED", "PROCESSING", "EXTRACTED", "VALIDATED", "FAILED", "DONE")
DOCUMENT_TYPES = ("invoice", "credit_note", "debit_note", "receipt")


class Document(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "documents"
    __table_args__ = (
        Index("idx_documents_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False)
    s3_version_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    document_type: Mapped[str] = mapped_column(
        SAEnum(*DOCUMENT_TYPES, name="document_type_enum"), default="invoice"
    )
    status: Mapped[str] = mapped_column(
        SAEnum(*DOCUMENT_STATUSES, name="document_status_enum"), default="UPLOADED"
    )
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    tenant = relationship("Tenant", back_populates="documents")
    uploader = relationship("User", lazy="selectin")
    extraction = relationship("Extraction", back_populates="document", uselist=False, lazy="selectin")
    validations = relationship("Validation", back_populates="document", lazy="noload")
    canonical_invoice = relationship("CanonicalInvoice", back_populates="document", uselist=False, lazy="noload")
