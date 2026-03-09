from pydantic import BaseModel
from typing import Optional


class PnLItem(BaseModel):
    period: str
    revenue: float
    expenses: float
    profit: float


class ExpenseCategory(BaseModel):
    category: str
    amount: float
    percentage: float


class CashFlowItem(BaseModel):
    period: str
    inflow: float
    outflow: float
    net: float


class PipelineStatus(BaseModel):
    uploaded: int
    processing: int
    done: int
    failed: int
    total: int


class GSTTrackerItem(BaseModel):
    period: str
    output_gst: float
    input_gst: float
    net_liability: float


class RecentInvoice(BaseModel):
    id: str
    document_id: str
    invoice_number: str
    vendor_name: Optional[str] = None
    buyer_name: Optional[str] = None
    document_type: str
    transaction_nature: Optional[str] = None
    total: float
    invoice_date: str
    status: str


class DashboardOverview(BaseModel):
    total_documents: int
    total_invoices: int
    total_revenue: float
    total_expenses: float
    net_profit: float = 0
    gst_liability: float
    total_receivables: float = 0
    total_payables: float = 0
    pipeline: PipelineStatus
    pnl: list[PnLItem] = []
    expenses_by_category: list[ExpenseCategory] = []
    gst_tracker: list[GSTTrackerItem] = []
    cashflow: list[CashFlowItem] = []
    recent_invoices: list[RecentInvoice] = []
