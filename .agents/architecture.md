# Provenance: Procurement Agent Architecture

**Version:** 2.0 | **Date:** 2026-10-12 | **Status:** Implementation-ready

---

## 1. Executive Summary

Provenance today monitors external risk signals, resolves them against a supplier graph, scores impact, and delivers alerts. The transformation adds a transactional procurement backbone: RFQ/RFP lifecycle, PO management, invoice processing, goods receipt, spend analytics, and risk analytics. Most workflows are driven through the Agent Trace conversational interface.

### Scope of change

- 7 new backend modules (procurement, rfx, invoices, items, approvals, analytics, scorecards)
- 7 new frontend pages in the sidebar
- 12 new database tables, extensions to 3 existing tables
- 10 new agent tools for the conversational interface
- 3 new Celery task modules

### What stays the same

- Risk pipeline, entity resolution, alert system: untouched
- Deterministic-first principle preserved: procurement workflows are deterministic; LLM assists with parsing, classification, and conversation
- Multi-tenancy, RLS, auth: extended, not rewritten
- Agent Trace remains the primary interaction surface

---

## 2. Current State Analysis

### 2.1 Existing strengths

| Component | State | Procurement relevance |
|---|---|---|
| Multi-tenant core | Orgs, Clerk auth, RLS | POs and invoices need tenant isolation. Foundation is correct |
| Company registry | Global `companies` with GLEIF enrichment | Suppliers in procurement = companies in graph. No duplication |
| Supplier relationships | `supplier_relationships` with tier, criticality, spend | Direct reuse as vendor master |
| Spend module | `uploaded_documents`, `contracts`, `purchase_orders`, `spend_records`, `spend_leakage_findings` | Core tables exist but serve only document-parsing and leakage. Need extension |
| Risk module | Deterministic scoring, `risk_assessments` | Overlay risk scores on purchase decisions via `regulatory_overlap` |
| Agent Trace | Conversational interface with trace steps, citations, streaming | Primary surface for procurement actions. Needs new tools |
| AI provider | Vendor-neutral (Gemini, Claude, OpenAI, Mock), structured output | Same layer parses invoices and POs |
| Ingestion pipeline | 12 connectors, dedup, circuit breaker | Pattern reusable for procurement documents |
| Celery workers | Queues (ingest, ai, notify), Beat scheduler | Add `procurement` queue |

### 2.2 Gap analysis

#### Missing modules

| Module | Gap |
|---|---|
| Material Request | No request-to-buy workflow, no entry point for P2P flow |
| RFx (RFQ/RFP/RFI) | No sourcing event lifecycle |
| PO Management | Table exists but no lifecycle states, no approval routing, no line-item CRUD |
| Invoice Processing | No 3-way/2-way matching, no exception handling, no payment tracking |
| Goods Receipt | No GRN table or workflow |
| Items / Material Master | No item catalog; line items are free-text |
| Approval Workflow Engine | No generic approval routing or delegation-of-authority rules |
| Spend Analytics | No aggregation APIs, no category breakdowns, no trends |
| Supplier Scorecards | No operational KPIs (on-time delivery, quality) |
| Contract Lifecycle | No renewal alerting, no obligation tracking, no amendment history |

#### Missing frontend

| Page | Status |
|---|---|
| Material Requests | Does not exist |
| RFx Management | Does not exist |
| Purchase Orders | Does not exist |
| Invoices | Does not exist |
| Purchase Receipts (GRN) | Does not exist |
| Items Catalog | Does not exist |
| Reports / Analytics | Does not exist |

#### Missing sidebar items

Current: Trace, Dashboard, Onboarding, Alerts, Suppliers, Graph, Settings

Needed (matching screenshot reference):

```
Trace (Agent)           existing
Dashboard               existing, extend with procurement KPIs
Suppliers               existing, add performance tab
Material Request        NEW
Request for Quotation   NEW
Supplier Quotation      NEW
Purchase Order          NEW
Purchase Receipt        NEW
Purchase Invoice        NEW
Reports                 NEW (expandable)
Items                   NEW
Settings                existing, extend
```

---

## 3. Database Schema

All new tables follow conventions: UUID PK with `gen_random_uuid()`, AuditMixin, SoftDeleteMixin, org_id FK with RLS.

### 3.1 New tables

