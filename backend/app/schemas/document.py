from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    id: str
    upload_url: str
    s3_key: str


class DocumentResponse(BaseModel):
    id: str
    file_name: str
    file_type: Optional[str] = None
    document_type: str
    status: str
    uploaded_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
