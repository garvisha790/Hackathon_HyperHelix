from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func

from app.dependencies import DB, require_role
from app.models.audit import AuditLog

router = APIRouter()


@router.get("/logs")
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user=Depends(require_role("owner")),
    db: DB = None,
):
    query = (
        select(AuditLog)
        .where(AuditLog.tenant_id == user.tenant_id)
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    total_q = select(func.count(AuditLog.id)).where(AuditLog.tenant_id == user.tenant_id)

    result = await db.execute(query)
    total = await db.execute(total_q)

    logs = [
        {
            "id": str(log.id),
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "details": log.details,
            "created_at": log.created_at.isoformat(),
        }
        for log in result.scalars().all()
    ]

    return {"logs": logs, "total": total.scalar() or 0}