**items** - Item/material master catalog

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | gen_random_uuid() |
| org_id | UUID FK organizations | RLS |
| item_code | TEXT | UNIQUE per org |
| name | TEXT | |
| description | TEXT | |
| category | TEXT | UNSPSC or custom taxonomy |
| unit_of_measure | VARCHAR(20) | |
| default_unit_price | NUMERIC(18,2) | |
| currency | VARCHAR(3) | |
| preferred_supplier_id | UUID FK companies | nullable |
| lead_time_days | INT | |
| min_order_qty | NUMERIC | |
| is_active | BOOLEAN | |
| metadata | JSONB | |

**material_requests** - Purchase requisitions

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| org_id | UUID FK | RLS |
| mr_number | TEXT | UNIQUE per org, sequential |
| title | TEXT | |
| status | VARCHAR(20) | draft, pending_approval, approved, ordered, partially_ordered, cancelled |
| requested_by | VARCHAR | Clerk user_id |
| required_by_date | DATE | |
| priority | VARCHAR(10) | low, medium, high, critical |
| department | TEXT | |
| justification | TEXT | |
| total_estimated_amount | NUMERIC(18,2) | |
| currency | VARCHAR(3) | |

**material_request_items** - Line items for MRs

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| material_request_id | UUID FK | |
| item_id | UUID FK items | nullable (free-text allowed) |
| description | TEXT | |
| quantity | NUMERIC(18,4) | |
| unit_of_measure | VARCHAR(20) | |
| estimated_unit_price | NUMERIC(18,2) | |
| currency | VARCHAR(3) | |
| preferred_supplier_id | UUID FK companies | nullable |

**rfx_events** - Sourcing events (RFQ/RFP/RFI)

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| org_id | UUID FK | RLS |
| rfx_number | TEXT | UNIQUE per org |
| rfx_type | VARCHAR(10) | rfi, rfq, rfp, rft |
| title | TEXT | |
| description | TEXT | |
| status | VARCHAR(20) | draft, published, q_and_a, evaluation, negotiation, awarded, cancelled, closed |
| material_request_id | UUID FK | nullable |
| category | TEXT | |
| evaluation_criteria | JSONB | [{criterion, weight, description}] |
| published_at | TIMESTAMPTZ | |
| submission_deadline | TIMESTAMPTZ | |
| awarded_at | TIMESTAMPTZ | |
| awarded_supplier_id | UUID FK companies | nullable |
| created_by | VARCHAR | |

**rfx_invitations** - Supplier invitations to RFx

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| rfx_event_id | UUID FK | |
| supplier_id | UUID FK companies | |
| status | VARCHAR(20) | invited, viewed, responded, declined, shortlisted, awarded, rejected |
| invited_at | TIMESTAMPTZ | |
| responded_at | TIMESTAMPTZ | |

**rfx_responses** - Supplier quotations/proposals

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| rfx_event_id | UUID FK | |
| supplier_id | UUID FK companies | |
| response_number | TEXT | |
| total_amount | NUMERIC(18,2) | |
| currency | VARCHAR(3) | |
| line_items | JSONB | [{item, qty, unit_price, lead_time}] |
| evaluation_scores | JSONB | [{criterion, score, notes}] |
| validity_date | DATE | |
| payment_terms | TEXT | |
| delivery_terms | TEXT | Incoterms |
| attachments | JSONB | S3 keys |
| submitted_at | TIMESTAMPTZ | |
| is_best_offer | BOOLEAN | |
| source_document_id | UUID FK uploaded_documents | nullable |

**goods_receipts** - Goods receipt notes

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| org_id | UUID FK | RLS |
| grn_number | TEXT | UNIQUE per org |
| purchase_order_id | UUID FK | |
| received_date | DATE | |
| received_by | VARCHAR | |
| status | VARCHAR(20) | draft, confirmed, partial |
| line_items | JSONB | [{po_line_index, qty_received, qty_rejected, inspection_notes}] |
| delivery_note_ref | TEXT | |

**approval_workflows** - Generic approval tracking

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| org_id | UUID FK | RLS |
| document_type | VARCHAR(30) | material_request, purchase_order, invoice, rfx |
| document_id | UUID | polymorphic reference |
| current_step | INT | |
| status | VARCHAR(20) | pending, approved, rejected |
| initiated_by | VARCHAR | |
| initiated_at | TIMESTAMPTZ | |
| completed_at | TIMESTAMPTZ | |

