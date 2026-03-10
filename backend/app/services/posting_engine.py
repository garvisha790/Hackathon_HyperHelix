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
    """Create ledger entries for an approved invoice.

    Uses a savepoint so that if journal-line creation fails (e.g. balance
    check), the orphaned LedgerTransaction is rolled back automatically.
    """
    # Guard against duplicate ledger entries: physically delete old journal lines + txns
    existing = await db.execute(
        select(LedgerTransaction).where(
            LedgerTransaction.canonical_invoice_id == invoice.id,
        )
    )
    for old_txn in existing.scalars().all():
        logger.info(f"[POST] Removing old ledger txn {old_txn.id} for invoice {invoice.id}")
        old_lines = await db.execute(
            select(JournalLine).where(JournalLine.transaction_id == old_txn.id)
        )
        for old_line in old_lines.scalars().all():
            await db.delete(old_line)
        await db.delete(old_txn)
    await db.flush()

    accounts = await _get_system_accounts(db, tenant_id)
    category_result = await assign_category(
        db, tenant_id, invoice.vendor_name, _items_description(invoice.line_items)
    )

    expense_account = await _resolve_expense_account(db, tenant_id, category_result.get("category"))

    # Use a savepoint so a posting failure rolls back the txn + lines atomically
    async with db.begin_nested():
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
    # Detect bill_of_supply from document_type (set by AI classifier)
    is_bill_of_supply = getattr(inv, "document_type", None) == "bill_of_supply"
    is_purchase = _is_purchase(inv)
    interstate = inv.igst > 0

    # Ensure consistent amounts — derive subtotal from total minus taxes if needed
    taxes = float(inv.cgst or 0) + float(inv.sgst or 0) + float(inv.igst or 0)
    effective_total = float(inv.total) if inv.total else 0
    effective_subtotal = float(inv.subtotal) if inv.subtotal else 0
    if effective_total > 0 and taxes > 0 and (effective_subtotal == 0 or abs(effective_subtotal - effective_total) < 0.01):
        effective_subtotal = round(effective_total - taxes, 2)
    elif effective_subtotal == 0 and effective_total > 0:
        effective_subtotal = effective_total

    doc_label = "Bill of Supply" if is_bill_of_supply else ("Purchase" if is_purchase else "Sales") + " Invoice"
    txn = LedgerTransaction(
        tenant_id=tenant_id,
        document_id=inv.document_id,
        canonical_invoice_id=inv.id,
        transaction_date=inv.invoice_date,
        description=f"{doc_label} {inv.invoice_number} - {inv.vendor_name or 'Unknown'}",
        status="AUTO_POSTED",
        assigned_category=category_result.get("category"),
        category_confidence=category_result.get("confidence"),
        category_method=category_result.get("method", "rule"),
    )
    db.add(txn)
    await db.flush()

    lines = []

    if is_bill_of_supply:
        # Bill of supply = sale with NO GST: DR Sundry Debtors, CR Sales (total = subtotal)
        lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sundry_debtors"].id, debit=effective_total, credit=0))
        revenue_acct = accounts.get("sales_accounts", expense_account)
        lines.append(JournalLine(transaction_id=txn.id, account_id=revenue_acct.id, debit=0, credit=effective_total))
    elif is_purchase:
        lines.append(JournalLine(transaction_id=txn.id, account_id=expense_account.id, debit=effective_subtotal, credit=0))

        if interstate:
            lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["igst_input"].id, debit=float(inv.igst), credit=0))
        else:
            if inv.cgst > 0:
                lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["cgst_input"].id, debit=float(inv.cgst), credit=0))
            if inv.sgst > 0:
                lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sgst_input"].id, debit=float(inv.sgst), credit=0))

        lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sundry_creditors"].id, debit=0, credit=effective_total))
    else:
        lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sundry_debtors"].id, debit=effective_total, credit=0))

        revenue_acct = accounts.get("sales_accounts", expense_account)
        lines.append(JournalLine(transaction_id=txn.id, account_id=revenue_acct.id, debit=0, credit=effective_subtotal))

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
    """Credit note = reversal of original invoice entries.
    
    Purchase credit note: DR Sundry Creditors, CR Expense + CR Input GST
    Sale credit note: DR Revenue + DR Output GST, CR Sundry Debtors
    """
    is_purchase = _is_purchase(inv)

    # Derive consistent amounts for credit notes
    taxes = float(inv.cgst or 0) + float(inv.sgst or 0) + float(inv.igst or 0)
    effective_total = float(inv.total) if inv.total else 0
    effective_subtotal = float(inv.subtotal) if inv.subtotal else 0
    if effective_total > 0 and taxes > 0 and (effective_subtotal == 0 or abs(effective_subtotal - effective_total) < 0.01):
        effective_subtotal = round(effective_total - taxes, 2)
    elif effective_subtotal == 0 and effective_total > 0:
        effective_subtotal = effective_total

    txn = LedgerTransaction(
        tenant_id=tenant_id,
        document_id=inv.document_id,
        canonical_invoice_id=inv.id,
        transaction_date=inv.invoice_date,
        description=f"Credit Note {inv.invoice_number} ({'Purchase' if is_purchase else 'Sale'}) against {inv.original_invoice_number or 'N/A'}",
        status="AUTO_POSTED",
        assigned_category="Credit Note Reversal",
    )
    db.add(txn)
    await db.flush()

    lines = []
    interstate = inv.igst > 0

    if is_purchase:
        # Reverse purchase: reduce creditors, reduce expense + input GST
        lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sundry_creditors"].id, debit=effective_total, credit=0))
        lines.append(JournalLine(transaction_id=txn.id, account_id=expense_account.id, debit=0, credit=effective_subtotal))
        if interstate:
            lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["igst_input"].id, debit=0, credit=float(inv.igst)))
        else:
            if inv.cgst > 0:
                lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["cgst_input"].id, debit=0, credit=float(inv.cgst)))
            if inv.sgst > 0:
                lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sgst_input"].id, debit=0, credit=float(inv.sgst)))
    else:
        # Reverse sale: reduce debtors, reduce revenue + output GST
        revenue_acct = accounts.get("sales_accounts", expense_account)
        lines.append(JournalLine(transaction_id=txn.id, account_id=revenue_acct.id, debit=effective_subtotal, credit=0))
        if interstate:
            lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["igst_output"].id, debit=float(inv.igst), credit=0))
        else:
            if inv.cgst > 0:
                lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["cgst_output"].id, debit=float(inv.cgst), credit=0))
            if inv.sgst > 0:
                lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sgst_output"].id, debit=float(inv.sgst), credit=0))
        lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sundry_debtors"].id, debit=0, credit=effective_total))

    _verify_balance(lines)
    for line in lines:
        db.add(line)
    await db.flush()
    return txn


