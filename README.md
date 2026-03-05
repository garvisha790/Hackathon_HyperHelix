# Digital CA — AI-Powered Chartered Accountant for Indian Businesses

A multi-tenant financial intelligence platform that converts invoices into structured accounting data, maintains automated double-entry books, calculates real-time GST and income tax liability, provides financial dashboards, and answers business questions using grounded AI.

## Architecture

```
Frontend (Next.js 14)  →  Backend (FastAPI)  →  PostgreSQL + Redis
                                ↓
                    AWS (S3 · Textract · Bedrock)
```

**Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic  
**Frontend**: Next.js 14, React Query, Recharts, Tailwind CSS  
**Database**: PostgreSQL 16 + pgvector  
**AI/ML**: AWS Textract (OCR), AWS Bedrock (Claude 3)  
**Storage**: AWS S3 with versioning  
**Auth**: AWS Cognito (JWT)  
**Cache**: Redis  

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.12+
- AWS account (S3, Textract, Bedrock, Cognito)

### 1. Environment Setup
```bash
cp .env.example .env
# Edit .env with your AWS credentials and Cognito config
```

### 2. Start Infrastructure
```bash
docker-compose up -d postgres redis
```

### 3. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
alembic upgrade head
python -m seed.demo_data     # Seed demo data
uvicorn app.main:app --reload
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 5. Access
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Features

| Phase | Feature | Status |
|-------|---------|--------|
| 0 | Multi-tenant auth, RBAC, S3 upload, pipeline state machine | Done |
| 1 | Document Intelligence (Textract OCR, Bedrock validation, duplicate detection) | Done |
| 2 | Automated Bookkeeping (double-entry posting, Tally-aligned CoA, category engine) | Done |
| 3 | Tax Intelligence (GST GSTR-3B aligned, IT FY25-26 slabs, period summaries) | Done |
| 4 | Financial Dashboard (P&L, expenses, GST tracker, cash flow, pipeline status) | Done |
| 5 | AI Copilot (intent routing, SQL aggregation, grounded answers, citations) | Done |
| 6 | Security Hardening (soft delete, tenant isolation tests, audit log, RBAC matrix) | Done |

## Indian Financial System Compliance

- GST: CGST+SGST (intra-state) / IGST (inter-state), rates 0/5/12/18/28%
- GSTIN: Algorithmic checksum validation (15-char format)
- Chart of Accounts: Tally-aligned 15 primary groups
- Financial Year: April 1 - March 31
- Income Tax: New Regime FY 2025-26 slabs with Section 87A rebate
- Document Types: Invoice, Credit Note, Debit Note, Receipt
- Retention: 7-year default (Indian tax law compliance)
