"""GST + Income Tax computation engine.

GST: Aggregates from ledger's GST accounts by period (monthly/quarterly).
IT: Builds P&L from ledger categories, applies FY 2025-26 slabs.
"""
import uuid
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case

from app.models.ledger import JournalLine, LedgerTransaction, ChartOfAccounts
from app.models.tax import GSTSummary, ITEstimate
from app.models.tenant import Tenant
from app.utils.indian_tax_slabs import compute_income_tax


async def compute_gst_summary(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    period_start: date,
    period_end: date,
    period_type: str = "monthly",
) -> GSTSummary:
    """Compute GST summary from ledger journal lines. Skips recompute if not stale."""
    # Fast path: return cached summary if not stale
    existing_check = await db.execute(
        select(GSTSummary).where(
            GSTSummary.tenant_id == tenant_id,
            GSTSummary.period_start == period_start,
            GSTSummary.period_type == period_type,
        )
    )
    cached = existing_check.scalar_one_or_none()
    if cached and not cached.is_stale:
        return cached

    gst_accounts = await db.execute(
        select(ChartOfAccounts).where(
            ChartOfAccounts.tenant_id == tenant_id,
            ChartOfAccounts.tally_group == "Duties & Taxes",
            ChartOfAccounts.is_system.is_(True),
        )
    )
    accounts = {acc.code: acc for acc in gst_accounts.scalars().all()}

    async def _sum_for_account(code: str, side: str) -> float:
        """Get NET amount for an account: debit-credit or credit-debit.
        
        For input GST accounts (side='debit'): net = sum(debit) - sum(credit)
          - Normal purchase debits input GST → adds
          - Credit note reversal credits input GST → subtracts
        For output GST accounts (side='credit'): net = sum(credit) - sum(debit)
          - Normal sale credits output GST → adds
          - Sale credit note debits output GST → subtracts
        """
        acc = accounts.get(code)
        if not acc:
            return 0.0
        result = await db.execute(
            select(
                func.coalesce(func.sum(JournalLine.debit), 0),
                func.coalesce(func.sum(JournalLine.credit), 0),
            ).select_from(JournalLine).join(
                LedgerTransaction, JournalLine.transaction_id == LedgerTransaction.id
            ).where(
                JournalLine.account_id == acc.id,
                LedgerTransaction.tenant_id == tenant_id,
                LedgerTransaction.transaction_date >= period_start,
                LedgerTransaction.transaction_date <= period_end,
            )
        )
        row = result.one()
        total_debit = float(row[0])
        total_credit = float(row[1])
        if side == "debit":
            return max(total_debit - total_credit, 0)
        else:
            return max(total_credit - total_debit, 0)

    output_cgst = await _sum_for_account("cgst_output", "credit")
    output_sgst = await _sum_for_account("sgst_output", "credit")
    output_igst = await _sum_for_account("igst_output", "credit")
    input_cgst = await _sum_for_account("cgst_input", "debit")
    input_sgst = await _sum_for_account("sgst_input", "debit")
    input_igst = await _sum_for_account("igst_input", "debit")

    net = (output_cgst + output_sgst + output_igst) - (input_cgst + input_sgst + input_igst)

    existing = await db.execute(
        select(GSTSummary).where(
            GSTSummary.tenant_id == tenant_id,
            GSTSummary.period_start == period_start,
            GSTSummary.period_type == period_type,
        )
    )
    summary = existing.scalar_one_or_none()

    if summary:
        summary.output_cgst = output_cgst
        summary.output_sgst = output_sgst
        summary.output_igst = output_igst
        summary.input_cgst = input_cgst
        summary.input_sgst = input_sgst
        summary.input_igst = input_igst
        summary.net_liability = net
        summary.is_stale = False
        summary.computed_at = datetime.utcnow()
    else:
        summary = GSTSummary(
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            period_type=period_type,
            output_cgst=output_cgst,
            output_sgst=output_sgst,
            output_igst=output_igst,
            input_cgst=input_cgst,
            input_sgst=input_sgst,
            input_igst=input_igst,
            net_liability=net,
        )
        db.add(summary)

    await db.flush()
    return summary


