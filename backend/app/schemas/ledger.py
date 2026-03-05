from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class JournalLineResponse(BaseModel):
    id: str
    account_id: str
    account_name: Optional[str] = None
    account_code: Optional[str] = None
    debit: float
    credit: float

    model_config = {"from_attributes": True}


class LedgerTransactionResponse(BaseModel):
    id: str
    document_id: Optional[str] = None
    transaction_date: date
    description: Optional[str] = None
    status: str
    version: int
    assigned_category: Optional[str] = None
    category_method: Optional[str] = None
    journal_lines: list[JournalLineResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class LedgerTransactionListResponse(BaseModel):
    transactions: list[LedgerTransactionResponse]
    total: int


class TransactionEditRequest(BaseModel):
    description: Optional[str] = None
    assigned_category: Optional[str] = None
    journal_lines: Optional[list[dict]] = None
    reason: str


class AccountTreeResponse(BaseModel):
    id: str
    code: str
    name: str
    account_type: str
    tally_group: Optional[str] = None
    is_system: bool
    is_cash_or_bank: bool
    children: list["AccountTreeResponse"] = []

    model_config = {"from_attributes": True}
