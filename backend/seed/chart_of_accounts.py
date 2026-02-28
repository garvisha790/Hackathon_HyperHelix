"""Seed Tally-aligned chart of accounts for a tenant.

15 primary groups mirroring the standard Indian accounting structure
that every CA and Tally user recognizes.
"""
import uuid
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ledger import ChartOfAccounts

SEED_ACCOUNTS: list[dict] = [
    # ─── Capital & Equity ───
    {"code": "capital_account", "name": "Capital Account", "type": "equity", "group": "Capital Account"},
    {"code": "reserves_surplus", "name": "Reserves & Surplus", "type": "equity", "group": "Reserves & Surplus"},

    # ─── Current Assets ───
    {"code": "bank_accounts", "name": "Bank Accounts", "type": "asset", "group": "Bank Accounts", "cash_bank": True},
    {"code": "cash_in_hand", "name": "Cash-in-Hand", "type": "asset", "group": "Cash-in-Hand", "cash_bank": True},
    {"code": "deposits_asset", "name": "Deposits (Asset)", "type": "asset", "group": "Deposits (Asset)"},
    {"code": "loans_advances_asset", "name": "Loans & Advances (Asset)", "type": "asset", "group": "Loans & Advances (Asset)"},
    {"code": "stock_in_hand", "name": "Stock-in-Hand", "type": "asset", "group": "Stock-in-Hand"},
    {"code": "sundry_debtors", "name": "Sundry Debtors", "type": "asset", "group": "Sundry Debtors", "system": True},

    # ─── Current Liabilities ───
    {"code": "sundry_creditors", "name": "Sundry Creditors", "type": "liability", "group": "Sundry Creditors", "system": True},
    {"code": "provisions", "name": "Provisions", "type": "liability", "group": "Provisions"},

    # ─── Duties & Taxes (GST System Accounts) ───
    {"code": "cgst_input", "name": "CGST Input", "type": "asset", "group": "Duties & Taxes", "system": True},
    {"code": "sgst_input", "name": "SGST Input", "type": "asset", "group": "Duties & Taxes", "system": True},
    {"code": "igst_input", "name": "IGST Input", "type": "asset", "group": "Duties & Taxes", "system": True},
    {"code": "cgst_output", "name": "CGST Output", "type": "liability", "group": "Duties & Taxes", "system": True},
    {"code": "sgst_output", "name": "SGST Output", "type": "liability", "group": "Duties & Taxes", "system": True},
    {"code": "igst_output", "name": "IGST Output", "type": "liability", "group": "Duties & Taxes", "system": True},
    {"code": "gst_cess", "name": "GST Cess", "type": "liability", "group": "Duties & Taxes", "system": True},
    {"code": "tds_payable", "name": "TDS Payable", "type": "liability", "group": "Duties & Taxes", "system": True},

    # ─── Fixed Assets ───
    {"code": "fixed_assets", "name": "Fixed Assets", "type": "asset", "group": "Fixed Assets"},

    # ─── Investments ───
    {"code": "investments", "name": "Investments", "type": "asset", "group": "Investments"},

    # ─── Loans (Liability) ───
    {"code": "bank_od", "name": "Bank OD A/c", "type": "liability", "group": "Loans (Liability)"},
    {"code": "secured_loans", "name": "Secured Loans", "type": "liability", "group": "Loans (Liability)"},
    {"code": "unsecured_loans", "name": "Unsecured Loans", "type": "liability", "group": "Loans (Liability)"},

    # ─── Revenue (P&L) ───
    {"code": "sales_accounts", "name": "Sales Accounts", "type": "revenue", "group": "Sales Accounts", "system": True},
    {"code": "direct_incomes", "name": "Direct Incomes", "type": "revenue", "group": "Direct Incomes"},
    {"code": "indirect_incomes", "name": "Indirect Incomes", "type": "revenue", "group": "Indirect Incomes"},

    # ─── Expenses (P&L) ───
    {"code": "purchase_accounts", "name": "Purchase Accounts", "type": "expense", "group": "Purchase Accounts", "system": True},
    {"code": "direct_expenses", "name": "Direct Expenses", "type": "expense", "group": "Direct Expenses"},
    {"code": "indirect_expenses", "name": "Indirect Expenses", "type": "expense", "group": "Indirect Expenses"},

    # ─── Indirect Expense Sub-accounts ───
    {"code": "telephone", "name": "Telephone Expenses", "type": "expense", "group": "Indirect Expenses", "parent": "indirect_expenses"},
    {"code": "internet_hosting", "name": "Internet & Hosting", "type": "expense", "group": "Indirect Expenses", "parent": "indirect_expenses"},
    {"code": "travel", "name": "Travel Expenses", "type": "expense", "group": "Indirect Expenses", "parent": "indirect_expenses"},
    {"code": "office_supplies", "name": "Office Supplies", "type": "expense", "group": "Indirect Expenses", "parent": "indirect_expenses"},
    {"code": "professional_fees", "name": "Professional Fees", "type": "expense", "group": "Indirect Expenses", "parent": "indirect_expenses"},
    {"code": "rent", "name": "Rent", "type": "expense", "group": "Indirect Expenses", "parent": "indirect_expenses"},
    {"code": "electricity", "name": "Electricity", "type": "expense", "group": "Indirect Expenses", "parent": "indirect_expenses"},
    {"code": "insurance", "name": "Insurance", "type": "expense", "group": "Indirect Expenses", "parent": "indirect_expenses"},
    {"code": "repairs_maintenance", "name": "Repairs & Maintenance", "type": "expense", "group": "Indirect Expenses", "parent": "indirect_expenses"},
    {"code": "printing_stationery", "name": "Printing & Stationery", "type": "expense", "group": "Indirect Expenses", "parent": "indirect_expenses"},
    {"code": "fuel_conveyance", "name": "Fuel & Conveyance", "type": "expense", "group": "Indirect Expenses", "parent": "indirect_expenses"},
    {"code": "software_subscriptions", "name": "Software & Subscriptions", "type": "expense", "group": "Indirect Expenses", "parent": "indirect_expenses"},
    {"code": "advertising_marketing", "name": "Advertising & Marketing", "type": "expense", "group": "Indirect Expenses", "parent": "indirect_expenses"},
    {"code": "salary_wages", "name": "Salary & Wages", "type": "expense", "group": "Direct Expenses", "parent": "direct_expenses"},
    {"code": "food_beverages", "name": "Food & Beverages", "type": "expense", "group": "Indirect Expenses", "parent": "indirect_expenses"},
]


