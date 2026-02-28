"""AI Copilot: RAG-based Q&A over financial data.

Three-step process:
1. Intent classification (SQL aggregate / document lookup / explanation)
2. Data retrieval (guardrailed SQL or vector search)
3. Grounded answer generation with citations
"""
import uuid
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func

from app.models.invoice import CanonicalInvoice
from app.models.ledger import LedgerTransaction, JournalLine, ChartOfAccounts
from app.models.tax import GSTSummary
from app.services.bedrock_service import copilot_query, _invoke_claude


INTENT_PROMPT = """Classify this user question into exactly ONE intent:
- "sql_aggregate": Questions about totals, sums, counts, comparisons (e.g., "How much did I spend?", "Total GST this month?")
- "document_lookup": Questions about specific invoices or vendors (e.g., "Show invoices from Reliance", "Find invoice #123")
- "explanation": Questions asking why or how (e.g., "Why is my GST higher?", "How does ITC work?")

Question: {question}

Return ONLY a JSON: {{"intent": "sql_aggregate|document_lookup|explanation"}}"""


async def handle_copilot_query(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    question: str,
) -> dict:
    """Process a natural language financial question."""
    intent = _classify_intent(question)

    if intent == "sql_aggregate":
        context = await _get_aggregate_context(db, tenant_id, question)
    elif intent == "document_lookup":
        context = await _get_document_context(db, tenant_id, question)
    else:
        context = await _get_general_context(db, tenant_id)

    if not context or context.strip() == "No data found.":
        return {
            "answer": "I don't have enough data to answer this question. Try uploading more documents or ask about a different period.",
            "intent": intent,
            "has_data": False,
            "sources": [],
        }

    result = copilot_query(question, context)
    return {
        "answer": result["answer"],
        "intent": intent,
        "has_data": result["has_data"],
        "sources": [],
    }


def _classify_intent(question: str) -> str:
    try:
        raw = _invoke_claude(INTENT_PROMPT.format(question=question), max_tokens=64)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(cleaned)
        return data.get("intent", "explanation")
    except Exception:
        return "explanation"


async def _get_aggregate_context(db: AsyncSession, tenant_id: uuid.UUID, question: str) -> str:
    """Build context from ledger aggregates."""
    lines = []

    rev_result = await db.execute(
        select(func.coalesce(func.sum(JournalLine.credit), 0)).select_from(JournalLine).join(
            LedgerTransaction, JournalLine.transaction_id == LedgerTransaction.id
        ).join(ChartOfAccounts, JournalLine.account_id == ChartOfAccounts.id).where(
            LedgerTransaction.tenant_id == tenant_id,
            LedgerTransaction.deleted_at.is_(None),
            ChartOfAccounts.account_type == "revenue",
        )
    )
    total_revenue = float(rev_result.scalar() or 0)
    lines.append(f"Total Revenue: Rs {total_revenue:,.2f}")

    exp_result = await db.execute(
        select(func.coalesce(func.sum(JournalLine.debit), 0)).select_from(JournalLine).join(
            LedgerTransaction, JournalLine.transaction_id == LedgerTransaction.id
        ).join(ChartOfAccounts, JournalLine.account_id == ChartOfAccounts.id).where(
            LedgerTransaction.tenant_id == tenant_id,
            LedgerTransaction.deleted_at.is_(None),
            ChartOfAccounts.account_type == "expense",
        )
    )
    total_expenses = float(exp_result.scalar() or 0)
    lines.append(f"Total Expenses: Rs {total_expenses:,.2f}")
    lines.append(f"Net Profit: Rs {total_revenue - total_expenses:,.2f}")

    gst_result = await db.execute(
        select(GSTSummary).where(GSTSummary.tenant_id == tenant_id).order_by(GSTSummary.period_start.desc()).limit(6)
    )
    for s in gst_result.scalars().all():
        output = float(s.output_cgst + s.output_sgst + s.output_igst)
        inp = float(s.input_cgst + s.input_sgst + s.input_igst)
        lines.append(f"GST Period {s.period_start} to {s.period_end}: Output Rs {output:,.2f}, Input Rs {inp:,.2f}, Net Rs {float(s.net_liability):,.2f}")

    cat_result = await db.execute(
        select(LedgerTransaction.assigned_category, func.sum(JournalLine.debit)).select_from(JournalLine).join(
            LedgerTransaction, JournalLine.transaction_id == LedgerTransaction.id
        ).join(ChartOfAccounts, JournalLine.account_id == ChartOfAccounts.id).where(
            LedgerTransaction.tenant_id == tenant_id,
            LedgerTransaction.deleted_at.is_(None),
            ChartOfAccounts.account_type == "expense",
        ).group_by(LedgerTransaction.assigned_category)
    )
    for cat, amount in cat_result.all():
        lines.append(f"Expense Category '{cat or 'Uncategorized'}': Rs {float(amount or 0):,.2f}")

    return "\n".join(lines) if lines else "No data found."


async def _get_document_context(db: AsyncSession, tenant_id: uuid.UUID, question: str) -> str:
    """Build context from invoice records."""
    result = await db.execute(
        select(CanonicalInvoice).where(
            CanonicalInvoice.tenant_id == tenant_id,
            CanonicalInvoice.deleted_at.is_(None),
        ).order_by(CanonicalInvoice.invoice_date.desc()).limit(20)
    )
    invoices = result.scalars().all()
    if not invoices:
        return "No data found."

    lines = []
    for inv in invoices:
        lines.append(
            f"Invoice #{inv.invoice_number} | Date: {inv.invoice_date} | "
            f"Vendor: {inv.vendor_name} | GSTIN: {inv.vendor_gstin} | "
            f"Total: Rs {float(inv.total):,.2f} | Type: {inv.document_type}"
        )
    return "\n".join(lines)


async def _get_general_context(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    """Provide general financial context for explanation queries."""
    agg = await _get_aggregate_context(db, tenant_id, "")
    doc = await _get_document_context(db, tenant_id, "")
    return f"FINANCIAL SUMMARY:\n{agg}\n\nRECENT INVOICES:\n{doc}"
