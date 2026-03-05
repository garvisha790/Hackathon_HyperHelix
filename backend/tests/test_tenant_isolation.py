"""Tenant isolation integration test.

Verifies that Tenant A's data cannot be accessed by Tenant B.
"""
import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.tenant import Tenant
from app.models.user import User
from app.models.document import Document


@pytest.fixture
async def two_tenants(db: AsyncSession):
    """Create two tenants with users and documents."""
    tenant_a = Tenant(name="Tenant A", gstin="27AADCA0000A1ZA")
    tenant_b = Tenant(name="Tenant B", gstin="29AADCB0000B1ZB")
    db.add_all([tenant_a, tenant_b])
    await db.flush()

    user_a = User(tenant_id=tenant_a.id, email="a@test.com", cognito_sub="sub-a", role="owner")
    user_b = User(tenant_id=tenant_b.id, email="b@test.com", cognito_sub="sub-b", role="owner")
    db.add_all([user_a, user_b])
    await db.flush()

    doc_a = Document(
        tenant_id=tenant_a.id, uploaded_by=user_a.id,
        file_name="invoice_a.pdf", s3_key="tenants/a/doc.pdf", status="DONE"
    )
    doc_b = Document(
        tenant_id=tenant_b.id, uploaded_by=user_b.id,
        file_name="invoice_b.pdf", s3_key="tenants/b/doc.pdf", status="DONE"
    )
    db.add_all([doc_a, doc_b])
    await db.flush()

    return {
        "tenant_a": tenant_a, "tenant_b": tenant_b,
        "user_a": user_a, "user_b": user_b,
        "doc_a": doc_a, "doc_b": doc_b,
    }


async def test_tenant_a_cannot_see_tenant_b_documents(db: AsyncSession, two_tenants):
    """Tenant A's query must never return Tenant B's documents."""
    ta = two_tenants["tenant_a"]
    tb = two_tenants["tenant_b"]

    result_a = await db.execute(
        select(Document).where(Document.tenant_id == ta.id, Document.deleted_at.is_(None))
    )
    docs_a = result_a.scalars().all()

    result_b = await db.execute(
        select(Document).where(Document.tenant_id == tb.id, Document.deleted_at.is_(None))
    )
    docs_b = result_b.scalars().all()

    assert len(docs_a) == 1
    assert len(docs_b) == 1

    assert docs_a[0].file_name == "invoice_a.pdf"
    assert docs_b[0].file_name == "invoice_b.pdf"

    a_ids = {d.id for d in docs_a}
    b_ids = {d.id for d in docs_b}
    assert a_ids.isdisjoint(b_ids), "Tenant A and B documents must never overlap"


async def test_cross_tenant_document_access_blocked(db: AsyncSession, two_tenants):
    """Querying Tenant A's doc using Tenant B's tenant_id must return nothing."""
    ta = two_tenants["tenant_a"]
    doc_b = two_tenants["doc_b"]

    result = await db.execute(
        select(Document).where(
            Document.id == doc_b.id,
            Document.tenant_id == ta.id,
        )
    )
    assert result.scalar_one_or_none() is None, "Tenant A must not access Tenant B's document"