**approval_steps** - Individual approval decisions

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| workflow_id | UUID FK | |
| step_number | INT | |
| approver_id | VARCHAR | Clerk user_id |
| approver_role | VARCHAR(50) | |
| status | VARCHAR(20) | pending, approved, rejected |
| decision_at | TIMESTAMPTZ | |
| comments | TEXT | |
| delegated_to | VARCHAR | nullable |

**approval_rules** - Delegation of authority

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| org_id | UUID FK | RLS |
| document_type | VARCHAR(30) | |
| min_amount | NUMERIC(18,2) | |
| max_amount | NUMERIC(18,2) | |
| currency | VARCHAR(3) | |
| required_role | VARCHAR(50) | |
| auto_approve_below | NUMERIC(18,2) | nullable |
| is_active | BOOLEAN | |
| priority | INT | evaluation order |

**supplier_scorecards** - Supplier performance KPIs

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| org_id | UUID FK | RLS |
| company_id | UUID FK companies | |
| period_start | DATE | |
| period_end | DATE | |
| on_time_delivery_pct | NUMERIC(5,2) | |
| quality_acceptance_pct | NUMERIC(5,2) | |
| responsiveness_score | NUMERIC(3,2) | 0 to 1 |
| price_competitiveness | NUMERIC(3,2) | |
| overall_score | NUMERIC(5,2) | |
| total_orders | INT | |
| total_spend_usd | NUMERIC(18,2) | |
| active_risk_score | NUMERIC(5,2) | from risk_assessments |
| computed_at | TIMESTAMPTZ | |

### 3.2 Extensions to existing tables

**purchase_orders** - add lifecycle:
- status (draft/pending_approval/approved/sent/acknowledged/partially_received/received/closed/cancelled)
- approved_by, approved_at, sent_at, acknowledged_at
- expected_delivery_date, delivery_address (JSONB)
- payment_terms, delivery_terms, notes
- material_request_id FK, rfx_event_id FK

**contracts** - add lifecycle:
- status (draft/active/expired/terminated/renewed)
- title, contract_type (msa/sow/blanket_po/framework)
- total_value, currency, auto_renew, renewal_notice_days
- obligations (JSONB), amendment_history (JSONB)
- last_review_date, next_review_date

**spend_records** - add matching:
- invoice_date, due_date
- payment_status (unpaid/partially_paid/paid/overdue/disputed)
- match_status (unmatched/matched_2way/matched_3way/exception)
- match_exceptions (JSONB), goods_receipt_id FK
- approved_by, approved_at, paid_at

---

## 4. Backend Modules

Each follows existing pattern: models.py, schemas.py, repository.py, service.py, router in api/v1/.

```
backend/app/modules/
  procurement/        NEW - Material Requests + number generation
  rfx/                NEW - RFQ/RFP/RFI lifecycle + bid comparison engine
  invoices/           NEW - Invoice processing + 2-way/3-way match engine
  items/              NEW - Item/Material master
  approvals/          NEW - Generic approval workflow + DoA rules engine
  analytics/          NEW - Spend cube, savings tracking, risk-weighted views
  scorecards/         NEW - Supplier performance scorecards

  spend/              EXISTING - extended
  risk/               EXISTING - unchanged
  companies/          EXISTING - unchanged
  graph/              EXISTING - unchanged
  events/             EXISTING - unchanged
  alerts/             EXISTING - unchanged
  ai/                 EXISTING - extended with procurement tools
  organizations/      EXISTING - unchanged
  admin/              EXISTING - extended
  notifications/      EXISTING - extended
```

### New API routes

```
api/v1/material_requests.py   CRUD + submit + approve/reject
api/v1/rfx.py                 CRUD + publish + invite + evaluate + award
api/v1/supplier_quotations.py Submit/view RFx responses
api/v1/purchase_orders_v2.py  Extended PO CRUD with lifecycle
api/v1/goods_receipts.py      Create GRN against PO
api/v1/invoices_v2.py         Invoice processing + match status
api/v1/items.py               Item master CRUD
api/v1/approvals.py           Approval queue + approve/reject
api/v1/analytics.py           Spend analytics, savings, risk analytics
api/v1/scorecards.py          Supplier scorecard endpoints
api/v1/reports.py             Report generation (CSV/PDF export)
```

### New Celery tasks

```
workers/tasks/procurement.py
  process_approval()        Route document through approval chain
  compute_scorecard()       Compute supplier scorecard for period
  check_contract_renewals() Alert on approaching renewals
  auto_match_invoices()     Run 3-way match on new invoices
  generate_analytics()      Precompute spend analytics caches
```

