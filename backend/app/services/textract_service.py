"""AWS Textract integration using AnalyzeExpense API optimized for invoices."""
import time
import logging
import boto3
from botocore.config import Config
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def _get_textract_client():
    return boto3.client(
        "textract",
        region_name=settings.textract_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
        config=Config(connect_timeout=10, read_timeout=60, retries={"max_attempts": 2}),
    )


def _analyze_expense_async(s3_key: str) -> dict:
    """Async Textract job for multi-page PDFs. Polls until complete (max 60s)."""
    client = _get_textract_client()
    logger.info(f"[TEXTRACT] Starting async expense analysis for {s3_key}")

    job = client.start_expense_analysis(
        DocumentLocation={
            "S3Object": {
                "Bucket": settings.s3_bucket_name,
                "Name": s3_key,
            }
        }
    )
    job_id = job["JobId"]
    logger.info(f"[TEXTRACT] Async job started: {job_id}")

    # Poll with backoff — max 60 seconds
    for attempt in range(12):
        time.sleep(5)
        result = client.get_expense_analysis(JobId=job_id)
        status = result["JobStatus"]
        logger.info(f"[TEXTRACT] Job {job_id} status: {status} (attempt {attempt + 1})")

        if status == "SUCCEEDED":
            # Merge all pages into a single response structure
            all_docs = result.get("ExpenseDocuments", [])
            # Fetch remaining pages if paginated
            next_token = result.get("NextToken")
            while next_token:
                page = client.get_expense_analysis(JobId=job_id, NextToken=next_token)
                all_docs.extend(page.get("ExpenseDocuments", []))
                next_token = page.get("NextToken")
            logger.info(f"[TEXTRACT] Async job complete — {len(all_docs)} expense documents")
            return {"ExpenseDocuments": all_docs}

        if status == "FAILED":
            raise RuntimeError(f"Textract async job failed: {result.get('StatusMessage', 'unknown')}")

    raise TimeoutError(f"Textract async job {job_id} did not complete within 60s")


def analyze_expense(s3_key: str) -> dict:
    """Call Textract AnalyzeExpense on an S3 object.

    Tries the synchronous API first (fast, single-page).
    Falls back to asynchronous API for multi-page PDFs.
    """
    client = _get_textract_client()
    try:
        response = client.analyze_expense(
            Document={
                "S3Object": {
                    "Bucket": settings.s3_bucket_name,
                    "Name": s3_key,
                }
            }
        )
        return response
    except client.exceptions.UnsupportedDocumentException:
        logger.warning(f"[TEXTRACT] Sync AnalyzeExpense rejected {s3_key} — trying async (multi-page PDF)")
        return _analyze_expense_async(s3_key)


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
            value = field.get("ValueDetection", {}).get("Text", "")
            confidence = field.get("ValueDetection", {}).get("Confidence", 0)

            structured["raw_fields"][field_type] = {
                "value": value,
                "confidence": confidence,
            }

            mapping = {
                "VENDOR_NAME": "vendor_name",
                "NAME": "vendor_name",
                "RECEIVER_NAME": "buyer_name",
                "INVOICE_RECEIPT_ID": "invoice_number",
                "INVOICE_RECEIPT_DATE": "invoice_date",
                "SUBTOTAL": "subtotal",
                "TOTAL": "total",
                "TAX": "igst",
            }

            if field_type in mapping:
                key = mapping[field_type]
                if key in ("subtotal", "total", "igst", "cgst", "sgst"):
                    try:
                        cleaned = value.replace(",", "").replace("₹", "").replace("Rs", "").strip()
                        structured[key] = float(cleaned)
                    except (ValueError, TypeError):
                        pass
                else:
                    structured[key] = value

            if "GSTIN" in field_type or "GST" in field_type:
                import re
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
                        try:
                            item["rate"] = float(val.replace(",", "").replace("₹", "").strip())
                        except (ValueError, TypeError):
                            pass
                    elif ft == "EXPENSE_ROW_TOTAL":
                        try:
                            item["taxable_value"] = float(val.replace(",", "").replace("₹", "").strip())
                        except (ValueError, TypeError):
                            pass

                if item["description"] or item["taxable_value"]:
                    structured["line_items"].append(item)

    return structured
