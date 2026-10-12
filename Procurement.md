Procurement is about much more than supply chain risk, and the rest of it is where most of a procurement person's day goes. Below is how the function works, who does what, how ERPs fit in, and the vocabulary. Treat the day-in-the-life details as typical rather than universal, since they vary a lot by company size and industry.

## How procurement works

Procurement is how an organization buys what it needs from outside suppliers, at the right price, quality, and time, with proper controls. The end-to-end flow is called **source-to-pay (S2P)**:

1. **Identify need.** Someone requests something (a factory needs steel, HR needs a recruiting tool).
2. **Source.** Find suppliers, compare them, negotiate, and pick one.
3. **Contract.** Lock in price, terms, and legal protections.
4. **Order.** Place purchase orders against the contract.
5. **Receive.** Confirm the goods or services actually arrived.
6. **Invoice and pay.** Match the invoice to the order and receipt, then pay.
7. **Manage the supplier.** Track performance, risk, and renewals.

The two halves have names. **Source-to-contract (S2C)** is the strategic half, steps 2 and 3. **Procure-to-pay (P2P)** is the transactional half, steps 4 to 6.

Two distinctions shape everything else:
- **Direct vs. indirect spend.** Direct goods go into the product you sell (raw materials, components). Indirect is everything else (software, marketing, travel, cleaning, consulting). Direct procurement is tied to production schedules and bills of materials. Indirect is usually higher-volume and lower-stakes per purchase.
- **Strategic vs. tactical work.** Strategic work is category strategy, big negotiations, and supplier selection, done by a few people on a long horizon. Tactical work is raising POs, expediting deliveries, and fixing invoice problems, done by many people daily.

## Roles and what they do day to day

| Role | Core job | Typical daily work |
|---|---|---|
| **Buyer / Procurement Specialist** | Executes purchases | Reviews purchase requisitions, creates POs, chases suppliers for confirmations and delivery dates, resolves delivery and price discrepancies, handles urgent requests |
| **Category Manager** | Owns a spend category (e.g., electronics, packaging, IT services) | Analyzes spend, sets category strategy, runs sourcing events, negotiates, manages the supplier base for that category |
| **Strategic Sourcing Manager** | Leads big sourcing projects | Builds RFx packages, evaluates bids, runs negotiations, drives savings targets |
| **Procurement Analyst** | Data and reporting | Spend analysis, savings tracking, dashboards, cleaning supplier and item data, classifying spend |
| **Supplier Relationship / Performance Manager** | Keeps suppliers performing | Scorecards, quarterly business reviews, corrective actions, development plans |
| **Contract Manager** | Owns the paper | Drafting and redlining with legal, tracking renewals and obligations, price-escalation clauses |
| **Procurement Ops / P2P** | Keeps the process running | Catalog maintenance, approval workflows, supplier onboarding, ERP master data |
| **Accounts Payable** (often finance, not procurement) | Pays correctly | Invoice matching, exceptions, payment runs, duplicate prevention |
| **CPO** | Runs the function | Savings targets, risk posture, stakeholder alignment, board-level reporting |

**A realistic buyer's day:**
- Morning: check the queue of new requisitions. Approve or push back on incomplete ones, and convert approved ones to POs.
- Chase three suppliers about late shipments. Update the production planner on revised delivery dates.
- Handle an invoice exception where the invoiced price is above the PO price. Work out who is right and fix the PO or dispute the invoice.
- Answer a stakeholder asking "can we buy this from someone cheaper?" Check whether a contract already covers it.
- Afternoon: get quotes from two or three suppliers for a one-off need and compare them.
- Update supplier records and respond to a new supplier's onboarding paperwork.

**A realistic category manager's week:**
- Review spend data for the category and spot consolidation or savings opportunities.
- Prepare for a negotiation, or run one.
- Check supplier performance data ahead of a quarterly review.
- Prepare an RFP or review incoming bids.
- Check upcoming contract renewals (the most overlooked task) and decide whether to renew, renegotiate, or re-source.
- Get asked what a news event means for supply: "Does this tariff affect us?" This is the piece your current project covers.

