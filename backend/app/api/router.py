from fastapi import APIRouter

from app.api.v1 import auth, tenants, documents, invoices, ledger, tax, dashboard, copilot, audit

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(ledger.router, prefix="/ledger", tags=["Ledger"])
api_router.include_router(tax.router, prefix="/tax", tags=["Tax"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(copilot.router, prefix="/copilot", tags=["AI Copilot"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit"])
