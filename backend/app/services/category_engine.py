"""Two-tier expense categorization: keyword rules first, Bedrock fallback."""
import uuid
import re
from sqlalchemy.ext.asyncio import AsyncSession

KEYWORD_RULES: list[tuple[list[str], str]] = [
    (["airtel", "jio", "vodafone", "bsnl", "telephone", "mobile"], "Telephone Expenses"),
    (["aws", "azure", "google cloud", "hosting", "domain", "server"], "Internet & Hosting"),
    (["uber", "ola", "irctc", "railway", "flight", "makemytrip", "travel"], "Travel Expenses"),
    (["swiggy", "zomato", "food", "restaurant", "canteen", "catering"], "Food & Beverages"),
    (["amazon", "flipkart", "office", "stationery", "printer", "ink"], "Office Supplies"),
    (["rent", "lease", "property"], "Rent"),
    (["electricity", "power", "bescom", "msedcl", "light bill"], "Electricity"),
    (["insurance", "lic", "policy", "premium"], "Insurance"),
    (["repair", "maintenance", "service charge", "amc"], "Repairs & Maintenance"),
    (["salary", "wages", "payroll", "bonus"], "Salary & Wages"),
    (["audit", "ca ", "chartered accountant", "legal", "advocate", "lawyer", "consultant"], "Professional Fees"),
    (["petrol", "diesel", "fuel", "hp ", "iocl", "bpcl"], "Fuel & Conveyance"),
    (["software", "license", "subscription", "saas"], "Software & Subscriptions"),
    (["advertising", "marketing", "google ads", "facebook ads", "promotion"], "Advertising & Marketing"),
]


def _match_keyword_rules(text: str) -> dict | None:
    text_lower = text.lower()
    for keywords, category in KEYWORD_RULES:
        for kw in keywords:
            if kw in text_lower:
                return {"category": category, "confidence": 0.85, "method": "rule"}
    return None


async def assign_category(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    vendor_name: str | None,
    description: str,
) -> dict:
    """Categorize expense. Returns {"category": str, "confidence": float, "method": str}."""
    combined = f"{vendor_name or ''} {description}"

    rule_match = _match_keyword_rules(combined)
    if rule_match:
        return rule_match

    try:
        from app.services.bedrock_service import categorize_expense
        result = categorize_expense(description, vendor_name)
        return {
            "category": result.get("subcategory") or result.get("category", "Indirect Expenses"),
            "confidence": result.get("confidence", 0.5),
            "method": "bedrock",
        }
    except Exception:
        return {"category": "Indirect Expenses", "confidence": 0.3, "method": "fallback"}