A large share of the day is **exception handling and chasing people**. The strategic work is smaller and more valuable, and often gets squeezed out by the transactional work. That squeeze is the main argument for automation.

## ERPs: what they are and how procurement uses them

An **ERP (Enterprise Resource Planning) system** is the company's central system of record. It handles finance and accounting, inventory, manufacturing, sales orders, HR, and procurement in one integrated database. The big names are **SAP (S/4HANA, ECC)**, **Oracle (Fusion, NetSuite)**, **Microsoft Dynamics 365**, and **Infor**. NetSuite and Dynamics are common in mid-size companies.

In procurement, the ERP handles:
- **Vendor master data**: the official supplier record (name, address, tax ID, bank details, payment terms).
- **Material/item master**: every part or item the company buys, with specs and units.
- **Purchase requisitions and POs**: the internal request, then the formal order.
- **Goods receipt**: warehouse staff confirm what arrived.
- **Invoice verification and payment**: matching and posting to the general ledger.
- **Inventory and MRP (material requirements planning)**: calculating what to buy and when, based on production plans, stock levels, and lead times. For direct materials, MRP often generates the purchase suggestions.

**Where S2P suites like JAGGAER fit:** ERPs are strong at transactions and accounting but weak at the strategic and collaborative parts: running sourcing events, managing supplier onboarding, contract lifecycle, supplier portals, and spend analytics. S2P platforms (JAGGAER, Coupa, SAP Ariba, Ivalua, GEP) sit **on top of or alongside** the ERP. They handle the front end (sourcing, contracts, requisitioning, supplier management), then exchange data with the ERP (POs, vendor records, invoices, payments). That integration is a large part of what enterprise procurement IT teams do.

## RFx: the sourcing documents

"RFx" is the family of formal requests used to collect supplier proposals.

| Term | Stands for | Purpose | When used |
|---|---|---|---|
| **RFI** | Request for Information | Learn what the market offers, with no commitment | Early exploration, when you don't yet know who can do this |
| **RFQ** | Request for Quotation | Get **prices** for a well-defined item or spec | You know exactly what you want and mainly need price, delivery, and terms. Common for commodities and standard parts |
| **RFP** | Request for Proposal | Get proposed **solutions** plus price | The need is complex (services, software, solutions), and approach and capability matter as much as price |
| **RFT / ITT** | Request/Invitation to Tender | Formal competitive bid, common in public sector | Regulated buying where process rules are strict |
| **Reverse auction** | | Suppliers bid prices downward in real time | Commodity-like items with many qualified suppliers |

**Typical sourcing event flow:**
1. Define requirements and the evaluation criteria and weights.
2. Shortlist and invite suppliers.
3. Run Q&A, with all questions and answers shared with all bidders for fairness.
4. Receive bids.
5. Evaluate. Typically this is a weighted scorecard covering price, quality, capability, risk, and sometimes ESG. Don't confuse price with **total cost of ownership (TCO)**, which includes shipping, duties, quality costs, and so on.
6. Negotiate, often with a shortlist. A **BAFO (best and final offer)** round is common.
7. Award, then move to the contract.

## Glossary: terms you'll hear constantly

