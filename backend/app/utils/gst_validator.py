"""Indian GST validation utilities.

GSTIN format: 2-digit state code + 10-char PAN + 1 entity number + 1Z + 1 check digit
Example: 27AAPFU0939F1ZV (Maharashtra, PAN: AAPFU0939F)
"""
import re

VALID_GST_RATES = {0.0, 0.25, 3.0, 5.0, 12.0, 18.0, 28.0}

INDIAN_STATE_CODES = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana",
    "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
    "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
    "16": "Tripura", "17": "Meghalaya", "18": "Assam",
    "19": "West Bengal", "20": "Jharkhand", "21": "Odisha",
    "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "26": "Dadra & Nagar Haveli and Daman & Diu", "27": "Maharashtra",
    "29": "Karnataka", "30": "Goa", "31": "Lakshadweep",
    "32": "Kerala", "33": "Tamil Nadu", "34": "Puducherry",
    "35": "Andaman & Nicobar", "36": "Telangana", "37": "Andhra Pradesh",
    "38": "Ladakh",
}

GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")

_GSTIN_CHAR_MAP = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _gstin_checksum(gstin_without_check: str) -> str:
    """Compute the GSTIN check digit using the standard algorithm."""
    total = 0
    for i, ch in enumerate(gstin_without_check):
        val = _GSTIN_CHAR_MAP.index(ch)
        if i % 2 != 0:
            val *= 2
        quotient, remainder = divmod(val, 36)
        total += quotient + remainder
    check_val = (36 - (total % 36)) % 36
    return _GSTIN_CHAR_MAP[check_val]


def validate_gstin(gstin: str) -> dict:
    """Validate GSTIN format and checksum. Returns status dict."""
    if not gstin:
        return {"valid": False, "message": "GSTIN is empty"}

    gstin = gstin.strip().upper()

    if not GSTIN_PATTERN.match(gstin):
        return {"valid": False, "message": "GSTIN format invalid (expected 15 chars: 2-digit state + PAN + entity + Z + check)"}

    state_code = gstin[:2]
    if state_code not in INDIAN_STATE_CODES:
        return {"valid": False, "message": f"Invalid state code: {state_code}"}

    expected_check = _gstin_checksum(gstin[:14])
    if gstin[14] != expected_check:
        return {"valid": False, "message": f"Checksum mismatch: expected {expected_check}, got {gstin[14]}"}

    return {
        "valid": True,
        "state_code": state_code,
        "state_name": INDIAN_STATE_CODES[state_code],
        "pan": gstin[2:12],
    }


def extract_state_from_gstin(gstin: str) -> str | None:
    """Extract 2-digit state code from GSTIN."""
    if gstin and len(gstin) >= 2:
        return gstin[:2]
    return None


def is_interstate(supplier_state: str | None, place_of_supply: str | None) -> bool:
    """Determine if transaction is inter-state (IGST) or intra-state (CGST+SGST)."""
    if not supplier_state or not place_of_supply:
        return False
    return supplier_state != place_of_supply


def validate_gst_rate(rate: float) -> bool:
    return rate in VALID_GST_RATES


def validate_total_consistency(subtotal: float, cgst: float, sgst: float, igst: float, cess: float, total: float) -> dict:
    """Check if total = subtotal + all GST components."""
    expected = subtotal + cgst + sgst + igst + cess
    diff = abs(total - expected)
    if diff > 0.50:
        return {
            "valid": False,
            "message": f"Total mismatch: expected {expected:.2f} (subtotal {subtotal} + taxes), got {total:.2f}, diff={diff:.2f}",
        }
    return {"valid": True}


def validate_gst_split(cgst: float, sgst: float, igst: float, is_interstate_txn: bool) -> dict:
    """Validate GST split: interstate should have IGST only, intrastate should have CGST=SGST."""
    if is_interstate_txn:
        if cgst > 0 or sgst > 0:
            return {"valid": False, "message": "Inter-state transaction should have IGST only, but CGST/SGST found"}
    else:
        if igst > 0:
            return {"valid": False, "message": "Intra-state transaction should have CGST+SGST, but IGST found"}
        if abs(cgst - sgst) > 0.01:
            return {"valid": False, "message": f"CGST ({cgst}) should equal SGST ({sgst}) for intra-state"}
    return {"valid": True}


def normalize_state_to_code(state_input: str | None) -> str | None:
    """
    Normalize state name or code to 2-digit state code.
    
    Args:
        state_input: Can be state code ("27") or state name ("Maharashtra")
    
    Returns:
        2-digit state code or None
    
    Examples:
        "27" -> "27"
        "Maharashtra" -> "27"
        "maharashtra" -> "27"
        "MAHARASHTRA" -> "27"
    """
    if not state_input:
        return None
    
    state_input = str(state_input).strip()
    
    # If already a 2-digit code, return it
    if len(state_input) == 2 and state_input.isdigit():
        if state_input in INDIAN_STATE_CODES:
            return state_input
        return None
    
    # Try to find by state name (case-insensitive)
    state_input_lower = state_input.lower()
    for code, name in INDIAN_STATE_CODES.items():
        if name.lower() == state_input_lower:
            return code
    
    return None
