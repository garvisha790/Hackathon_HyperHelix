"""Document processing pipeline: Upload -> Textract OCR -> Bedrock Validation -> Canonical Invoice.

v2: Inline processing with duplicate handling.
"""
import asyncio
import uuid
import logging
import traceback
from pathlib import Path
import re
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.extraction import Extraction
from app.models.validation import Validation
from app.models.invoice import CanonicalInvoice
from app.models.tenant import Tenant
from app.services.textract_service import analyze_expense, parse_textract_expense
from app.services.bedrock_service import validate_invoice_fields, generate_ai_review, classify_document
from app.utils.gst_validator import (
    validate_gstin, extract_state_from_gstin, is_interstate,
    validate_total_consistency, validate_gst_split,
)
from app.services.posting_engine import post_invoice
from app.services.tax_service import mark_gst_stale
from app.utils.duplicate_detector import compute_duplicate_hash, check_duplicate


logger = logging.getLogger(__name__)
_LOG_FILE = Path(__file__).resolve().parent.parent.parent / "pipeline.log"


def _log(msg: str):
    """Write to both the logger AND directly to the log file for guaranteed visibility."""
    logger.info(msg)
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%H:%M:%S')} {msg}\n")
    except Exception:
        pass


async def _set_status(db: AsyncSession, doc: Document, status: str):
    """Update document status and commit immediately so the frontend can poll."""
    doc.status = status
    await db.commit()
    _log(f"[PIPELINE]   Status -> {status}")


