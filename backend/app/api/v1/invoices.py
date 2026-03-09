import uuid
import asyncio
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.dependencies import CurrentUser, TenantId, DB
from app.models.invoice import CanonicalInvoice
from app.models.validation import Validation
from app.models.document import Document
from app.schemas.invoice import CanonicalInvoiceResponse, ValidationResponse, ValidationFieldResult, CanonicalInvoiceUpdateRequest, AISuggestionResponse
from app.services.posting_engine import post_invoice
from app.services.tax_service import mark_gst_stale
from app.services.bedrock_service import validate_invoice_fields, generate_ai_review, generate_approval_error_review
from app.middleware.audit import log_action
from app.utils.s3 import generate_presigned_download_url

router = APIRouter()


@router.get("/{document_id}", response_model=CanonicalInvoiceResponse)
async def get_invoice(document_id: uuid.UUID, tenant_id: TenantId = None, db: DB = None):
    # First, try to find invoice directly linked to this document
    result = await db.execute(
        select(CanonicalInvoice).where(
            CanonicalInvoice.document_id == document_id,
            CanonicalInvoice.tenant_id == tenant_id,
            CanonicalInvoice.deleted_at.is_(None),
        )
    )
    invoice = result.scalar_one_or_none()
    
    # If not found, this might be a duplicate document - find the original invoice
    if not invoice:
        # Get the document to check its extraction data
        doc_result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.tenant_id == tenant_id,
                Document.deleted_at.is_(None),
            )
        )
        doc = doc_result.scalar_one_or_none()
        
        if doc and doc.status == "DONE":
            # Get the extraction to compute duplicate hash
            from app.models.extraction import Extraction
            from app.utils.duplicate_detector import compute_duplicate_hash
            
            extraction_result = await db.execute(
                select(Extraction).where(
                    Extraction.document_id == document_id,
                    Extraction.tenant_id == tenant_id,
                ).order_by(Extraction.created_at.desc()).limit(1)
            )
            extraction = extraction_result.scalar_one_or_none()
            
            if extraction:
                structured = extraction.structured_data
                # Compute the duplicate hash
                dup_hash = compute_duplicate_hash(
                    tenant_id,
                    structured.get("vendor_gstin"),
                    structured.get("invoice_number", ""),
                    str(structured.get("invoice_date", "")),
                    structured.get("total", 0),
                )
                
                # Find the original invoice with this hash
                original_result = await db.execute(
                    select(CanonicalInvoice).where(
                        CanonicalInvoice.tenant_id == tenant_id,
                        CanonicalInvoice.duplicate_hash == dup_hash,
                        CanonicalInvoice.is_duplicate.is_(False),
                        CanonicalInvoice.deleted_at.is_(None),
                    )
                )
                invoice = original_result.scalar_one_or_none()
    
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
    # First try to find validation for this document
    result = await db.execute(
        select(Validation).where(
            Validation.document_id == document_id,
            Validation.tenant_id == tenant_id,
        ).order_by(Validation.created_at.desc()).limit(1)
    )
    validation = result.scalar_one_or_none()
    
    # If not found and document is a duplicate, get validation from original document
    if not validation:
        # Find the original invoice (using same logic as get_invoice)
        from app.models.extraction import Extraction
        from app.utils.duplicate_detector import compute_duplicate_hash
        
        doc_result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.tenant_id == tenant_id,
                Document.deleted_at.is_(None),
            )
        )
        doc = doc_result.scalar_one_or_none()
        
        if doc and doc.status == "DONE":
            extraction_result = await db.execute(
                select(Extraction).where(
                    Extraction.document_id == document_id,
                    Extraction.tenant_id == tenant_id,
                ).order_by(Extraction.created_at.desc()).limit(1)
            )
            extraction = extraction_result.scalar_one_or_none()
            
            if extraction:
                structured = extraction.structured_data
                dup_hash = compute_duplicate_hash(
                    tenant_id,
                    structured.get("vendor_gstin"),
                    structured.get("invoice_number", ""),
                    str(structured.get("invoice_date", "")),
                    structured.get("total", 0),
                )
                
                # Find original invoice
                original_invoice_result = await db.execute(
                    select(CanonicalInvoice).where(
                        CanonicalInvoice.tenant_id == tenant_id,
                        CanonicalInvoice.duplicate_hash == dup_hash,
                        CanonicalInvoice.is_duplicate.is_(False),
                        CanonicalInvoice.deleted_at.is_(None),
                    )
                )
                original_invoice = original_invoice_result.scalar_one_or_none()
                
                if original_invoice:
                    # Get validation from original document
                    validation_result = await db.execute(
                        select(Validation).where(
                            Validation.document_id == original_invoice.document_id,
                            Validation.tenant_id == tenant_id,
                        ).order_by(Validation.created_at.desc()).limit(1)
                    )
                    validation = validation_result.scalar_one_or_none()
    
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
    is_image = doc.s3_key.lower().endswith((".jpg", ".jpeg", ".png"))
    return {"download_url": url, "is_image": is_image, "file_name": doc.file_name}


