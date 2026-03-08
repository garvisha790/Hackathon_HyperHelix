import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func, or_

from app.dependencies import CurrentUser, TenantId, DB
from app.models.ledger import LedgerTransaction, JournalLine, ChartOfAccounts, Correction
from app.models.invoice import CanonicalInvoice
from app.schemas.ledger import (
    LedgerTransactionResponse, LedgerTransactionListResponse,
    JournalLineResponse, TransactionEditRequest, AccountTreeResponse,
)
from app.services.posting_engine import post_invoice
from app.services.tax_service import mark_gst_stale
from app.middleware.audit import log_action

router = APIRouter()


@router.get("/accounts", response_model=list[AccountTreeResponse])
async def get_chart_of_accounts(tenant_id: TenantId = None, db: DB = None):
    result = await db.execute(
        select(ChartOfAccounts).where(
            ChartOfAccounts.tenant_id == tenant_id,
            ChartOfAccounts.parent_id.is_(None),
            ChartOfAccounts.deleted_at.is_(None),
        ).order_by(ChartOfAccounts.code)
    )
    roots = result.scalars().all()
    return [_build_account_tree(acc) for acc in roots]


@router.get("/transactions", response_model=LedgerTransactionListResponse)
async def list_transactions(
    search: str | None = None,
    status: str | None = None,
    category: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    tenant_id: TenantId = None,
    db: DB = None,
):
    query = select(LedgerTransaction).where(
        LedgerTransaction.tenant_id == tenant_id,
        LedgerTransaction.deleted_at.is_(None),
    )
    count_q = select(func.count(LedgerTransaction.id)).where(
        LedgerTransaction.tenant_id == tenant_id,
        LedgerTransaction.deleted_at.is_(None),
    )

    if status:
        query = query.where(LedgerTransaction.status == status)
        count_q = count_q.where(LedgerTransaction.status == status)
    if category:
        query = query.where(LedgerTransaction.assigned_category == category)
        count_q = count_q.where(LedgerTransaction.assigned_category == category)
    if search:
        query = query.where(LedgerTransaction.description.ilike(f"%{search}%"))
        count_q = count_q.where(LedgerTransaction.description.ilike(f"%{search}%"))
    if date_from:
        query = query.where(LedgerTransaction.transaction_date >= date_from)
    if date_to:
        query = query.where(LedgerTransaction.transaction_date <= date_to)

    query = query.order_by(LedgerTransaction.transaction_date.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    total = await db.execute(count_q)
    txns = result.scalars().all()

    return LedgerTransactionListResponse(
        transactions=[_txn_response(t) for t in txns],
        total=total.scalar() or 0,
    )


@router.get("/transactions/{txn_id}", response_model=LedgerTransactionResponse)
async def get_transaction(txn_id: uuid.UUID, tenant_id: TenantId = None, db: DB = None):
    result = await db.execute(
        select(LedgerTransaction).where(
            LedgerTransaction.id == txn_id,
            LedgerTransaction.tenant_id == tenant_id,
            LedgerTransaction.deleted_at.is_(None),
        )
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(404, "Transaction not found")
    return _txn_response(txn)


@router.put("/transactions/{txn_id}", response_model=LedgerTransactionResponse)
async def edit_transaction(
    txn_id: uuid.UUID,
    edit: TransactionEditRequest,
    user: CurrentUser = None,
    tenant_id: TenantId = None,
    db: DB = None,
):
    result = await db.execute(
        select(LedgerTransaction).where(
            LedgerTransaction.id == txn_id,
            LedgerTransaction.tenant_id == tenant_id,
            LedgerTransaction.deleted_at.is_(None),
        )
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(404, "Transaction not found")

    old_data = {"description": txn.description, "assigned_category": txn.assigned_category}
    new_data = {}

    if edit.description is not None:
        new_data["description"] = edit.description
        txn.description = edit.description
    if edit.assigned_category is not None:
        new_data["assigned_category"] = edit.assigned_category
        txn.assigned_category = edit.assigned_category
        txn.category_method = "manual"

    correction = Correction(
        transaction_id=txn.id,
        tenant_id=tenant_id,
        user_id=user.id,
        old_data=old_data,
        new_data=new_data,
        reason=edit.reason,
    )
    db.add(correction)

    txn.status = "CORRECTED"
    txn.version += 1
    await db.flush()

    await log_action(db, tenant_id, user.id, "ledger.edit", "ledger_transaction", txn.id, {"reason": edit.reason})

    return _txn_response(txn)


@router.post("/transactions/{txn_id}/recompute", response_model=LedgerTransactionResponse)
async def recompute_transaction(
    txn_id: uuid.UUID,
    user: CurrentUser = None,
    tenant_id: TenantId = None,
    db: DB = None,
):
    """Recompute journal lines from canonical invoice + corrections."""
    result = await db.execute(
        select(LedgerTransaction).where(
            LedgerTransaction.id == txn_id,
            LedgerTransaction.tenant_id == tenant_id,
            LedgerTransaction.deleted_at.is_(None),
        )
    )
    txn = result.scalar_one_or_none()
    if not txn or not txn.canonical_invoice_id:
        raise HTTPException(404, "Transaction not found or has no linked invoice")

    invoice_result = await db.execute(
        select(CanonicalInvoice).where(CanonicalInvoice.id == txn.canonical_invoice_id)
    )
    invoice = invoice_result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Linked invoice not found")

    for line in txn.journal_lines:
        await db.delete(line)
    await db.flush()

    new_txn = await post_invoice(db, invoice, tenant_id)
    await mark_gst_stale(db, tenant_id, txn.transaction_date)

    txn.version += 1
    await db.flush()

    await log_action(db, tenant_id, user.id, "ledger.recompute", "ledger_transaction", txn.id)
    return _txn_response(txn)


@router.delete("/transactions/{txn_id}")
async def delete_transaction(
    txn_id: uuid.UUID,
    user: CurrentUser = None,
    tenant_id: TenantId = None,
    db: DB = None,
):
    """Hard delete a ledger transaction and its journal lines."""
    result = await db.execute(
        select(LedgerTransaction).where(
            LedgerTransaction.id == txn_id,
            LedgerTransaction.tenant_id == tenant_id,
            LedgerTransaction.deleted_at.is_(None),
        )
    )
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(404, "Transaction not found")

    # Log before deletion (since we won't have the record after)
    await log_action(db, tenant_id, user.id, "ledger.delete", "ledger_transaction", txn.id)
    
    # Hard delete journal lines first (FK constraint)
    for line in txn.journal_lines:
        await db.delete(line)
    
    # Then delete the transaction
    await db.delete(txn)
    await db.flush()
    
    return {"status": "deleted", "transaction_id": str(txn_id)}


def _txn_response(txn: LedgerTransaction) -> LedgerTransactionResponse:
    return LedgerTransactionResponse(
        id=str(txn.id),
        document_id=str(txn.document_id) if txn.document_id else None,
        transaction_date=txn.transaction_date,
        description=txn.description,
        status=txn.status,
        version=txn.version,
        assigned_category=txn.assigned_category,
        category_method=txn.category_method,
        journal_lines=[
            JournalLineResponse(
                id=str(jl.id),
                account_id=str(jl.account_id),
                account_name=jl.account.name if jl.account else None,
                account_code=jl.account.code if jl.account else None,
                debit=float(jl.debit),
                credit=float(jl.credit),
            )
            for jl in txn.journal_lines
        ],
        created_at=txn.created_at,
    )


def _build_account_tree(acc: ChartOfAccounts) -> AccountTreeResponse:
    return AccountTreeResponse(
        id=str(acc.id),
        code=acc.code,
        name=acc.name,
        account_type=acc.account_type,
        tally_group=acc.tally_group,
        is_system=acc.is_system,
        is_cash_or_bank=acc.is_cash_or_bank,
        children=[_build_account_tree(child) for child in (acc.children or []) if not child.deleted_at],
    )