async def _post_debit_note(
    db: AsyncSession, inv: CanonicalInvoice, tenant_id: uuid.UUID,
    accounts: dict, expense_account: ChartOfAccounts,
) -> LedgerTransaction:
    """Debit note = additional charge entries.
    
    Purchase debit note: DR Expense + DR Input GST, CR Sundry Creditors (more charges from seller)
    Sale debit note: DR Sundry Debtors, CR Revenue + CR Output GST (additional charges to buyer)
    """
    is_purchase = _is_purchase(inv)

    # Derive consistent amounts for debit notes
    taxes = float(inv.cgst or 0) + float(inv.sgst or 0) + float(inv.igst or 0)
    effective_total = float(inv.total) if inv.total else 0
    effective_subtotal = float(inv.subtotal) if inv.subtotal else 0
    if effective_total > 0 and taxes > 0 and (effective_subtotal == 0 or abs(effective_subtotal - effective_total) < 0.01):
        effective_subtotal = round(effective_total - taxes, 2)
    elif effective_subtotal == 0 and effective_total > 0:
        effective_subtotal = effective_total

    txn = LedgerTransaction(
        tenant_id=tenant_id,
        document_id=inv.document_id,
        canonical_invoice_id=inv.id,
        transaction_date=inv.invoice_date,
        description=f"Debit Note {inv.invoice_number} ({'Purchase' if is_purchase else 'Sale'}) against {inv.original_invoice_number or 'N/A'}",
        status="AUTO_POSTED",
        assigned_category="Debit Note Addition",
    )
    db.add(txn)
    await db.flush()

    lines = []
    interstate = inv.igst > 0

    if is_purchase:
        # Additional purchase charges
        lines.append(JournalLine(transaction_id=txn.id, account_id=expense_account.id, debit=effective_subtotal, credit=0))
        if interstate:
            lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["igst_input"].id, debit=float(inv.igst), credit=0))
        else:
            if inv.cgst > 0:
                lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["cgst_input"].id, debit=float(inv.cgst), credit=0))
            if inv.sgst > 0:
                lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sgst_input"].id, debit=float(inv.sgst), credit=0))
        lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sundry_creditors"].id, debit=0, credit=effective_total))
    else:
        # Additional sale charges
        lines.append(JournalLine(transaction_id=txn.id, account_id=accounts["sundry_debtors"].id, debit=effective_total, credit=0))
        revenue_acct = accounts.get("sales_accounts", expense_account)
        lines.append(JournalLine(transaction_id=txn.id, account_id=revenue_acct.id, debit=0, credit=effective_subtotal))
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


def _is_purchase(inv: CanonicalInvoice) -> bool:
    """Determine if the invoice is a purchase based on AI classification.

    Uses the transaction_nature field set during pipeline processing.
    Falls back to True (purchase) for legacy invoices without classification.
    """
    nature = getattr(inv, "transaction_nature", None)
    if nature:
        return nature in ("purchase",)
    # Legacy fallback: no classification available
    logger.warning(f"[POST] Invoice {inv.id} has no transaction_nature — defaulting to purchase")
    return True


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
        )
    )
    accounts = result.scalars().all()
    if not accounts:
        raise ValueError("Chart of Accounts not seeded. Please re-login or contact support.")
    mapping = {}
    for acc in accounts:
        key = acc.code.lower().replace(" ", "_")
        mapping[key] = acc
    # Verify required accounts exist
    required = ["cgst_input", "sgst_input", "igst_input", "sundry_creditors", "sundry_debtors"]
    missing = [k for k in required if k not in mapping]
    if missing:
        raise ValueError(f"Missing system accounts: {', '.join(missing)}. Please re-seed Chart of Accounts.")
    return mapping


async def _resolve_expense_account(db: AsyncSession, tenant_id: uuid.UUID, category: str | None) -> ChartOfAccounts:
    """Find the matching chart of accounts entry for the category, or fall back to Indirect Expenses."""
    if category:
        result = await db.execute(
            select(ChartOfAccounts).where(
                ChartOfAccounts.tenant_id == tenant_id,
                ChartOfAccounts.name == category,
            )
        )
        account = result.scalar_one_or_none()
        if account:
            return account

    result = await db.execute(
        select(ChartOfAccounts).where(
            ChartOfAccounts.tenant_id == tenant_id,
            ChartOfAccounts.code == "indirect_expenses",
        )
    )
    return result.scalar_one()
