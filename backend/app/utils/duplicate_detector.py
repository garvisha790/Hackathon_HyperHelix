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
    """Check if a canonical invoice with this hash already exists.
    
    Only returns invoices where the associated document is not deleted.
    This allows users to replace documents without triggering duplicate detection.
    """
    from app.models.document import Document
    from sqlalchemy import and_
    
    result = await db.execute(
        select(CanonicalInvoice)
        .join(Document, Document.id == CanonicalInvoice.document_id)
        .where(
            and_(
                CanonicalInvoice.tenant_id == tenant_id,
                CanonicalInvoice.duplicate_hash == duplicate_hash,
                CanonicalInvoice.is_duplicate.is_(False),
                CanonicalInvoice.deleted_at.is_(None),
                Document.deleted_at.is_(None),  # Exclude invoices from deleted documents
            )
        )
    )
    return result.scalar_one_or_none()
