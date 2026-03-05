from pydantic import BaseModel, field_validator
from typing import Optional
import re


class TenantProfileUpdate(BaseModel):
    name: Optional[str] = None
    gstin: Optional[str] = None
    state_code: Optional[str] = None
    business_type: Optional[str] = None
    return_frequency: Optional[str] = None
    tax_regime: Optional[str] = None

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$", v):
            raise ValueError("Invalid GSTIN format")
        return v

    @field_validator("state_code")
    @classmethod
    def validate_state_code(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid_codes = {str(i).zfill(2) for i in range(1, 38)}
        if v not in valid_codes:
            raise ValueError("Invalid Indian state code")
        return v


class TenantResponse(BaseModel):
    id: str
    name: str
    gstin: Optional[str] = None
    pan: Optional[str] = None
    state_code: Optional[str] = None
    business_type: Optional[str] = None
    return_frequency: str
    fy_start_month: int
    tax_regime: str

    model_config = {"from_attributes": True}
