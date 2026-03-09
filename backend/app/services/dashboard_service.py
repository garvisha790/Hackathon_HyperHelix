"""Dashboard aggregation service with Redis caching."""
import uuid
import json
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from app.models.document import Document
from app.models.invoice import CanonicalInvoice
from app.models.ledger import LedgerTransaction, JournalLine, ChartOfAccounts
from app.models.tax import GSTSummary
from app.schemas.dashboard import (
    DashboardOverview, PipelineStatus, PnLItem,
    ExpenseCategory, GSTTrackerItem, CashFlowItem, RecentInvoice,
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
    receivables, payables = await _get_receivables_payables(db, tenant_id)
    recent = await _get_recent_invoices(db, tenant_id)

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
        net_profit=total_rev - total_exp,
        gst_liability=gst_liability,
        total_receivables=receivables,
        total_payables=payables,
        pipeline=pipeline,
        pnl=pnl,
        expenses_by_category=expenses,
        gst_tracker=gst,
        cashflow=cashflow,
        recent_invoices=recent,
    )

    if redis:
        await redis.set(cache_key, json.dumps(overview.model_dump(), default=str), ex=30)

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
            func.coalesce(func.sum(JournalLine.debit), 0).label("dr"),
            func.coalesce(func.sum(JournalLine.credit), 0).label("cr"),
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
    exp_map = {str(r[0])[:7]: float(r[1]) - float(r[2]) for r in exp_result.all()}

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
            func.coalesce(func.sum(JournalLine.debit), 0).label("dr"),
            func.coalesce(func.sum(JournalLine.credit), 0).label("cr"),
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
    rows = [(r[0], float(r[1] or 0) - float(r[2] or 0)) for r in result.all()]
    # Filter out categories with zero or negative net (fully reversed)
    rows = [(cat, amt) for cat, amt in rows if amt > 0]
    grand_total = sum(amt for _, amt in rows) or 1
    return [
        ExpenseCategory(
            category=cat or "Uncategorized",
            amount=amt,
            percentage=round(amt / grand_total * 100, 1),
        )
        for cat, amt in rows
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
    """Cash flow derived from revenue (inflow) and expense (outflow) accounts.

    Since payment tracking isn't implemented yet, we approximate cash flow
    from the invoice-level revenue and expense postings per month.
    """
    # Inflow = credits to revenue accounts (Sales, BOS)
    inflow_q = await db.execute(
        select(
            func.date_trunc("month", LedgerTransaction.transaction_date).label("period"),
            func.coalesce(func.sum(JournalLine.credit), 0).label("inflow"),
        )
        .select_from(JournalLine)
        .join(LedgerTransaction, JournalLine.transaction_id == LedgerTransaction.id)
        .join(ChartOfAccounts, JournalLine.account_id == ChartOfAccounts.id)
        .where(
            LedgerTransaction.tenant_id == tenant_id,
            LedgerTransaction.transaction_date.between(start, end),
            LedgerTransaction.deleted_at.is_(None),
            ChartOfAccounts.tally_group.in_(["Sales Accounts"]),
        )
        .group_by("period")
    )
    inflows = {str(r[0])[:7]: float(r[1]) for r in inflow_q.all()}

    # Outflow = net debits to expense accounts (DR - CR for credit note reversals)
    outflow_q = await db.execute(
        select(
            func.date_trunc("month", LedgerTransaction.transaction_date).label("period"),
            func.coalesce(func.sum(JournalLine.debit), 0).label("dr"),
            func.coalesce(func.sum(JournalLine.credit), 0).label("cr"),
        )
        .select_from(JournalLine)
        .join(LedgerTransaction, JournalLine.transaction_id == LedgerTransaction.id)
        .join(ChartOfAccounts, JournalLine.account_id == ChartOfAccounts.id)
        .where(
            LedgerTransaction.tenant_id == tenant_id,
            LedgerTransaction.transaction_date.between(start, end),
            LedgerTransaction.deleted_at.is_(None),
            ChartOfAccounts.tally_group.in_([
                "Purchase Accounts", "Direct Expenses", "Indirect Expenses",
            ]),
        )
        .group_by("period")
    )
    outflows = {str(r[0])[:7]: float(r[1]) - float(r[2]) for r in outflow_q.all()}

    all_periods = sorted(set(list(inflows.keys()) + list(outflows.keys())))
    return [
        CashFlowItem(
            period=p,
            inflow=inflows.get(p, 0),
            outflow=outflows.get(p, 0),
            net=inflows.get(p, 0) - outflows.get(p, 0),
        )
        for p in all_periods
    ]


async def _get_receivables_payables(
    db: AsyncSession, tenant_id: uuid.UUID,
) -> tuple[float, float]:
    """Get total receivables (Sundry Debtors balance) and payables (Sundry Creditors balance)."""
    result = await db.execute(
        select(
            ChartOfAccounts.tally_group,
            func.coalesce(func.sum(JournalLine.debit), 0).label("total_dr"),
            func.coalesce(func.sum(JournalLine.credit), 0).label("total_cr"),
        )
        .select_from(JournalLine)
        .join(LedgerTransaction, JournalLine.transaction_id == LedgerTransaction.id)
        .join(ChartOfAccounts, JournalLine.account_id == ChartOfAccounts.id)
        .where(
            LedgerTransaction.tenant_id == tenant_id,
            LedgerTransaction.deleted_at.is_(None),
            ChartOfAccounts.tally_group.in_(["Sundry Debtors", "Sundry Creditors"]),
        )
        .group_by(ChartOfAccounts.tally_group)
    )
    receivables = 0.0
    payables = 0.0
    for row in result.all():
        balance = float(row[1]) - float(row[2])
        if row[0] == "Sundry Debtors":
            receivables = balance  # Debit balance = money owed to us
        elif row[0] == "Sundry Creditors":
            payables = abs(balance)  # Credit balance = money we owe
    return receivables, payables


async def _get_recent_invoices(
    db: AsyncSession, tenant_id: uuid.UUID, limit: int = 8,
) -> list[RecentInvoice]:
    """Get most recent canonical invoices."""
    result = await db.execute(
        select(CanonicalInvoice)
        .where(
            CanonicalInvoice.tenant_id == tenant_id,
            CanonicalInvoice.deleted_at.is_(None),
        )
        .order_by(CanonicalInvoice.created_at.desc())
        .limit(limit)
    )
    return [
        RecentInvoice(
            id=str(inv.id),
            document_id=str(inv.document_id),
            invoice_number=inv.invoice_number or "—",
            vendor_name=inv.vendor_name,
            buyer_name=inv.buyer_name,
            document_type=inv.document_type,
            transaction_nature=inv.transaction_nature,
            total=float(inv.total),
            invoice_date=str(inv.invoice_date),
            status=inv.validation_status,
        )
        for inv in result.scalars().all()
    ]
