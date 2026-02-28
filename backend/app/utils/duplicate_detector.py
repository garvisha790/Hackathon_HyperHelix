import hashlib
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.invoice import CanonicalInvoice


def compute_duplicate_hash(
    tenant_id: uuid.UUID,
    vendor_gstin: str | None,
    invoice_number: str,
    invoice_date: str,
    total: float,
) -> str:
    raw = f"{tenant_id}|{(vendor_gstin or '').upper()}|{invoice_number.strip().upper()}|{invoice_date}|{total:.2f}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def check_duplicate(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    duplicate_hash: str,
) -> CanonicalInvoice | None:
    """Check if a canonical invoice with this hash already exists."""
    result = await db.execute(
        select(CanonicalInvoice).where(
            CanonicalInvoice.tenant_id == tenant_id,
            CanonicalInvoice.duplicate_hash == duplicate_hash,
            CanonicalInvoice.is_duplicate.is_(False),
            CanonicalInvoice.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()
