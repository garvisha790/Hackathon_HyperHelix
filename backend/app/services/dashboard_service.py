"""Dashboard aggregation service with Redis caching."""
import uuid
import json
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from app.models.document import Document
from app.models.ledger import LedgerTransaction, JournalLine, ChartOfAccounts
from app.models.tax import GSTSummary
from app.schemas.dashboard import (
    DashboardOverview, PipelineStatus, PnLItem,
    ExpenseCategory, GSTTrackerItem, CashFlowItem,
)


async def get_dashboard_overview(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    redis,
    fy_start: date,
    fy_end: date,
) -> DashboardOverview:
    cache_key = f"dashboard:{tenant_id}:{fy_start}:{fy_end}"
    if redis:
        cached = await redis.get(cache_key)
        if cached:
            return DashboardOverview(**json.loads(cached))

    pipeline = await _get_pipeline_status(db, tenant_id)
    pnl = await _get_pnl(db, tenant_id, fy_start, fy_end)
    expenses = await _get_expenses_by_category(db, tenant_id, fy_start, fy_end)
    gst = await _get_gst_tracker(db, tenant_id, fy_start, fy_end)
    cashflow = await _get_cashflow(db, tenant_id, fy_start, fy_end)

    total_rev = sum(p.revenue for p in pnl)
    total_exp = sum(p.expenses for p in pnl)
    gst_liability = sum(g.net_liability for g in gst)

    doc_count = await db.execute(
        select(func.count(Document.id)).where(
            Document.tenant_id == tenant_id, Document.deleted_at.is_(None)
        )
    )

    overview = DashboardOverview(
        total_documents=doc_count.scalar() or 0,
        total_invoices=pipeline.done,
        total_revenue=total_rev,
        total_expenses=total_exp,
        gst_liability=gst_liability,
        pipeline=pipeline,
        pnl=pnl,
        expenses_by_category=expenses,
        gst_tracker=gst,
        cashflow=cashflow,
    )

    if redis:
        await redis.set(cache_key, json.dumps(overview.model_dump(), default=str), ex=300)

    return overview


async def _get_pipeline_status(db: AsyncSession, tenant_id: uuid.UUID) -> PipelineStatus:
    result = await db.execute(
        select(Document.status, func.count(Document.id)).where(
            Document.tenant_id == tenant_id, Document.deleted_at.is_(None)
        ).group_by(Document.status)
    )
    counts = {row[0]: row[1] for row in result.all()}
    return PipelineStatus(
        uploaded=counts.get("UPLOADED", 0),
        processing=counts.get("PROCESSING", 0) + counts.get("EXTRACTED", 0) + counts.get("VALIDATED", 0),
        done=counts.get("DONE", 0),
        failed=counts.get("FAILED", 0),
        total=sum(counts.values()),
    )


async def _get_pnl(db: AsyncSession, tenant_id: uuid.UUID, start: date, end: date) -> list[PnLItem]:
    """Monthly P&L from ledger."""
    revenue_q = (
        select(
            func.date_trunc("month", LedgerTransaction.transaction_date).label("period"),
            func.coalesce(func.sum(JournalLine.credit), 0).label("amount"),
        )
        .select_from(JournalLine)
        .join(LedgerTransaction, JournalLine.transaction_id == LedgerTransaction.id)
        .join(ChartOfAccounts, JournalLine.account_id == ChartOfAccounts.id)
        .where(
            LedgerTransaction.tenant_id == tenant_id,
            LedgerTransaction.transaction_date.between(start, end),
            LedgerTransaction.deleted_at.is_(None),
            ChartOfAccounts.account_type == "revenue",
        )
        .group_by("period")
    )

    expense_q = (
        select(
            func.date_trunc("month", LedgerTransaction.transaction_date).label("period"),
            func.coalesce(func.sum(JournalLine.debit), 0).label("amount"),
        )
        .select_from(JournalLine)
        .join(LedgerTransaction, JournalLine.transaction_id == LedgerTransaction.id)
        .join(ChartOfAccounts, JournalLine.account_id == ChartOfAccounts.id)
        .where(
            LedgerTransaction.tenant_id == tenant_id,
            LedgerTransaction.transaction_date.between(start, end),
            LedgerTransaction.deleted_at.is_(None),
            ChartOfAccounts.account_type == "expense",
        )
        .group_by("period")
    )

    rev_result = await db.execute(revenue_q)
    exp_result = await db.execute(expense_q)

    rev_map = {str(r[0])[:7]: float(r[1]) for r in rev_result.all()}
    exp_map = {str(r[0])[:7]: float(r[1]) for r in exp_result.all()}

    all_periods = sorted(set(list(rev_map.keys()) + list(exp_map.keys())))
    return [
        PnLItem(
            period=p,
            revenue=rev_map.get(p, 0),
            expenses=exp_map.get(p, 0),
            profit=rev_map.get(p, 0) - exp_map.get(p, 0),
        )
        for p in all_periods
    ]


