# Contract Agentic Society (CAS)
### *A Federation of Independent Multi-Agent Systems for Autonomous Contract Lifecycle Management*

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![LLM](https://img.shields.io/badge/Reasoning-Google%20Gemini%20API-4285F4.svg)](https://ai.google.dev/)
[![Fastn](https://img.shields.io/badge/Nervous%20System-Fastn%20MCP-FF6B6B.svg)](https://fastn.ai/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%2B%20asyncpg-336791.svg)](https://www.postgresql.org/)
[![Tests](https://img.shields.io/badge/Tests-14%2F14%20Passing-brightgreen.svg)]()

---

## 1. Vision & Architecture

The **Contract Agentic Society (CAS)** is a production-grade autonomous multi-agent federation built for enterprise legal and commercial contracts. Rather than a monolithic chatbot or a simple sequential prompt chain, CAS is engineered as **six independent, specialized multi-agent societies** that can each operate autonomously, but gain exponential capabilities when connected into the **Contract Negotiation Mesh** through the **Fastn MCP nervous system**.

```text
                               ┌───────────────────────────┐
                               │   CONTRACT MESH DIRECTOR  │
                               │  Dynamic Society Routing  │
                               │  Cross-Domain Arbitration │
                               └─────────────┬─────────────┘
                                             │
                   ┌─────────────────────────┼─────────────────────────┐
                   ▼                         ▼                         ▼
        ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
        │ SYSTEM 1: CONTRACT  │   │  SYSTEM 2: RISK     │   │ SYSTEM 3: NEGOTIATE │
        │ Parallel + Verified │   │  Adversarial Debate │   │ Planner + Simulator │
        └──────────┬──────────┘   └──────────┬──────────┘   └──────────┬──────────┘
                   │                         │                         │
                   ├─────────────────────────┼─────────────────────────┤
                   ▼                         ▼                         ▼
        ┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
        │ SYSTEM 4: COMPLY    │   │ SYSTEM 5: OBLIGATE  │   │ SYSTEM 6: DISPUTE   │
        │ Retrieval + Rules   │   │ Event-Driven Sched  │   │ Multi-Perspective   │
        └──────────┬──────────┘   └──────────┬──────────┘   └──────────┬──────────┘
                   │                         │                         │
                   └─────────────────────────┼─────────────────────────┘
                                             ▼
                               ┌───────────────────────────┐
                               │     FASTN MCP SERVER      │
                               │  Enterprise Nervous System│
                               └─────────────┬─────────────┘
                                             ▼
                         Slack • Google Calendar • Webhooks • Airtable
```

---

## 2. Core Architectural Highlights

1. **Sole Cognitive Engine: Google Gemini API**
   - **Google Gemini API** (`gemini-2.5-flash`) is the exclusive reasoning provider for all agent decisions, adversarial debates, counterparty simulations, and conflict arbitration.
   - Centralized via `backend/core/gemini_service.py` (`GeminiService`) with structured Pydantic schema generation, automatic validation repair, and exponential backoff.
   - Python code is strictly limited to deterministic orchestration, schema routing, arithmetic calculations, database persistence, and scheduling.

2. **External Nervous System: Fastn MCP Platform**
   - All interactions with external enterprise tools, SaaS integrations, and scheduled events flow through real, deployed **Fastn Workflows** (Org: `personal_867cccac2ec39658a401`):
     - `cas-contract-intake` (`wf_0c61baf31b93`): Inbound Webhook trigger from cloud drives / DocuSign.
     - `cas-risk-escalation` (`wf_7330f03b75f6`): Severity-gated risk escalation to Slack channels.
     - `cas-approval-dispatch` (`wf_5ccc14b11936`): Interactive Human-In-The-Loop review requests.
     - `cas-obligation-sync` (`wf_2783a17803cc`): Google Calendar and Airtable sync for post-signature milestones.
     - `cas-renewal-monitor` (`wf_ef794f8dd239`): Cron scheduler monitoring impending notice windows.

3. **Production PostgreSQL + Zero-Dependency Test Isolation**
   - Production persistence uses **PostgreSQL** via SQLAlchemy 2.0 and `asyncpg` with full transactional integrity and JSON column datetime serialization.
   - For offline test isolation and rapid CI/CD, an automated in-memory SQLite runner is provided (`TESTING=true`), enabling full federation test execution in under 4 seconds without external dependencies.

4. **Bidirectional Cross-Society Feedback Loops**
   - Risk Intelligence findings automatically inject mandatory positions into Negotiation Intelligence.
   - Compliance Intelligence violations update redline fallback thresholds.
   - Dispute Intelligence simulations adjust Risk severity indexes.

---

## 3. The 6 Multi-Agent Systems

| System | Architecture Pattern | Specialized Agents | Standalone Purpose |
| :--- | :--- | :--- | :--- |
| **1. Contract Intelligence** | Parallel Extraction + Adversarial Verification | ClauseExtractor, EntityExtractor, ObligationExtractor, DeadlineExtractor, CriticAgent, GraphBuilder | Normalizes raw contracts into a verified Contract Knowledge Graph. |
| **2. Risk Intelligence** | Adversarial Debate (Prosecution vs Defense vs Arbiter) | RiskHunter, LegalReasoner, CounterargumentAgent, EvidenceVerifier, SeverityAssessor, RiskSynthesizer | Rebuts ungrounded alarms via counterargument defense to yield calibrated Net Severity. |
| **3. Negotiation Intelligence** | Planner + Counterparty Simulator + Critic | NegotiationPlanner, StrategyAgent, CounterpartySimulator, ConcessionAgent, GameTheorist, Critic, FinalAdvisor | Simulates opposing party reactions and formulates executable redline markup. |
| **4. Compliance Intelligence** | Policy Retrieval + Rule Engine + Contextual Reasoning | PolicyRetriever, RuleMatcher, ComplianceAnalyzer, ConflictDetector, EvidenceAgent, Critic, Auditor | Audits contracts against corporate governance and regulatory standards. |
| **5. Obligation Intelligence** | Event-Driven Temporal Scheduling | ObligationItemExtractor, DependencyAnalyzer, DeadlinePlanner, MonitoringAgent, EscalationAgent, Reporter | Tracks post-signature milestones, payment schedules, and SLA breach risks. |
| **6. Dispute Intelligence** | Multi-Perspective Simulation & Polarized Debate | AmbiguityDetector, PartyAInterpreter, PartyBInterpreter, ConflictSimulator, ResolutionStrategist, DisputeCritic | Models crisis scenarios where opposing interpretations collide to prevent litigation. |

---

## 4. Evaluation Benchmark Results

CAS includes an automated benchmark suite (`backend/evaluation/benchmark.py`) that evaluates the federation across critical commercial dimensions:

```text
                       CAS Federation Benchmark Scorecard                       
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ System / Dimension   ┃ Key Metric           ┃ Result Value ┃ Status / Target ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ Contract             │ Clauses & Entities   │         100% │ PASSED (>=90%)  │
│ Intelligence         │ Completeness         │              │                 │
│ Risk Intelligence    │ Counterargument      │         100% │  PASSED (100%)  │
│                      │ Defense Rate         │              │                 │
│ Risk Intelligence    │ Verbatim Evidence    │         100% │ PASSED (>=95%)  │
│                      │ Coverage             │              │                 │
│ Negotiation          │ Concrete             │         100% │  PASSED (100%)  │
│ Intelligence         │ Counter-Proposal     │              │                 │
│                      │ Rate                 │              │                 │
│ Negotiation          │ Counterparty         │         100% │  PASSED (100%)  │
│ Intelligence         │ Simulation Coverage  │              │                 │
│ Compliance           │ Evidence Grounding   │         100% │ PASSED (>=90%)  │
│ Intelligence         │ Rate                 │              │                 │
│ Compliance           │ Violations           │            1 │    GROUNDED     │
│ Intelligence         │ Accurately Flagged   │              │                 │
│ Dispute Intelligence │ Opposing Perspective │         100% │  PASSED (100%)  │
│                      │ Polarization         │              │                 │
│ CAS Mesh Director    │ Cross-Society        │            1 │  RESOLVED/HITL  │
│                      │ Conflicts Arbitrated │              │                 │
│ CAS Mesh Director    │ Human-In-The-Loop    │         True │    ESCALATED    │
│                      │ Escalation           │              │                 │
└──────────────────────┴──────────────────────┴──────────────┴─────────────────┘
```

---

## 5. Quick Start

### 5.1 Environment Setup
```powershell
cd c:\CAS
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 5.2 Configure `.env`
```ini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cas_db
FASTN_ORG_ID=personal_867cccac2ec39658a401
```

### 5.3 Run Test Suite
```powershell
.\.venv\Scripts\pytest -v
# 14 passed in 3.06s
```

### 5.4 Run Evaluation Benchmark
```powershell
.\.venv\Scripts\python -m backend.evaluation.benchmark
```

### 5.5 Run 11-Stage Interactive Demo
```powershell
.\.venv\Scripts\python -m backend.demo_scenario
```

### 5.6 Start the REST API & Web Application
```powershell
.\.venv\Scripts\uvicorn backend.main:app --port 8000 --reload
```
- **Web App (React UI):** [http://localhost:8000/ui/](http://localhost:8000/ui/)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

### 5.7 Run Frontend in Development Mode (Vite)
```powershell
cd frontend
npm run dev
# Access dev UI at http://localhost:5173/
```

---

## 6. Project Structure

```text
c:\CAS\
├── backend/
│   ├── main.py                     # FastAPI application entrypoint
│   ├── demo_scenario.py            # End-to-end 11-stage demo runner
│   ├── core/                       # Core infrastructure & settings
│   │   ├── config.py               # Central configuration & Fastn workflow IDs
│   │   ├── gemini_service.py       # Centralized Google Gemini API reasoning engine
│   │   ├── logging.py              # Structured JSON logging
│   │   └── security.py             # Guardrails & prompt isolation
│   ├── models/                     # Shared Pydantic data schemas
│   │   ├── cas_message.py          # Standardized CASMessage protocol
│   │   ├── graph.py                # ContractGraph, Clause, Party, Obligation
│   │   ├── findings.py             # RiskReport, NegotiationStrategy, ComplianceReport
│   │   └── hitl.py                 # HumanReviewRequest, HumanDecision
│   ├── database/                   # Database layer
│   │   ├── schema.py               # SQLAlchemy models (PostgreSQL + asyncpg)
│   │   └── db.py                   # Async session management & connection pool
│   ├── director/                   # Contract Mesh Director
│   │   ├── coordinator.py          # Dynamic routing & mesh orchestration
│   │   ├── conflict_resolver.py    # Cross-society arbitration
│   │   └── lifecycle.py            # Contract lifecycle state machine
│   ├── systems/                    # 6 Independent Autonomous Societies
│   │   ├── contract_intelligence/  # Parallel extraction + verification
│   │   ├── risk_intelligence/      # Adversarial debate (Hunter vs Counter vs Assessor)
│   │   ├── negotiation_intelligence/# Planner + counterparty simulator + critic
│   │   ├── compliance_intelligence/# Policy retrieval + rules + contextual audit
│   │   ├── obligation_intelligence/# Event-driven operational scheduling
│   │   └── dispute_intelligence/   # Multi-perspective simulation & conflict modeling
│   ├── memory/                     # Persistent CAS memory & feedback loops
│   ├── events/                     # CASMessage asynchronous pub/sub event bus
│   ├── integrations/               # Fastn client & enterprise adapters
│   ├── evaluation/                 # Metrics & benchmark runner
│   └── tests/                      # Pytest automated test suites (14 tests)
├── contracts/                      # Sample enterprise vendor contracts
├── policies/                       # Corporate governance & compliance policies
├── docs/                           # Documentation
│   ├── FASTN_MCP_OPERATIONS.md     # Audit trail of Fastn MCP tools & workflows
│   ├── ARCHITECTURE.md             # Detailed architectural specification
│   ├── API_DOCUMENTATION.md        # REST API specifications & curl examples
│   └── SETUP_AND_RUN.md            # Setup, execution, and deployment guide
├── requirements.txt                # Python dependencies
└── pytest.ini                      # Pytest configuration
```

---

## 7. Documentation Links
- [Fastn MCP Operations & Audit Trail](docs/FASTN_MCP_OPERATIONS.md)
- [Federation Architecture Specification](docs/ARCHITECTURE.md)
- [REST API Documentation](docs/API_DOCUMENTATION.md)
- [Setup and Run Guide](docs/SETUP_AND_RUN.md)