@router.get("/{document_id}/extraction")
async def get_extraction(document_id: uuid.UUID, tenant_id: TenantId = None, db: DB = None):
    """Return raw extracted fields with confidence scores for source preview."""
    from app.models.extraction import Extraction
    result = await db.execute(
        select(Extraction).where(
            Extraction.document_id == document_id,
            Extraction.tenant_id == tenant_id,
        ).order_by(Extraction.created_at.desc()).limit(1)
    )
    extraction = result.scalar_one_or_none()
    if not extraction:
        raise HTTPException(404, "No extraction found for this document")

    # Build clean field list from structured_data with confidence from raw_fields
    structured = extraction.structured_data or {}
    raw_fields = structured.get("raw_fields", {})

    fields = []
    key_map = {
        "VENDOR_NAME": "Vendor Name",
        "VENDOR_ADDRESS": "Vendor Address",
        "RECEIVER_NAME": "Buyer Name",
        "INVOICE_RECEIPT_ID": "Invoice Number",
        "INVOICE_RECEIPT_DATE": "Invoice Date",
        "SUBTOTAL": "Subtotal",
        "TAX": "Tax",
        "TOTAL": "Total",
        "VENDOR_PHONE": "Phone",
        "VENDOR_URL": "Website",
        "ACCOUNT_NUMBER": "Account Number",
        "PO_NUMBER": "PO Number",
    }

    for key, display in key_map.items():
        if key in raw_fields:
            f = raw_fields[key]
            fields.append({
                "key": key,
                "label": display,
                "value": f.get("value", ""),
                "confidence": round(f.get("confidence", 0), 1),
            })

    # Add any custom fields not in our map
    for key, f in raw_fields.items():
        if key not in key_map and isinstance(f, dict):
            fields.append({
                "key": key,
                "label": key.replace("_", " ").title(),
                "value": f.get("value", ""),
                "confidence": round(f.get("confidence", 0), 1),
            })

    return {
        "fields": fields,
        "line_items": structured.get("line_items", []),
        "confidence_score": float(extraction.confidence_score or 0),
    }


@router.patch("/{document_id}", response_model=CanonicalInvoiceResponse)
async def update_invoice(
    document_id: uuid.UUID,
    request: CanonicalInvoiceUpdateRequest,
    user: CurrentUser = None,
    tenant_id: TenantId = None,
    db: DB = None,
):
    """Update editable fields on the invoice and re-run AI validation."""
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

    if invoice.validation_status == "APPROVED":
        raise HTTPException(400, "Cannot edit an approved invoice")

    # Apply updates
    updates = request.model_dump(exclude_unset=True)
    if not updates:
        return get_invoice(document_id, tenant_id, db)  # Just return it

    # Normalize state codes to 2-digit format
    from app.utils.gst_validator import normalize_state_to_code
    for field in ("place_of_supply", "vendor_state_code", "buyer_state_code"):
        if field in updates and updates[field]:
            normalized = normalize_state_to_code(str(updates[field]))
            if normalized:
                updates[field] = normalized

    for key, value in updates.items():
        setattr(invoice, key, value)

    # Convert to dict for validation
    inv_data = {
        "vendor_name": invoice.vendor_name,
        "vendor_gstin": invoice.vendor_gstin,
        "buyer_name": invoice.buyer_name,
        "buyer_gstin": invoice.buyer_gstin,
        "invoice_number": invoice.invoice_number,
        "invoice_date": str(invoice.invoice_date) if invoice.invoice_date else None,
        "subtotal": float(invoice.subtotal),
        "total": float(invoice.total),
        "cgst": float(invoice.cgst),
        "sgst": float(invoice.sgst),
        "igst": float(invoice.igst),
        "cess": float(invoice.cess),
        "line_items": invoice.line_items,
    }

    # Re-run validation
    import asyncio
    val_result = await asyncio.to_thread(validate_invoice_fields, inv_data)
    
    invoice.validation_status = "PENDING"  # Reset status after edit
    
    # Get the extraction_id from the latest extraction for this document
    from app.models.extraction import Extraction
    ext_result = await db.execute(
        select(Extraction).where(
            Extraction.document_id == document_id,
            Extraction.tenant_id == tenant_id,
        ).order_by(Extraction.created_at.desc()).limit(1)
    )
    extraction = ext_result.scalar_one_or_none()
    extraction_id = extraction.id if extraction else None

    # Save new validation record
    overall_status = val_result.get("overall_status", "warn")
    new_val = Validation(
        tenant_id=tenant_id,
        document_id=document_id,
        extraction_id=extraction_id,
        overall_status=overall_status,
        field_results=val_result.get("field_results", {}),
        warnings_count=sum(1 for v in val_result.get("field_results", {}).values() if v.get("status") == "warn"),
        errors_count=sum(1 for v in val_result.get("field_results", {}).values() if v.get("status") == "fail"),
        validated_by="bedrock+user",
    )
    db.add(new_val)
    await db.flush()

    if overall_status in ("fail", "warn"):
        try:
            ai_review = await asyncio.to_thread(
                generate_ai_review,
                inv_data,
                val_result.get("field_results", {}),
                {}
            )
            new_val.ai_suggestions = ai_review
        except Exception:
            pass

    await log_action(db, tenant_id, user.id, "invoice.update", "canonical_invoice", invoice.id, {"fields": list(updates.keys())})
    await db.flush()

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


