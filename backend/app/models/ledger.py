import uuid
from sqlalchemy import (
    String, ForeignKey, Numeric, Boolean, Integer, Date, Text, Index,
    Enum as SAEnum, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from sqlalchemy import DateTime, func

from app.database import Base, TimestampMixin


class ChartOfAccounts(Base):
    __tablename__ = "chart_of_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(
        SAEnum("asset", "liability", "equity", "revenue", "expense", name="account_type_enum"),
        nullable=False,
    )
    tally_group: Mapped[str | None] = mapped_column(String(100), nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=True
    )
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    is_cash_or_bank: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    children = relationship("ChartOfAccounts", back_populates="parent", lazy="selectin")
    parent = relationship("ChartOfAccounts", back_populates="children", remote_side=[id], lazy="noload")


class LedgerTransaction(Base, TimestampMixin):
    __tablename__ = "ledger_transactions"
    __table_args__ = (
        Index("idx_ledger_tenant_date", "tenant_id", "transaction_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    canonical_invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_invoices.id"), nullable=True
    )
    transaction_date: Mapped[str] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        SAEnum("AUTO_POSTED", "NEEDS_REVIEW", "CORRECTED", "REVERSED", name="txn_status_enum"),
        default="AUTO_POSTED",
    )
    reverses_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ledger_transactions.id"), nullable=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1)
    assigned_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category_confidence: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    category_method: Mapped[str | None] = mapped_column(
        SAEnum("rule", "bedrock", "manual", name="category_method_enum"), default="rule"
    )

    journal_lines = relationship("JournalLine", back_populates="transaction", lazy="selectin", cascade="all, delete-orphan")
    corrections = relationship("Correction", back_populates="transaction", lazy="noload")


class JournalLine(Base):
    __tablename__ = "journal_lines"
    __table_args__ = (
        CheckConstraint("debit >= 0", name="ck_debit_positive"),
        CheckConstraint("credit >= 0", name="ck_credit_positive"),
        Index("idx_journal_transaction", "transaction_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ledger_transactions.id"), nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=False
    )
    debit: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    credit: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    transaction = relationship("LedgerTransaction", back_populates="journal_lines")
    account = relationship("ChartOfAccounts", lazy="selectin")


class Correction(Base):
    __tablename__ = "corrections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ledger_transactions.id"), nullable=False, index=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    old_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    new_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    transaction = relationship("LedgerTransaction", back_populates="corrections")
