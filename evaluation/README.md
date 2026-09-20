# Contract Agentic Society (CAS) — Evaluation Center

The **CAS Evaluation Center** provides a rigorous, ground-truth benchmarking and accuracy-testing layer for the Contract Agentic Society. It measures how accurately CAS societies understand contracts, evaluate risk, detect compliance variances, manage obligations, resolve cross-society conflicts, and trigger Human-In-The-Loop (HITL) escalations.

All evaluation cases execute through the **real CAS multi-agent pipeline**—invoking the CAS Director, Contract Intelligence, Risk Intelligence, Compliance Intelligence, Negotiation Intelligence, Dispute Intelligence, and Obligation Intelligence.

---

## 1. Directory Structure

```text
evaluation/
├── datasets/
│   ├── contract_cases.json       # 30 deterministic standard, risk, compliance, obligation, conflict, and ambiguous cases
│   ├── adversarial_cases.json    # 10 adversarial cases (buried clauses, contradictory terms, false signals)
│   └── routing_cases.json        # 10 CAS Director routing scenarios and inbound event graphs
├── evaluator.py                  # CaseEvaluator: compares outputs against ground truth & generates failure records
├── metrics.py                    # Extraction, risk, compliance, agentic metrics & 0-100 Workflow Score
├── runner.py                     # EvaluationRunner: handles execution modes, tracking, and history persistence
└── README.md                     # Architecture and evaluation documentation
```

---

## 2. Dataset Overview

The evaluation suite comprises **50 deterministic, human-curated evaluation cases**:

| Dataset | File | Case Count | Description |
| :--- | :--- | :--- | :--- |
| **Contract Suite** | `contract_cases.json` | 30 | Standard agreements (NDA, SaaS, Service, Employment, Vendor), high-risk clauses (uncapped liability, 500% liquidated damages), compliance violations (RULE-001 through RULE-006), multi-deadline obligations, and internal clause conflicts. |
| **Adversarial Suite** | `adversarial_cases.json` | 10 | Deceptive agreements designed to test resilience: benign titles masking unlimited indemnity, contradictory payment clauses, buried termination in definitions, conflicting chronology, and false compliance assurances. |
| **Routing Suite** | `routing_cases.json` | 10 | Dynamic supervisor tests for CAS Director: intake dispatch, post-signature obligation transitions, renewal window activation, dispute escalation, inbound approval/rejection handling, and conflict arbitration. |

---

## 3. Metrics & Scoring Methodology

### A. Extraction & Classification Metrics
- **Contract Classification Accuracy**: Verifies correct categorization (SaaS, NDA, Vendor, Employment, etc.).
- **Clause & Entity Extraction Precision/Recall**: Compares extracted structures against normalized ground truth.
- **Normalized Set Similarity**: Uses order-insensitive, canonical synonym matching for categories and obligation types.

### B. Risk & Compliance Metrics
- **Risk Detection Precision & Recall**:
  $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}, \quad \text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}, \quad F_1 = \frac{2 \cdot P \cdot R}{P + R}$$
- **False Positive / False Negative Rates**: Measures over-escalation vs. missed severe exposure.
- **Compliance Detection Accuracy**: Validates correct flagging of corporate policy violations (RULE-001 through RULE-006).

### C. Agentic & Workflow Metrics
- **Routing Accuracy**: Whether the expected societies were selected by CAS Director.
- **HITL Decision Accuracy**: Whether Human-In-The-Loop review was triggered when needed and avoided when unnecessary.
- **Workflow Score (0–100)**:
  $$\text{Workflow Score} = (\text{Routing Correct} [25] + \text{Execution Correct} [25] + \text{HITL Correct} [25] + \text{Decision Correct} [25]) \times \text{Completeness Ratio}$$

---

## 4. Execution Modes & CLI Usage

### Run All Test Cases
```bash
python -m evaluation.runner
```

### Run a Specific Category
```bash
python -c "import asyncio; from evaluation.runner import evaluation_runner; asyncio.run(evaluation_runner.run(mode='category', category='risk'))"
```

### Run a Single Case
```bash
python -c "import asyncio; from evaluation.runner import evaluation_runner; asyncio.run(evaluation_runner.run(mode='single', case_id='CASE-006'))"
```

---

## 5. API Endpoints

The Evaluation Center exposes comprehensive REST endpoints mounted at `/evaluation`:

- `GET /evaluation/summary`: Executive metrics, pass/fail counts, and category breakdowns.
- `GET /evaluation/cases`: Catalog of all 50 evaluation cases.
- `GET /evaluation/cases/{case_id}`: Detailed definition of a specific test case.
- `POST /evaluation/run`: Triggers a synchronous or background evaluation run.
- `POST /evaluation/run/{case_id}`: Executes evaluation for an individual test case.
- `GET /evaluation/results`: Retrieves latest or selected run case-level results.
- `GET /evaluation/failures`: Filters and groups failure records by category.
- `GET /evaluation/runs`: Lists historical evaluation runs.
- `GET /evaluation/runs/{run_id}`: Retrieves details and traces for a past evaluation run.

---

## 6. Execution Trace Validation

For every case, CAS captures discrete execution events from `ExecutionTracker`:
1. `01 Contract Intelligence` — Structure, clause, entity, and obligation extraction
2. `02 Director Routing` — Dispatches parallel assessment
3. `03 Risk Intelligence` — Adversarial debate, counterarguments, exposure calibration
4. `04 Compliance Intelligence` — Policy rule matching and verification
5. `05 Negotiation Intelligence` — Redlines and counter-proposals
6. `06 Dispute Intelligence` — Ambiguity detection and litigation simulation
7. `07 CAS Director Conflict Resolver` — Cross-society arbitration
8. `08 Human-In-The-Loop` — Intentional pause for review (if required)
9. `09 Fastn Automation` — Outbound escalation and decision archiving

Evaluation traces are verified against expected state sequences to detect any skipped, duplicate, or misordered transitions.