@router.post("/{document_id}/generate-ai-review", response_model=AISuggestionResponse)
async def generate_invoice_ai_review(
    document_id: uuid.UUID,
    user: CurrentUser = None,
    tenant_id: TenantId = None,
    db: DB = None,
):
    """Trigger Bedrock to analyze the invoice against validation errors and suggest field-level fixes."""
    # 1. Fetch current invoice state
    inv_result = await db.execute(
        select(CanonicalInvoice).where(
            CanonicalInvoice.document_id == document_id,
            CanonicalInvoice.tenant_id == tenant_id,
            CanonicalInvoice.deleted_at.is_(None),
        )
    )
    invoice = inv_result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Invoice not found")

    # 2. Fetch latest validation results
    val_result = await db.execute(
        select(Validation).where(
            Validation.document_id == document_id,
            Validation.tenant_id == tenant_id,
        ).order_by(Validation.created_at.desc()).limit(1)
    )
    validation = val_result.scalar_one_or_none()
    if not validation:
        raise HTTPException(404, "Validation results not found for invoice")

    # 3. Compile context for Bedrock
    inv_data = {
        "vendor_name": invoice.vendor_name,
        "vendor_gstin": invoice.vendor_gstin,
        "buyer_name": invoice.buyer_name,
        "buyer_gstin": invoice.buyer_gstin,
        "invoice_number": invoice.invoice_number,
        "invoice_date": str(invoice.invoice_date) if invoice.invoice_date else None,
        "place_of_supply": invoice.place_of_supply,
        "subtotal": float(invoice.subtotal),
        "total": float(invoice.total),
        "cgst": float(invoice.cgst),
        "sgst": float(invoice.sgst),
        "igst": float(invoice.igst),
        "cess": float(invoice.cess),
        "line_items": invoice.line_items,
    }
    val_data = {
        "overall_status": validation.overall_status,
        "field_results": validation.field_results
    }

    # 3b. Also fetch the raw Textract extraction enriched data for richer suggestions
    from app.models.extraction import Extraction
    ext_result = await db.execute(
        select(Extraction).where(
            Extraction.document_id == document_id,
            Extraction.tenant_id == tenant_id,
        ).order_by(Extraction.created_at.desc()).limit(1)
    )
    extraction_record = ext_result.scalar_one_or_none()
    raw_extraction_data = None
    if extraction_record:
        structured = extraction_record.structured_data or {}
        raw_extraction_data = {
            "raw_fields": structured.get("raw_fields", {}),
            "line_items_raw": structured.get("line_items", []),
            "confidence_score": float(extraction_record.confidence_score or 0),
        }

    # 4. Trigger Bedrock Review
    import asyncio
    ai_review = await asyncio.to_thread(generate_ai_review, inv_data, val_data, raw_extraction_data)

    # 5. Log the action
    await log_action(db, tenant_id, user.id, "invoice.generate_ai_review", "canonical_invoice", invoice.id)
    await db.flush()

    return ai_review


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

    if invoice.validation_status == "APPROVED":
        raise HTTPException(400, "Invoice already approved")

    invoice.validation_status = "APPROVED"

    try:
        txn = await post_invoice(db, invoice, tenant_id)
        await mark_gst_stale(db, tenant_id, invoice.invoice_date)
    except ValueError as e:
        # Approval failed - rollback status and generate AI suggestions
        invoice.validation_status = "PENDING"
        await db.flush()
        
        # Generate AI review for the approval error
        invoice_data = {
            "vendor_name": invoice.vendor_name,
            "invoice_number": invoice.invoice_number,
            "invoice_date": str(invoice.invoice_date) if invoice.invoice_date else None,
            "vendor_gstin": invoice.vendor_gstin,
            "buyer_gstin": invoice.buyer_gstin,
            "place_of_supply": invoice.place_of_supply,
            "subtotal": float(invoice.subtotal or 0),
            "cgst": float(invoice.cgst or 0),
            "sgst": float(invoice.sgst or 0),
            "igst": float(invoice.igst or 0),
            "cess": float(invoice.cess or 0),
            "total": float(invoice.total or 0),
            "line_items": invoice.line_items if invoice.line_items else [],
        }
        
        try:
            ai_suggestions = await asyncio.to_thread(
                generate_approval_error_review,
                invoice_data,
                str(e)
            )
        except Exception as ai_err:
            print(f"[APPROVE] AI suggestion generation failed: {ai_err}")
            ai_suggestions = {
                "error_type": "approval_failed",
                "root_cause": str(e),
                "suggestions": [],
                "summary": "Approval failed. Please review the invoice data."
            }
        
        raise HTTPException(
            status_code=400,
            detail={
                "error": str(e),
                "ai_suggestions": ai_suggestions
            }
        )

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
