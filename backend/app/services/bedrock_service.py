"""AWS Bedrock (Claude) integration for invoice validation, categorization, and copilot."""
import json
import boto3
from app.config import get_settings

settings = get_settings()


def _get_bedrock_client():
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.bedrock_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )


def _invoke_claude(prompt: str, max_tokens: int = 4096) -> str:
    client = _get_bedrock_client()
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    })
    response = client.invoke_model(
        modelId=settings.bedrock_model_id,
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def validate_invoice_fields(structured_data: dict) -> dict:
    """Use Claude to validate GST invoice fields and return per-field results."""
    prompt = f"""You are an Indian GST compliance expert. Analyze this extracted invoice data and validate each field.

Invoice data:
{json.dumps(structured_data, indent=2, default=str)}

For each field, determine if it passes validation, fails, or has a warning.

Validation rules:
1. vendor_gstin: Must be valid 15-char GSTIN format (2-digit state + 10-char PAN + entity + Z + check digit)
2. buyer_gstin: Same GSTIN format validation if present
3. invoice_number: Must be non-empty
4. invoice_date: Must be a valid date
5. total: Must equal subtotal + cgst + sgst + igst + cess (tolerance of Rs 1)
6. gst_split: If interstate (vendor state != buyer state from GSTIN), only IGST should be present. If intrastate, CGST should equal SGST and IGST should be 0
7. gst_rate: Check if effective GST rate is one of 0%, 5%, 12%, 18%, 28%
8. line_items: Each should have description and amount

Return ONLY a JSON object with this exact structure (no markdown, no explanation):
{{
  "field_results": {{
    "vendor_gstin": {{"status": "pass|fail|warn", "message": "explanation or null", "confidence": 0.0-1.0}},
    "buyer_gstin": {{"status": "pass|fail|warn", "message": "explanation or null", "confidence": 0.0-1.0}},
    "invoice_number": {{"status": "pass|fail|warn", "message": "explanation or null", "confidence": 0.0-1.0}},
    "invoice_date": {{"status": "pass|fail|warn", "message": "explanation or null", "confidence": 0.0-1.0}},
    "total": {{"status": "pass|fail|warn", "message": "explanation or null", "confidence": 0.0-1.0}},
    "gst_split": {{"status": "pass|fail|warn", "message": "explanation or null", "confidence": 0.0-1.0}},
    "gst_rate": {{"status": "pass|fail|warn", "message": "explanation or null", "confidence": 0.0-1.0}},
    "line_items": {{"status": "pass|fail|warn", "message": "explanation or null", "confidence": 0.0-1.0}}
  }},
  "overall_status": "pass|fail|warn",
  "summary": "brief validation summary"
}}"""

    try:
        raw = _invoke_claude(prompt)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(cleaned)
    except Exception as e:
        return {
            "field_results": {
                "validation_error": {"status": "warn", "message": f"Bedrock validation failed: {e}", "confidence": 0}
            },
            "overall_status": "warn",
            "summary": f"Automated validation unavailable: {e}",
        }


def categorize_expense(description: str, vendor_name: str | None) -> dict:
    """Use Claude to categorize an expense into a chart of accounts category."""
    prompt = f"""You are an Indian accountant using Tally-style chart of accounts.

Given this invoice:
- Vendor: {vendor_name or 'Unknown'}
- Description: {description}

Classify this into ONE of these Indian accounting categories:
- Purchase Accounts
- Direct Expenses
- Indirect Expenses (subcategories: Telephone, Internet, Travel, Office Supplies, Professional Fees, Rent, Electricity, Insurance, Repairs & Maintenance, Printing & Stationery, Other)
- Sales Accounts
- Direct Incomes
- Indirect Incomes

Return ONLY a JSON object:
{{"category": "category name", "subcategory": "subcategory or null", "confidence": 0.0-1.0}}"""

    try:
        raw = _invoke_claude(prompt, max_tokens=256)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(cleaned)
    except Exception:
        return {"category": "Indirect Expenses", "subcategory": "Other", "confidence": 0.3}


def copilot_query(question: str, context: str) -> dict:
    """Answer a natural language question grounded in the provided financial context."""
    prompt = f"""You are an AI financial assistant for an Indian business. Answer the user's question using ONLY the data provided.

RULES:
- Only use numbers and facts from the provided context
- If the data doesn't contain enough information, say "I don't have enough data to answer this question"
- Always cite which records/invoices/transactions your answer is based on
- Never make up or estimate numbers that aren't in the data
- Format currency as INR (Rs or ₹)

CONTEXT DATA:
{context}

USER QUESTION: {question}

Provide a clear, concise answer with source citations."""

    try:
        answer = _invoke_claude(prompt, max_tokens=1024)
        return {"answer": answer, "has_data": True}
    except Exception as e:
        return {"answer": f"Unable to process query: {e}", "has_data": False}