async def process_document(db: AsyncSession, document_id: uuid.UUID, tenant_id: uuid.UUID):
    """Full pipeline: OCR -> Validate -> Create Canonical Invoice."""
    _log(f"[PIPELINE] === process_document called for {document_id} ===")

    doc = await db.get(Document, document_id)
    if not doc:
        _log(f"[PIPELINE] ERROR: Document {document_id} not found in DB!")
        return

    _log(f"[PIPELINE] Found doc: file={doc.file_name}, s3_key={doc.s3_key}, status={doc.status}")

    try:
        await _set_status(db, doc, "PROCESSING")
        _log(f"[PIPELINE] ▶ Starting pipeline for {doc.file_name} (id={document_id})")

        # Step 1: Textract OCR
        _log(f"[PIPELINE]   1/3 Calling Textract on s3://{doc.s3_key} ...")
        try:
            raw_response = await asyncio.to_thread(analyze_expense, doc.s3_key)
        except Exception as tex_err:
            _log(f"[PIPELINE]   1/3 Textract EXCEPTION: {type(tex_err).__name__}: {tex_err}")
            raise

        structured = parse_textract_expense(raw_response)
        avg_confidence = _avg_confidence(structured.get("raw_fields", {}))
        _log(
            f"[PIPELINE]   1/3 Textract done — vendor={structured.get('vendor_name')}, "
            f"total={structured.get('total')}, confidence={avg_confidence}, "
            f"fields={len(structured.get('raw_fields', {}))}, "
            f"line_items={len(structured.get('line_items', []))}"
        )

        extraction = Extraction(
            document_id=doc.id,
            tenant_id=tenant_id,
            raw_textract_json=raw_response,
            structured_data=structured,
            confidence_score=avg_confidence,
        )
        db.add(extraction)
        await db.flush()
        await _set_status(db, doc, "EXTRACTED")

        # Step 2: Validation
        _log("[PIPELINE]   2/3 Running algorithmic validation...")
        algo_results = _algorithmic_validation(structured)
        algo_summary = ", ".join(f"{k}={v['status']}" for k, v in algo_results.items())
        _log(f"[PIPELINE]   2/3 Algo results: {algo_summary}")

        validated_by = "algo"
        try:
            _log("[PIPELINE]   2/3 Calling Bedrock for AI validation...")
            bedrock_results = await asyncio.to_thread(validate_invoice_fields, structured)
            validated_by = "bedrock+algo"
            _log(f"[PIPELINE]   2/3 Bedrock done — overall={bedrock_results.get('overall_status')}")
        except Exception as be:
            _log(f"[PIPELINE]   2/3 Bedrock skipped: {type(be).__name__}: {be}")
            bedrock_results = {"field_results": {}, "overall_status": "warn", "summary": "AI validation unavailable"}

        merged_results = _merge_validations(algo_results, bedrock_results)
        overall = _compute_overall_status(merged_results)
        warnings = sum(1 for v in merged_results.values() if v["status"] == "warn")
        errors = sum(1 for v in merged_results.values() if v["status"] == "fail")
        _log(f"[PIPELINE]   2/3 Validation complete — overall={overall}, warnings={warnings}, errors={errors}, by={validated_by}")

        validation = Validation(
            document_id=doc.id,
            extraction_id=extraction.id,
            tenant_id=tenant_id,
            field_results=merged_results,
            overall_status=overall,
            warnings_count=warnings,
            errors_count=errors,
            validated_by=validated_by,
        )
        db.add(validation)
        await db.flush()

        if overall in ("fail", "warn"):
            _log("[PIPELINE]   2.5/3 Generating AI suggestions...")
            try:
                ai_review = await asyncio.to_thread(
                    generate_ai_review, 
                    structured, 
                    merged_results,
                    raw_response
                )
                validation.ai_suggestions = ai_review
                _log(f"[PIPELINE]   2.5/3 Generated {len(ai_review.get('suggestions', []))} suggestions")
            except Exception as e:
                _log(f"[PIPELINE]   2.5/3 AI suggestions failed: {e}")

        await _set_status(db, doc, "VALIDATED")

        # Step 2.8: Classify document (purchase vs sale vs credit note etc.)
        _log("[PIPELINE]   2.8 Classifying document type...")
        tenant = await db.get(Tenant, tenant_id)
        tenant_gstin = tenant.gstin if tenant else None
        try:
            classification = await asyncio.to_thread(classify_document, structured, tenant_gstin, raw_response)
        except Exception as cls_err:
            _log(f"[PIPELINE]   2.8 Classification failed, defaulting to purchase: {cls_err}")
            classification = {"transaction_nature": "purchase", "document_type": "invoice", "confidence": 0.3, "method": "fallback"}
        _log(f"[PIPELINE]   2.8 Classification: nature={classification['transaction_nature']}, "
             f"doc_type={classification['document_type']}, confidence={classification['confidence']}, "
             f"method={classification['method']}")

        classified_nature = classification["transaction_nature"]
        classified_doc_type = classification.get("document_type", "invoice")
        # Always trust AI classification for document_type when confidence is reasonable
        effective_doc_type = classified_doc_type if classification['confidence'] >= 0.4 else doc.document_type
        _log(f"[PIPELINE]   2.8 Effective doc_type={effective_doc_type} (AI={classified_doc_type}, upload={doc.document_type})")

        # Step 3: Create canonical invoice
        _log("[PIPELINE]   3/3 Creating canonical invoice...")
        from app.utils.gst_validator import normalize_state_to_code
        vendor_state = extract_state_from_gstin(structured.get("vendor_gstin"))
        buyer_state = extract_state_from_gstin(structured.get("buyer_gstin"))
        pos_raw = structured.get("place_of_supply") or buyer_state
        pos = normalize_state_to_code(pos_raw) if pos_raw else None
        vendor_state = normalize_state_to_code(vendor_state) if vendor_state else None
        buyer_state = normalize_state_to_code(buyer_state) if buyer_state else None

        raw_date_str = structured.get("invoice_date")
        invoice_date = _parse_date(raw_date_str)
        _log(f"[PIPELINE]   3/3 Date: raw='{raw_date_str}' -> parsed={invoice_date}")
        invoice_number = structured.get("invoice_number") or f"AUTO-{doc.id}"

        # For debit/credit notes: use AI-detected document number if available
        ai_doc_number = classification.get("document_number")
        ai_original_ref = classification.get("original_invoice_ref")
        if ai_doc_number and effective_doc_type in ("credit_note", "debit_note"):
            _log(f"[PIPELINE]   3/3 AI detected doc number: {ai_doc_number} (OCR had: {invoice_number})")
            # Store the OCR-extracted number as the original invoice reference
            original_invoice_ref = ai_original_ref or invoice_number
            invoice_number = ai_doc_number
        else:
            original_invoice_ref = ai_original_ref

        dup_hash = compute_duplicate_hash(
            tenant_id,
            structured.get("vendor_gstin"),
            invoice_number,
            str(invoice_date),
            structured.get("total", 0),
        )
        existing = await check_duplicate(db, tenant_id, dup_hash)
        if existing:
            _log(f"[PIPELINE]   3/3 Duplicate detected! Matches invoice {existing.id}")

        from sqlalchemy import select as sa_select

        existing_ci_result = await db.execute(
            sa_select(CanonicalInvoice).where(CanonicalInvoice.document_id == doc.id)
        )
        existing_ci = existing_ci_result.scalar_one_or_none()

        if existing_ci:
            _log(f"[PIPELINE]   3/3 Canonical invoice already exists for this doc, updating")
            existing_ci.invoice_number = invoice_number
            existing_ci.invoice_date = invoice_date
            existing_ci.vendor_name = structured.get("vendor_name")
            existing_ci.vendor_gstin = structured.get("vendor_gstin")
            existing_ci.vendor_state_code = vendor_state
            existing_ci.buyer_name = structured.get("buyer_name")
            existing_ci.buyer_gstin = structured.get("buyer_gstin")
            existing_ci.buyer_state_code = buyer_state
            existing_ci.place_of_supply = pos
            existing_ci.subtotal = structured.get("subtotal", 0)
            existing_ci.cgst = structured.get("cgst", 0)
            existing_ci.sgst = structured.get("sgst", 0)
            existing_ci.igst = structured.get("igst", 0)
            existing_ci.cess = structured.get("cess", 0)
            existing_ci.total = structured.get("total", 0)
            existing_ci.line_items = structured.get("line_items", [])
            existing_ci.validation_status = "VALID" if overall == "pass" else "PENDING"
            existing_ci.transaction_nature = classified_nature
            existing_ci.document_type = effective_doc_type
            if original_invoice_ref:
                existing_ci.original_invoice_number = original_invoice_ref
        elif existing:
            _log(f"[PIPELINE]   3/3 Duplicate hash already in DB (invoice {existing.id}), creating duplicate record")
            # Create a duplicate invoice record (is_duplicate=True, duplicate_hash=None to avoid constraint)
            canonical = CanonicalInvoice(
                document_id=doc.id,
                tenant_id=tenant_id,
                document_type=effective_doc_type,
                transaction_nature=classified_nature,
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                vendor_name=structured.get("vendor_name"),
                vendor_gstin=structured.get("vendor_gstin"),
                vendor_state_code=vendor_state,
                buyer_name=structured.get("buyer_name"),
                buyer_gstin=structured.get("buyer_gstin"),
                buyer_state_code=buyer_state,
                place_of_supply=pos,
                subtotal=structured.get("subtotal", 0),
                cgst=structured.get("cgst", 0),
                sgst=structured.get("sgst", 0),
                igst=structured.get("igst", 0),
                cess=structured.get("cess", 0),
                total=structured.get("total", 0),
                line_items=structured.get("line_items", []),
                is_duplicate=True,
                duplicate_of=existing.id,
                duplicate_hash=None,  # Set to None to avoid unique constraint violation
                validation_status="VALID" if overall == "pass" else "PENDING",
            )
            db.add(canonical)
        else:
            canonical = CanonicalInvoice(
                document_id=doc.id,
                tenant_id=tenant_id,
                document_type=effective_doc_type,
                transaction_nature=classified_nature,
                invoice_number=invoice_number,
                invoice_date=invoice_date,
                vendor_name=structured.get("vendor_name"),
                vendor_gstin=structured.get("vendor_gstin"),
                vendor_state_code=vendor_state,
                buyer_name=structured.get("buyer_name"),
                buyer_gstin=structured.get("buyer_gstin"),
                buyer_state_code=buyer_state,
                place_of_supply=pos,
                subtotal=structured.get("subtotal", 0),
                cgst=structured.get("cgst", 0),
                sgst=structured.get("sgst", 0),
                igst=structured.get("igst", 0),
                cess=structured.get("cess", 0),
                total=structured.get("total", 0),
                line_items=structured.get("line_items", []),
                is_duplicate=False,
                duplicate_of=None,
                duplicate_hash=dup_hash,
                validation_status="VALID" if overall == "pass" else "PENDING",
            )
            db.add(canonical)
        await db.flush()

        # Step 4: Post to Ledger (create LedgerTransaction + JournalLines)
        _log("[PIPELINE]   4/4 Posting to ledger...")
        try:
            # Get the canonical invoice we just created/updated
            from sqlalchemy import select as sa_select2
            ci_result = await db.execute(
                sa_select2(CanonicalInvoice).where(CanonicalInvoice.document_id == doc.id)
            )
            ci = ci_result.scalar_one_or_none()
            if ci:
                ledger_txn = await post_invoice(db, ci, tenant_id)
                await mark_gst_stale(db, tenant_id, ci.invoice_date)
                _log(f"[PIPELINE]   4/4 Ledger posted: txn={ledger_txn.id}, category={ledger_txn.assigned_category}")
            else:
                _log("[PIPELINE]   4/4 No canonical invoice found to post (duplicate skipped)")
        except Exception as post_err:
            _log(f"[PIPELINE]   4/4 Ledger posting failed (non-fatal): {type(post_err).__name__}: {post_err}")

        await _set_status(db, doc, "DONE")

        # Invalidate dashboard Redis cache so new data shows instantly
        try:
            import redis.asyncio as aioredis
            from app.config import settings
            redis = await aioredis.from_url(settings.redis_url, decode_responses=True)
            keys = await redis.keys(f"dashboard:{tenant_id}:*")
            if keys:
                await redis.delete(*keys)
                _log(f"[PIPELINE]   Cache invalidated: {len(keys)} dashboard keys")
            await redis.close()
        except Exception:
            pass  # Redis optional


        _log(
            f"[PIPELINE] ✓ Complete — {doc.file_name} | "
            f"invoice#{invoice_number} | date={invoice_date} | "
            f"total={structured.get('total')} | status={overall}"
        )

    except Exception as e:
        _log(f"[PIPELINE] ✗ FAILED for {document_id}: {type(e).__name__}: {e}")
        try:
            with open(_LOG_FILE, "a", encoding="utf-8") as f:
                traceback.print_exc(file=f)
        except Exception:
            pass
        try:
            await db.rollback()
            doc_reload = await db.get(Document, document_id)
            if doc_reload:
                doc_reload.status = "FAILED"
                await db.commit()
        except Exception as db_err:
            _log(f"[PIPELINE] Could not set FAILED status: {db_err}")


