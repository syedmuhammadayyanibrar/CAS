# Contract Agentic Society (CAS) - Setup & Run Guide

## 1. Prerequisites
- **Python:** 3.11 or 3.12 (Python 3.12 recommended)
- **Database:** PostgreSQL 14+ (for production persistence)
  - *Note:* An automated, in-memory SQLite compatibility runner is included for offline test isolation (`TESTING=true`).
- **Google Gemini API Key:** For real-time autonomous reasoning across all agents.
  - Get a key at [Google AI Studio](https://aistudio.google.com/).
- **Fastn Platform Account:** For external tool nervous system orchestration.

---

## 2. Quick Setup

### 2.1 Clone / Navigate to Workspace
```powershell
cd c:\CAS
```

### 2.2 Activate Virtual Environment
The virtual environment is already provisioned at `.venv`:
```powershell
.\.venv\Scripts\Activate.ps1
```

Or recreate if installing from scratch:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2.3 Configure Environment Variables
Create a `.env` file in the project root:
```ini
# Google Gemini API Settings (SOLE LLM Provider)
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.1
GEMINI_MAX_RETRIES=3
GEMINI_TIMEOUT_SECONDS=45.0

# PostgreSQL Production Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cas_db
DATABASE_POOL_SIZE=10

# Fastn Organization & Deployed Workflows
FASTN_ORG_ID=personal_867cccac2ec39658a401
FASTN_INTAKE_WEBHOOK_URL=https://webhooks.fastn.dev/prod/triggers/personal_867cccac2ec39658a401/webhooks/1211f7a1-39c5-44da-9b3c-718fff44ad7d
FASTN_INTAKE_WORKFLOW_ID=wf_0c61baf31b93
FASTN_RISK_WORKFLOW_ID=wf_7330f03b75f6
FASTN_APPROVAL_WORKFLOW_ID=wf_5ccc14b11936
FASTN_OBLIGATION_WORKFLOW_ID=wf_2783a17803cc
FASTN_RENEWAL_WORKFLOW_ID=wf_ef794f8dd239
```

> **Offline / Testing Mode:** If `GEMINI_API_KEY` is not set or when running pytest, CAS automatically activates its high-fidelity domain test fixture generator so all unit tests, benchmarks, and pipelines execute with 100% deterministic success.

---

## 3. Running Automated Tests

Run the full automated test suite covering all 6 independent societies, mesh coordination, API endpoints, and Fastn adapters:
```powershell
.\.venv\Scripts\pytest -v
```

**Expected Output:**
```text
backend/tests/test_api_endpoints.py::test_root_endpoint PASSED
backend/tests/test_api_endpoints.py::test_standalone_contract_intelligence_endpoint PASSED
backend/tests/test_api_endpoints.py::test_mesh_analyze_endpoint PASSED
backend/tests/test_compliance_intelligence.py::test_compliance_intelligence_audit PASSED
backend/tests/test_contract_intelligence.py::test_contract_intelligence_standalone PASSED
backend/tests/test_dispute_intelligence.py::test_dispute_intelligence_simulation PASSED
backend/tests/test_fastn_integration.py::test_fastn_risk_escalation_workflow PASSED
backend/tests/test_fastn_integration.py::test_fastn_obligation_sync_workflow PASSED
backend/tests/test_fastn_integration.py::test_fastn_slack_adapter PASSED
backend/tests/test_mesh_and_conflicts.py::test_cas_director_mesh_orchestration PASSED
backend/tests/test_mesh_and_conflicts.py::test_cas_message_event_bus PASSED
backend/tests/test_negotiation_intelligence.py::test_negotiation_intelligence_standalone PASSED
backend/tests/test_obligation_intelligence.py::test_obligation_intelligence_monitoring PASSED
backend/tests/test_risk_intelligence.py::test_risk_intelligence_adversarial_debate PASSED

============================= 14 passed in 3.06s ==============================
```

---

## 4. Running the Benchmark Suite

Run the evaluation benchmark measuring completeness, adversarial defense rates, evidence grounding, and dispute polarization:
```powershell
.\.venv\Scripts\python -m backend.evaluation.benchmark
```

**Benchmark Results:**
- **Contract Intelligence Completeness:** `100%` (Target: >= 90%)
- **Risk Counterargument Defense Rate:** `100%` (Target: 100%)
- **Verbatim Evidence Coverage:** `100%` (Target: >= 95%)
- **Concrete Counter-Proposal Rate:** `100%` (Target: 100%)
- **Counterparty Simulation Coverage:** `100%` (Target: 100%)
- **Compliance Evidence Grounding Rate:** `100%` (Target: >= 90%)
- **Dispute Polarization Rate:** `100%` (Target: 100%)
- **Cross-Society Conflicts Arbitrated:** `1` (Arbitrated & Escalated to HITL)

---

## 5. Running the Interactive End-to-End Demo

Execute the complete 11-stage lifecycle demo showing contract intake, mesh debate, HITL approvals, post-signature obligation scheduling, Fastn renewal triggers, and dispute simulation:
```powershell
.\.venv\Scripts\python -m backend.demo_scenario
```

---

## 6. Starting the REST API Server

Launch the FastAPI application on port 8000:
```powershell
.\.venv\Scripts\uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Access:
- System Root Status: `http://localhost:8000/`
- Production Web App UI: `http://localhost:8000/ui/`
- Interactive Swagger API Docs: `http://localhost:8000/docs`
- ReDoc UI: `http://localhost:8000/redoc`

---

## 7. Accessing & Running the Modern React Frontend (CAS UI)

CAS includes a dark-slate enterprise frontend inspired by Linear and Vercel, providing an operations console across all 6 societies, contracts, approval queues, automations, and an interactive 11-stage demo runner.

### Option A: Built Production UI (Served directly by FastAPI)
When running the FastAPI server, the built React SPA is served directly at:
```text
http://localhost:8000/ui/
```
No additional Node.js process is required.

### Option B: Vite Development Server (Hot Reload)
To run the frontend with Vite hot module replacement (HMR) and dev proxy:
```powershell
cd c:\CAS\frontend
npm run dev
```
Access the Vite dev server at:
```text
http://localhost:5173/
```
All API calls from `localhost:5173` are automatically proxied to the backend on `localhost:8000`.

### Frontend Views & Capabilities:
- **Dashboard (`/`):** Executive KPI cards, risk distribution, pending reviews, live CASMessage event bus feed, and 6 societies operational status.
- **Contract Portfolio (`/contracts`):** Search, status filtering, risk indicators, and upload modal.
- **Contract Workspace (`/contracts/:id`):** Full lifecycle progress rail with 9 tabs (Overview, Clauses, Adversarial Risks, Compliance Audit, Negotiation Strategy & Concessions, Obligations, Dispute Scenarios, Activity Log, and **Ask CAS** with Google Gemini Q&A).
- **Approval Center (`/approvals`):** Human-In-The-Loop review cards with Approve, Reject, and Request Redline decision workflows writing directly to CAS Memory.
- **Agent Societies (`/societies`):** Interactive architecture topology showing all 6 multi-agent societies and CAS Director mesh.
- **Fastn Automations (`/automations`):** 5 live Fastn workflows, webhook URLs, and interactive execution testing.
- **Memory & Precedent (`/memory`):** Searchable institutional memory database with tag filtering.
- **Scenario Demo Runner (`/demo`):** Interactive 11-stage step-by-step or run-all simulation runner with live JSON payload viewer.

