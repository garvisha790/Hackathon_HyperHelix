import uuid
from sqlalchemy import (
    String, ForeignKey, Numeric, Boolean, Integer, Date,
    Enum as SAEnum, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from sqlalchemy import DateTime, func

from app.database import Base


class GSTSummary(Base):
    __tablename__ = "gst_summaries"
    __table_args__ = (
        UniqueConstraint("tenant_id", "period_start", "period_type", name="uq_gst_summary_period"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    period_start: Mapped[str] = mapped_column(Date, nullable=False)
    period_end: Mapped[str] = mapped_column(Date, nullable=False)
    period_type: Mapped[str] = mapped_column(
        SAEnum("monthly", "quarterly", name="gst_period_type_enum"), nullable=False
    )

    output_cgst: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    output_sgst: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    output_igst: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    output_cess: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    input_cgst: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    input_sgst: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    input_igst: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    input_cess: Mapped[float] = mapped_column(Numeric(15, 2), default=0)

    net_liability: Mapped[float] = mapped_column(Numeric(15, 2), default=0)

    is_stale: Mapped[bool] = mapped_column(Boolean, default=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ITEstimate(Base):
    __tablename__ = "it_estimates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "fy", name="uq_it_estimate_fy"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    fy: Mapped[str] = mapped_column(String(7), nullable=False)  # '2025-26'

    total_revenue: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    total_expenses: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    gross_profit: Mapped[float] = mapped_column(Numeric(15, 2), default=0)

    tax_regime: Mapped[str] = mapped_column(
        SAEnum("new", "old", name="it_regime_enum"), nullable=False, default="new"
    )
    taxable_income: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    estimated_tax: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    cess: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    total_tax_liability: Mapped[float] = mapped_column(Numeric(15, 2), default=0)

    assumptions: Mapped[dict] = mapped_column(JSONB, default=dict)
    slab_breakup: Mapped[dict] = mapped_column(JSONB, default=list)

    is_stale: Mapped[bool] = mapped_column(Boolean, default=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AggregateCache(Base):
    __tablename__ = "aggregate_cache"
    __table_args__ = (
        UniqueConstraint("tenant_id", "cache_key", name="uq_aggregate_cache_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    cache_key: Mapped[str] = mapped_column(String(255), nullable=False)
    cache_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
