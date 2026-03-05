from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class GSTSummaryResponse(BaseModel):
    id: str
    period_start: date
    period_end: date
    period_type: str
    output_cgst: float
    output_sgst: float
    output_igst: float
    output_cess: float
    input_cgst: float
    input_sgst: float
    input_igst: float
    input_cess: float
    net_liability: float
    is_stale: bool
    computed_at: datetime

    model_config = {"from_attributes": True}


class ITSlabBreakup(BaseModel):
    range: str
    rate: float
    tax: float


class ITEstimateResponse(BaseModel):
    id: str
    fy: str
    total_revenue: float
    total_expenses: float
    gross_profit: float
    tax_regime: str
    taxable_income: float
    estimated_tax: float
    cess: float
    total_tax_liability: float
    slab_breakup: list[ITSlabBreakup] = []
    assumptions: dict = {}
    is_stale: bool
    computed_at: datetime

    model_config = {"from_attributes": True}
