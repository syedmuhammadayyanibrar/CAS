# Contract Agentic Society (CAS) - REST API Documentation

## 1. Overview
CAS provides an asynchronous FastAPI application exposing endpoints for full mesh orchestration, standalone execution of each of the 6 societies, human-in-the-loop approvals, inbound Fastn webhook triggers, and contract audit events.

- **Base URL:** `http://localhost:8000`
- **Interactive OpenAPI Documentation:** `http://localhost:8000/docs`
- **ReDoc Documentation:** `http://localhost:8000/redoc`

---

## 2. Health & System Status

### `GET /`
Returns the operational health, active autonomous societies, and Fastn integration status.

**Response (200 OK):**
```json
{
  "system": "Contract Agentic Society (CAS)",
  "version": "1.0.0",
  "status": "OPERATIONAL",
  "llm_provider": "Google Gemini API (gemini-2.5-flash)",
  "database": "PostgreSQL via SQLAlchemy + asyncpg",
  "nervous_system": "Fastn MCP (Org: personal_867cccac2ec39658a401)",
  "active_societies": [
    "Contract Intelligence (Parallel + Verification)",
    "Risk Intelligence (Adversarial Debate)",
    "Negotiation Intelligence (Planner + Simulator + Critic)",
    "Compliance Intelligence (Retrieval + Rules + Verification)",
    "Obligation Intelligence (Event-Driven Monitoring)",
    "Dispute Intelligence (Multi-Perspective Simulation)"
  ]
}
```

---

## 3. Dynamic Contract Mesh Director

### `POST /mesh/analyze`
Executes full dynamic orchestration across all societies, applying bidirectional feedback loops and cross-society conflict arbitration.

**Request Body:**
```json
{
  "contract_text": "THIS MASTER SERVICES AGREEMENT...",
  "contract_id": "CTR-2026-001",
  "commercial_objective": "Cap aggregate liability at 12 months fees, delete uncapped indemnity, and ensure mutual 30-day termination.",
  "policy_path": "policies/corporate_compliance_policy.json"
}
```

**curl Example:**
```bash
curl -X POST http://localhost:8000/mesh/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "contract_text": "Section 8.2: Customer aggregate liability shall be uncapped. Vendor aggregate liability capped at 1 month.",
    "contract_id": "CTR-TEST-001",
    "commercial_objective": "Mutual 12-month cap"
  }'
```

**Response (200 OK):**
```json
{
  "contract_id": "CTR-TEST-001",
  "title": "Master Services Agreement",
  "director_routing": {
    "activated_societies": [
      "contract_intelligence",
      "risk_intelligence",
      "compliance_intelligence",
      "negotiation_intelligence",
      "dispute_intelligence"
    ],
    "activation_rationale": {
      "contract_intelligence": "Mandatory foundational parsing",
      "risk_intelligence": "Mandatory risk evaluation",
      "negotiation_intelligence": "Targeted commercial objectives present"
    }
  },
  "contract_graph": { "clauses": [], "parties": [], "obligations": [] },
  "risk_report": { "overall_risk_score": 0.63, "requires_human_escalation": true, "findings": [] },
  "compliance_report": { "overall_status": "NON_COMPLIANT", "violations_count": 1, "findings": [] },
  "negotiation_strategy": { "positions": [], "negotiation_sequence": [] },
  "dispute_assessment": { "overall_dispute_risk": "MEDIUM", "scenarios": [] },
  "detected_conflicts": [
    {
      "clause_reference": "Section 8.2",
      "conflict_description": "Risk Intelligence demands immediate strike of Section 8.2 while Negotiation Intelligence uses it for concession leverage.",
      "resolution_rationale": "Hold firm on mutual 12-month cap; offer multi-year commitment as leverage.",
      "requires_human_escalation": false
    }
  ],
  "human_in_the_loop": null,
  "status": "ANALYZED"
}
```

---

## 4. Standalone Society Endpoints

### 4.1 Contract Intelligence
`POST /systems/contract-intelligence/analyze`
- Parses raw contract into a normalized Contract Knowledge Graph with verified clause citations.
- **Request:** `{"contract_text": "...", "contract_id": "CTR-001"}`
- **Response:** Returns `ContractGraph` with clauses, parties, obligations, deadlines, and critic verification scores.

### 4.2 Risk Intelligence (Adversarial Debate)
`POST /systems/risk-intelligence/analyze`
- Executes Hunter vs. Counterargument vs. Assessor debate.
- **Request:** `{"contract": "...", "contract_id": "CTR-001"}`
- **Response:** Returns `RiskReport` with debated findings, counterarguments, and net severity scores.

### 4.3 Negotiation Intelligence
`POST /systems/negotiation-intelligence/plan`
- Plans redlines, counterparty simulation, and concession packages.
- **Request:** `{"contract": "...", "objective": "Cap liability at 12 months", "contract_id": "CTR-001"}`
- **Response:** Returns `NegotiationStrategy` with draft redlines, simulated counterparty reactions, and game-theoretic rationales.

### 4.4 Compliance Intelligence
`POST /systems/compliance-intelligence/audit`
- Evaluates contract against corporate policy rules with contextual Gemini reasoning.
- **Request:** `{"contract": "...", "policy_path": "policies/corporate_compliance_policy.json", "contract_id": "CTR-001"}`
- **Response:** Returns `ComplianceReport` with rule matches, evidence citations, and recommended actions.

### 4.5 Obligation Intelligence
`POST /systems/obligation-intelligence/register`
- Schedules post-signature commitments, dependencies, and monitoring triggers.
- **Request:** `{"contract": "...", "effective_date": "2026-10-01", "contract_id": "CTR-001"}`
- **Response:** Returns `ObligationSchedule` with calendar milestones, notice windows, and SLA obligations.

### 4.6 Dispute Intelligence
`POST /systems/dispute-intelligence/analyze`
- Simulates opposing party interpretations and models high-stakes conflict scenarios.
- **Request:** `{"contract": "...", "party_a_name": "Customer", "party_b_name": "Vendor", "contract_id": "CTR-001"}`
- **Response:** Returns `DisputeAssessment` with crisis narratives, likelihood ratings, and preventative drafting redlines.

---

## 5. Human-In-The-Loop (HITL) Reviews

### `GET /mesh/reviews/pending`
Lists all active review requests requiring human legal approval.

### `POST /mesh/reviews/{review_id}/decision`
Submits human counsel decision (`APPROVE`, `REJECT`, `OVERRIDE_REDLINE`).

**Request Body:**
```json
{
  "review_id": "REV-2026-001",
  "decision": "APPROVE",
  "reviewer_id": "general_counsel@enterprise.com",
  "decision_notes": "Approved redline strategy. Mandate mutual 12-month liability cap."
}
```

---

## 6. Fastn Webhook Integration

### `POST /webhooks/fastn/intake`
Inbound webhook endpoint receiving contracts from Fastn `cas-contract-intake` (`wf_0c61baf31b93`).

**Request Body:**
```json
{
  "contractId": "CTR-EXT-001",
  "documentName": "enterprise_saas_vendor_contract.pdf",
  "source": "google_drive",
  "content": "Raw contract text..."
}
```

---

## 7. Audit Trail & CAS Messages

### `GET /audit/events/{contract_id}`
Returns the immutable, chronological audit trail of all `CASMessage` events emitted for a given contract.
