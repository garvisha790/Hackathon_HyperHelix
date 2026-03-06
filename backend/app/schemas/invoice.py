from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import date, datetime


class LineItemSchema(BaseModel):
    description: str = ""
    hsn_sac: Optional[str] = None
    qty: float = 1
    rate: float = 0
    taxable_value: float = 0
    gst_rate: float = 0
    cgst: float = 0
    sgst: float = 0
    igst: float = 0


class CanonicalInvoiceResponse(BaseModel):
    id: str
    document_id: str
    document_type: str
    invoice_number: str
    invoice_date: date
    vendor_name: Optional[str] = None
    vendor_gstin: Optional[str] = None
    vendor_state_code: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_gstin: Optional[str] = None
    buyer_state_code: Optional[str] = None
    place_of_supply: Optional[str] = None
    subtotal: float
    cgst: float
    sgst: float
    igst: float
    cess: float
    total: float
    line_items: list[dict]
    validation_status: str
    is_duplicate: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ValidationFieldResult(BaseModel):
    status: str  # pass, fail, warn
    message: Optional[str] = None
    confidence: Optional[float] = None


class ValidationResponse(BaseModel):
    id: str
    document_id: str
    overall_status: str
    field_results: dict[str, ValidationFieldResult]
    warnings_count: int
    errors_count: int
    validated_by: str
    created_at: datetime

    model_config = {"from_attributes": True}

class CanonicalInvoiceUpdateRequest(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    vendor_name: Optional[str] = None
    vendor_gstin: Optional[str] = None
    buyer_gstin: Optional[str] = None
    place_of_supply: Optional[str] = None
    subtotal: Optional[float] = None
    cgst: Optional[float] = None
    sgst: Optional[float] = None
    igst: Optional[float] = None
    total: Optional[float] = None

class FieldSuggestion(BaseModel):
    field_name: str
    old_value: Any
    suggested_value: Any
    reasoning: str

class AISuggestionResponse(BaseModel):
    suggestions: List[FieldSuggestion]
    summary_of_analysis: str