def _avg_confidence(raw_fields: dict) -> float:
    confidences = [f.get("confidence", 0) for f in raw_fields.values() if isinstance(f, dict)]
    return round(sum(confidences) / max(len(confidences), 1), 2)


def _algorithmic_validation(structured: dict) -> dict:
    """Run rule-based validations (no LLM needed)."""
    results = {}

    vendor_gstin = structured.get("vendor_gstin")
    if vendor_gstin:
        gstin_check = validate_gstin(vendor_gstin)
        results["vendor_gstin"] = {
            "status": "pass" if gstin_check["valid"] else "fail",
            "message": gstin_check.get("message"),
            "confidence": 1.0,
            "source": "algorithmic",
        }
    else:
        results["vendor_gstin"] = {"status": "warn", "message": "Vendor GSTIN not detected", "confidence": 0.5, "source": "algorithmic"}

    buyer_gstin = structured.get("buyer_gstin")
    if buyer_gstin:
        gstin_check = validate_gstin(buyer_gstin)
        results["buyer_gstin"] = {
            "status": "pass" if gstin_check["valid"] else "fail",
            "message": gstin_check.get("message"),
            "confidence": 1.0,
            "source": "algorithmic",
        }

    total_check = validate_total_consistency(
        structured.get("subtotal", 0), structured.get("cgst", 0),
        structured.get("sgst", 0), structured.get("igst", 0),
        structured.get("cess", 0), structured.get("total", 0),
    )
    results["total"] = {
        "status": "pass" if total_check["valid"] else "fail",
        "message": total_check.get("message"),
        "confidence": 1.0,
        "source": "algorithmic",
    }

    vendor_state = extract_state_from_gstin(vendor_gstin)
    buyer_state = extract_state_from_gstin(buyer_gstin)
    if vendor_state and buyer_state:
        interstate = is_interstate(vendor_state, structured.get("place_of_supply") or buyer_state)
        split_check = validate_gst_split(
            structured.get("cgst", 0), structured.get("sgst", 0),
            structured.get("igst", 0), interstate,
        )
        results["gst_split"] = {
            "status": "pass" if split_check["valid"] else "fail",
            "message": split_check.get("message"),
            "confidence": 1.0,
            "source": "algorithmic",
        }

    return results