async def seed_chart_of_accounts(db: AsyncSession, tenant_id: uuid.UUID):
    """Seed the full Tally-aligned chart of accounts for a tenant."""
    code_to_id: dict[str, uuid.UUID] = {}

    for acc_def in SEED_ACCOUNTS:
        if acc_def.get("parent"):
            continue

        acc = ChartOfAccounts(
            tenant_id=tenant_id,
            code=acc_def["code"],
            name=acc_def["name"],
            account_type=acc_def["type"],
            tally_group=acc_def.get("group"),
            is_system=acc_def.get("system", False),
            is_cash_or_bank=acc_def.get("cash_bank", False),
        )
        db.add(acc)
        await db.flush()
        code_to_id[acc_def["code"]] = acc.id

    for acc_def in SEED_ACCOUNTS:
        parent_code = acc_def.get("parent")
        if not parent_code:
            continue

        acc = ChartOfAccounts(
            tenant_id=tenant_id,
            code=acc_def["code"],
            name=acc_def["name"],
            account_type=acc_def["type"],
            tally_group=acc_def.get("group"),
            parent_id=code_to_id.get(parent_code),
            is_system=acc_def.get("system", False),
            is_cash_or_bank=acc_def.get("cash_bank", False),
        )
        db.add(acc)
        await db.flush()
        code_to_id[acc_def["code"]] = acc.id

    await db.flush()
    return code_to_id