---

## 5. Agent Trace: Procurement Tools

### 5.1 New action types

```typescript
// Add to existing TraceRecord.action_type
| "create_material_request"
| "create_rfq"
| "compare_quotations"
| "create_purchase_order"
| "record_receipt"
| "process_invoice"
| "match_invoice"
| "approve_document"
| "analyze_spend"
| "check_contract"
| "supplier_scorecard"
| "generate_report"
```

### 5.2 Conversational workflow: Create Material Request

```
User: "I need 500 units of stainless steel sheet 304, 2mm thickness,
       required by next month for the Chennai plant"

Agent steps:
  1. [search_items] Search catalog for "stainless steel sheet 304 2mm"
  2. [resolve_supplier] Find preferred supplier(s)
  3. [check_risk] Check risk status of preferred supplier(s)
  4. [create_mr] Create Material Request MR-2026-0042
  5. [route_approval] Route to approver based on estimated amount

Response:
  Created MR-2026-0042:
  - 500 units x SS Sheet 304 (2mm) @ 4,200/unit
  - Estimated total: 21,00,000
  - Preferred supplier: Jindal Stainless Ltd.
  - Warning: Jindal has MEDIUM risk alert (EU tariff review)
  - Routed for approval to Category Manager per DoA rules
```

### 5.3 Conversational workflow: Create RFQ

```
User: "Create an RFQ for that material request,
       invite our top 3 steel suppliers"

Agent steps:
  1. [lookup_mr] Fetch MR-2026-0042 details
  2. [find_suppliers] Query by category ranked by scorecard + risk
  3. [create_rfx] Create RFQ RFQ-2026-0018
  4. [invite_suppliers] Send invitations
  5. [set_deadline] Set submission deadline (14 days)

Response:
  Created RFQ-2026-0018:
  - Items: 500 x SS Sheet 304, 2mm
  - Invited: Jindal (87/100), POSCO India (82/100), Acerinox (78/100)
  - Deadline: 2026-10-26
  - Criteria: Price 40%, Quality 25%, Delivery 20%, Risk 15%
```

### 5.4 Conversational workflow: Spend analysis

```
User: "Show me our spend breakdown for Q3 2026"

Agent steps:
  1. [query_spend] Aggregate spend_records for Jul-Sep 2026
  2. [compute_analytics] Category breakdown, supplier concentration
  3. [check_leakage] Cross-reference with leakage findings

Response:
  Q3 2026: Total 4.2Cr across 47 suppliers
  Top: Raw Materials 50%, Packaging 19%, MRO 12%, IT 10%
  Flags: 3 maverick findings (12.4L), 2 duplicate suspects (3.2L),
         62% raw material spend single-sourced
```

### 5.5 Tool definitions

10 new tools registered in the AI investigation service:

1. **create_material_request** - title, items[], required_by, priority, justification
2. **create_rfx** - rfx_type, title, material_request_id, supplier_ids[], criteria[], deadline_days
3. **compare_quotations** - rfx_event_id
4. **create_purchase_order** - supplier_id, line_items[], rfx_response_id, payment/delivery terms
5. **record_goods_receipt** - purchase_order_id, items_received[]
6. **match_invoice** - invoice_id
7. **analyze_spend** - period_start, period_end, group_by, filters
8. **supplier_scorecard** - supplier_id, period
9. **check_contract_status** - contract_id or supplier_id
10. **approve_document** - document_type, document_id, action, comments

---

## 6. Frontend Architecture

### 6.1 New pages

```
(dashboard)/
  material-requests/           List + create/edit
    [id]/                      Detail with line items + approval
  rfx/                         RFx list
    create/                    Multi-step creation wizard
    [id]/                      Detail with responses
      compare/                 Side-by-side bid comparison
  quotations/                  Supplier quotation list
  purchase-orders/             PO list with lifecycle filters
    [id]/                      Detail with line items, GRNs, invoices
  receipts/                    Goods receipt list + create
  invoices/                    Invoice list with match status
    [id]/                      Detail with 3-way match view
  items/                       Item catalog
  reports/                     Reports hub
    spend/                     Spend analytics dashboard
    savings/                   Savings tracker
    risk/                      Risk analytics overlay
```

### 6.2 New components

