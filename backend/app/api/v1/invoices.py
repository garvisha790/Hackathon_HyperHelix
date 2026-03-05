import uuid
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.dependencies import CurrentUser, TenantId, DB
from app.models.invoice import CanonicalInvoice
from app.models.validation import Validation
from app.models.document import Document
from app.schemas.invoice import CanonicalInvoiceResponse, ValidationResponse, ValidationFieldResult
from app.services.posting_engine import post_invoice
from app.services.tax_service import mark_gst_stale
from app.middleware.audit import log_action
from app.utils.s3 import generate_presigned_download_url

router = APIRouter()


@router.get("/{document_id}", response_model=CanonicalInvoiceResponse)
async def get_invoice(document_id: uuid.UUID, tenant_id: TenantId = None, db: DB = None):
    result = await db.execute(
        select(CanonicalInvoice).where(
            CanonicalInvoice.document_id == document_id,
            CanonicalInvoice.tenant_id == tenant_id,
            CanonicalInvoice.deleted_at.is_(None),
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Invoice not found for this document")

    return CanonicalInvoiceResponse(
        id=str(invoice.id), document_id=str(invoice.document_id),
        document_type=invoice.document_type, invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date, vendor_name=invoice.vendor_name,
        vendor_gstin=invoice.vendor_gstin, vendor_state_code=invoice.vendor_state_code,
        buyer_name=invoice.buyer_name, buyer_gstin=invoice.buyer_gstin,
        buyer_state_code=invoice.buyer_state_code, place_of_supply=invoice.place_of_supply,
        subtotal=float(invoice.subtotal), cgst=float(invoice.cgst), sgst=float(invoice.sgst),
        igst=float(invoice.igst), cess=float(invoice.cess), total=float(invoice.total),
        line_items=invoice.line_items, validation_status=invoice.validation_status,
        is_duplicate=invoice.is_duplicate, created_at=invoice.created_at,
    )


@router.get("/{document_id}/validation", response_model=ValidationResponse)
async def get_validation(document_id: uuid.UUID, tenant_id: TenantId = None, db: DB = None):
    result = await db.execute(
        select(Validation).where(
            Validation.document_id == document_id,
            Validation.tenant_id == tenant_id,
        ).order_by(Validation.created_at.desc()).limit(1)
    )
    validation = result.scalar_one_or_none()
    if not validation:
        raise HTTPException(404, "No validation found for this document")

    field_results = {
        k: ValidationFieldResult(**v) if isinstance(v, dict) else ValidationFieldResult(status="warn", message=str(v))
        for k, v in validation.field_results.items()
    }

    return ValidationResponse(
        id=str(validation.id), document_id=str(validation.document_id),
        overall_status=validation.overall_status, field_results=field_results,
        warnings_count=validation.warnings_count, errors_count=validation.errors_count,
        validated_by=validation.validated_by, created_at=validation.created_at,
    )


@router.get("/{document_id}/download-url")
async def get_download_url(document_id: uuid.UUID, tenant_id: TenantId = None, db: DB = None):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.tenant_id == tenant_id, Document.deleted_at.is_(None)
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    url = generate_presigned_download_url(doc.s3_key)
    return {"download_url": url}


@router.post("/{document_id}/approve")
async def approve_invoice(
    document_id: uuid.UUID,
    user: CurrentUser = None,
    tenant_id: TenantId = None,
    db: DB = None,
):
    result = await db.execute(
        select(CanonicalInvoice).where(
            CanonicalInvoice.document_id == document_id,
            CanonicalInvoice.tenant_id == tenant_id,
            CanonicalInvoice.deleted_at.is_(None),
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Invoice not found")

    if invoice.is_duplicate:
        raise HTTPException(400, "Cannot approve a duplicate invoice")

    invoice.validation_status = "APPROVED"

    txn = await post_invoice(db, invoice, tenant_id)
    await mark_gst_stale(db, tenant_id, invoice.invoice_date)

    doc_result = await db.execute(select(Document).where(Document.id == document_id))
    doc = doc_result.scalar_one()
    doc.status = "DONE"

    await log_action(db, tenant_id, user.id, "invoice.approve", "canonical_invoice", invoice.id)
    await db.flush()

    return {"status": "approved", "transaction_id": str(txn.id)}


@router.post("/{document_id}/reject")
async def reject_invoice(
    document_id: uuid.UUID,
    reason: str = "Rejected by user",
    user: CurrentUser = None,
    tenant_id: TenantId = None,
    db: DB = None,
):
    result = await db.execute(
        select(CanonicalInvoice).where(
            CanonicalInvoice.document_id == document_id,
            CanonicalInvoice.tenant_id == tenant_id,
            CanonicalInvoice.deleted_at.is_(None),
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Invoice not found")

    invoice.validation_status = "REJECTED"

    await log_action(db, tenant_id, user.id, "invoice.reject", "canonical_invoice", invoice.id, {"reason": reason})
    return {"status": "rejected"}
