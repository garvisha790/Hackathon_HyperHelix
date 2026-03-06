"""
Indian GST & Accounting Expert Knowledge Base
Used to build the system-level instructions for the AI Tax Review agent.
"""

# All 38 Indian State/UT codes
INDIA_STATE_CODES = {
    "01": "Jammu and Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "25": "Daman and Diu",
    "26": "Dadra and Nagar Haveli",
    "27": "Maharashtra",
    "28": "Andhra Pradesh (Old)",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman and Nicobar Islands",
    "36": "Telangana",
    "37": "Andhra Pradesh",
    "38": "Ladakh",
    "97": "Other Territory",
    "99": "Centre Jurisdiction",
}

# Valid GST rates under Indian law
VALID_GST_RATES = {0, 0.1, 0.25, 1, 1.5, 3, 5, 6, 7.5, 9, 12, 14, 18, 28}

# Food/restaurant items typically attract 5% GST (CGST 2.5% + SGST 2.5%)
# Some luxury restaurants attract 18%
RESTAURANT_GST_RATE = 5.0

def validate_gstin_format(gstin: str | None) -> dict:
    """Pure format validation of a 15-character GSTIN."""
    if not gstin:
        return {"valid": False, "error": "GSTIN is empty"}
    gstin = gstin.strip().upper()
    if len(gstin) != 15:
        return {"valid": False, "error": f"GSTIN must be 15 characters, got {len(gstin)}"}
    
    state_code = gstin[:2]
    if state_code not in INDIA_STATE_CODES:
        return {"valid": False, "error": f"Invalid state code '{state_code}' in GSTIN"}
    
    # PAN is chars 3-12 (must be alphanumeric)
    pan_part = gstin[2:12]
    if not pan_part.isalnum():
        return {"valid": False, "error": "PAN section of GSTIN (chars 3-12) must be alphanumeric"}
    
    # Entity and check digit (chars 13-15)
    entity_num = gstin[12]
    if not entity_num.isdigit() or entity_num == "0":
        return {"valid": False, "error": "Entity number (char 13) must be 1-9"}
    
    return {
        "valid": True,
        "state_code": state_code,
        "state_name": INDIA_STATE_CODES[state_code],
        "pan": pan_part,
    }


def determine_transaction_type(vendor_gstin: str | None, buyer_gstin: str | None, place_of_supply: str | None) -> dict:
    """Determine if transaction is intra-state (CGST+SGST) or inter-state (IGST)."""
    vendor_state = (vendor_gstin or "")[:2].strip()
    buyer_state = (buyer_gstin or "")[:2].strip()
    pos_state = (place_of_supply or "")[:2].strip()

    supply_state = pos_state or buyer_state

    if not vendor_state or not supply_state:
        return {"type": "unknown", "reason": "Cannot determine - vendor or buyer GSTIN missing"}

    if vendor_state == supply_state:
        return {
            "type": "intrastate",
            "reason": f"Vendor state ({vendor_state}: {INDIA_STATE_CODES.get(vendor_state, '?')}) == Supply state ({supply_state})",
            "expected_tax": "CGST + SGST",
            "igst_should_be_zero": True,
        }
    else:
        return {
            "type": "interstate",
            "reason": f"Vendor state ({vendor_state}: {INDIA_STATE_CODES.get(vendor_state, '?')}) != Supply state ({supply_state}: {INDIA_STATE_CODES.get(supply_state, '?')})",
            "expected_tax": "IGST only",
            "cgst_sgst_should_be_zero": True,
        }


def verify_tax_split(cgst: float, sgst: float, igst: float) -> dict:
    """Verify the CGST/SGST symmetry rule under Indian GST law."""
    issues = []
    if cgst > 0 and igst > 0:
        issues.append("CGST and IGST cannot both be non-zero on the same invoice")
    if sgst > 0 and igst > 0:
        issues.append("SGST and IGST cannot both be non-zero on the same invoice")
    if cgst > 0 and abs(cgst - sgst) > 0.02:
        issues.append(f"CGST ({cgst}) and SGST ({sgst}) must be equal for intrastate transactions (difference: {abs(cgst - sgst):.2f})")
    return {"valid": len(issues) == 0, "issues": issues}


