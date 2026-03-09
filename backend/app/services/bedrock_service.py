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
3. If place_of_supply is empty but determinable from GSTINs, suggest the 2-DIGIT STATE CODE (e.g. "07" for Delhi, "27" for Maharashtra). NEVER suggest state names like "New Delhi" or "Maharashtra" - always use the 2-digit code.
4. vendor_state_code and buyer_state_code MUST also be 2-digit codes (e.g. "07", "27"), NOT state names.
5. If CGST != SGST for an intrastate transaction, flag it.
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
        result = json.loads(cleaned.strip())
        # Normalize state code suggestions (AI may return names like "New Delhi" instead of "07")
        from app.utils.gst_validator import normalize_state_to_code
        state_fields = {"place_of_supply", "vendor_state_code", "buyer_state_code"}
        for s in result.get("suggestions", []):
            if s.get("field_name") in state_fields and s.get("suggested_value"):
                normalized = normalize_state_to_code(str(s["suggested_value"]))
                if normalized:
                    s["suggested_value"] = normalized
        return result
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
    prompt = f"""You are an AI Tax & Finance Copilot for an Indian MSME business. You are helpful, precise, and professional.

BEHAVIOR RULES:
- If the user is greeting you (e.g. "hi", "hello", "hey"), warmly introduce yourself, explain what you can help with (invoice queries, GST analysis, spending summaries, tax explanations), and invite them to ask a question. Do NOT reference the financial data.
- For financial questions, use ONLY the numbers and facts from the CONTEXT DATA below.
- If the data doesn't contain enough to answer, say so honestly and suggest uploading more invoices.
- Always cite which records your answer is based on.
- Format all currency amounts as ₹ with Indian comma grouping (e.g. ₹12,50,000).

FORMATTING RULES (Markdown):
- Use **bold** for key numbers and labels.
- Use markdown tables when presenting multiple items, invoices, or comparisons. Always include a header row and alignment.
- Use bullet points for lists of 2-3 items. Use tables for 4+ items.
- Start with a one-line **summary sentence** before the table/details.
- Add a brief **Insight** or **Tip** line at the end when relevant (e.g. tax saving tips, anomalies).
- Keep responses concise — no filler text.
- Use horizontal rules (---) to separate sections if the answer has multiple parts.

Example table format:
| Invoice # | Type | Amount |
|:----------|:-----|-------:|
| INV-001 | Sales | ₹1,00,000 |

CONTEXT DATA:
{context}

USER: {question}

Respond with well-formatted markdown."""

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


def _extract_document_text(raw_textract_json: dict | None) -> str:
    """Extract all LINE-type text blocks from Textract raw response."""
    if not raw_textract_json:
        return ""
    lines = []
    for doc in raw_textract_json.get("ExpenseDocuments", []):
        for block in doc.get("Blocks", []):
            if block.get("BlockType") == "LINE" and block.get("Text"):
                lines.append(block["Text"])
    return "\n".join(lines)


