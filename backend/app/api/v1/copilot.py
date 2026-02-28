from fastapi import APIRouter
from pydantic import BaseModel

from app.dependencies import TenantId, DB
from app.services.copilot_service import handle_copilot_query

router = APIRouter()


class CopilotRequest(BaseModel):
    question: str


class CopilotResponse(BaseModel):
    answer: str
    intent: str
    has_data: bool
    sources: list = []


@router.post("/ask", response_model=CopilotResponse)
async def ask_copilot(
    req: CopilotRequest,
    tenant_id: TenantId = None,
    db: DB = None,
):
    result = await handle_copilot_query(db, tenant_id, req.question)
    return CopilotResponse(**result)