```
components/
  procurement/
    material-request-form.tsx
    material-request-list.tsx
    rfx-creation-wizard.tsx
    rfx-list.tsx
    bid-comparison-table.tsx
    purchase-order-form.tsx
    purchase-order-list.tsx
    purchase-order-detail.tsx
    goods-receipt-form.tsx
    invoice-list.tsx
    invoice-match-view.tsx       Visual 3-way match
    item-catalog.tsx
    approval-queue.tsx
    approval-action-bar.tsx
    document-status-badge.tsx

  analytics/
    spend-breakdown-chart.tsx
    spend-trend-chart.tsx
    supplier-concentration.tsx
    savings-waterfall.tsx
    category-treemap.tsx
    risk-spend-overlay.tsx

  scorecards/
    supplier-scorecard.tsx
    performance-radar.tsx
```

### 6.3 Sidebar update

```typescript
const navItems: NavItem[] = [
  { title: "Trace",             href: "/trace",             icon: Sparkles,       badge: "Agent", badgeVariant: "ai" },
  { title: "Dashboard",         href: "/dashboard",         icon: Gauge },
  { title: "Material Request",  href: "/material-requests", icon: ClipboardList },
  { title: "RFQ / RFP",        href: "/rfx",               icon: FileQuestion },
  { title: "Quotations",       href: "/quotations",         icon: FileText },
  { title: "Purchase Order",   href: "/purchase-orders",    icon: ShoppingCart },
  { title: "Purchase Receipt", href: "/receipts",           icon: PackageCheck },
  { title: "Purchase Invoice", href: "/invoices",           icon: Receipt },
  { title: "Suppliers",         href: "/suppliers",          icon: Building2 },
  { title: "Alerts",            href: "/alerts",             icon: AlertTriangle },
  { title: "Graph",             href: "/graph",              icon: Network },
  { title: "Reports",           href: "/reports",            icon: BarChart3 },
  { title: "Items",             href: "/items",              icon: Package },
  { title: "Settings",          href: "/settings",           icon: Settings },
];
```

---

## 7. Deterministic vs. AI Split

| Task | Impl | Why |
|---|---|---|
| PO/MR number generation | Deterministic | Must be unique, predictable, sequential |
| Approval routing | Deterministic | Amount thresholds + role-based routing are exact |
| 3-way matching (PO/GRN/Invoice) | Deterministic | Exact arithmetic comparison |
| Spend aggregation | Deterministic | SQL GROUP BY; exact numbers for finance |
| Scorecard computation | Deterministic | Weighted average of KPIs from PO/GRN/invoice data |
| Bid comparison scoring | Deterministic | Weighted criteria applied to normalized responses |
| Invoice exception classification | Deterministic | Rule-based: price variance, qty mismatch, missing PO |
| Leakage detection | Deterministic | Existing rules (maverick, duplicate, price variance) |
| Document parsing (PDF) | LLM | Layouts vary too much for templates |
| NL procurement commands | LLM | Understanding "I need 500 units of SS304" |
| Spend classification (UNSPSC) | LLM | Mapping messy descriptions to categories |
| RFx response summarization | LLM | Summarizing supplier proposals |
| Contract obligation extraction | LLM | Parsing legal text for dates and terms |

---

## 8. Data Flows

### 8.1 Procure-to-Pay

```
Material Request --> RFx Event --> Supplier Quotations
       |                |                |
       |         Evaluation & Award      |
       |                |                |
       v                v                v
Purchase Order --> Goods Receipt --> Invoice (3-way match) --> Payment
```

### 8.2 Approval flow

```
Document Created
  --> Evaluate DoA Rules
    --> Below auto-approve threshold? --> Approved
    --> Above threshold? --> Route to approver(s) by role+amount
      --> Approve --> Next step or Final Approved
      --> Reject --> Back to Requester
```

### 8.3 3-way invoice match

```
PO (500 x 4200) + GRN (495 received) + Invoice (495 x 4250)
  Qty: GRN=INV=495 (match), 5 short vs PO (note)
  Price: 4250 vs 4200 = +1.19% variance (within 2% tolerance)
  Result: MATCHED with notes
```

### 8.4 Risk-procurement integration

```
Risk Pipeline (events/scoring/alerts)
  |
  +--> RFx: risk badge on invited suppliers
  +--> PO: risk alerts for this supplier
  +--> Scorecard: include active risk score
  +--> Agent: automatically include risk context when discussing suppliers
```

---

## 9. Implementation Phases

