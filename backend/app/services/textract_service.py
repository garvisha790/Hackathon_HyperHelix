"""AWS Textract integration using AnalyzeExpense API optimized for invoices."""
import boto3
from botocore.config import Config
from app.config import get_settings

settings = get_settings()


def _get_textract_client():
    return boto3.client(
        "textract",
        region_name=settings.textract_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
        config=Config(connect_timeout=10, read_timeout=60, retries={"max_attempts": 2}),
    )


def analyze_expense(s3_key: str) -> dict:
    """Call Textract AnalyzeExpense on an S3 object. Returns raw Textract response."""
    client = _get_textract_client()
    response = client.analyze_expense(
        Document={
            "S3Object": {
                "Bucket": settings.s3_bucket_name,
                "Name": s3_key,
            }
        }
    )
    return response


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
