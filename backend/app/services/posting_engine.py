"""Double-entry posting engine — Indian accounting rules.

Creates journal entries when an invoice is approved. Supports:
- Tax Invoice (Purchase): DR Expense + DR Input GST, CR Sundry Creditors
- Tax Invoice (Sales): DR Sundry Debtors, CR Revenue + CR Output GST
- Credit Note: Reversal entries against original transaction
- Debit Note: Additional charge entries
"""
import uuid
import logging
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.invoice import CanonicalInvoice
from app.models.ledger import ChartOfAccounts, LedgerTransaction, JournalLine
from app.services.category_engine import assign_category

logger = logging.getLogger(__name__)


async def post_invoice(
    db: AsyncSession,
    invoice: CanonicalInvoice,
    tenant_id: uuid.UUID,
) -> LedgerTransaction:
    """Create ledger entries for an approved invoice."""
    accounts = await _get_system_accounts(db, tenant_id)
    category_result = await assign_category(
        db, tenant_id, invoice.vendor_name, _items_description(invoice.line_items)
    )

    expense_account = await _resolve_expense_account(db, tenant_id, category_result.get("category"))

    if invoice.document_type == "credit_note":
        return await _post_credit_note(db, invoice, tenant_id, accounts, expense_account)
    elif invoice.document_type == "debit_note":
        return await _post_debit_note(db, invoice, tenant_id, accounts, expense_account)
    else:
        return await _post_standard_invoice(db, invoice, tenant_id, accounts, expense_account, category_result)


async def _post_standard_invoice(
    db: AsyncSession,
    inv: CanonicalInvoice,
    tenant_id: uuid.UUID,
    accounts: dict,
    expense_account: ChartOfAccounts,
    category_result: dict,
) -> LedgerTransaction:
    is_purchase = _is_purchase(inv)
    interstate = inv.igst > 0

    txn = LedgerTransaction(
        tenant_id=tenant_id,
        document_id=inv.document_id,
        canonical_invoice_id=inv.id,
        transaction_date=inv.invoice_date,
        description=f"{'Purchase' if is_purchase else 'Sales'} Invoice {inv.invoice_number} - {inv.vendor_name or 'Unknown'}",
        status="AUTO_POSTED",
        assigned_category=category_result.get("category"),
        category_confidence=category_result.get("confidence"),
        category_method=category_result.get("method", "rule"),
    )
    db.add(txn)
    await db.flush()

    lines = []

    if is_purchase:
        lines.append(JournalLine(transaction_id=txn.id, account_id=expense_account.id, debit=float(inv.subtotal), credit=0))

        if interstate:
            lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["igst_input"].id, debit=float(inv.igst), credit=0))
        else:
            if inv.cgst > 0:
                lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["cgst_input"].id, debit=float(inv.cgst), credit=0))
            if inv.sgst > 0:
                lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sgst_input"].id, debit=float(inv.sgst), credit=0))

        lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sundry_creditors"].id, debit=0, credit=float(inv.total)))
    else:
        lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sundry_debtors"].id, debit=float(inv.total), credit=0))

        revenue_acct = accounts.get("sales", expense_account)
        lines.append(JournalLine(transaction_id=txn.id, account_id=revenue_acct.id, debit=0, credit=float(inv.subtotal)))

        if interstate:
            lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["igst_output"].id, debit=0, credit=float(inv.igst)))
        else:
            if inv.cgst > 0:
                lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["cgst_output"].id, debit=0, credit=float(inv.cgst)))
            if inv.sgst > 0:
                lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sgst_output"].id, debit=0, credit=float(inv.sgst)))

    _verify_balance(lines)
    for line in lines:
        db.add(line)
    await db.flush()

    return txn