| Term | Meaning |
|---|---|
| **PR (Purchase Requisition)** | Internal request to buy something, before it becomes an order |
| **PO (Purchase Order)** | Formal, legally meaningful order sent to the supplier |
| **Blanket / Contract PO** | One PO covering repeated purchases over time against agreed terms |
| **GR / GRN (Goods Receipt)** | Record that goods arrived |
| **3-way match** | Checking that the **PO**, **goods receipt**, and **invoice** agree before paying. 2-way skips the receipt |
| **Invoice exception** | A mismatch that blocks payment and needs a human to resolve |
| **MSA** | Master Services Agreement: the overarching contract terms |
| **SOW** | Statement of Work: what exactly will be delivered, when, and for how much |
| **SLA** | Service Level Agreement: measurable service commitments, with penalties |
| **KPI / Scorecard** | Supplier performance measures (on-time delivery, quality, responsiveness) |
| **QBR** | Quarterly Business Review with a key supplier |
| **TCO** | Total cost of ownership, beyond unit price |
| **Spend analysis / spend cube** | Categorizing and analyzing what the company buys, from whom, and how much |
| **Spend classification** | Mapping messy line items to a standard taxonomy (e.g., UNSPSC) |
| **Tail spend** | The long tail of small, scattered purchases, a small share of spend but a large share of suppliers |
| **Maverick / rogue spend** | Buying outside approved channels, suppliers, or contracts |
| **Contract leakage** | Paying more than contract terms allow, or buying off-contract despite a deal existing |
| **PPV (Purchase Price Variance)** | Gap between standard/expected price and what was actually paid |
| **Hard savings vs. cost avoidance** | Hard savings reduce actual spend compared to the prior price. Cost avoidance means preventing an increase. Finance treats them very differently |
| **Lead time** | Time from order to delivery |
| **MOQ** | Minimum order quantity |
| **Incoterms** | Standard shipping terms (EXW, FOB, DDP) defining who pays for freight, insurance, and risk |
| **Payment terms** | e.g., "Net 30" (pay in 30 days), "2/10 net 30" (2% discount if paid in 10 days) |
| **Sole source vs. single source vs. dual sourcing** | One legally only supplier / one chosen supplier / deliberately two suppliers for resilience |
| **Preferred supplier list** | Pre-approved suppliers staff are expected to use |
| **Catalog / punchout** | Pre-negotiated item lists employees can order from, or links into supplier web stores |
| **BOM (Bill of Materials)** | Every component and raw material in a product, key for direct procurement |
| **Kraljic matrix** | Framework sorting categories by supply risk and spend impact (strategic, leverage, bottleneck, routine) |
| **Delegation of authority** | Rules on who can approve what spend amount |
| **SRM** | Supplier Relationship Management |
| **EDI / cXML** | Standard formats for exchanging POs and invoices between systems |
| **ASN (Advance Ship Notice)** | Supplier's notice that a shipment is on its way |
| **CLM** | Contract Lifecycle Management |
| **Scope 3 / ESG** | Supplier-related emissions and sustainability and ethics compliance, increasingly a procurement responsibility |

## What this means for your project

The fuller view opens up real candidates, but I'd be doing you a disservice if I didn't flag the scope trap. "Cover most of what a procurement manager does" is the largest version of this idea. That's roughly what JAGGAER, Coupa, and Ivalua each spend hundreds of engineers on, and a prototype that touches 15 tasks shallowly will look weaker than one that does 2 or 3 convincingly.

The tasks where automation helps most are the ones that are **repetitive, rule-governed, and document-heavy**, and where the answer can be checked:
- **Invoice exception triage**: classify the mismatch (price, quantity, duplicate), find the PO and contract terms, and propose the resolution. This is checkable and high-volume.
- **Contract renewal and obligation monitoring**: extract dates, auto-renewal clauses, and price escalators, then alert before the deadline.
- **RFx bid comparison**: normalize supplier responses into a scorecard against stated criteria, with citations back to each response.
- **Spend classification and tail-spend analysis**: map messy line items to categories and flag consolidation opportunities.
- **Supplier risk monitoring**: what you have already designed.

Procurement work tends to be a **chain** of these (a renewal notice triggers a spend check, then a risk check, then a sourcing recommendation), so a small orchestrated set of them could share the entity graph you've already designed. That is a more natural way to "cover more" than adding unrelated features.

If you tell me which two or three tasks interest you most, I can walk through what real data for each looks like, what a realistic synthetic dataset needs, and how they'd connect to the graph design.