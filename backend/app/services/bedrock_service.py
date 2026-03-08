"""AWS Bedrock (Claude) integration for invoice validation, categorization, and copilot.

Dual-mode support:
  - If ANTHROPIC_API_KEY is set in .env  → uses direct Anthropic API (no Bedrock needed).
  - Otherwise                            → uses AWS Bedrock with the configured model.
"""
import json
import logging
import boto3
from botocore.config import Config
from app.config import get_settings
from app.services.gst_expert_system import (
    EXPERT_SYSTEM_INSTRUCTIONS,
    compute_math_verification,
    determine_transaction_type,
    validate_gstin_format,
)

settings = get_settings()
logger = logging.getLogger(__name__)

_bedrock_available = True


# ─────────────────────────────────────────────────────────────
# Internal: pick the right backend
# ─────────────────────────────────────────────────────────────

def _invoke_claude_direct_api(prompt: str, max_tokens: int = 4096, system_prompt: str | None = None) -> str:
    """Call Anthropic API directly using the anthropic SDK."""
    import anthropic  # installed: pip install anthropic
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    kwargs = dict(
        model="claude-3-haiku-20240307",
        max_tokens=max_tokens,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    if system_prompt:
        kwargs["system"] = system_prompt
    message = client.messages.create(**kwargs)
    return message.content[0].text


def _invoke_claude_bedrock(prompt: str, max_tokens: int = 4096, system_prompt: str | None = None) -> str:
    """Call Claude via AWS Bedrock runtime."""
    global _bedrock_available
    if not _bedrock_available:
        raise RuntimeError("Bedrock previously failed with AccessDeniedException — skipping")

    client = boto3.client(
        "bedrock-runtime",
        region_name=settings.bedrock_region,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
        config=Config(connect_timeout=5, read_timeout=30, retries={"max_attempts": 1}),
    )
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }
    if system_prompt:
        payload["system"] = system_prompt
    body = json.dumps(payload)
    try:
        response = client.invoke_model(
            modelId=settings.bedrock_model_id,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
    except client.exceptions.AccessDeniedException as e:
        logger.warning(f"Bedrock access denied, disabling for this session: {e}")
        _bedrock_available = False
        raise
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def _invoke_claude(prompt: str, max_tokens: int = 4096, system_prompt: str | None = None) -> str:
    """Smart dispatcher: prefer direct Anthropic API if key is set, else use Bedrock."""
    if getattr(settings, "anthropic_api_key", None):
        logger.debug("[AI] Using direct Anthropic API")
        return _invoke_claude_direct_api(prompt, max_tokens, system_prompt=system_prompt)
    else:
        logger.debug("[AI] Using AWS Bedrock")
        return _invoke_claude_bedrock(prompt, max_tokens, system_prompt=system_prompt)


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

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
7. gst_rate: Calculate the effective GST rate (Total Tax / Subtotal). Check if it is approximately 0%, 5%, 12%, 18%, or 28%. Restaurant bills are typically exactly 5% (2.5% CGST + 2.5% SGST). Do not flag minor rounding differences.
8. line_items: Each should have a description and amount. Do NOT issue a warning for missing HSN/SAC codes (they are not strictly required for restaurant receipts or B2C bills).

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
                "validation_error": {"status": "warn", "message": f"AI validation failed: {e}", "confidence": 0}
            },
            "overall_status": "warn",
            "summary": f"Automated validation unavailable: {e}",
        }


def generate_ai_review(structured_data: dict, validation_results: dict, raw_extraction_data: dict | None = None) -> dict:
    """Use Claude to generate GitHub PR-style field suggestions to fix validation errors."""

    raw_extraction_section = ""
    if raw_extraction_data:
        raw_extraction_section = f"""
Raw Extraction Data (directly from Textract OCR, before any processing):
{json.dumps(raw_extraction_data, indent=2, default=str)}

IMPORTANT: Use the raw extraction data as the ground truth to determine what values the original document contains. When the canonical invoice totals don't balance, look at the raw_fields and line_items_raw to find the exact source-of-truth values.
"""

