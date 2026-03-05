"""Seed demo data for hackathon presentation.

Creates a sample tenant, user, and Indian GST invoices.
Run: python -m seed.demo_data
"""
import asyncio
import uuid
from datetime import date

from app.database import engine, async_session, Base
from app.models import *  # noqa
from seed.chart_of_accounts import seed_chart_of_accounts


DEMO_INVOICES = [
    {
        "invoice_number": "INV-2025-001",
        "invoice_date": date(2025, 4, 15),
        "vendor_name": "Reliance Jio Infocomm Ltd",
        "vendor_gstin": "27AABCR5055K1ZT",
        "buyer_gstin": "27AADCS0472N1Z2",
        "subtotal": 5000.00,
        "cgst": 450.00,
        "sgst": 450.00,
        "igst": 0,
        "total": 5900.00,
        "doc_type": "invoice",
        "category": "Telephone Expenses",
    },
    {
        "invoice_number": "INV-2025-002",
        "invoice_date": date(2025, 5, 1),
        "vendor_name": "Amazon Web Services India",
        "vendor_gstin": "29AABCT1332L1ZC",
        "buyer_gstin": "27AADCS0472N1Z2",
        "subtotal": 25000.00,
        "cgst": 0,
        "sgst": 0,
        "igst": 4500.00,
        "total": 29500.00,
        "doc_type": "invoice",
        "category": "Internet & Hosting",
    },
    {
        "invoice_number": "INV-2025-003",
        "invoice_date": date(2025, 6, 10),
        "vendor_name": "Hindustan Petroleum Corp",
        "vendor_gstin": "27AAACH3749J1ZK",
        "buyer_gstin": "27AADCS0472N1Z2",
        "subtotal": 8000.00,
        "cgst": 1440.00,
        "sgst": 1440.00,
        "igst": 0,
        "total": 10880.00,
        "doc_type": "invoice",
        "category": "Fuel & Conveyance",
    },
    {
        "invoice_number": "SALE-2025-001",
        "invoice_date": date(2025, 4, 20),
        "vendor_name": "Demo Business (self)",
        "vendor_gstin": "27AADCS0472N1Z2",
        "buyer_gstin": "29AABCT5678M1ZD",
        "subtotal": 100000.00,
        "cgst": 0,
        "sgst": 0,
        "igst": 18000.00,
        "total": 118000.00,
        "doc_type": "invoice",
        "category": "Sales Accounts",
        "is_sale": True,
    },
    {
        "invoice_number": "CN-2025-001",
        "invoice_date": date(2025, 5, 15),
        "vendor_name": "Reliance Jio Infocomm Ltd",
        "vendor_gstin": "27AABCR5055K1ZT",
        "buyer_gstin": "27AADCS0472N1Z2",
        "subtotal": 1000.00,
        "cgst": 90.00,
        "sgst": 90.00,
        "igst": 0,
        "total": 1180.00,
        "doc_type": "credit_note",
        "category": "Telephone Expenses",
    },
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        tenant = Tenant(
            name="HyperHelix Demo Pvt Ltd",
            gstin="27AADCS0472N1Z2",
            pan="AADCS0472N",
            state_code="27",
            business_type="service",
            return_frequency="quarterly",
            tax_regime="new",
        )
        db.add(tenant)
        await db.flush()

        user = User(
            tenant_id=tenant.id,
            email="demo@hyperhelix.in",
            name="Demo User",
            cognito_sub=str(uuid.uuid4()),
            role="owner",
        )
        db.add(user)
        await db.flush()

        account_ids = await seed_chart_of_accounts(db, tenant.id)

        for inv_data in DEMO_INVOICES:
            doc = Document(
                tenant_id=tenant.id,
                uploaded_by=user.id,
                file_name=f"{inv_data['invoice_number']}.pdf",
                s3_key=f"tenants/{tenant.id}/documents/{uuid.uuid4()}.pdf",
                document_type=inv_data["doc_type"],
                status="DONE",
            )
            db.add(doc)
            await db.flush()

            invoice = CanonicalInvoice(
                document_id=doc.id,
                tenant_id=tenant.id,
                document_type=inv_data["doc_type"],
                invoice_number=inv_data["invoice_number"],
                invoice_date=inv_data["invoice_date"],
                vendor_name=inv_data["vendor_name"],
                vendor_gstin=inv_data["vendor_gstin"],
                vendor_state_code=inv_data["vendor_gstin"][:2] if inv_data["vendor_gstin"] else None,
                buyer_gstin=inv_data["buyer_gstin"],
                buyer_state_code=inv_data["buyer_gstin"][:2] if inv_data["buyer_gstin"] else None,
                place_of_supply=inv_data["buyer_gstin"][:2] if inv_data["buyer_gstin"] else "27",
                subtotal=inv_data["subtotal"],
                cgst=inv_data["cgst"],
                sgst=inv_data["sgst"],
                igst=inv_data["igst"],
                total=inv_data["total"],
                line_items=[{"description": inv_data["vendor_name"], "taxable_value": inv_data["subtotal"]}],
                validation_status="APPROVED",
                duplicate_hash=str(uuid.uuid4()),
            )
            db.add(invoice)
            await db.flush()

        await db.commit()
        print(f"Demo data seeded. Tenant ID: {tenant.id}")
        print(f"Login email: demo@hyperhelix.in")
        print(f"Dev token: dev:{user.cognito_sub}:{user.email}")


if __name__ == "__main__":
    asyncio.run(seed())
