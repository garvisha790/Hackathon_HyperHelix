# AGENT.md - Taxodo AI Project Guide

## Project Identity

- Product name: `Taxodo AI` (some code/docs still use the older name `Digital CA`).
- Category: AI-powered finance, bookkeeping, and tax intelligence SaaS for Indian SMEs.
- Core goal: convert uploaded business documents into validated accounting data, automate ledger posting, compute GST/IT estimates, and provide grounded AI answers.

## What We Are Building

Taxodo AI is an "auditor-grade" financial copilot with four core outcomes:

1. Remove manual bookkeeping for standard invoices/receipts.
2. Keep books continuously updated with double-entry ledger integrity.
3. Provide real-time GST and income tax visibility.
4. Let business users ask natural-language questions over their own financial data.

## Scope Implemented (Current Codebase)

- Multi-tenant auth and RBAC (`owner`, `accountant`) with Cognito-backed flows.
- Document upload pipeline: S3 upload -> Textract OCR -> algorithmic + Bedrock validation.
- Canonical invoice generation with duplicate detection.
- Approval/rejection workflow before posting to ledger.
- Double-entry posting engine aligned to Indian accounting categories.
- GST summary and FY-based income tax estimation.
- Dashboard (P&L, expenses, GST tracker, cash flow, pipeline).
- AI copilot with intent routing (`sql_aggregate`, `document_lookup`, `explanation`).
- Audit logging and tenant isolation tests.

## Architecture Snapshot

```text
Next.js frontend (React Query + Tailwind + Recharts)
        ->
FastAPI backend (/api/v1)
        ->
PostgreSQL (primary financial store) + Redis (cache/session)
        ->
AWS services: S3, Textract, Bedrock, Cognito
```

## Key Domain Entities

- `Tenant`: business-level container and financial settings (FY start, tax regime).
- `User`: belongs to tenant, role-based access.
- `Document`: uploaded file + processing status lifecycle.
- `Extraction`: raw Textract output + structured extraction + confidence.
- `Validation`: field-level pass/warn/fail results.
- `CanonicalInvoice`: normalized invoice record used for downstream accounting.
- `LedgerTransaction` + `JournalLine`: double-entry journal system.
- `GSTSummary` + `ITEstimate`: computed tax outputs.
- `AuditLog`: immutable action trail.

## Critical Invariants (Do Not Break)

- Tenant isolation: every data query must be tenant-scoped.
- Soft delete awareness: exclude `deleted_at` rows in reads.
- Ledger integrity: total debit must equal total credit for every transaction.
- Approval gate: only approved invoices should post to the ledger.
- Financial AI grounding: responses must be based on tenant data, not hallucinated.

## Primary Workflows

1. Authentication
   - User signs up/logs in, receives token, frontend stores session metadata.

2. Document Processing
   - Upload metadata created -> pre-signed URL returned.
   - Client uploads file to S3.
   - Backend pipeline sets status transitions:
     - `UPLOADED -> PROCESSING -> EXTRACTED -> VALIDATED -> DONE` (or `FAILED`).
   - Canonical invoice and validation records are generated.

3. Approval and Posting
   - User reviews extracted invoice and validation details.
   - Approve: posting engine creates balanced ledger transaction + journal lines.
   - Reject: invoice marked rejected; no posting.

4. Tax and Dashboard
   - GST summary aggregates duty/tax ledger accounts by period.
   - Income tax estimate derives P&L and applies FY slabs.
   - Dashboard pulls aggregate metrics and chart series.

5. AI Copilot
   - Intent classification.
   - Data retrieval (aggregates/documents/context).
   - Bedrock-generated grounded answer.

## API Surface (Backend `/api/v1`)

- `auth`: signup, login.
- `tenants`: get/update tenant settings.
- `documents`: upload init, list, detail, delete.
- `invoices`: invoice detail, validation detail, approve/reject, download URL.
- `ledger`: account tree, transaction list/detail, update, recompute.
- `tax`: GST summary, income tax estimate.
- `dashboard`: overview metrics/charts.
- `copilot`: ask financial question.
- `audit`: list audit logs.

## Repository Map

- `backend/app/api/v1/*`: API endpoints.
- `backend/app/services/*`: business workflows (pipeline, posting, tax, copilot).
- `backend/app/models/*`: SQLAlchemy models.
- `backend/alembic/*`: DB migrations.
- `backend/seed/*`: chart of accounts + demo seed data.
- `frontend/src/app/*`: Next.js routes (auth + dashboard pages).
- `frontend/src/components/*`: UI/layout/dashboard components.
- `frontend/src/lib/api.ts`: axios client with bearer token interceptor.

## Local Development

1. `cp .env.example .env` and set AWS/Cognito values.
2. `docker-compose up -d postgres redis`.
3. Backend:
   - `cd backend`
   - `pip install -r requirements.txt`
   - `alembic upgrade head`
   - `python -m seed.demo_data`
   - `uvicorn app.main:app --reload`
4. Frontend:
   - `cd frontend`
   - `npm install`
   - `npm run dev`

## UI/UX Direction (Current Product Intent)

- Light mode only.
- Tone: trustworthy, government-adjacent, precise, calm.
- Data-first layouts: left-aligned content, sticky table headers, tabular numerics.
- Primary visual language: deep teal + restrained neutrals, amber only for high-importance CTAs.
- Motion: subtle (about 120ms), no playful or elastic effects.
- Accessibility: WCAG AA text contrast, status never color-only (icon + label).

## Known Gaps / Technical Debt

- Naming drift: product naming still mixed (`Digital CA` vs `Taxodo AI`).
- Posting heuristic `_is_purchase` currently defaults to purchase and needs stronger logic.
- Copilot response currently returns empty `sources`; citation support can be expanded.
- Development auth mode bypasses strict JWT verification for local convenience.

## Agent Working Rules

- Prefer incremental, verifiable changes over big rewrites.
- Preserve API contracts used by frontend pages.
- When changing financial logic, add/adjust tests before merge.
- Never ship cross-tenant query paths.
- Keep docs in sync when changing pipeline states, tax logic, or workflows.

## Definition of Done for New Features

- Business behavior implemented end-to-end (API + service + UI where relevant).
- Tenant and role constraints enforced.
- Financial calculations validated with sample cases.
- Errors handled with actionable user messaging.
- Tests pass (or test gaps are explicitly documented).
- Documentation updated (`README.md`, this `AGENT.md`, and API docs as needed).