def generate_ai_review(structured_data: dict, validation_results: dict, raw_extraction_data: dict | None = None) -> dict:
    """Use Claude with expert-level Indian GST knowledge to review invoice and suggest fixes."""

    # ═══════════════════════════════════════════════════════
    # STEP 1: Pre-compute all verifiable facts in Python first
    # (This removes the AI's need to do math — it just interprets)
    # ═══════════════════════════════════════════════════════
    math_check = compute_math_verification(structured_data)

    vendor_gstin = structured_data.get("vendor_gstin")
    buyer_gstin = structured_data.get("buyer_gstin")
    place_of_supply = structured_data.get("place_of_supply")

    vendor_gstin_check = validate_gstin_format(vendor_gstin)
    buyer_gstin_check = validate_gstin_format(buyer_gstin)
    txn_type = determine_transaction_type(vendor_gstin, buyer_gstin, place_of_supply)

    pre_computed_context = f"""
== VERIFIED MATHEMATICAL ANALYSIS (computed by Python, NOT by you) ==
subtotal={math_check['subtotal']}, cgst={structured_data.get('cgst', 0)}, sgst={structured_data.get('sgst', 0)}, igst={structured_data.get('igst', 0)}, cess={structured_data.get('cess', 0)}
total_tax={math_check['total_tax']}
computed_total (subtotal+taxes) = {math_check['computed_total']}
declared_total = {math_check['declared_total']}
difference = {math_check['difference']} rupees
computed_subtotal (total-taxes) = {math_check['computed_subtotal']}
line_items taxable sum = {math_check['line_items_taxable_sum']}

Pre-detected math issues:
{json.dumps(math_check['issues'], indent=2)}

Pre-computed suggestions from math engine:
{json.dumps(math_check['pre_computed_suggestions'], indent=2)}

== VERIFIED GSTIN ANALYSIS ==
Vendor GSTIN ({vendor_gstin}): {json.dumps(vendor_gstin_check)}
Buyer GSTIN ({buyer_gstin}): {json.dumps(buyer_gstin_check)}

== VERIFIED TRANSACTION TYPE ==
{json.dumps(txn_type, indent=2)}
"""

    raw_extraction_section = ""
    if raw_extraction_data:
        raw_extraction_section = f"""
== RAW OCR EXTRACTION DATA (source of truth from original document) ==
{json.dumps(raw_extraction_data, indent=2, default=str)}
Use this to find field values that the canonical extraction may have missed or garbled.
"""

    # ═══════════════════════════════════════════════════════
    # STEP 2: Ask Claude to interpret and generate suggestions
    # ONLY based on the pre-computed verified facts above.
    # ═══════════════════════════════════════════════════════
    prompt = f"""You are reviewing this invoice. All mathematical computations have already been done for you by a Python engine. Your job is to:
1. Review the pre-computed analysis.
2. Use the raw OCR data to fill in any fields that are missing.
3. Generate a list of field-level suggestions.

== CANONICAL INVOICE DATA ==
{json.dumps(structured_data, indent=2, default=str)}

{raw_extraction_section}
{pre_computed_context}

== VALIDATION STATUS FROM PREVIOUS ENGINE ==
{json.dumps(validation_results, indent=2, default=str)}

== YOUR TASK ==
Based on ALL the information above:
1. Start with the pre_computed_suggestions from the math engine as your primary suggestions. Refine them if you find better data in the raw OCR.
2. If vendor_gstin or buyer_gstin format is invalid, suggest the correct format or the raw OCR value.
3. If place_of_supply is empty but determinable from GSTINs, suggest it.
4. If CGST != SGST for an intrastate transaction, flag it.
5. If the transaction type says IGST should be 0 but it's not (or vice versa), flag it.
6. Add a clear, professional 2-3 sentence summary of your review.

DO NOT:
- Change the total to just the sum of taxes (e.g., don't suggest total=14.5 when total=305)
- Suggest changes for fields that are already correct
- Invent GSTIN values not found in the data

Return ONLY valid JSON (no Markdown, no backticks):
{{
  "suggestions": [
    {{
      "field_name": "subtotal",
      "old_value": 0,
      "suggested_value": 290.5,
      "reasoning": "Subtotal was 0. Calculated as: total(305) - CGST(7.25) - SGST(7.25) = 290.5"
    }}
  ],
  "summary_of_analysis": "The subtotal field was not captured from the OCR. All other fields are mathematically consistent."
}}"""

    try:
        raw = _invoke_claude(prompt, system_prompt=EXPERT_SYSTEM_INSTRUCTIONS, max_tokens=2000)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        if cleaned.startswith("json"):
            cleaned = cleaned.split("\n", 1)[1]
        return json.loads(cleaned.strip())
    except Exception as e:
        logger.error(f"Failed to generate AI review: {e}")
        # Fallback: use math engine pre-computed suggestions directly
        fallback_suggestions = [
            {"field_name": s["field"], "old_value": structured_data.get(s["field"]), "suggested_value": s["suggested_value"], "reasoning": s["reason"]}
            for s in math_check["pre_computed_suggestions"]
        ]
        return {
            "suggestions": fallback_suggestions,
            "summary_of_analysis": f"Mathematical analysis found {len(math_check['issues'])} issue(s). AI narrative unavailable: {e}"
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
    prompt = f"""You are an AI Tax & Finance Copilot for an Indian business. You are helpful, concise, and professional.

BEHAVIOR RULES:
- If the user is greeting you (e.g. "hi", "hello", "hey"), warmly introduce yourself, explain what you can help with (invoice queries, GST analysis, spending summaries, tax explanations), and invite them to ask a question. Do NOT reference the financial data.
- For financial questions, use ONLY the numbers and facts from the CONTEXT DATA below.
- If the data doesn't contain enough to answer, say so honestly and suggest uploading more invoices.
- Always cite which records your answer is based on.
- Format currency as INR (Rs or ₹).
 
CONTEXT DATA:
{context}

USER: {question}

Respond clearly and concisely."""

    try:
        answer = _invoke_claude(prompt, max_tokens=1024)
        return {"answer": answer, "has_data": True}
    except Exception as e:
        return {"answer": f"Unable to process query: {e}", "has_data": False}


def generate_approval_error_review(invoice_data: dict, error_message: str) -> dict:
    """Generate AI suggestions to fix approval-time errors like double-entry violations."""
    
    prompt = f"""You are an expert accountant reviewing an invoice that failed approval validation.

INVOICE DATA:
{json.dumps(invoice_data, indent=2, default=str)}

APPROVAL ERROR:
{error_message}

TASK:
Analyze why this invoice failed approval and provide specific, actionable suggestions to fix the issue.

For double-entry violations:
1. Identify which amounts don't balance
2. Check if subtotal + taxes = total amount
3. Suggest which fields need correction
4. Provide the exact corrected values

OUTPUT FORMAT (JSON):
{{
  "error_type": "double_entry_violation" | "missing_data" | "invalid_format",
  "root_cause": "Brief explanation of what caused the error",
  "suggestions": [
    {{
      "field_name": "field to correct",
      "current_value": "current incorrect value",
      "suggested_value": "correct value",
      "reasoning": "why this change fixes the issue"
    }}
  ],
  "summary": "Overall recommendation"
}}

Provide ONLY valid JSON output, no additional text."""

    try:
        response = _invoke_claude(prompt, max_tokens=2048)
        # Parse JSON from response
        result = json.loads(response.strip())
        return result
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI approval error review: {e}")
        logger.error(f"Raw response: {response}")
        return {
            "error_type": "system_error",
            "root_cause": "Failed to parse AI response",
            "suggestions": [],
            "summary": f"Error: {error_message}"
        }
    except Exception as e:
        logger.error(f"Failed to generate approval error review: {e}")
        return {
            "error_type": "system_error",
            "root_cause": str(e),
            "suggestions": [],
            "summary": f"Error: {error_message}"
        }