def classify_document(structured_data: dict, tenant_gstin: str | None = None, raw_textract_json: dict | None = None) -> dict:
    """Classify a document using the FULL document text from OCR.

    Strategy:
      1. Extract all text lines from raw Textract output (titles like DEBIT NOTE, CREDIT NOTE etc.)
      2. Use AI (Claude) to classify based on full document context.
      3. GSTIN matching as supporting signal (not sole determinant).

    Returns: {"transaction_nature": str, "document_type": str, "confidence": float, "method": str}
    """
    vendor_gstin = (structured_data.get("vendor_gstin") or "").strip().upper()
    buyer_gstin = (structured_data.get("buyer_gstin") or "").strip().upper()
    tenant_gstin_clean = (tenant_gstin or "").strip().upper()

    # Extract full document text from raw Textract for AI context
    document_text = _extract_document_text(raw_textract_json)
    logger.info(f"[CLASSIFY] Extracted {len(document_text)} chars of document text")

    # Build line-item summary for AI context
    line_items = structured_data.get("line_items", [])[:5]
    items_text = ""
    for li in line_items:
        if isinstance(li, dict):
            desc = li.get("description", "")
            amt = li.get("amount", "")
            qty = li.get("quantity", "")
            items_text += f"  - {desc} (qty: {qty}, amount: {amt})\n"

    # ── Build AI prompt with full document context ─────────
    prompt = f"""You are an Indian GST accounting expert. Classify this document using ALL available context.

FULL DOCUMENT TEXT (from OCR — read the ENTIRE text carefully):
---
{document_text or 'No raw text available'}
---

Extracted structured fields:
- Vendor/Seller Name: {structured_data.get('vendor_name', 'Unknown')}
- Vendor GSTIN: {vendor_gstin or 'Not provided'}
- Buyer Name: {structured_data.get('buyer_name', 'Unknown')}
- Buyer GSTIN: {buyer_gstin or 'Not provided'}
- Invoice Number: {structured_data.get('invoice_number', 'N/A')}
- Subtotal: {structured_data.get('subtotal', 0)}
- Total Amount: {structured_data.get('total', 0)}
- CGST: {structured_data.get('cgst', 0)}, SGST: {structured_data.get('sgst', 0)}, IGST: {structured_data.get('igst', 0)}
- Line Items:
{items_text or '  (none extracted)'}
{f'- Uploading company GSTIN: {tenant_gstin_clean}' if tenant_gstin_clean else '- Uploading company GSTIN: Not configured'}

=== DOCUMENT TYPE CLASSIFICATION ===

Determine the document_type using these rules IN ORDER OF PRIORITY:

PRIORITY 1 — EXPLICIT HEADING: If the document text contains an explicit title/heading like:
  - "Tax Invoice" / "Invoice" / "Bill" → document_type = "invoice"
  - "Credit Note" / "Credit Memo" → document_type = "credit_note"
  - "Debit Note" / "Debit Memo" → document_type = "debit_note"
  - "Bill of Supply" → document_type = "bill_of_supply"

PRIORITY 2 — IMPLICIT DETECTION (when NO explicit heading exists, deduce from context):
  a) CREDIT NOTE indicators:
     - Words like "return", "refund", "reversal", "cancelled", "goods returned", "discount allowed"
     - Negative amounts or amounts marked as reduction
     - Reference to an "original invoice" with intent to REDUCE the value
     - Document number patterns like CN-xxx, CR-xxx
     - Phrases: "credit against", "adjustment (credit)", "amount refunded"
  b) DEBIT NOTE indicators:
     - Mentions of "additional charges", "price difference", "rate revision (upward)", "shortage", "damaged goods claim"
     - Reference to an original invoice with intent to INCREASE the value
     - Document number patterns like DN-xxx, DR-xxx
     - Phrases: "debit against", "supplementary invoice", "price escalation", "additional amount due"
  c) BILL OF SUPPLY indicators:
     - Total GST (CGST+SGST+IGST) = 0 OR no GST breakdown at all
     - Mentions "composition dealer", "composition scheme", "exempt supply", "nil rated"
     - Registered under section 10 of CGST Act
     - No GST columns in the line items
  d) INVOICE (default if none of the above match):
     - Standard purchase/sales document with GST charges
     - Regular line items with tax breakdowns

=== TRANSACTION NATURE CLASSIFICATION ===

Determine if this is a PURCHASE or SALE from the uploading company's perspective:
  - "purchase" — Uploading company is the BUYER/recipient. Document was issued BY someone else TO the company.
  - "sale" — Uploading company is the SELLER/issuer. Document was issued BY the company.

Key signals:
  1. If uploading company GSTIN matches Vendor/Seller GSTIN → SALE
  2. If uploading company GSTIN matches Buyer GSTIN → PURCHASE
  3. If no GSTIN match: most uploaded documents are purchase bills from vendors → default to "purchase"
  4. For credit notes: if issued by the vendor (reducing their invoice) → "purchase" side; if issued by uploading company → "sale" side
  5. For debit notes: if issued to vendor (claiming more) → "purchase" side; if issued to customer → "sale" side

Return ONLY valid JSON (no markdown, no explanation outside JSON):
{{"transaction_nature": "purchase|sale", "document_type": "invoice|credit_note|debit_note|bill_of_supply", "confidence": 0.0-1.0, "document_number": "the actual document number (e.g. DN-xxx for debit notes, CN-xxx for credit notes, or the invoice number)", "original_invoice_ref": "if this is a credit/debit note, the reference original invoice number, otherwise null", "reasoning": "brief reason"}}"""

    try:
        raw = _invoke_claude(prompt, max_tokens=300)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        result = json.loads(cleaned)
        nature = result.get("transaction_nature", "purchase")
        doc_type = result.get("document_type", "invoice")
        confidence = float(result.get("confidence", 0.7))
        logger.info(f"[CLASSIFY] AI classified as {nature}/{doc_type} (conf={confidence}): {result.get('reasoning', '')}")
        return {
            "transaction_nature": nature,
            "document_type": doc_type,
            "confidence": confidence,
            "method": "ai",
            "document_number": result.get("document_number"),
            "original_invoice_ref": result.get("original_invoice_ref"),
        }
    except Exception as e:
        logger.warning(f"[CLASSIFY] AI classification failed, defaulting to purchase: {e}")
        return {
            "transaction_nature": "purchase",
            "document_type": "invoice",
            "confidence": 0.3,
            "method": "fallback",
        }

