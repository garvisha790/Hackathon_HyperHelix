"""AWS Textract integration using AnalyzeExpense API optimized for invoices.

Strategy:
  1. Try synchronous AnalyzeExpense with raw bytes (works for single-page docs).
  2. If Textract rejects the bytes (multi-page PDF → UnsupportedDocumentException),
     fall back to the async StartExpenseAnalysis API using the S3 reference.
     We poll until the job is SUCCEEDED or FAILED (max ~120 s).
"""
import time
import logging
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_POLL_INTERVAL = 3   # seconds between GetExpenseAnalysis calls
_POLL_TIMEOUT  = 120 # maximum seconds to wait for async job


def _get_textract_client():
    return boto3.client(
        "textract",
        region_name=settings.textract_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
        config=Config(connect_timeout=10, read_timeout=60, retries={"max_attempts": 2}),
    )


def _get_s3_client():
    """Return an S3 client for downloading document bytes."""
    from app.utils.s3 import _get_s3_client as s3_client_factory
    return s3_client_factory()


def _analyze_expense_sync(file_bytes: bytes) -> dict:
    """Synchronous AnalyzeExpense – works for single-page PDFs and images."""
    client = _get_textract_client()
    return client.analyze_expense(Document={"Bytes": file_bytes})


def _analyze_expense_async(s3_key: str) -> dict:
    """
    Async StartExpenseAnalysis – handles multi-page PDFs via S3 reference.
    Polls until the job finishes, then aggregates all pages into one response
    that matches the synchronous AnalyzeExpense response shape.
    """
    client = _get_textract_client()

    logger.info("[Textract] Starting async expense analysis job for key=%s", s3_key)
    start_resp = client.start_expense_analysis(
        DocumentLocation={
            "S3Object": {
                "Bucket": settings.s3_bucket_name,
                "Name": s3_key,
            }
        }
    )
    job_id = start_resp["JobId"]
    logger.info("[Textract] Async job started: JobId=%s", job_id)

    # Poll for completion
    deadline = time.time() + _POLL_TIMEOUT
    all_expense_docs: list = []
    next_token = None

    while time.time() < deadline:
        time.sleep(_POLL_INTERVAL)

        kwargs: dict = {"JobId": job_id}
        if next_token:
            kwargs["NextToken"] = next_token

        resp = client.get_expense_analysis(**kwargs)
        status = resp.get("JobStatus")
        logger.info("[Textract] Polling job %s → status=%s", job_id, status)

        if status == "FAILED":
            raise RuntimeError(
                f"Textract async job {job_id} FAILED: "
                f"{resp.get('StatusMessage', 'No message')}"
            )

        if status == "SUCCEEDED":
            all_expense_docs.extend(resp.get("ExpenseDocuments", []))
            next_token = resp.get("NextToken")
            # Fetch remaining pages of results
            while next_token:
                time.sleep(0.5)
                page_resp = client.get_expense_analysis(JobId=job_id, NextToken=next_token)
                all_expense_docs.extend(page_resp.get("ExpenseDocuments", []))
                next_token = page_resp.get("NextToken")
            break
    else:
        raise TimeoutError(
            f"Textract async job {job_id} did not complete within {_POLL_TIMEOUT}s"
        )

    logger.info(
        "[Textract] Async job %s succeeded. Pages/docs=%d", job_id, len(all_expense_docs)
    )
    # Return a response in the same shape as synchronous AnalyzeExpense
    return {"ExpenseDocuments": all_expense_docs}


def analyze_expense(s3_key: str) -> dict:
    """
    Smart entry point: try synchronous first (bytes), fall back to async (S3).

    - Single-page PDFs / images → synchronous bytes-based call (fast).
    - Multi-page PDFs           → async job via S3 reference + polling.
    """
    from app.utils.s3 import get_s3_object_bytes

    # Attempt 1: synchronous with bytes
    try:
        file_bytes = get_s3_object_bytes(s3_key)
        logger.info("[Textract] Trying sync AnalyzeExpense (%d bytes) …", len(file_bytes))
        return _analyze_expense_sync(file_bytes)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code != "UnsupportedDocumentException":
            raise  # re-raise unexpected errors
        logger.warning(
            "[Textract] Sync AnalyzeExpense failed with %s — "
            "falling back to async StartExpenseAnalysis for multi-page PDF.",
            code,
        )

    # Attempt 2: async via S3 reference
    return _analyze_expense_async(s3_key)


