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


class DashboardOverview(BaseModel):
    total_documents: int
    total_invoices: int
    total_revenue: float
    total_expenses: float
    gst_liability: float
    pipeline: PipelineStatus
    pnl: list[PnLItem] = []
    expenses_by_category: list[ExpenseCategory] = []
    gst_tracker: list[GSTTrackerItem] = []
    cashflow: list[CashFlowItem] = []