async def compute_income_tax_estimate(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    fy: str,
) -> ITEstimate:
    """Compute income tax estimate from P&L derived from ledger."""
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = tenant_result.scalar_one()

    fy_start_year = int(fy.split("-")[0])
    fy_start = date(fy_start_year, tenant.fy_start_month, 1)
    fy_end = date(fy_start_year + 1, tenant.fy_start_month, 1) - relativedelta(days=1)

    # Revenue = NET credits on revenue accounts (credits - debits)
    # This properly handles sale credit notes which DEBIT revenue
    revenue_result = await db.execute(
        select(
            func.coalesce(func.sum(JournalLine.credit), 0),
            func.coalesce(func.sum(JournalLine.debit), 0),
        ).select_from(JournalLine).join(
            LedgerTransaction, JournalLine.transaction_id == LedgerTransaction.id
        ).join(
            ChartOfAccounts, JournalLine.account_id == ChartOfAccounts.id
        ).where(
            LedgerTransaction.tenant_id == tenant_id,
            LedgerTransaction.transaction_date >= fy_start,
            LedgerTransaction.transaction_date <= fy_end,
            ChartOfAccounts.account_type == "revenue",
        )
    )
    rev_row = revenue_result.one()
    total_revenue = max(float(rev_row[0]) - float(rev_row[1]), 0)

    # Expenses = NET debits on expense accounts (debits - credits)
    # This properly handles purchase credit notes which CREDIT expense
    expense_result = await db.execute(
        select(
            func.coalesce(func.sum(JournalLine.debit), 0),
            func.coalesce(func.sum(JournalLine.credit), 0),
        ).select_from(JournalLine).join(
            LedgerTransaction, JournalLine.transaction_id == LedgerTransaction.id
        ).join(
            ChartOfAccounts, JournalLine.account_id == ChartOfAccounts.id
        ).where(
            LedgerTransaction.tenant_id == tenant_id,
            LedgerTransaction.transaction_date >= fy_start,
            LedgerTransaction.transaction_date <= fy_end,
            ChartOfAccounts.account_type == "expense",
            ChartOfAccounts.tally_group != "Duties & Taxes",
        )
    )
    exp_row = expense_result.one()
    total_expenses = max(float(exp_row[0]) - float(exp_row[1]), 0)

    gross_profit = total_revenue - total_expenses
    taxable_income = max(gross_profit, 0)

    tax_result = compute_income_tax(taxable_income, regime=tenant.tax_regime)

    existing = await db.execute(
        select(ITEstimate).where(ITEstimate.tenant_id == tenant_id, ITEstimate.fy == fy)
    )
    estimate = existing.scalar_one_or_none()

    assumptions = {}
    if tax_result.get("rebate"):
        assumptions["rebate"] = tax_result["rebate"]
    if tax_result.get("note"):
        assumptions["note"] = tax_result["note"]

    if estimate:
        estimate.total_revenue = total_revenue
        estimate.total_expenses = total_expenses
        estimate.gross_profit = gross_profit
        estimate.tax_regime = tenant.tax_regime
        estimate.taxable_income = taxable_income
        estimate.estimated_tax = tax_result["estimated_tax"]
        estimate.cess = tax_result["cess"]
        estimate.total_tax_liability = tax_result["total_tax_liability"]
        estimate.slab_breakup = tax_result["slab_breakup"]
        estimate.assumptions = assumptions
        estimate.is_stale = False
        estimate.computed_at = datetime.utcnow()
    else:
        estimate = ITEstimate(
            tenant_id=tenant_id,
            fy=fy,
            total_revenue=total_revenue,
            total_expenses=total_expenses,
            gross_profit=gross_profit,
            tax_regime=tenant.tax_regime,
            taxable_income=taxable_income,
            estimated_tax=tax_result["estimated_tax"],
            cess=tax_result["cess"],
            total_tax_liability=tax_result["total_tax_liability"],
            slab_breakup=tax_result["slab_breakup"],
            assumptions=assumptions,
        )
        db.add(estimate)

    await db.flush()
    return estimate


async def mark_gst_stale(db: AsyncSession, tenant_id: uuid.UUID, transaction_date: date):
    """Mark GST summaries as stale when ledger changes. Called by posting engine."""
    result = await db.execute(
        select(GSTSummary).where(
            GSTSummary.tenant_id == tenant_id,
            GSTSummary.period_start <= transaction_date,
            GSTSummary.period_end >= transaction_date,
        )
    )
    for summary in result.scalars().all():
        summary.is_stale = True
    await db.flush()
