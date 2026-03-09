import uuid
from sqlalchemy import (
    String, ForeignKey, Numeric, Boolean, Date, Index,
    Enum as SAEnum, Computed,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base, TimestampMixin, SoftDeleteMixin

INVOICE_VALIDATION_STATUSES = ("PENDING", "VALID", "INVALID", "APPROVED", "REJECTED")


class CanonicalInvoice(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "canonical_invoices"
    __table_args__ = (
        Index("idx_invoices_tenant_date", "tenant_id", "invoice_date"),
        Index("idx_invoices_duplicate_hash", "tenant_id", "duplicate_hash", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    document_type: Mapped[str] = mapped_column(
        SAEnum("invoice", "credit_note", "debit_note", "receipt", "bill_of_supply", name="invoice_doc_type_enum", create_constraint=False, native_enum=True),
        default="invoice",
    )
    transaction_nature: Mapped[str | None] = mapped_column(
        String(30), nullable=True, default=None,
        comment="purchase | sale | bill_of_supply",
    )

    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_date: Mapped[str] = mapped_column(Date, nullable=False)

    vendor_name: Mapped[str | None] = mapped_column(String(255))
    vendor_gstin: Mapped[str | None] = mapped_column(String(15))
    vendor_state_code: Mapped[str | None] = mapped_column(String(2))
    buyer_name: Mapped[str | None] = mapped_column(String(255))
    buyer_gstin: Mapped[str | None] = mapped_column(String(15))
    buyer_state_code: Mapped[str | None] = mapped_column(String(2))
    place_of_supply: Mapped[str | None] = mapped_column(String(2))

    subtotal: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    cgst: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    sgst: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    igst: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    cess: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)

    line_items: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)

    original_invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_invoices.id"), nullable=True
    )
    original_invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    duplicate_of: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_invoices.id"), nullable=True
    )
    duplicate_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    validation_status: Mapped[str] = mapped_column(
        SAEnum(*INVOICE_VALIDATION_STATUSES, name="invoice_validation_status_enum"),
        default="PENDING",
    )

    document = relationship("Document", back_populates="canonical_invoice")
