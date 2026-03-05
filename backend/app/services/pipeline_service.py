"""Document processing pipeline: Upload -> Textract OCR -> Bedrock Validation -> Canonical Invoice.

v2: Inline processing with duplicate handling.
"""
import asyncio
import uuid
import logging
import traceback
from pathlib import Path
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.extraction import Extraction
from app.models.validation import Validation
from app.models.invoice import CanonicalInvoice
from app.services.textract_service import analyze_expense, parse_textract_expense
from app.services.bedrock_service import validate_invoice_fields
from app.utils.gst_validator import (
    validate_gstin, extract_state_from_gstin, is_interstate,
    validate_total_consistency, validate_gst_split,
)
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
        await _set_status(db, doc, "VALIDATED")

        # Step 3: Create canonical invoice
        _log("[PIPELINE]   3/3 Creating canonical invoice...")
        vendor_state = extract_state_from_gstin(structured.get("vendor_gstin"))
        buyer_state = extract_state_from_gstin(structured.get("buyer_gstin"))
        pos = structured.get("place_of_supply") or buyer_state

        invoice_date = _parse_date(structured.get("invoice_date"))
        invoice_number = structured.get("invoice_number") or f"AUTO-{doc.id}"

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
            existing_ci.total = structured.get("total", 0)
            existing_ci.validation_status = "VALID" if overall == "pass" else "PENDING"
        elif existing:
            _log(f"[PIPELINE]   3/3 Duplicate hash already in DB (invoice {existing.id}), linking without new insert")
        else:
            canonical = CanonicalInvoice(
                document_id=doc.id,
                tenant_id=tenant_id,
                document_type=doc.document_type,
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

        await _set_status(db, doc, "DONE")

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
    if not date_str:
        return date.today()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %b %Y", "%d %B %Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return date.today()