### P1: Foundation (2-3 weeks)

Items, material requests, approval engine.

- Alembic migrations: items, material_requests, material_request_items, approval tables
- Backend: items, procurement, approvals modules
- API routes: /v1/items, /v1/material-requests, /v1/approvals
- Frontend: Items catalog, MR list + form, approval queue
- Agent tools: create_material_request, approve_document

### P2: Sourcing (2-3 weeks)

RFQ/RFP, quotations, bid comparison.

- Migrations: rfx_events, rfx_invitations, rfx_responses
- Backend: rfx module with lifecycle + comparison engine
- API routes: /v1/rfx, /v1/supplier-quotations
- Frontend: RFx list + wizard, bid comparison table, quotation list
- Agent tools: create_rfx, compare_quotations

### P3: Order-to-Receipt (2-3 weeks)

PO lifecycle, goods receipt.

- Extend purchase_orders table
- Migrations: goods_receipts
- Backend: PO lifecycle service, goods receipt module
- API routes: /v1/purchase-orders (extended), /v1/goods-receipts
- Frontend: PO list + detail, goods receipt form
- Agent tools: create_purchase_order, record_goods_receipt

### P4: Invoice and Matching (2-3 weeks)

Invoice processing, 3-way matching, exceptions.

- Extend spend_records table
- Backend: invoices module + deterministic matching engine
- Celery: auto_match_invoices
- API routes: /v1/invoices
- Frontend: Invoice list, invoice detail with visual 3-way match
- Agent tools: match_invoice, process_invoice

### P5: Analytics and Scorecards (2-3 weeks)

Spend analytics, scorecards, contract lifecycle.

- Extend contracts table
- Migrations: supplier_scorecards
- Backend: analytics module (spend cube, savings), scorecards module, contract lifecycle
- Celery: compute_scorecard, check_contract_renewals, generate_analytics
- Frontend: Spend dashboard, scorecard component, reports hub, dashboard KPIs
- Agent tools: analyze_spend, supplier_scorecard, check_contract_status

### P6: Polish and Integration (1-2 weeks)

Cross-module flows, notifications, refinement.

- End-to-end flow: MR to RFQ to Quotation to PO to GRN to Invoice to Payment
- Notification integration: approval requests, PO acknowledgments, contract renewals
- Risk overlay on all procurement screens
- Dashboard procurement summary cards
- Testing: unit, integration, E2E for all new modules

**Total estimated effort: 14-17 weeks**

---

## 10. Key Decisions

### Agent-first, not forms-only

Every procurement action expressible in natural language is executable through Agent Trace. CRUD forms exist as a parallel path for tabular review. The agent handles transactional work through conversation, freeing users for strategic work.

### No vendor portal in MVP

RFx is buyer-side only. Supplier responses are entered by the buyer or parsed from uploaded PDFs. A supplier portal (separate auth domain, separate UI) is Phase 2.

### Generic approval engine

One approval system handles material requests, POs, invoices, and RFx awards through the same tables. DoA rules are evaluated by amount threshold and role.

### Analytics are deterministic SQL, cached by Celery

Spend analytics never use LLM. Aggregate SQL queries cached in Redis. Beat task precomputes hourly. Agent reads caches and presents conversationally.

### Configurable match tolerances

3-way match uses per-org configurable tolerances:
- Price: default +/-2%
- Quantity: default +/-5%
- Amount: default +/-500

Within tolerance = auto-approved. Outside = exception for human review.

---

## 11. Files to Modify

| File | Change |
|---|---|
| frontend/src/components/shell/sidebar.tsx | Add 7 new nav items |
| backend/app/main.py | Register new routers |
| backend/app/modules/spend/models.py | Extend PO, contract, spend_record columns |
| frontend/src/components/investigate/agent-trace-workspace.tsx | Add new action types, render procurement outputs |
| backend/app/modules/ai/investigation/service.py | Register procurement tools |
| workers/schedules.py | Add Beat schedules for contracts, scorecards, analytics |
| docker-compose.yml | Add procurement queue to worker command |

---

## 12. Success Metrics

| Metric | Target |
|---|---|
| End-to-end P2P completable | MR to match in under 10 interactions |
| Agent handles procurement commands | 90%+ of tool actions executable via chat |
| 3-way match accuracy | 95%+ auto-match on clean data |
| Spend analytics query time | Under 500ms per tenant |
| Approval routing correctness | 100% per DoA rules |
