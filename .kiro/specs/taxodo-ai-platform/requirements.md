# Taxodo AI – Comprehensive Requirements Document

## AWS-Native, AI-First Financial Copilot for Indian SMEs

## Table of Contents

1. [Project Title & Identity](#1-project-title--identity)
2. [Executive Summary](#2-executive-summary)
3. [Problem Statement](#3-problem-statement)
4. [Vision & Objectives](#4-vision--objectives)
5. [Scope of the System](#5-scope-of-the-system)
6. [Target Users & Personas](#6-target-users--personas)
7. [Functional Requirements (Detailed)](#7-functional-requirements-detailed)
8. [Non-Functional Requirements (Deep Technical)](#8-non-functional-requirements-deep-technical)
9. [System Architecture Requirements (AWS-Native)](#9-system-architecture-requirements-aws-native)
10. [Data Flow Requirements](#10-data-flow-requirements)
11. [AI & ML Requirements](#11-ai--ml-requirements)
12. [API & Integration Requirements](#12-api--integration-requirements)
13. [DevOps & Deployment Requirements](#13-devops--deployment-requirements)
14. [Data Model Requirements](#14-data-model-requirements)
15. [Multi-Tenancy Requirements](#15-multi-tenancy-requirements)
16. [Compliance & Regulatory Requirements](#16-compliance--regulatory-requirements)
17. [Assumptions & Constraints](#17-assumptions--constraints)
18. [Risks & Mitigations](#18-risks--mitigations)
19. [Future Enhancements (Phase 2 & 3)](#19-future-enhancements-phase-2--3)
20. [Success Metrics (KPIs)](#20-success-metrics-kpis)
21. [Glossary](#21-glossary)

---

## 1. Project Title & Identity

**Project Name:** Taxodo AI  
**Tagline:** AI-Powered Business & Tax Copilot for Indian SMEs  
**Type:** Cloud-Native SaaS Platform  
**Architecture:** Microservices, Event-Driven, AI-First  
**Primary Cloud Provider:** Amazon Web Services (AWS)  
**AI Engine:** Amazon Bedrock (LLM) + RAG Architecture  

---

## 2. Executive Summary

Taxodo AI is a cloud-native, AI-driven financial and tax intelligence platform designed for small business owners, freelancers, traders, and online sellers in India. The system automates document ingestion, bookkeeping, real-time tax estimation (GST and Income Tax), and AI-powered financial advisory through a conversational interface.

Unlike traditional accounting tools that focus on compliance and manual entry, Taxodo AI functions as an **intelligent financial copilot** that converts raw financial data into actionable business decisions.

### Key Differentiators

| Feature | Traditional Tools | Taxodo AI |
|---------|------------------|-----------|
| Data Entry | Manual | AI-Automated (OCR + LLM) |
| Tax Estimation | End of period | Real-time, event-driven |
| Financial Insights | Static reports | Conversational AI copilot |
| Document Handling | Manual upload & filing | Intelligent ingestion & classification |
| Advisory | None (CA dependent) | AI-powered financial advisor |
| Architecture | Monolithic, on-premise | Cloud-native, microservices |
| Scalability | Limited | Auto-scaling, serverless |

The platform will be built using a scalable AWS-native architecture leveraging AI, RAG (Retrieval-Augmented Generation), event-driven pipelines, and secure fintech-grade infrastructure.

---

## 3. Problem Statement

### 3.1 Core Problem

Small businesses and freelancers in India face significant challenges in financial management due to:

- **Fragmented financial tools** – Reliance on disconnected systems like Tally, Excel, ClearTax, and manual CA consultations
- **Manual bookkeeping processes** – Time-consuming, error-prone data entry that diverts focus from business operations
- **Lack of real-time tax visibility** – Tax liabilities are only discovered at filing time, leading to cash flow surprises
- **Poor financial decision-making** – No intelligent insights or predictions available for daily business decisions
- **Scattered financial data** – Invoices in PDFs, receipts as images, WhatsApp bills, leading to data silos
- **Late tax realization** – Financial stress caused by unexpected tax obligations at the end of filing periods

### 3.2 Current Market Gap

Current tools focus on:
- ✅ Compliance (filing)
- ✅ Data entry
- ✅ Static dashboards

They do **NOT** provide:
- ❌ Real-time financial intelligence
- ❌ Conversational financial insights
- ❌ Decision-level advisory
- ❌ Automated document understanding
- ❌ Predictive tax estimation
- ❌ AI-powered expense categorization

### 3.3 Impact of the Problem

| Impact Area | Description |
|-------------|-------------|
| Financial Loss | Missed tax deductions, ITC losses averaging ₹50K-2L/year for SMEs |
| Time Waste | 8-12 hours/week spent on manual bookkeeping by business owners |
| Decision Quality | Decisions made without data-backed financial context |
| Compliance Risk | Late filings, incorrect GST returns, penalty exposure |
| Growth Limitation | Lack of financial clarity prevents strategic business growth |

---

## 4. Vision & Objectives

### 4.1 Vision Statement

> To build an AI-native financial copilot that autonomously reads, understands, and advises on business finance and taxation in real time using cloud-native AI infrastructure — making intelligent financial management accessible to every Indian SME.

### 4.2 Mission

Democratize financial intelligence for India's 63+ million MSMEs by providing an affordable, AI-powered platform that eliminates the gap between raw financial data and actionable business decisions.

### 4.3 Primary Objectives

| # | Objective | Key Result |
|---|-----------|------------|
| O1 | Automate financial data ingestion from documents | >90% OCR accuracy on Indian invoices |
| O2 | Maintain real-time digital bookkeeping | Zero manual entry for standard documents |
| O3 | Provide live GST & Income Tax estimation | <1 second cached tax recalculation |
| O4 | Enable AI-powered financial decision support | <3 second AI response latency |
| O5 | Offer multi-device cloud dashboard access | <2 second dashboard load time |
| O6 | Reduce accountant dependency for operational insights | 70% reduction in routine CA queries |

### 4.4 Design Principles

1. **AI-First** – Every feature should leverage AI where possible
2. **Cloud-Native** – No on-premise dependencies; fully managed AWS services
3. **Event-Driven** – Real-time reactivity to financial events
4. **Security-First** – Fintech-grade encryption and access control
5. **User-Centric** – Simple interfaces hiding complex AI infrastructure
6. **Scalable** – Architecture that grows with user base without redesign

---

## 5. Scope of the System

### 5.1 In-Scope (Phase 1 – MVP)

| Module | Features |
|--------|----------|
| **Document Ingestion** | Invoice/receipt upload, OCR extraction, AI categorization |
| **Bookkeeping Engine** | Automated ledger entries, transaction categorization, expense/revenue tracking |
| **Tax Intelligence Engine** | Real-time GST calculation, Income Tax estimation, ITC tracking |
| **AI Copilot** | Natural language financial Q&A, RAG-based contextual insights |
| **Financial Dashboard** | P&L view, cash flow tracking, expense analytics, tax tracker |
| **User Management** | Authentication, RBAC (Owner/Accountant), multi-tenant isolation |
| **Cloud Infrastructure** | Full AWS-native deployment with CI/CD |

### 5.2 Out-of-Scope (Phase 1)

| Feature | Reason | Target Phase |
|---------|--------|:------------:|
| Direct GST filing integration | Requires GSTN API partnership | Phase 2 |
| Banking API integrations | Open Banking standards evolving | Phase 2 |
| Offline desktop software | Cloud-first strategy | N/A |
| Multi-country tax systems | India-first focus | Phase 3 |
| Mobile native apps (iOS/Android) | PWA sufficient for MVP | Phase 2 |
| Bank statement auto-ingestion | Requires bank integrations | Phase 2 |
| CA collaboration portal | B2B feature | Phase 3 |
| Multi-language AI assistant | English-first | Phase 2 |

---

## 6. Target Users & Personas

### 6.1 Primary User Segments

| Segment | Description | Size (India) | Key Need |
|---------|-------------|:------------:|----------|
| **MSMEs** | Small business owners with <₹5Cr revenue | 63M+ | Automated bookkeeping, tax clarity |
| **Freelancers & Consultants** | Independent professionals | 15M+ | Expense tracking, ITR estimation |
| **D2C & E-commerce Sellers** | Online sellers (Amazon, Flipkart, Shopify) | 5M+ | GST tracking across platforms |
| **Traders & Shop Owners** | Retail and wholesale traders | 20M+ | Invoice management, ITC optimization |
| **Startups** | Early-stage companies (<50 employees) | 1L+ | Financial dashboard, tax planning |
| **CA-Assisted Businesses** | Businesses working with chartered accountants | All | Organized data for CA review |

### 6.2 User Personas (Detailed)

#### Persona 1: Rajesh – Small Business Owner
- **Age:** 42 | **Location:** Pune | **Business:** Manufacturing (₹2Cr revenue)
- **Pain Points:** Spends 10+ hours/week on manual bookkeeping, surprised by quarterly GST dues, relies entirely on CA for tax planning
- **Goals:** Automate invoice processing, real-time tax visibility, reduce CA dependency
- **Tech Comfort:** Medium (uses smartphone, WhatsApp, basic Excel)

#### Persona 2: Priya – Freelance Designer
- **Age:** 28 | **Location:** Bangalore | **Business:** Freelance UI/UX (₹18L/year)
- **Pain Points:** Messy expense tracking (mix of UPI, cash, cards), confused about GST registration threshold, multiple income sources
- **Goals:** Automated expense categorization, ITR estimation, financial clarity
- **Tech Comfort:** High (digital native, comfortable with SaaS tools)

#### Persona 3: Amit – E-commerce Seller
- **Age:** 35 | **Location:** Delhi | **Business:** D2C Apparel (₹4Cr revenue)
- **Pain Points:** Multi-platform sales (Amazon, Flipkart, own website), complex GST across states (IGST/CGST/SGST), high volume of invoices
- **Goals:** Automated GST reconciliation, ITC tracking, cash flow visibility
- **Tech Comfort:** High (uses multiple platforms, cloud tools)

---

## 7. Functional Requirements (Detailed)

### 7.1 User Authentication & Access Management

#### 7.1.1 Features
- Secure user signup/login with email and phone
- OAuth integration (Google, Microsoft)
- Email OTP and SMS OTP verification
- Role-based access control (RBAC)
  - **Owner:** Full access to all features and settings
  - **Accountant:** Access to financial data, no settings changes
  - **Viewer:** Read-only dashboard access (future)
- Session management with automatic timeout
- Multi-factor authentication (MFA) support
- Password complexity enforcement
- Account recovery flow

#### 7.1.2 AWS Services Required
| Service | Purpose |
|---------|---------|
| **Amazon Cognito** | User pool management, authentication flows, OAuth integration |
| **AWS IAM** | Service-level role policies, least-privilege access |
| **AWS KMS** | Encryption key management for user credentials |
| **AWS WAF** | Protection against authentication attacks (brute force, credential stuffing) |

#### 7.1.3 Acceptance Criteria
- [ ] User can sign up with email + OTP in <30 seconds
- [ ] OAuth (Google) login completes in <5 seconds
- [ ] Role change reflects immediately across all sessions
- [ ] Failed login attempts trigger lockout after 5 attempts
- [ ] Session expires after 30 minutes of inactivity

---

### 7.2 Document Ingestion & Processing Module

#### 7.2.1 Supported Input Formats
| Format | Type | Max Size | Processing |
|--------|------|:--------:|------------|
| PDF Invoices | `.pdf` | 10 MB | Textract AnalyzeExpense |
| Image Receipts | `.jpg`, `.jpeg`, `.png` | 5 MB | Textract AnalyzeExpense |
| WhatsApp Bills | Compressed `.jpg` | 2 MB | Pre-processing + Textract |
| Scanned Documents | `.tiff`, `.pdf` (scanned) | 15 MB | Multi-page Textract |
| Bulk Upload | `.zip` (multiple files) | 50 MB | Batch processing pipeline |

#### 7.2.2 Functional Capabilities (Detailed)

**Document Upload:**
- Drag-and-drop upload interface
- Multi-file upload support (up to 20 files simultaneously)
- Upload progress indicator with real-time status
- Automatic file type validation
- Client-side compression for large images
- Pre-signed S3 URL generation for secure direct upload

**OCR & Data Extraction:**
- Automatic text extraction from invoices and receipts
- Vendor/business name detection
- GSTIN (Goods and Services Tax Identification Number) extraction and validation
- Invoice number and date parsing
- Tax breakdown parsing:
  - CGST (Central GST)
  - SGST (State GST)
  - IGST (Integrated GST)
  - Cess (if applicable)
- Line item table extraction (description, quantity, rate, amount)
- Total amount extraction with tax segregation
- HSN/SAC code extraction
- Payment terms detection

**AI-Powered Classification:**
- Document type classification:
  - Sales Invoice
  - Purchase Invoice
  - Expense Receipt
  - Credit Note
  - Debit Note
  - Payment Receipt
- Expense category auto-assignment (travel, office, salary, raw material, etc.)
- Revenue vs. expense classification
- Duplicate document detection
- Confidence scoring for extracted data

#### 7.2.3 AWS Native Requirements (Detailed)

| Service | API/Feature | Purpose |
|---------|-------------|---------|
| **Amazon S3** | PutObject, GetObject, Pre-signed URLs | Secure document storage with versioning |
| **Amazon Textract** | AnalyzeExpense API | Specialized invoice/receipt OCR |
| **Amazon Textract** | AnalyzeDocument (Tables) | Table structure extraction |
| **AWS Lambda** | Event-triggered functions | Processing triggers on S3 upload events |
| **Amazon SQS** | Standard Queue | Async processing queue for document jobs |
| **Amazon SQS** | Dead Letter Queue (DLQ) | Failed processing retry & monitoring |
| **AWS Step Functions** | State Machine | Multi-step workflow orchestration |
| **Amazon Bedrock** | LLM Inference | AI-powered data validation & classification |

#### 7.2.4 Processing Pipeline Flow

```
User Upload → S3 Event → SQS Queue → Lambda Trigger → 
Textract OCR → Raw Data Extraction → Bedrock LLM Validation → 
Categorization → RDS Ledger Entry → OpenSearch Embedding → 
Dashboard Notification
```

#### 7.2.5 Acceptance Criteria
- [ ] PDF invoice processed and categorized within 30 seconds
- [ ] Image receipt processed within 15 seconds
- [ ] OCR accuracy > 90% on standard Indian GST invoices
- [ ] GSTIN extracted and validated against format rules
- [ ] Tax components (CGST/SGST/IGST) correctly parsed
- [ ] Duplicate detection prevents double-entry
- [ ] Failed documents routed to DLQ with admin notification
- [ ] Bulk upload of 20 files completes within 5 minutes

---

### 7.3 Automated Bookkeeping Engine

#### 7.3.1 Features (Detailed)

**Ledger Management:**
- Automatic ledger entry creation from processed documents
- Double-entry bookkeeping support (debit/credit)
- Multi-ledger support (Cash, Bank, Sales, Purchase, Expense categories)
- Ledger reconciliation tools
- Transaction reversal and adjustment

**Transaction Categorization:**
- AI-based automatic categorization using Bedrock LLM
- Custom category creation by user
- Category suggestion with confidence score
- Learning from user corrections (feedback loop)
- Default Indian accounting categories:
  - Sales Revenue
  - Cost of Goods Sold (COGS)
  - Operating Expenses (Rent, Utilities, Salary, Travel, Office)
  - Capital Expenditure
  - Tax Payments
  - Other Income/Expenses

**Revenue & Expense Tracking:**
- Real-time revenue tracking with source attribution
- Expense categorization and trend analysis
- Monthly/quarterly/yearly comparison views
- Budget vs. actual tracking (future phase)
- Recurring transaction identification

**Historical Data Management:**
- Full transaction history with search and filter
- Date range queries
- Vendor-wise transaction history
- Category-wise breakdowns
- Export to CSV/Excel/PDF
- Audit trail for all modifications

#### 7.3.2 Data Storage Architecture

| Storage | Technology | Data Type |
|---------|-----------|-----------|
| **Primary Financial DB** | Amazon RDS PostgreSQL | Ledger entries, transactions, accounts, tax records |
| **Structured Extracted Data** | Amazon DynamoDB (optional) | Raw OCR results, processing metadata |
| **Document Archive** | Amazon S3 | Original uploaded documents |
| **Cache Layer** | Amazon ElastiCache Redis | Frequently accessed financial summaries |

#### 7.3.3 Database Schema Requirements (Key Tables)

```
tenants
├── tenant_id (PK)
├── business_name
├── gstin
├── pan
├── business_type
└── created_at

users
├── user_id (PK)
├── tenant_id (FK)
├── email
├── role (owner/accountant)
└── cognito_sub

documents
├── document_id (PK)
├── tenant_id (FK)
├── s3_key
├── document_type
├── processing_status
├── extracted_data (JSONB)
├── confidence_score
└── uploaded_at

ledger_entries
├── entry_id (PK)
├── tenant_id (FK)
├── document_id (FK)
├── entry_date
├── account_type
├── category
├── debit_amount
├── credit_amount
├── description
├── gstin_vendor
├── tax_details (JSONB)
└── created_at

tax_records
├── tax_id (PK)
├── tenant_id (FK)
├── period (month/quarter)
├── gst_payable
├── gst_input_credit
├── net_gst_liability
├── income_tax_estimated
├── total_revenue
├── total_expenses
├── net_profit
└── calculated_at
```

#### 7.3.4 Acceptance Criteria
- [ ] Ledger entry auto-created within 5 seconds of document processing
- [ ] AI categorization accuracy > 85%
- [ ] User can override/edit any auto-generated entry
- [ ] Transaction search returns results within 1 second
- [ ] Export generates accurate CSV/PDF within 10 seconds
- [ ] Audit trail captures all modifications with timestamp and user

---

### 7.4 Real-Time Tax Intelligence Engine

#### 7.4.1 Core Capabilities (Detailed)

**GST Engine:**
- Real-time GST payable calculation (output tax - input tax)
- Input Tax Credit (ITC) tracking and optimization
- CGST/SGST/IGST computation based on transaction type
- Inter-state vs. intra-state classification
- Monthly and quarterly GST summary
- GSTR-1 & GSTR-3B data preparation
- Reverse Charge Mechanism (RCM) detection
- GST rate mapping by HSN/SAC code
- Threshold monitoring (₹20L/₹40L registration limit)

**Income Tax Engine:**
- Estimated income tax based on net profit
- Old regime vs. new regime comparison
- Section-wise deduction tracking (80C, 80D, etc.)
- Advance tax computation and due date alerts
- Presumptive taxation (Section 44AD/44ADA) eligibility check
- TDS tracking on income received
- Annual tax projection with seasonal adjustments

**Tax Forecasting:**
- Rolling tax liability projection (3-month, 6-month, 12-month)
- Scenario simulation ("What if I make this purchase?")
- Tax-saving opportunity alerts
- Advance tax installment reminders

#### 7.4.2 Example User Queries Handled
| Query | Engine Response |
|-------|----------------|
| "How much GST do I owe this month?" | Calculated GST liability with ITC offset |
| "What will be my tax liability this year?" | Projected income tax with current data |
| "Should I opt for new or old tax regime?" | Comparative analysis with recommendations |
| "Impact of buying ₹5L equipment on taxes?" | Simulation with depreciation and ITC impact |
| "Am I eligible for presumptive taxation?" | Eligibility check based on revenue threshold |

#### 7.4.3 AWS Requirements (Detailed)

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **ECS Fargate** | Tax Engine Microservice hosting | 1 vCPU, 2GB RAM, auto-scaling |
| **EventBridge** | Event-driven recalculation triggers | Rules on transaction events |
| **ElastiCache Redis** | Fast tax computation caching | Cache cluster, 1 node (r6g.large) |
| **RDS PostgreSQL** | Tax data persistence | Multi-AZ, encrypted, automated backups |
| **CloudWatch** | Tax calculation monitoring | Custom metrics, alarms |

#### 7.4.4 Computation Logic

```
GST Liability = Output Tax (Sales) - Input Tax Credit (Purchases)
  where:
    Output Tax = Σ (sale_amount × applicable_gst_rate)
    Input Tax = Σ (purchase_amount × gst_rate) [valid ITC only]
    
Income Tax (New Regime FY 2025-26):
  0-3L    → 0%
  3-7L    → 5%
  7-10L   → 10%
  10-12L  → 15%
  12-15L  → 20%
  >15L    → 30%
  + Surcharge & Cess as applicable
```

#### 7.4.5 Acceptance Criteria
- [ ] GST calculation updates within 1 second of new transaction (cached)
- [ ] Income tax estimation refreshes within 5 seconds of ledger change
- [ ] Tax forecast accuracy within 5% variance of actual
- [ ] Scenario simulation returns results in <2 seconds
- [ ] Tax regime comparison generates accurate side-by-side analysis
- [ ] Advance tax alerts sent 15 days before due dates

---

### 7.5 AI Copilot (Conversational Financial Advisor)

#### 7.5.1 Capabilities (Detailed)

**Natural Language Financial Q&A:**
- Understand and respond to financial queries in plain English
- Support for Hindi-English (Hinglish) queries (future)
- Multi-turn conversation with context retention
- Follow-up question handling

**RAG-Based Contextual Insights:**
- Retrieve relevant financial context from user's data
- Combine structured data (RDS) with semantic search (OpenSearch)
- Generate responses grounded in user's actual financial data
- Reference specific transactions and documents in responses

**Business Advisory Recommendations:**
- Expense optimization suggestions
- Revenue growth pattern insights
- Cash flow management advice
- Tax-saving strategies based on user's profile
- Seasonal business pattern recognition

**Financial Explanations:**
- Break down complex tax concepts in simple language
- Explain financial metrics and their implications
- Provide context for financial trends
- Educational responses about GST, Income Tax, and bookkeeping

#### 7.5.2 Example Interactions

```
User: "Why is my profit decreasing?"
AI: "Based on your last 3 months data, your revenue has remained stable 
at ~₹8.5L/month, but your operating expenses have increased by 23% — 
primarily driven by a ₹1.2L increase in raw material costs and ₹45K 
increase in logistics. I'd recommend reviewing your vendor contracts 
for raw materials."

User: "Can I afford to hire an employee?"
AI: "Based on your current monthly profit of ₹1.8L and cash reserves 
of ₹5.2L, hiring at ₹35K/month salary would reduce your monthly profit 
to ₹1.45L. You'd maintain a 6-month runway. However, if the hire drives 
even 10% revenue growth, it would be net positive within 4 months."

User: "Which expense category is highest?"
AI: "Your top expense categories this quarter are:
1. Raw Materials: ₹12.4L (45%)
2. Salaries: ₹6.8L (25%)
3. Rent & Utilities: ₹3.2L (12%)
4. Logistics: ₹2.8L (10%)
5. Others: ₹2.2L (8%)
Raw materials have increased 15% compared to last quarter."
```

#### 7.5.3 AWS AI Stack (Detailed)

| Service | Purpose | Model/Config |
|---------|---------|--------------|
| **Amazon Bedrock** | LLM inference for response generation | Claude 3.5 Sonnet / Titan |
| **Amazon OpenSearch** | Vector database for RAG retrieval | k-NN plugin enabled, HNSW index |
| **Amazon Bedrock** | Embedding generation | Titan Embedding v2 |
| **ECS Fargate** | AI Copilot microservice | 2 vCPU, 4GB RAM |
| **ElastiCache Redis** | Conversation session caching | Session state management |

#### 7.5.4 RAG Pipeline Architecture

```
User Query → Query Embedding (Bedrock Titan) → 
OpenSearch k-NN Search (Top-K relevant chunks) → 
RDS SQL Query (Relevant financial data) → 
Context Assembly → 
Prompt Construction (System + Context + Query) → 
Bedrock LLM Inference → 
Response Formatting → 
User Response
```

#### 7.5.5 Acceptance Criteria
- [ ] AI response latency < 3 seconds (P95)
- [ ] Responses grounded in user's actual financial data
- [ ] No hallucinated financial figures
- [ ] Multi-turn conversation maintains context for 10+ turns
- [ ] Graceful handling of out-of-scope queries
- [ ] Source attribution for financial data referenced in responses

---

### 7.6 Financial Dashboard & Analytics

#### 7.6.1 Features (Detailed)

**Profit & Loss Visualization:**
- Monthly/quarterly/yearly P&L statement
- Revenue breakdown by source/category
- Expense breakdown by category
- Gross profit and net profit trends
- Year-over-year comparison

**Cash Flow Tracking:**
- Real-time cash position
- Cash inflow vs. outflow visualization
- Projected cash flow (30/60/90 days)
- Cash runway calculation

**Expense Analytics:**
- Category-wise expense distribution (pie/donut chart)
- Vendor-wise expense ranking
- Monthly expense trends (line chart)
- Anomaly detection and alerts
- Budget vs. actual comparison (future)

**Tax Liability Tracker:**
- Monthly GST liability dashboard
- ITC utilization tracker
- Income tax projection meter
- Advance tax due date reminders
- Tax payment history

**Financial KPIs (Real-Time):**
- Revenue growth rate
- Profit margin (gross & net)
- Expense ratio
- Cash conversion cycle
- Customer acquisition cost (if applicable)
- Working capital ratio

**Risk Alerts & Anomaly Detection:**
- Unusual transaction alerts
- Sudden expense spikes
- Revenue drop notifications
- Cash flow crunch warnings
- GST threshold approaching alerts

#### 7.6.2 AWS Services for Dashboard

| Service | Purpose |
|---------|---------|
| **Amazon CloudFront** | Fast global content delivery for dashboard assets |
| **Amazon S3** | Static frontend hosting (React/Next.js build) |
| **API Gateway** | RESTful APIs for dashboard data |
| **API Gateway WebSocket** | Real-time dashboard updates (push) |
| **ElastiCache Redis** | Real-time KPI caching and pre-computation |
| **CloudWatch** | Dashboard performance monitoring |

#### 7.6.3 Acceptance Criteria
- [ ] Dashboard loads within 2 seconds (Time to Interactive)
- [ ] Charts render within 1 second of data load
- [ ] Real-time updates reflect within 5 seconds of transaction
- [ ] Mobile-responsive layout works on screens ≥ 320px
- [ ] Export generates PDF/CSV within 10 seconds
- [ ] All financial figures match to the paisa (₹0.01 precision)

---

### 7.7 Multi-Device Cloud Access

#### 7.7.1 Requirements (Detailed)

| Requirement | Specification |
|-------------|---------------|
| **Primary Platform** | Web-first responsive dashboard (React/Next.js) |
| **Mobile Access** | Progressive Web App (PWA) with offline capability |
| **Tablet Support** | Responsive layout optimized for tablet screens |
| **Real-time Sync** | WebSocket-based state synchronization across devices |
| **Offline Mode** | Service worker caching for dashboard viewing (read-only) |
| **State Management** | Cloud-state backend, stateless frontend |
| **Session Handling** | Single sign-on across devices with Cognito |
| **Push Notifications** | Web push for tax alerts, anomalies, and reminders |

---

## 8. Non-Functional Requirements (Deep Technical)

### 8.1 Scalability Requirements

| Metric | Target | Strategy |
|--------|--------|----------|
| **Concurrent Users** | 10,000+ | ECS auto-scaling, stateless services |
| **Document Processing** | 100K documents/day | SQS queue-based async processing |
| **Database Connections** | 500+ concurrent | RDS connection pooling (PgBouncer) |
| **AI Queries** | 50K queries/day | Bedrock throughput provisioning |
| **Data Growth** | 10TB/year | S3 lifecycle policies, RDS storage auto-scaling |

**Scaling Strategy:**
- Cloud-native microservices architecture (no monolith bottleneck)
- ECS Fargate auto-scaling (CPU/Memory-based)
- SQS-based async processing (decouple producers/consumers)
- Horizontal scaling for all stateless services
- Event-driven pipelines (EventBridge) for loose coupling
- Read replicas for RDS under heavy query load

### 8.2 Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Dashboard Load** | < 2 seconds | Time to Interactive (TTI) |
| **API Response (P50)** | < 200ms | Server-side latency |
| **API Response (P95)** | < 500ms | Server-side latency |
| **AI Copilot Response** | < 3 seconds | End-to-end latency |
| **Document Processing** | < 30 seconds | Upload to ledger entry |
| **Tax Recalculation (Cached)** | < 1 second | Redis-cached computation |
| **Tax Recalculation (Full)** | < 5 seconds | Full database computation |
| **Search Queries** | < 500ms | OpenSearch response time |

**Performance Strategy:**
- CloudFront CDN for static assets (global edge locations)
- ElastiCache Redis for frequently accessed data
- Pre-computed financial summaries (materialized views)
- Async processing for all non-blocking operations
- Connection pooling for database access
- Optimized SQL queries with proper indexing

### 8.3 Security (Fintech Grade)

| Layer | Requirement | AWS Service |
|-------|-------------|-------------|
| **Transport** | TLS 1.2+ for all communications | ACM, CloudFront, ALB |
| **Encryption at Rest** | AES-256 for all stored data | AWS KMS |
| **Authentication** | MFA, OAuth, OTP | Amazon Cognito |
| **Authorization** | RBAC with least privilege | AWS IAM, Cognito Groups |
| **Network** | VPC isolation, private subnets | VPC, Security Groups, NACLs |
| **Secrets** | No hardcoded credentials | AWS Secrets Manager |
| **WAF** | SQL injection, XSS protection | AWS WAF |
| **DDoS** | Protection against DDoS | AWS Shield Standard |
| **Audit** | Full API and access logging | AWS CloudTrail |
| **Data Isolation** | Per-tenant data segregation | Row-level security (RLS) |

**Security Architecture Principles:**
1. Zero trust networking – all services authenticate
2. Encryption everywhere – in transit and at rest
3. Least privilege access – minimal IAM permissions
4. Defense in depth – multiple security layers
5. Continuous monitoring – CloudTrail + CloudWatch alarms
6. Incident response – automated alerting and runbooks

### 8.4 Availability & Reliability

| Metric | Target |
|--------|--------|
| **Uptime SLA** | 99.9% (8.76 hours downtime/year max) |
| **RTO (Recovery Time Objective)** | < 1 hour |
| **RPO (Recovery Point Objective)** | < 5 minutes |
| **Database Availability** | Multi-AZ RDS deployment |
| **Compute Availability** | Multi-AZ ECS tasks |
| **Data Durability** | 99.999999999% (S3 eleven 9s) |

**Reliability Strategy:**
- Multi-AZ deployment for all critical services
- Automated health checks and service recovery
- Circuit breaker patterns in microservices
- Graceful degradation (AI features degrade, core bookkeeping continues)
- Automated backups with point-in-time recovery
- Blue-green deployment for zero-downtime updates

### 8.5 Compliance Readiness (India Fintech Context)

| Requirement | Implementation |
|-------------|---------------|
| **Data Residency** | All data stored in AWS Mumbai (ap-south-1) region |
| **Financial Data Encryption** | KMS-managed encryption for all financial records |
| **Access Control** | RBAC with full audit trail |
| **Audit Logs** | CloudTrail logging for all API calls |
| **Privacy** | No sharing of user financial data with third parties |
| **Data Retention** | Configurable retention policies per tenant |
| **Right to Delete** | User data deletion capability on request |

---

## 9. System Architecture Requirements (AWS-Native)

### 9.1 Compute Layer

| Service | Use Case | Configuration |
|---------|----------|---------------|
| **ECS Fargate** | Primary microservices hosting | Auto-scaling, 6 services |
| **AWS Lambda** | Event-driven processing | Document processing triggers |
| **API Gateway (REST)** | RESTful API management | Rate limiting, API keys |
| **API Gateway (WebSocket)** | Real-time push updates | Dashboard live updates |
| **Application Load Balancer** | Traffic distribution | Health checks, path routing |

### 9.2 Storage Layer

| Service | Data Type | Purpose |
|---------|-----------|---------|
| **Amazon S3** | Unstructured (Documents) | Invoice/receipt storage, data lake |
| **Amazon RDS PostgreSQL** | Structured (Financial) | Ledger, transactions, tax records |
| **Amazon OpenSearch** | Vector + Search | RAG embeddings, semantic search |
| **Amazon ElastiCache Redis** | Cache | Real-time metrics, session cache |
| **Amazon DynamoDB** | Semi-structured (Optional) | Processing metadata, raw OCR data |

### 9.3 AI & ML Layer

| Service | Purpose | Model |
|---------|---------|-------|
| **Amazon Bedrock** | LLM reasoning & inference | Claude 3.5 Sonnet |
| **Amazon Bedrock** | Text embedding generation | Titan Embedding v2 |
| **Amazon Textract** | Document OCR & extraction | AnalyzeExpense API |
| **Amazon OpenSearch** | Vector indexing & k-NN search | HNSW algorithm |

### 9.4 Networking Layer

| Service | Purpose |
|---------|---------|
| **Amazon VPC** | Network isolation |
| **Public Subnets** | ALB, NAT Gateway |
| **Private Subnets (App)** | ECS services, Lambda |
| **Private Subnets (Data)** | RDS, ElastiCache, OpenSearch |
| **NAT Gateway** | Outbound internet for private subnets |
| **Security Groups** | Service-level firewall rules |
| **NACLs** | Subnet-level access control |

---

## 10. Data Flow Requirements

### 10.1 Document Processing Flow
```
1. User uploads invoice/receipt via dashboard
2. File stored in S3 with encryption (SSE-KMS)
3. S3 event triggers SQS message
4. Lambda/ECS worker picks up processing job
5. Amazon Textract performs OCR extraction (AnalyzeExpense)
6. Bedrock LLM validates, structures, and categorizes data
7. Ledger entry auto-created in RDS PostgreSQL
8. Tax engine recalculates liabilities (EventBridge trigger)
9. Document embedding indexed in OpenSearch
10. Dashboard updates via WebSocket push
11. User notified of processing completion
```

### 10.2 AI Query Flow
```
1. User asks financial question via chat interface
2. Query sent to AI Copilot service via API Gateway
3. Query embedded using Bedrock Titan Embedding
4. OpenSearch k-NN search retrieves relevant document chunks
5. RDS queried for relevant financial data (SQL)
6. Context assembled from vector search + structured data
7. Prompt constructed with system instructions + context + query
8. Bedrock LLM generates context-aware response
9. Response formatted and returned to user
10. Conversation cached in Redis for multi-turn support
```

### 10.3 Tax Computation Flow
```
1. New transaction added/modified in ledger
2. EventBridge event triggered
3. Tax Engine microservice processes event
4. GST liability recalculated
5. Income tax projection updated
6. Results cached in Redis
7. WebSocket push updates dashboard
8. Tax records persisted in RDS
```

---

## 11. AI & ML Requirements

### 11.1 OCR & Document Understanding
| Requirement | Specification |
|-------------|---------------|
| OCR Engine | Amazon Textract (AnalyzeExpense) |
| Accuracy Target | >90% on standard Indian invoices |
| Supported Languages | English, Hindi (printed text) |
| Table Extraction | Line items, quantities, rates, amounts |
| Handwritten Text | Best-effort (not guaranteed) |
| Processing Time | <15 seconds per document |

### 11.2 LLM Requirements
| Requirement | Specification |
|-------------|---------------|
| Primary Model | Amazon Bedrock (Claude 3.5 Sonnet) |
| Fallback Model | Amazon Bedrock (Titan Text) |
| Max Tokens | 4096 (response) |
| Temperature | 0.3 (factual, low creativity) |
| Guardrails | Bedrock Guardrails (financial safety) |
| Grounding | RAG-based, no hallucinated figures |

### 11.3 Embedding & Vector Search
| Requirement | Specification |
|-------------|---------------|
| Embedding Model | Amazon Bedrock Titan Embedding v2 |
| Vector Dimensions | 1024 |
| Index Type | HNSW (OpenSearch k-NN) |
| Top-K Retrieval | 5-10 relevant chunks |
| Similarity Metric | Cosine similarity |
| Chunk Size | 500-800 tokens |

---

## 12. API & Integration Requirements

### 12.1 REST API Endpoints (Key)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/signup` | POST | User registration |
| `/api/auth/login` | POST | User authentication |
| `/api/documents/upload` | POST | Document upload (pre-signed URL) |
| `/api/documents/{id}` | GET | Get document details |
| `/api/documents/{id}/status` | GET | Processing status |
| `/api/ledger/entries` | GET | List ledger entries (paginated) |
| `/api/ledger/entries` | POST | Manual ledger entry |
| `/api/ledger/entries/{id}` | PUT | Edit ledger entry |
| `/api/tax/gst/summary` | GET | GST liability summary |
| `/api/tax/income/estimate` | GET | Income tax estimation |
| `/api/tax/simulate` | POST | Tax scenario simulation |
| `/api/analytics/pnl` | GET | Profit & Loss data |
| `/api/analytics/cashflow` | GET | Cash flow data |
| `/api/analytics/expenses` | GET | Expense breakdown |
| `/api/copilot/query` | POST | AI copilot query |
| `/api/copilot/history` | GET | Conversation history |

### 12.2 WebSocket APIs
| Channel | Purpose |
|---------|---------|
| `/ws/dashboard` | Real-time dashboard updates |
| `/ws/processing` | Document processing status updates |
| `/ws/alerts` | Tax alerts and notifications |

### 12.3 API Standards
- RESTful design principles
- JSON request/response format
- JWT-based authentication (Cognito tokens)
- API versioning (v1/v2)
- Rate limiting (100 requests/minute per user)
- Pagination for list endpoints (cursor-based)
- Consistent error response format
- OpenAPI 3.0 specification

---

## 13. DevOps & Deployment Requirements

### 13.1 CI/CD Pipeline

| Stage | Tool | Description |
|-------|------|-------------|
| **Source** | GitHub | Version control, PR-based workflow |
| **Build** | AWS CodeBuild | Docker image build, unit tests |
| **Test** | CodeBuild | Integration tests, security scan |
| **Registry** | Amazon ECR | Docker image storage |
| **Deploy** | AWS CodePipeline | Automated deployment pipeline |
| **Staging** | ECS (Staging cluster) | Pre-production validation |
| **Production** | ECS (Prod cluster) | Blue-green deployment |

### 13.2 Infrastructure as Code
- **Terraform** or **AWS CDK** for all infrastructure provisioning
- Version-controlled infrastructure definitions
- Environment parity (dev/staging/prod)
- Automated environment provisioning

### 13.3 Monitoring & Observability

| Service | Purpose |
|---------|---------|
| **CloudWatch Logs** | Centralized logging for all services |
| **CloudWatch Metrics** | Custom application metrics |
| **CloudWatch Alarms** | Automated alerting on thresholds |
| **AWS X-Ray** | Distributed tracing across services |
| **CloudTrail** | API audit logging |
| **OpenTelemetry** | Advanced distributed tracing (future) |

### 13.4 Key Monitoring Metrics

| Metric | Alert Threshold |
|--------|-----------------|
| API Error Rate | > 1% |
| API Latency (P95) | > 1 second |
| ECS CPU Utilization | > 80% |
| RDS Connection Count | > 80% of max |
| SQS Queue Depth | > 1000 messages |
| Document Processing Failures | > 5% |
| AI Response Latency | > 5 seconds |
| Redis Cache Hit Rate | < 70% |

---

## 14. Data Model Requirements

### 14.1 Data Classification

| Data Type | Sensitivity | Encryption | Retention |
|-----------|:-----------:|:----------:|:---------:|
| User Credentials | Critical | KMS + Hashing | Account lifetime |
| Financial Records | High | KMS at-rest | 7 years (India regulation) |
| Tax Calculations | High | KMS at-rest | 7 years |
| Uploaded Documents | High | SSE-S3/KMS | 7 years |
| AI Conversation Logs | Medium | KMS at-rest | 1 year |
| Application Logs | Low | Default | 90 days |
| Analytics Data | Medium | KMS at-rest | 3 years |

### 14.2 Data Backup Strategy

| Data Store | Backup Method | Frequency | Retention |
|------------|---------------|:---------:|:---------:|
| RDS PostgreSQL | Automated snapshots | Daily | 30 days |
| RDS PostgreSQL | Point-in-time recovery | Continuous | 7 days |
| S3 Documents | Versioning + cross-region replication | Real-time | Indefinite |
| OpenSearch | Automated snapshots | Daily | 14 days |
| Redis | No persistence needed | N/A | Session-based |

---

## 15. Multi-Tenancy Requirements

### 15.1 Tenant Isolation Strategy

| Aspect | Approach |
|--------|----------|
| **Database** | Shared database, tenant-aware schema (tenant_id on all tables) |
| **Row-Level Security** | PostgreSQL RLS policies for tenant isolation |
| **S3 Storage** | Tenant-prefixed paths (`s3://bucket/{tenant_id}/documents/`) |
| **AI Context** | Tenant-scoped OpenSearch index filtering |
| **Caching** | Tenant-prefixed Redis keys |
| **API Access** | Tenant validation in all API middleware |

### 15.2 Tenant-Level Features
- Independent tax configurations per tenant
- Custom expense categories per tenant
- Tenant-specific AI training context (future)
- Separate billing and usage tracking
- Admin dashboard for tenant management

---

## 16. Compliance & Regulatory Requirements

### 16.1 India-Specific Compliance

| Regulation | Applicability | Implementation |
|------------|:-------------:|----------------|
| **GST Act, 2017** | Tax calculations | GST rate engine, ITC rules |
| **Income Tax Act, 1961** | Tax estimation | Slab rates, deductions, regimes |
| **IT Act, 2000** | Data protection | Encryption, access controls |
| **DPDP Act, 2023** | Data privacy | Consent management, data deletion |
| **Companies Act (Books)** | Record keeping | 7-year data retention |

### 16.2 AWS Compliance Certifications Leveraged
- SOC 1/2/3
- ISO 27001
- PCI DSS (infrastructure level)
- MTCS (Multi-Tier Cloud Security)

---

## 17. Assumptions & Constraints

### 17.1 Assumptions
- Users upload financial documents regularly (weekly minimum)
- Internet connectivity available for all platform operations
- AWS services available and stable in Mumbai (ap-south-1) region
- Users have basic smartphone/computer literacy
- English is the primary interface language (Phase 1)
- Documents are primarily in English (Hindi OCR best-effort)
- Financial data relates to Indian business operations

### 17.2 Constraints
- Phase 1 budget constraint: ≤ $2000/month AWS spend
- Team size: 3-5 developers for initial development
- Timeline: 3-month MVP development cycle
- No direct government API access (GST portal) in Phase 1
- Bedrock model availability in ap-south-1 may require cross-region calls
- OpenSearch costs may require optimization for small tenants

---

## 18. Risks & Mitigations

| # | Risk | Probability | Impact | Mitigation |
|---|------|:-----------:|:------:|------------|
| R1 | OCR accuracy below target on poor quality images | Medium | High | Image pre-processing pipeline, user re-upload prompt |
| R2 | LLM hallucination of financial figures | High | Critical | RAG grounding, strict prompt engineering, guardrails |
| R3 | AWS cost overrun | Medium | Medium | Cost alerts, reserved instances, serverless where possible |
| R4 | Data breach / security incident | Low | Critical | Encryption, VPC, WAF, CloudTrail, incident response plan |
| R5 | Textract not supporting all Indian invoice formats | Medium | Medium | Fallback to generic OCR + LLM parsing |
| R6 | Tax rule changes (GST/Income Tax) | High | Medium | Rule engine with configurable tax tables |
| R7 | User adoption / onboarding friction | Medium | High | Intuitive UI, guided onboarding, demo mode |
| R8 | Multi-tenant data leakage | Low | Critical | RLS, tenant middleware, security testing |

---

## 19. Future Enhancements (Phase 2 & 3)

### Phase 2 (3-6 months post-MVP)
- Bank statement auto-ingestion (CSV/PDF parsing)
- GST return filing draft generation
- Mobile native app (React Native)
- Hindi language AI assistant
- CA collaboration portal (invite CA, share access)
- WhatsApp bot integration for document uploads

### Phase 3 (6-12 months post-MVP)
- AI predictive financial forecasting
- Open Banking API integration
- Multi-country tax system support
- Advanced analytics with ML-based pattern detection
- Automated compliance reporting
- SageMaker fine-tuned models for Indian invoice OCR
- Kafka (MSK) for large-scale event streaming

---

## 20. Success Metrics (KPIs)

### 20.1 Technical KPIs

| Metric | Target | Measurement Frequency |
|--------|--------|:---------------------:|
| OCR Extraction Accuracy | > 90% | Weekly |
| AI Response Latency (P95) | < 3 seconds | Real-time |
| Dashboard Load Time | < 2 seconds | Real-time |
| System Uptime | > 99.9% | Monthly |
| Tax Calculation Accuracy | > 95% | Weekly |
| Document Processing Success Rate | > 95% | Daily |
| API Error Rate | < 1% | Real-time |

### 20.2 Business KPIs

| Metric | Target (6 months) | Measurement |
|--------|:------------------:|-------------|
| Monthly Active Users (MAU) | 1,000+ | Monthly |
| Documents Processed/Month | 50,000+ | Monthly |
| AI Queries/Month | 25,000+ | Monthly |
| User Retention (30-day) | > 60% | Monthly |
| Manual Bookkeeping Reduction | > 70% | Quarterly survey |
| Average Session Duration | > 8 minutes | Real-time |
| NPS (Net Promoter Score) | > 40 | Quarterly |

---

## 21. Glossary

| Term | Definition |
|------|-----------|
| **CGST** | Central Goods and Services Tax |
| **SGST** | State Goods and Services Tax |
| **IGST** | Integrated Goods and Services Tax |
| **ITC** | Input Tax Credit |
| **GSTIN** | GST Identification Number |
| **HSN** | Harmonized System of Nomenclature (product codes) |
| **SAC** | Service Accounting Code |
| **PAN** | Permanent Account Number |
| **RAG** | Retrieval-Augmented Generation |
| **LLM** | Large Language Model |
| **OCR** | Optical Character Recognition |
| **RBAC** | Role-Based Access Control |
| **VPC** | Virtual Private Cloud |
| **ALB** | Application Load Balancer |
| **CDN** | Content Delivery Network |
| **MSME** | Micro, Small & Medium Enterprise |
| **D2C** | Direct to Consumer |
| **KMS** | Key Management Service |
| **RLS** | Row-Level Security |
| **ECS** | Elastic Container Service |
| **ECR** | Elastic Container Registry |
| **SQS** | Simple Queue Service |
| **DLQ** | Dead Letter Queue |
| **P&L** | Profit and Loss |
| **RTO** | Recovery Time Objective |
| **RPO** | Recovery Point Objective |
| **TTI** | Time to Interactive |
| **SLA** | Service Level Agreement |
| **MFA** | Multi-Factor Authentication |
| **PWA** | Progressive Web App |