def compute_math_verification(invoice_data: dict) -> dict:
    """Compute all mathematical verification metrics for an invoice."""
    subtotal = float(invoice_data.get("subtotal") or 0)
    cgst = float(invoice_data.get("cgst") or 0)
    sgst = float(invoice_data.get("sgst") or 0)
    igst = float(invoice_data.get("igst") or 0)
    cess = float(invoice_data.get("cess") or 0)
    total = float(invoice_data.get("total") or 0)
    line_items = invoice_data.get("line_items") or []

    total_tax = round(cgst + sgst + igst + cess, 2)
    computed_total_from_subtotal = round(subtotal + total_tax, 2)
    computed_subtotal_from_total = round(total - total_tax, 2)

    # Sum taxable values from line items
    line_items_taxable_sum = round(sum(
        float(item.get("taxable_value") or item.get("rate") or 0)
        for item in line_items if isinstance(item, dict)
    ), 2)
    line_items_tax_sum = round(sum(
        float(item.get("cgst_amount") or 0) + float(item.get("sgst_amount") or 0) + float(item.get("igst_amount") or 0)
        for item in line_items if isinstance(item, dict)
    ), 2)

    issues = []
    suggestions = []

    # Case 1: subtotal is 0 but total is valid — subtotal not extracted
    if subtotal == 0 and total > 0:
        issues.append("CRITICAL: subtotal is 0 but total is non-zero — subtotal was not extracted")
        suggestions.append({
            "field": "subtotal",
            "suggested_value": computed_subtotal_from_total,
            "reason": f"subtotal = total({total}) - cgst({cgst}) - sgst({sgst}) - igst({igst}) - cess({cess}) = {computed_subtotal_from_total}"
        })

    # Case 2: total is 0 — can try to compute from subtotal + taxes
    elif total == 0 and subtotal > 0:
        issues.append("CRITICAL: total is 0 but subtotal is non-zero — total amount was not extracted")
        suggestions.append({
            "field": "total",
            "suggested_value": computed_total_from_subtotal,
            "reason": f"total = subtotal({subtotal}) + cgst({cgst}) + sgst({sgst}) + igst({igst}) + cess({cess}) = {computed_total_from_subtotal}"
        })

    # Case 3: both present but don't balance (rounding error)
    elif subtotal > 0 and total > 0:
        diff = round(total - computed_total_from_subtotal, 2)
        if abs(diff) > 0.02:
            issues.append(f"MATH MISMATCH: subtotal({subtotal}) + taxes({total_tax}) = {computed_total_from_subtotal}, but declared total = {total} (diff = {diff})")
            # Round-off entries of ±1 are valid in Indian GST
            if abs(diff) <= 1.0:
                issues.append(f"Note: diff={diff} is within round-off range (±Re 1). This may be intentional.")
                suggestions.append({
                    "field": "total",
                    "suggested_value": computed_total_from_subtotal,
                    "reason": f"Adjust total to match subtotal+taxes. Current total has a round-off of {diff}"
                })
            else:
                suggestions.append({
                    "field": "subtotal",
                    "suggested_value": computed_subtotal_from_total,
                    "reason": f"Re-compute subtotal as total({total}) - taxes({total_tax}) = {computed_subtotal_from_total}"
                })

    # Case 4: line items don't match subtotal
    if line_items and line_items_taxable_sum > 0 and subtotal > 0:
        if abs(line_items_taxable_sum - subtotal) > 0.05:
            issues.append(f"LINE ITEMS MISMATCH: line items taxable sum={line_items_taxable_sum} != subtotal={subtotal}")

    # Case 5: Check CGST == SGST for intrastate
    tax_split = verify_tax_split(cgst, sgst, igst)
    if not tax_split["valid"]:
        for issue in tax_split["issues"]:
            issues.append(f"TAX SPLIT: {issue}")

    return {
        "subtotal": subtotal,
        "total_tax": total_tax,
        "computed_total": computed_total_from_subtotal,
        "computed_subtotal": computed_subtotal_from_total,
        "declared_total": total,
        "difference": round(total - computed_total_from_subtotal, 2),
        "line_items_taxable_sum": line_items_taxable_sum,
        "issues": issues,
        "pre_computed_suggestions": suggestions,
    }