def _merge_validations(algo: dict, bedrock: dict) -> dict:
    """Merge algorithmic and Bedrock validations. Algorithmic takes precedence."""
    merged = {}
    bedrock_fields = bedrock.get("field_results", {})

    for key in set(list(algo.keys()) + list(bedrock_fields.keys())):
        if key in algo and algo[key].get("source") == "algorithmic":
            merged[key] = algo[key]
        elif key in bedrock_fields:
            merged[key] = bedrock_fields[key]
        elif key in algo:
            merged[key] = algo[key]

    return merged


def _compute_overall_status(results: dict) -> str:
    statuses = [v.get("status", "pass") for v in results.values()]
    if "fail" in statuses:
        return "fail"
    if "warn" in statuses:
        return "warn"
    return "pass"


def _parse_date(date_str: str | None) -> date:
    logger = logging.getLogger("taxodo.pipeline")
    if not date_str:
        logger.warning("[PARSE_DATE] No date string provided, using today")
        return date.today()

    cleaned = date_str.strip()

    # Try explicit strptime formats first (most common Indian/international)
    for fmt in (
        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %b %Y", "%d %B %Y",
        "%m/%d/%Y", "%Y/%m/%d", "%d.%m.%Y", "%b %d, %Y", "%B %d, %Y",
        "%d-%b-%Y", "%d-%B-%Y", "%d %b, %Y", "%d %B, %Y",
        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ",
    ):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue

    # Fallback: python-dateutil (handles almost any format)
    try:
        from dateutil import parser as du_parser
        parsed = du_parser.parse(cleaned, dayfirst=True).date()
        logger.info(f"[PARSE_DATE] dateutil parsed '{cleaned}' -> {parsed}")
        return parsed
    except Exception:
        pass

    # Last resort: regex extract any date-like pattern
    m = re.search(r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})', cleaned)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if d > 12:  # day-first
            try:
                return date(y, mo, d)
            except ValueError:
                pass
        try:
            return date(y, mo, d)
        except ValueError:
            pass

    logger.warning(f"[PARSE_DATE] Could not parse '{cleaned}', using today")
    return date.today()
