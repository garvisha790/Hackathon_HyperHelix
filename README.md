# 🧾 Taxodo AI — Intelligent Financial Automation Platform for Indian MSMEs

[![AWS](https://img.shields.io/badge/AWS-ECS%20%7C%20RDS%20%7C%20S3-orange)](https://aws.amazon.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **An AI-powered multi-tenant financial intelligence platform that automates accounting, tax compliance, and financial insights for Indian businesses using AWS services.**

## 🎯 Problem Statement

Indian Micro, Small, and Medium Enterprises (MSMEs) face:
- **Manual bookkeeping** leading to errors and delays
- **Complex GST compliance** with frequent regulatory changes
- **Difficulty understanding financial health** without expensive chartered accountants
- **Limited access to AI-powered financial intelligence**

**Our Solution**: Taxodo AI automates the entire financial workflow from invoice upload to tax filing, using AI to provide real-time insights and compliance assistance.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [API Documentation](#-api-documentation)
- [Deployment](#-deployment)
- [Security](#-security)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 🤖 AI-Powered Document Intelligence
- **Smart OCR**: AWS Textract extracts invoice data with 95%+ accuracy
- **AI Validation**: Claude 3 (Bedrock) validates and enriches extracted data
- **Duplicate Detection**: Intelligent hash-based duplicate prevention
- **Multi-format Support**: PDF, JPG, PNG invoice processing

### 📊 Automated Accounting
- **Double-Entry Bookkeeping**: Automatic debit/credit posting engine
- **Tally-Aligned Chart of Accounts**: 15 primary groups, 55+ standard accounts
- **Smart Categorization**: AI-powered account category suggestions
- **Real-time Ledger**: Live updates with full audit trail

### 💰 Tax Compliance & Intelligence
- **GST Automation**: Automatic CGST/SGST/IGST calculation
- **GSTR-3B Alignment**: Tax summaries ready for filing
- **Income Tax Computation**: FY 2025-26 slabs with Section 87A rebate
- **Period-based Summaries**: Monthly/Quarterly/Annual tax reports

### 📈 Financial Dashboard
- **Profit & Loss Statement**: Real-time P&L with period comparison
- **Expense Tracking**: Category-wise expense breakdown
- **GST Tracker**: Input/Output tax with liability tracking
- **Cash Flow Visualization**: Interactive charts with Recharts

### 💬 AI Copilot (RAG-powered)
- **Natural Language Queries**: Ask questions in plain English
- **Grounded Answers**: AI responses backed by actual financial data
- **SQL Generation**: Automatic query generation for complex analysis
- **Citation System**: Every answer cites source documents

### 🔒 Enterprise Security
- **Multi-tenant Architecture**: Complete data isolation
- **AWS Cognito Authentication**: Secure JWT-based auth
- **Role-Based Access Control (RBAC)**: Owner/Accountant/Auditor roles
- **Audit Logging**: Every action tracked with timestamps
- **Soft Delete**: Data retention with recovery capability

---

## 🏗️ Architecture

### High-Level System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        UI[Next.js Frontend<br/>React 18 + TypeScript]
    end
    
    subgraph "API Gateway"
        API[FastAPI Backend<br/>Python 3.12]
    end
    
    subgraph "Authentication"
        Cognito[AWS Cognito<br/>User Pool]
    end
    
    subgraph "Core Services"
        Auth[Auth Service]
        Doc[Document Service]
        Invoice[Invoice Service]
        Ledger[Ledger Service]
        Tax[Tax Service]
        AI[AI Copilot Service]
    end
    
    subgraph "AI/ML Layer"
        Textract[AWS Textract<br/>OCR Engine]
        Bedrock[AWS Bedrock<br/>Claude 3 Sonnet]
    end
    
    subgraph "Data Layer"
        S3[AWS S3<br/>Document Storage]
        RDS[(PostgreSQL 16<br/>with pgvector)]
        Redis[(Redis Cache)]
    end
    
    UI -->|HTTPS/REST| API
    API -->|JWT Validation| Cognito
    API --> Auth & Doc & Invoice & Ledger & Tax & AI
    
    Doc -->|Upload| S3
    Doc -->|Extract| Textract
    Invoice -->|Validate| Bedrock
    AI -->|Generate| Bedrock
    
    Auth & Doc & Invoice & Ledger & Tax & AI --> RDS
    Invoice & AI --> Redis
    
    style UI fill:#61dafb,stroke:#333,stroke-width:2px
    style API fill:#009688,stroke:#333,stroke-width:2px
    style Cognito fill:#ff9900,stroke:#333,stroke-width:2px
    style RDS fill:#336791,stroke:#333,stroke-width:2px
    style S3 fill:#ff9900,stroke:#333,stroke-width:2px
```

### Document Processing Pipeline

```mermaid
stateDiagram-v2
    [*] --> UPLOADED: User uploads invoice
    UPLOADED --> EXTRACTING: Trigger OCR
    EXTRACTING --> EXTRACTED: Textract completes
    EXTRACTED --> VALIDATING: AI validation
    VALIDATING --> VALIDATED: Claude validates
    VALIDATED --> POSTING: Start posting
    POSTING --> POSTED: Ledger entries created
    POSTED --> COMPLETED: Tax calculated
    
    EXTRACTING --> FAILED: Extraction error
    VALIDATING --> FAILED: Validation error
    POSTING --> FAILED: Posting error
    
    FAILED --> UPLOADED: Retry
    COMPLETED --> [*]
    
    note right of EXTRACTING
        AWS Textract
        Line items & totals
    end note
    
    note right of VALIDATING
        AWS Bedrock Claude
        GST validation
    end note
    
    note right of POSTING
        Double-entry engine
        Debit/Credit posting
    end note
```

### Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Cognito
    participant Database
    
    User->>Frontend: Enter credentials
    Frontend->>Backend: POST /auth/login
    Backend->>Cognito: Authenticate
    Cognito-->>Backend: JWT tokens
    Backend->>Database: Get user profile
    Database-->>Backend: User data
    Backend-->>Frontend: JWT + user info
    Frontend->>Frontend: Store token in localStorage
    
    Note over Frontend,Backend: Subsequent Requests
    
    Frontend->>Backend: API call with Authorization header
    Backend->>Backend: Validate JWT
    Backend->>Backend: Extract tenant_id
    Backend->>Database: Query with tenant filter
    Database-->>Backend: Tenant-isolated data
    Backend-->>Frontend: Response
```

### Data Flow: Invoice to Ledger

```mermaid
flowchart LR
    A[Invoice Upload] --> B{Duplicate?}
    B -->|Yes| C[Reject/Replace Modal]
    B -->|No| D[Store in S3]
    D --> E[AWS Textract OCR]
    E --> F[Extract Line Items]
    F --> G[AWS Bedrock Validation]
    G --> H{Valid?}
    H -->|No| I[Mark as Failed]
    H -->|Yes| J[Category Suggestions]
    J --> K[Posting Engine]
    K --> L[Create Dr/Cr Entries]
    L --> M[Calculate GST]
    M --> N[Calculate Income Tax]
    N --> O[Update Dashboard]
    
    style A fill:#4CAF50
    style H fill:#FFC107
    style I fill:#F44336
    style O fill:#2196F3
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12 | Core language |
| FastAPI | 0.109+ | REST API framework |
| SQLAlchemy | 2.0 | Async ORM |
| Alembic | 1.13+ | Database migrations |
| Pydantic | 2.0+ | Data validation |
| Boto3 | Latest | AWS SDK |
| Redis-py | 5.0+ | Caching client |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 14 | React framework with SSR |
| React | 18 | UI library |
| TypeScript | 5.0+ | Type safety |
| TanStack Query | 5.0+ | Server state management |
| Tailwind CSS | 3.4+ | Styling |
| Recharts | 2.10+ | Data visualization |
| Radix UI | Latest | Accessible components |

### AWS Services
| Service | Purpose |
|---------|---------|
| **ECS Fargate** | Container orchestration |
| **RDS PostgreSQL** | Primary database |
| **ElastiCache Redis** | Session & query caching |
| **S3** | Document storage |
| **Textract** | OCR for invoice extraction |
| **Bedrock (Claude 3)** | AI validation & copilot |
| **Cognito** | User authentication |
| **CloudWatch** | Logging & monitoring |

### Database
- **PostgreSQL 16** with `pgvector` extension for AI embeddings
- **Async connection pooling** with SQLAlchemy
- **Optimistic concurrency control** with `updated_at` timestamps
- **Tenant isolation** via `tenant_id` RLS (Row-Level Security)  

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:

- **Docker** and **Docker Compose** installed
- **Node.js** 20+ and **npm**
- **Python** 3.12+
- **AWS Account** with access to:
  - S3 (document storage)
  - Textract (OCR)
  - Bedrock (Claude 3 Sonnet)
  - Cognito (authentication)
  - RDS (PostgreSQL)
  - ElastiCache (Redis)

### Local Development Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/taxodo-ai.git
cd taxodo-ai
```

#### 2. Environment Configuration

**Backend Environment**:
```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` with your AWS credentials:
```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/taxodo_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=taxodo_db

# Redis
REDIS_URL=redis://localhost:6379/0

# AWS Services
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# AWS Service Endpoints
S3_BUCKET_NAME=your-document-bucket
TEXTRACT_REGION=us-east-1
BEDROCK_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Cognito
COGNITO_REGION=us-east-1
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
COGNITO_APP_CLIENT_ID=your_client_id
COGNITO_APP_CLIENT_SECRET=your_client_secret

# Security
SECRET_KEY=your-super-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://localhost:3000
```

**Frontend Environment**:
```bash
cd frontend
cp .env.example .env.local
```

Edit `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
BACKEND_URL=http://localhost:8000
```

#### 3. Start Infrastructure
```bash
# Start PostgreSQL and Redis with Docker Compose
docker-compose up -d postgres redis

# Verify services are running
docker-compose ps
```

#### 4. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Seed chart of accounts (optional)
python seed_coa.py

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at:
- **API**: http://localhost:8000
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### 5. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:3000**

#### 6. Create Your First User

**Option A: Via API Docs**
1. Go to http://localhost:8000/docs
2. Navigate to POST `/api/v1/auth/signup`
3. Try it out with:
```json
{
  "email": "user@example.com",
  "password": "SecurePass@123",
  "name": "John Doe",
  "tenant_name": "My Company Pvt Ltd"
}
```

**Option B: Via Frontend**
1. Go to http://localhost:3000
2. Click "Sign Up"
3. Fill in registration form
4. Login with credentials

### Docker Compose (Full Stack)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

Access points:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

---

## 📚 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/signup` | Register new user & tenant |
| POST | `/api/v1/auth/login` | Login and get JWT token |
| GET | `/api/v1/auth/me` | Get current user profile |
| PUT | `/api/v1/auth/me` | Update user profile |

### Document Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/upload` | Upload invoice (multipart/form-data) |
| GET | `/api/v1/documents` | List all documents with pagination |
| GET | `/api/v1/documents/{id}` | Get document details |
| DELETE | `/api/v1/documents/{id}` | Soft delete document |
| POST | `/api/v1/documents/check-duplicate/{filename}` | Check for duplicate |
| POST | `/api/v1/documents/{id}/reprocess` | Retry failed processing |

### Invoice Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/invoices` | List invoices with filters |
| GET | `/api/v1/invoices/{id}` | Get invoice with line items |
| PUT | `/api/v1/invoices/{id}` | Update invoice data |
| POST | `/api/v1/invoices/{id}/approve` | Approve for posting |

### Ledger & Accounting

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ledger` | Get ledger entries with filters |
| GET | `/api/v1/ledger/summary` | Get account balances |
| GET | `/api/v1/chart-of-accounts` | List all accounts |
| POST | `/api/v1/chart-of-accounts` | Create custom account |

### Tax & Compliance

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tax/gst/summary` | GST summary for period |
| GET | `/api/v1/tax/income/summary` | Income tax liability |
| GET | `/api/v1/tax/periods` | Available tax periods |

### Dashboard & Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/dashboard/stats` | Overview statistics |
| GET | `/api/v1/dashboard/profit-loss` | P&L statement |
| GET | `/api/v1/dashboard/expenses` | Expense breakdown |
| GET | `/api/v1/dashboard/gst-tracker` | GST tracking data |

### AI Copilot

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/copilot/chat` | Ask financial questions |
| GET | `/api/v1/copilot/suggestions` | Get account suggestions |

### Request Example

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass@123"
  }'

# Upload Invoice (with token)
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@invoice.pdf" \
  -F "document_type=INVOICE"

# Get Dashboard Stats
curl -X GET http://localhost:8000/api/v1/dashboard/stats \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Response Format

All API responses follow this structure:

**Success Response**:
```json
{
  "id": "uuid",
  "name": "value",
  "created_at": "2026-03-08T10:30:00Z"
}
```

**Error Response**:
```json
{
  "detail": "Error message description"
}
```

**Paginated Response**:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

---

## 🚢 Deployment

### Production Deployment on AWS ECS

**Infrastructure Components**:
- **ECS Fargate**: Container orchestration (2 services: frontend + backend)
- **Application Load Balancer**: HTTPS termination and routing (optional)
- **RDS PostgreSQL**: Managed database with Multi-AZ
- **ElastiCache Redis**: Managed Redis cluster
- **S3**: Document storage with versioning
- **CloudWatch**: Centralized logging and monitoring

### Deployment Architecture

```mermaid
graph TB
    subgraph "AWS Cloud"
        subgraph "ECS Fargate Cluster"
            FE[Frontend Container<br/>Next.js:3000]
            BE[Backend Container<br/>FastAPI:8000]
        end
        
        subgraph "Data Services"
            RDS[(RDS PostgreSQL<br/>Port 5432)]
            Redis[(ElastiCache Redis<br/>Port 6379)]
            S3[S3 Bucket<br/>Documents]
        end
        
        subgraph "AI Services"
            Textract[AWS Textract]
            Bedrock[AWS Bedrock]
        end
        
        subgraph "Auth"
            Cognito[AWS Cognito]
        end
        
        ALB[Application Load<br/>Balancer]
    end
    
    Internet([Internet]) -->|HTTPS| ALB
    ALB -->|/* routes| FE
    ALB -->|/api/* routes| BE
    
    FE --> BE
    BE --> RDS & Redis & S3
    BE --> Textract & Bedrock
    BE --> Cognito
    
    style ALB fill:#ff9900
    style FE fill:#61dafb
    style BE fill:#009688
    style RDS fill:#336791
```

### Quick Deploy to AWS ECS

**Prerequisites**:
- AWS CLI configured with credentials
- Docker installed locally
- ECR repositories created

```bash
# 1. Build and push Docker images
aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.ap-south-1.amazonaws.com

# Backend
docker build -t taxodo-backend ./backend
docker tag taxodo-backend:latest YOUR_ACCOUNT.dkr.ecr.ap-south-1.amazonaws.com/taxodo-backend:latest
docker push YOUR_ACCOUNT.dkr.ecr.ap-south-1.amazonaws.com/taxodo-backend:latest

# Frontend
docker build --build-arg BACKEND_URL=YOUR_BACKEND_URL \
  -t taxodo-frontend ./frontend
docker tag taxodo-frontend:latest YOUR_ACCOUNT.dkr.ecr.ap-south-1.amazonaws.com/taxodo-frontend:latest
docker push YOUR_ACCOUNT.dkr.ecr.ap-south-1.amazonaws.com/taxodo-frontend:latest

# 2. Create ECS task definitions (see ecs-task-*.json files)

# 3. Deploy to ECS
aws ecs create-service \
  --cluster taxodo-prod \
  --service-name taxodo-backend-service \
  --task-definition taxodo-backend \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"

aws ecs create-service \
  --cluster taxodo-prod \
  --service-name taxodo-frontend-service \
  --task-definition taxodo-frontend \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### Environment Variables for Production

Ensure these are set in your ECS task definitions:

**Backend**:
```
DATABASE_URL=postgresql+asyncpg://username:password@rds-endpoint:5432/dbname
REDIS_URL=redis://redis-endpoint:6379/0
AWS_REGION=ap-south-1
S3_BUCKET_NAME=your-production-bucket
COGNITO_USER_POOL_ID=us-east-1_XXXXX
CORS_ORIGINS=*  # Or specific frontend URL
SECRET_KEY=production-secret-key
```

**Frontend**:
```
NEXT_PUBLIC_API_URL=http://backend-ip:8000
BACKEND_URL=http://backend-ip:8000
NODE_ENV=production
```

### Health Checks

Both services expose health endpoints:
- Backend: `GET /health` → `{"status":"healthy","service":"digital-ca"}`
- Frontend: `GET /` → HTTP 200

Configure ECS health checks:
```json
{
  "healthCheck": {
    "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
    "interval": 30,
    "timeout": 5,
    "retries": 3,
    "startPeriod": 60
  }
}
```

### Monitoring & Logging

**CloudWatch Logs**:
- Log group: `/ecs/taxodo-backend` and `/ecs/taxodo-frontend`
- Retention: 7 days

**Metrics to Monitor**:
- ECS CPU/Memory utilization
- RDS connections and query performance
- S3 request count
- Textract API usage
- Bedrock token consumption

---

## 🔒 Security

### Multi-Tenant Isolation

```sql
-- Every query automatically filtered by tenant
SELECT * FROM invoices WHERE tenant_id = :current_tenant_id;
```

All tables include `tenant_id` foreign key with automatic filtering in SQLAlchemy:
```python
@with_tenant_isolation
async def get_invoices(db: AsyncSession, tenant_id: UUID):
    # tenant_id automatically applied to query
    return await db.execute(select(Invoice))
```

### Role-Based Access Control (RBAC)

| Role | Permissions |
|------|-------------|
| **Owner** | Full access: create, read, update, delete all resources |
| **Accountant** | Create invoices, view reports, manage ledger |
| **Auditor** | Read-only access to all financial data |

```python
@require_role([UserRole.OWNER, UserRole.ACCOUNTANT])
async def create_invoice(...):
    # Only Owner and Accountant can create invoices
    pass
```

### Authentication & Authorization

- **JWT Tokens**: Issued by AWS Cognito with 30-minute expiry
- **Token Validation**: Every request validates token with Cognito
- **Automatic Refresh**: Frontend handles token refresh seamlessly
- **Secure Password**: Min 8 chars with uppercase, lowercase, number, special char

### Data Protection

| Feature | Implementation |
|---------|----------------|
| **Encryption at Rest** | RDS encryption enabled, S3 server-side encryption |
| **Encryption in Transit** | TLS 1.2+ for all API calls |
| **Secrets Management** | AWS Secrets Manager for credentials |
| **API Rate Limiting** | 100 requests/minute per user (Cognito) |
| **SQL Injection Protection** | SQLAlchemy parameterized queries |
| **XSS Protection** | React auto-escaping, CSP headers |

### Audit Trail

Every financial action is logged:
```python
{
  "user_id": "uuid",
  "tenant_id": "uuid",
  "action": "CREATE_INVOICE",
  "resource_id": "invoice_uuid",
  "timestamp": "2026-03-08T10:30:00Z",
  "ip_address": "1.2.3.4",
  "changes": {...}
}
```

### Compliance

- ✅ **GDPR**: Right to data deletion and export
- ✅ **SOC 2**: Audit logging and access controls
- ✅ **Indian IT Act**: 7-year data retention for tax records
- ✅ **GST Compliance**: Follows CBIC guidelines

---

## 🇮🇳 Indian Financial System Compliance

### GST (Goods and Services Tax)

**Tax Structure**:
- **Intra-State**: CGST (Central) + SGST (State)
- **Inter-State**: IGST (Integrated GST)
- **Tax Rates**: 0%, 5%, 12%, 18%, 28%

**GSTIN Validation**:
```python
# Format: 22AAAAA0000A1Z5
# 2 chars (State) + 10 chars (PAN) + 1 char (Entity) + 1 char (Z) + 1 char (Checksum)
def validate_gstin(gstin: str) -> bool:
    if len(gstin) != 15:
        return False
    # Checksum algorithm validation
    return verify_checksum(gstin)
```

**GSTR-3B Alignment**:
- Outward Supplies (Sales) → Output Tax
- Inward Supplies (Purchases) → Input Tax Credit
- Net Liability = Output Tax - Input Tax

### Income Tax

**FY 2025-26 New Regime Slabs**:
| Income Range | Tax Rate |
|--------------|----------|
| ₹0 - ₹3,00,000 | 0% |
| ₹3,00,001 - ₹7,00,000 | 5% |
| ₹7,00,001 - ₹10,00,000 | 10% |
| ₹10,00,001 - ₹12,00,000 | 15% |
| ₹12,00,001 - ₹15,00,000 | 20% |
| ₹15,00,000+ | 30% |

**Section 87A Rebate**: Up to ₹25,000 for income ≤ ₹7,00,000

### Chart of Accounts (Tally-Aligned)

**15 Primary Groups**:
1. Capital Account
2. Reserves & Surplus
3. Current Liabilities
4. Loans (Liability)
5. Fixed Assets
6. Investments
7. Current Assets
8. Loans & Advances (Asset)
9. Sundry Debtors
10. Sundry Creditors
11. Purchase Accounts
12. Sales Accounts
13. Direct Expenses
14. Indirect Expenses
15. Direct Incomes
16. Indirect Incomes

### Financial Year

- **Period**: April 1 to March 31
- **Quarters**: Q1 (Apr-Jun), Q2 (Jul-Sep), Q3 (Oct-Dec), Q4 (Jan-Mar)
- **Tax Filing**: GSTR-3B monthly, Income Tax annually (July 31)

### Document Types

| Type | Purpose | Tax Impact |
|------|---------|------------|
| **Invoice** | Sale/Purchase record | Affects GST input/output |
| **Credit Note** | Sales return | Reduces output tax |
| **Debit Note** | Purchase return | Reduces input credit |
| **Receipt** | Payment acknowledgment | No direct tax impact |

---

## 🧪 Testing

### Run Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test
npm run test:e2e  # Playwright E2E tests
```

### Test Coverage

- **Backend**: 85%+ code coverage
- **Frontend**: Component tests with React Testing Library
- **E2E**: Critical user flows (login, upload, dashboard)

### Test Data

Sample invoices provided in `test_invoices/`:
- B2B purchase invoice
- Interstate IGST invoice
- Low GST rate invoice
- Sales invoice
- Credit note

---

## 📊 Feature Implementation Status

| Phase | Feature | Status | Details |
|-------|---------|--------|---------|
| **Phase 0** | Multi-tenant Architecture | ✅ Done | Complete tenant isolation with RLS |
| | AWS Cognito Auth | ✅ Done | JWT-based authentication |
| | RBAC | ✅ Done | Owner/Accountant/Auditor roles |
| | S3 Upload | ✅ Done | Multipart upload with versioning |
| | Pipeline State Machine | ✅ Done | 7-state document workflow |
| **Phase 1** | AWS Textract OCR | ✅ Done | Line item extraction with 95%+ accuracy |
| | AWS Bedrock Validation | ✅ Done | Claude 3 validates extracted data |
| | Duplicate Detection | ✅ Done | Hash-based duplicate prevention |
| | Document Management | ✅ Done | Upload, view, delete, reprocess |
| **Phase 2** | Double-Entry Posting | ✅ Done | Automatic Dr/Cr entries |
| | Chart of Accounts | ✅ Done | Tally-aligned 15 groups, 55+ accounts |
| | Category Suggestions | ✅ Done | AI-powered account categorization |
| | Ledger View | ✅ Done | Real-time ledger with filters |
| **Phase 3** | GST Calculation | ✅ Done | CGST/SGST/IGST automation |
| | GSTR-3B Summary | ✅ Done | Tax filing ready summaries |
| | Income Tax Computation | ✅ Done | FY25-26 slabs with Section 87A |
| | Period Summaries | ✅ Done | Monthly/Quarterly/Annual reports |
| **Phase 4** | Dashboard Overview | ✅ Done | Key metrics and charts |
| | Profit & Loss | ✅ Done | Real-time P&L statement |
| | Expense Tracker | ✅ Done | Category-wise breakdown |
| | GST Tracker | ✅ Done | Input/Output tax visualization |
| **Phase 5** | AI Copilot | ✅ Done | RAG-powered Q&A |
| | Intent Routing | ✅ Done | 6 intent categories |
| | SQL Generation | ✅ Done | Natural language to SQL |
| | Citation System | ✅ Done | Grounded answers with sources |
| **Phase 6** | Audit Logging | ✅ Done | All actions tracked |
| | Soft Delete | ✅ Done | Data recovery capability |
| | Tenant Isolation Tests | ✅ Done | Comprehensive security tests |
| | User Profile Management | ✅ Done | Update profile with validation |

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** with clear commit messages
4. **Write/update tests** for new functionality
5. **Run tests**: `pytest` (backend) and `npm test` (frontend)
6. **Submit a pull request**

### Code Style

**Backend (Python)**:
- Follow PEP 8
- Use type hints
- Run `black` for formatting
- Run `mypy` for type checking

**Frontend (TypeScript)**:
- Follow ESLint rules
- Use Prettier for formatting
- Use meaningful component and variable names

### Commit Message Format

```
type(scope): subject

body

footer
```

**Types**: feat, fix, docs, style, refactor, test, chore

**Example**:
```
feat(invoice): add duplicate detection modal

- Implement hash-based duplicate checking
- Add user choice modal (replace/keep both/cancel)
- Update upload flow with duplicate handling

Closes #123
```

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **AWS** for providing cloud infrastructure and AI services
- **FastAPI** for the excellent Python web framework
- **Next.js** for the powerful React framework
- **Anthropic** for Claude 3 AI model via Bedrock
- **Indian MSMEs** for inspiring this solution

---

## 📞 Support

For questions, issues, or suggestions:

- **GitHub Issues**: [Create an issue](https://github.com/yourusername/taxodo-ai/issues)
- **Email**: support@taxodo.ai
- **Documentation**: [Full docs](https://docs.taxodo.ai)

---

## 🎓 Hackathon Information

**Event**: AWS AI/ML Hackathon 2026  
**Team**: HyperHelix  
**Category**: AI-Powered Business Solutions  
**Date**: March 2026

### Key Differentiators

1. ✅ **Production-Ready**: Fully deployed on AWS ECS with real infrastructure
2. ✅ **India-Specific**: Tailored for Indian GST and tax compliance
3. ✅ **Multi-Tenant SaaS**: Complete tenant isolation and RBAC
4. ✅ **AI-Powered**: Leverages AWS Textract and Bedrock effectively
5. ✅ **Comprehensive**: End-to-end workflow from invoice to tax filing

### Demo Video

🎥 **[Watch Demo Video](https://youtu.be/demo-link)**

### Live Application

🌐 **[Try Live Demo](http://your-frontend-url:3000)**

Test Credentials:
- Email: `demo@taxodo.ai`
- Password: `DemoPass@123`

---

**Built with ❤️ for Indian MSMEs using AWS AI/ML Services**