EXPERT_SYSTEM_INSTRUCTIONS = """
You are TAXAI, an elite Indian GST and Accounting Forensic Expert with 20+ years of experience in:
- Indian GST law (CGST Act 2017, IGST Act 2017, SGST Acts)
- Tally ERP accounting and double-entry bookkeeping
- Textract OCR error patterns and common extraction failures
- GSTN e-invoicing standards and IRN generation
- ITC (Input Tax Credit) claim eligibility rules
- GSTR-1, GSTR-2B, GSTR-3B filing requirements

== CORE RULES YOU MUST ENFORCE ==

### 1. Mathematical Invariants (ABSOLUTE RULES)
- subtotal + cgst + sgst + igst + cess = total (tolerance ≤ ₹0.02 for floating point)
- Round-off entries of ±Re 1 are valid under Indian GST
- If subtotal = 0 but total > 0: subtotal MUST be calculated as total - cgst - sgst - igst - cess
- If total = 0 but subtotal > 0: total = subtotal + cgst + sgst + igst + cess
- CGST must EXACTLY EQUAL SGST for intrastate transactions (both are 50% of the total GST rate)

### 2. Transaction Type Rules (Critical for ITC)
- INTRASTATE (vendor state == place of supply state): MUST use CGST + SGST, IGST MUST be zero
- INTERSTATE (vendor state != place of supply): MUST use IGST only, CGST and SGST MUST be zero
- State code is the FIRST 2 DIGITS of GSTIN (e.g., "33" = Tamil Nadu, "27" = Maharashtra)

### 3. GSTIN Validation Rules
- Format: 2-digit state code + 10-char PAN + 1-digit entity seq + 1 char + 1 check digit = 15 chars total
- First 2 digits MUST be a valid state/UT code (01-38, 97, 99)
- Cannot start with 00
- Entity number (char 13) must be 1-9
- Must be UPPERCASE

### 4. Tax Rate Rules
- Valid GST rates: 0%, 0.1%, 1%, 1.5%, 3%, 5%, 6%, 7.5%, 12%, 14%, 18%, 28%
- CGST rate = SGST rate = half the combined rate (e.g., 18% GST → CGST 9% + SGST 9%)
- Restaurants (non-AC): 5% GST (CGST 2.5% + SGST 2.5%)
- Restaurants (AC/5-star): 18% GST

### 5. Common OCR Extraction Failures to Detect and Fix
- "Sub Total" or "Taxable Amount" row is often missed by Textract → subtotal = 0
- GSTIN may be partially read (e.g., 14 characters instead of 15)
- Rupee symbol (₹) causing amount parsing failures → amounts appear as 0
- "2.5%" read as "25" (missing decimal point) → tax rates wrong 
- "0" and "O" confusion in GSTIN → flag if GSTIN contains the letter O

### 6. Invoice Date Rules
- Invoice date must be a valid date
- For purchases: date should not be in the future
- For ITC claims: invoice date must be within the current or previous financial year

### 7. Required Fields for Valid GST Invoice / ITC Claim
Mandatory for B2B (business-to-business):
- vendor_name, vendor_gstin, buyer_name, buyer_gstin
- invoice_number, invoice_date
- place_of_supply (as state name or code)
- subtotal (taxable value), cgst+sgst or igst, total
- HSN/SAC codes on line items (mandatory for turnover > Rs 5 Cr)

Mandatory for B2C (business-to-consumer, like restaurants):
- vendor_name, vendor_gstin
- invoice_number, invoice_date
- total, cgst+sgst or igst

### 8. ITC Eligibility Rules  
- Blocked credits under Section 17(5) NOT eligible: food & beverages, club membership, personal use
- Restaurant bills from B2C vendors: ITC is NOT claimable by the buyer
- Motor vehicle expenses: ITC restricted

== YOUR REVIEW METHODOLOGY ==

Step 1 - MATHEMATICAL CHECK: Verify subtotal + taxes = total using the pre-computed Python math
Step 2 - TAX TYPE CHECK: Based on GSTINs, verify correct use of CGST/SGST vs IGST
Step 3 - GSTIN FORMAT CHECK: Validate format and state codes of all GSTINs
Step 4 - MISSING FIELD CHECK: Identify critical missing fields (subtotal, GSTIN, place of supply)
Step 5 - LINE ITEMS RECONCILIATION: Verify line item total matches subtotal
Step 6 - RATE SANITY CHECK: Verify tax amounts match declared rates on line items
Step 7 - SUGGEST ONLY VERIFIED FIXES: Only suggest changes you can mathematically prove

== WHAT NOT TO DO ==
- NEVER suggest a total less than the sum of line items
- NEVER suggest total = cgst + sgst (that's mathematically absurd)
- NEVER invent GSTIN values you cannot find in the raw data
- NEVER change a field that is already correct
- NEVER suggest rounding changes below ₹1 unless a mathematical balance is needed
"""
