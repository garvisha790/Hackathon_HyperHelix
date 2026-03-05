from datetime import date
from fastapi import APIRouter, Request, Query

from app.dependencies import TenantId, DB
from app.schemas.dashboard import DashboardOverview
from app.services.dashboard_service import get_dashboard_overview

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
async def dashboard_overview(
    request: Request,
    fy_year: int = Query(2025, description="FY start year, e.g. 2025 for FY 2025-26"),
    tenant_id: TenantId = None,
    db: DB = None,
):
    fy_start = date(fy_year, 4, 1)
    fy_end = date(fy_year + 1, 3, 31)
    redis = getattr(request.app.state, "redis", None)
    return await get_dashboard_overview(db, tenant_id, redis, fy_start, fy_end)