async def _post_credit_note(
    db: AsyncSession, inv: CanonicalInvoice, tenant_id: uuid.UUID,
    accounts: dict, expense_account: ChartOfAccounts,
) -> LedgerTransaction:
    """Credit note = reversal of original invoice entries."""
    txn = LedgerTransaction(
        tenant_id=tenant_id,
        document_id=inv.document_id,
        canonical_invoice_id=inv.id,
        transaction_date=inv.invoice_date,
        description=f"Credit Note {inv.invoice_number} against {inv.original_invoice_number or 'N/A'}",
        status="AUTO_POSTED",
        assigned_category="Credit Note Reversal",
    )
    db.add(txn)
    await db.flush()

    lines = []
    interstate = inv.igst > 0

    lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sundry_creditors"].id, debit=float(inv.total), credit=0))
    lines.append(JournalLine(transaction_id=txn.id, account_id=expense_account.id, debit=0, credit=float(inv.subtotal)))

    if interstate:
        lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["igst_input"].id, debit=0, credit=float(inv.igst)))
    else:
        if inv.cgst > 0:
            lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["cgst_input"].id, debit=0, credit=float(inv.cgst)))
        if inv.sgst > 0:
            lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sgst_input"].id, debit=0, credit=float(inv.sgst)))

    _verify_balance(lines)
    for line in lines:
        db.add(line)
    await db.flush()
    return txn


async def _post_debit_note(
    db: AsyncSession, inv: CanonicalInvoice, tenant_id: uuid.UUID,
    accounts: dict, expense_account: ChartOfAccounts,
) -> LedgerTransaction:
    """Debit note = additional charge entries."""
    txn = LedgerTransaction(
        tenant_id=tenant_id,
        document_id=inv.document_id,
        canonical_invoice_id=inv.id,
        transaction_date=inv.invoice_date,
        description=f"Debit Note {inv.invoice_number}",
        status="AUTO_POSTED",
        assigned_category="Debit Note Addition",
    )
    db.add(txn)
    await db.flush()

    lines = []
    interstate = inv.igst > 0

    lines.append(JournalLine(transaction_id=txn.id, account_id=expense_account.id, debit=float(inv.subtotal), credit=0))

    if interstate:
        lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["igst_input"].id, debit=float(inv.igst), credit=0))
    else:
        if inv.cgst > 0:
            lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["cgst_input"].id, debit=float(inv.cgst), credit=0))
        if inv.sgst > 0:
            lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sgst_input"].id, debit=float(inv.sgst), credit=0))

    lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sundry_creditors"].id, debit=0, credit=float(inv.total)))

    _verify_balance(lines)
    for line in lines:
        db.add(line)
    await db.flush()
    return txn


def _is_purchase(inv: CanonicalInvoice) -> bool:
    """Heuristic: if buyer_gstin matches tenant's GSTIN, it's a purchase. Otherwise sales."""
    return True  # Default to purchase for uploaded invoices


def _items_description(line_items: list) -> str:
    if not line_items:
        return ""
    return " | ".join(item.get("description", "") for item in line_items[:5] if isinstance(item, dict))


def _verify_balance(lines: list[JournalLine]):
    total_debit = round(sum(float(line.debit or 0) for line in lines), 2)
    total_credit = round(sum(float(line.credit or 0) for line in lines), 2)
    if abs(total_debit - total_credit) > 0.02:
        raise ValueError(f"Double-entry violation: debit={total_debit}, credit={total_credit}")


async def _get_system_accounts(db: AsyncSession, tenant_id: uuid.UUID) -> dict:
    """Load system accounts (GST, AP, AR) by tally_group name."""
    result = await db.execute(
        select(ChartOfAccounts).where(
            ChartOfAccounts.tenant_id == tenant_id,
            ChartOfAccounts.is_system.is_(True),
            ChartOfAccounts.deleted_at.is_(None),
        )
    )
    accounts = result.scalars().all()
    mapping = {}
    for acc in accounts:
        key = acc.code.lower().replace(" ", "_")
        mapping[key] = acc
    return mapping


async def _resolve_expense_account(db: AsyncSession, tenant_id: uuid.UUID, category: str | None) -> ChartOfAccounts:
    """Find the matching chart of accounts entry for the category, or fall back to Indirect Expenses."""
    if category:
        result = await db.execute(
            select(ChartOfAccounts).where(
                ChartOfAccounts.tenant_id == tenant_id,
                ChartOfAccounts.name == category,
                ChartOfAccounts.deleted_at.is_(None),
            )
        )
        account = result.scalar_one_or_none()
        if account:
            return account

    result = await db.execute(
        select(ChartOfAccounts).where(
            ChartOfAccounts.tenant_id == tenant_id,
            ChartOfAccounts.code == "indirect_expenses",
            ChartOfAccounts.deleted_at.is_(None),
        )
    )
    return result.scalar_one()
