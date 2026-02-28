from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CurrentUser, DB, require_role
from app.models.tenant import Tenant
from app.schemas.tenant import TenantProfileUpdate, TenantResponse
from app.middleware.audit import log_action

router = APIRouter()


@router.get("/me", response_model=TenantResponse)
async def get_tenant_profile(user: CurrentUser, db: DB):
    tenant = await db.get(Tenant, user.tenant_id)
    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        gstin=tenant.gstin,
        pan=tenant.pan,
        state_code=tenant.state_code,
        business_type=tenant.business_type,
        return_frequency=tenant.return_frequency,
        fy_start_month=tenant.fy_start_month,
        tax_regime=tenant.tax_regime,
    )


@router.put("/me", response_model=TenantResponse)
async def update_tenant_profile(
    update: TenantProfileUpdate,
    user=Depends(require_role("owner")),
    db: DB = None,
):
    tenant = await db.get(Tenant, user.tenant_id)

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(tenant, field, value)

    if update.gstin and len(update.gstin) >= 12:
        tenant.pan = update.gstin[2:12]
        tenant.state_code = update.gstin[:2]

    await db.flush()
    await log_action(db, user.tenant_id, user.id, "tenant.update", "tenant", tenant.id)

    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        gstin=tenant.gstin,
        pan=tenant.pan,
        state_code=tenant.state_code,
        business_type=tenant.business_type,
        return_frequency=tenant.return_frequency,
        fy_start_month=tenant.fy_start_month,
        tax_regime=tenant.tax_regime,
    )