async def _get_expenses_by_category(
    db: AsyncSession, tenant_id: uuid.UUID, start: date, end: date,
) -> list[ExpenseCategory]:
    result = await db.execute(
        select(
            LedgerTransaction.assigned_category,
            func.sum(JournalLine.debit).label("total"),
        )
        .select_from(JournalLine)
        .join(LedgerTransaction, JournalLine.transaction_id == LedgerTransaction.id)
        .join(ChartOfAccounts, JournalLine.account_id == ChartOfAccounts.id)
        .where(
            LedgerTransaction.tenant_id == tenant_id,
            LedgerTransaction.transaction_date.between(start, end),
            LedgerTransaction.deleted_at.is_(None),
            ChartOfAccounts.account_type == "expense",
        )
        .group_by(LedgerTransaction.assigned_category)
    )
    rows = result.all()
    grand_total = sum(float(r[1] or 0) for r in rows) or 1
    return [
        ExpenseCategory(
            category=r[0] or "Uncategorized",
            amount=float(r[1] or 0),
            percentage=round(float(r[1] or 0) / grand_total * 100, 1),
        )
        for r in rows
    ]


async def _get_gst_tracker(
    db: AsyncSession, tenant_id: uuid.UUID, start: date, end: date,
) -> list[GSTTrackerItem]:
    result = await db.execute(
        select(GSTSummary).where(
            GSTSummary.tenant_id == tenant_id,
            GSTSummary.period_start >= start,
            GSTSummary.period_end <= end,
        ).order_by(GSTSummary.period_start)
    )
    return [
        GSTTrackerItem(
            period=f"{s.period_start}",
            output_gst=float(s.output_cgst + s.output_sgst + s.output_igst),
            input_gst=float(s.input_cgst + s.input_sgst + s.input_igst),
            net_liability=float(s.net_liability),
        )
        for s in result.scalars().all()
    ]


async def _get_cashflow(
    db: AsyncSession, tenant_id: uuid.UUID, start: date, end: date,
) -> list[CashFlowItem]:
    """Cash flow from cash/bank accounts."""
    result = await db.execute(
        select(
            func.date_trunc("month", LedgerTransaction.transaction_date).label("period"),
            func.coalesce(func.sum(JournalLine.debit), 0).label("inflow"),
            func.coalesce(func.sum(JournalLine.credit), 0).label("outflow"),
        )
        .select_from(JournalLine)
        .join(LedgerTransaction, JournalLine.transaction_id == LedgerTransaction.id)
        .join(ChartOfAccounts, JournalLine.account_id == ChartOfAccounts.id)
        .where(
            LedgerTransaction.tenant_id == tenant_id,
            LedgerTransaction.transaction_date.between(start, end),
            LedgerTransaction.deleted_at.is_(None),
            ChartOfAccounts.is_cash_or_bank.is_(True),
        )
        .group_by("period")
        .order_by("period")
    )
    return [
        CashFlowItem(
            period=str(r[0])[:7],
            inflow=float(r[1]),
            outflow=float(r[2]),
            net=float(r[1]) - float(r[2]),
        )
        for r in result.all()
    ]