import re

def _parse_currency(val: str) -> float:
    """Robustly extract float from currency strings like 'Rs. 404.00'."""
    if not val:
        return 0.0
    # Strip common prefixes and commas
    cleaned = val.upper().replace("RS.", "").replace("RS", "").replace("INR", "").replace("₹", "").replace(",", "")
    # Remove any remaining letters/symbols except digits, dot, and minus
    cleaned = re.sub(r'[^\d\.-]', '', cleaned).strip()
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def parse_textract_expense(raw_response: dict) -> dict:
    """Parse Textract AnalyzeExpense response into structured invoice fields."""
    structured = {
        "vendor_name": None,
        "vendor_gstin": None,
        "buyer_name": None,
        "buyer_gstin": None,
        "invoice_number": None,
        "invoice_date": None,
        "subtotal": 0,
        "total": 0,
        "cgst": 0,
        "sgst": 0,
        "igst": 0,
        "cess": 0,
        "place_of_supply": None,
        "line_items": [],
        "raw_fields": {},
    }

    for doc in raw_response.get("ExpenseDocuments", []):
        for field in doc.get("SummaryFields", []):
            field_type = field.get("Type", {}).get("Text", "").upper()
            label_text = field.get("LabelDetection", {}).get("Text", "").upper()
            value = field.get("ValueDetection", {}).get("Text", "")
            confidence = field.get("ValueDetection", {}).get("Confidence", 0)

            # Keep raw fields for confidence rendering
            # We append the label text to the key to avoid overwriting multiple TAX fields
            raw_key = f"{field_type}_{label_text}".strip("_") if field_type == "TAX" else field_type
            structured["raw_fields"][raw_key] = {
                "value": value,
                "confidence": confidence,
            }

            key = None
            mapping = {
                "VENDOR_NAME": "vendor_name",
                "NAME": "vendor_name",
                "RECEIVER_NAME": "buyer_name",
                "INVOICE_RECEIPT_ID": "invoice_number",
                "INVOICE_RECEIPT_DATE": "invoice_date",
                "SUBTOTAL": "subtotal",
                "TOTAL": "total",
            }

            if field_type in mapping:
                key = mapping[field_type]
            elif field_type == "TAX":
                if "CGST" in label_text:
                    key = "cgst"
                elif "SGST" in label_text:
                    key = "sgst"
                elif "IGST" in label_text:
                    key = "igst"
                else:
                    # Default generic tax to IGST if we can't determine
                    key = "igst"

            if key:
                if key in ("subtotal", "total", "igst", "cgst", "sgst", "cess"):
                    val_float = _parse_currency(value)
                    if key in ("cgst", "sgst", "igst", "cess"):
                        structured[key] += val_float  # aggregate multiple tax lines
                    else:
                        structured[key] = val_float
                else:
                    structured[key] = value

            if "GSTIN" in field_type or "GST" in field_type:
                gstin_match = re.search(r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]", value)
                if gstin_match:
                    gstin = gstin_match.group()
                    if not structured["vendor_gstin"]:
                        structured["vendor_gstin"] = gstin
                    elif not structured["buyer_gstin"]:
                        structured["buyer_gstin"] = gstin

        for line_item_group in doc.get("LineItemGroups", []):
            for line_item in line_item_group.get("LineItems", []):
                item = {"description": "", "qty": 1, "rate": 0, "taxable_value": 0, "hsn_sac": None}
                for expense_field in line_item.get("LineItemExpenseFields", []):
                    ft = expense_field.get("Type", {}).get("Text", "").upper()
                    val = expense_field.get("ValueDetection", {}).get("Text", "")

                    if ft in ("ITEM", "DESCRIPTION", "PRODUCT_CODE"):
                        item["description"] = val
                    elif ft == "QUANTITY":
                        try:
                            item["qty"] = float(val.replace(",", ""))
                        except (ValueError, TypeError):
                            pass
                    elif ft in ("UNIT_PRICE", "PRICE"):
                        rate = _parse_currency(val)
                        if rate > 0:
                            item["rate"] = rate
                    elif ft == "EXPENSE_ROW_TOTAL":
                        taxable = _parse_currency(val)
                        if taxable > 0:
                            item["taxable_value"] = taxable

                if item["description"] or item["taxable_value"]:
                    structured["line_items"].append(item)

    return structured
