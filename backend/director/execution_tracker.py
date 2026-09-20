import uuid
import time
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, AsyncGenerator
from backend.core.logging import get_logger

logger = get_logger("ExecutionTracker")


class ExecutionTracker:
    """
    Lightweight, real-time execution state tracker for CAS orchestration.
    Tracks societies, parallel and sequential agents, tasks, transitions,
    HITL review pauses, and Fastn external automations.
    """

    def __init__(self):
        # In-memory storage for active and completed executions: contract_id -> ExecutionState
        self._executions: Dict[str, Dict[str, Any]] = {}
        # Event queues for live streaming: contract_id -> list of asyncio.Queue
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        # Active operations registry for dashboard
        self._active_operations: Dict[str, Dict[str, Any]] = {}

    def _get_or_create_execution(self, contract_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        if contract_id not in self._executions:
            exec_id = f"EXEC-{uuid.uuid4().hex[:8].upper()}"
            self._executions[contract_id] = {
                "execution_id": exec_id,
                "contract_id": contract_id,
                "title": title or f"Contract {contract_id}",
                "status": "WAITING",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
                "current_step": None,
                "next_step": None,
                "stages": self._get_initial_stages(),
                "events": [],
            }
        elif title and self._executions[contract_id].get("title") == f"Contract {contract_id}":
            self._executions[contract_id]["title"] = title
        return self._executions[contract_id]

    def _get_initial_stages(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "contract_intake",
                "number": "01",
                "title": "Contract Received",
                "society": "Intake",
                "status": "COMPLETED",
                "summary": "Document ingested and ready for analysis",
                "is_transition": False,
                "agents": [
                    {
                        "id": "doc_intake",
                        "name": "Document Ingestion",
                        "task": "Sanitizing contract text and extracting metadata",
                        "status": "COMPLETED",
                        "result_summary": "Contract text loaded and sanitized",
                        "is_parallel": False,
                    }
                ]
            },
            {
                "id": "contract_intelligence",
                "number": "02",
                "title": "Contract Intelligence",
                "society": "Contract Intelligence",
                "status": "WAITING",
                "summary": "Structural graph extraction and mathematical verification",
                "is_transition": False,
                "is_parallel": True,
                "agents": [
                    {
                        "id": "doc_parser",
                        "name": "Document Parser",
                        "task": "Extracting structure, recitals, and core definitions",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": True,
                    },
                    {
                        "id": "clause_extractor",
                        "name": "Clause Extractor",
                        "task": "Segmenting operative clauses and cross-references",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": True,
                    },
                    {
                        "id": "entity_extractor",
                        "name": "Entity Extractor",
                        "task": "Identifying parties, legal entities, and roles",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": True,
                    },
                    {
                        "id": "obligation_extractor",
                        "name": "Obligation Extractor",
                        "task": "Extracting contractual commitments and milestones",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": True,
                    },
                    {
                        "id": "contract_critic",
                        "name": "Contract Critic Agent",
                        "task": "Verifying graph integrity and structural completeness",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": False,
                    },
                ]
            },
            {
                "id": "transition_director_1",
                "number": None,
                "title": "CAS Director Routing",
                "society": "CAS Director",
                "status": "WAITING",
                "summary": "Routing normalized graph to adversarial risk debate & compliance audit",
                "is_transition": True,
                "transition_details": {
                    "from_society": "Contract Intelligence",
                    "to_society": "Risk & Compliance Intelligence",
                    "action": "Director dispatching parallel assessment"
                },
                "agents": []
            },
            {
                "id": "risk_intelligence",
                "number": "03",
                "title": "Risk Intelligence",
                "society": "Risk Intelligence",
                "status": "WAITING",
                "summary": "Adversarial dialectic debate on liabilities, indemnity, and breach",
                "is_transition": False,
                "is_parallel": True,
                "agents": [
                    {
                        "id": "risk_hunter",
                        "name": "Risk Hunter",
                        "task": "Scanning indemnity, liability, and uncapped exposure",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": True,
                    },
                    {
                        "id": "legal_reasoner",
                        "name": "Legal Reasoner",
                        "task": "Evaluating worst-case financial and legal damages",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": True,
                    },
                    {
                        "id": "counterargument_agent",
                        "name": "Counterargument Agent",
                        "task": "Testing findings against standard market defenses",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": True,
                    },
                    {
                        "id": "evidence_verifier",
                        "name": "Evidence Verifier",
                        "task": "Validating clause citations against contract text",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": False,
                    },
                    {
                        "id": "risk_synthesizer",
                        "name": "Risk Synthesizer",
                        "task": "Synthesizing net exposure score and escalation flags",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": False,
                    },
                ]
            },
            {
                "id": "compliance_intelligence",
                "number": "04",
                "title": "Compliance Intelligence",
                "society": "Compliance Intelligence",
                "status": "WAITING",
                "summary": "Corporate policy audit and statutory regulation check",
                "is_transition": False,
                "is_parallel": True,
                "agents": [
                    {
                        "id": "policy_retriever",
                        "name": "Policy Retriever",
                        "task": "Retrieving corporate governance & statutory playbook rules",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": True,
                    },
                    {
                        "id": "rule_matcher",
                        "name": "Rule Matcher",
                        "task": "Indexing mandatory clause keywords and provisions",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": True,
                    },
                    {
                        "id": "compliance_analyzer",
                        "name": "Compliance Analyzer",
                        "task": "Auditing contractual commitments for compliance variances",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": False,
                    },
                    {
                        "id": "compliance_auditor",
                        "name": "Compliance Auditor",
                        "task": "Formulating compliance audit findings and evidence citations",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": False,
                    },
                ]
            },
            {
                "id": "negotiation_intelligence",
                "number": "05",
                "title": "Negotiation Intelligence",
                "society": "Negotiation Intelligence",
                "status": "WAITING",
                "summary": "Strategic redline planning, counterparty simulation, and concession modeling",
                "is_transition": False,
                "is_parallel": False,
                "agents": [
                    {
                        "id": "negotiation_planner",
                        "name": "Strategic Planner",
                        "task": "Synthesizing redlines aligned with commercial objective",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": False,
                    },
                    {
                        "id": "counterparty_simulator",
                        "name": "Counterparty Simulator",
                        "task": "Simulating vendor legal objections and deal sensitivities",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": False,
                    },
                    {
                        "id": "concession_agent",
                        "name": "Concession Agent",
                        "task": "Constructing fallback positions and concession packages",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": False,
                    },
                ]
            },
            {
                "id": "dispute_intelligence",
                "number": "06",
                "title": "Dispute Intelligence",
                "society": "Dispute Intelligence",
                "status": "WAITING",
                "summary": "Dual-perspective litigation simulation and ambiguity stress-testing",
                "is_transition": False,
                "is_parallel": True,
                "agents": [
                    {
                        "id": "ambiguity_detector",
                        "name": "Ambiguity Detector",
                        "task": "Scanning clauses for subjective and discretionary terms",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": False,
                    },
                    {
                        "id": "litigation_sim",
                        "name": "Litigation Simulator",
                        "task": "Simulating opposing legal stances and clash scenarios",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": True,
                    },
                ]
            },
            {
                "id": "cas_director",
                "number": "07",
                "title": "CAS Director Synthesis",
                "society": "CAS Director",
                "status": "WAITING",
                "summary": "Detecting cross-society conflicts and arbitrating compromises",
                "is_transition": False,
                "agents": [
                    {
                        "id": "conflict_resolver",
                        "name": "Conflict Resolver",
                        "task": "Arbitrating conflicts between risk findings and negotiation redlines",
                        "status": "WAITING",
                        "result_summary": None,
                        "is_parallel": False,
                    }
                ]
            },
            {
                "id": "human_review",
                "number": "08",
                "title": "Human-In-The-Loop Review",
                "society": "Human-In-The-Loop",
                "status": "WAITING",
                "summary": "Intentional pause for General Counsel review and decision",
                "is_transition": False,
                "agents": []
            },
            {
                "id": "fastn_automation",
                "number": "09",
                "title": "External Automation",
                "society": "Fastn Adapter",
                "status": "WAITING",
                "summary": "Escalation notification dispatched to external systems",
                "is_transition": False,
                "agents": []
            }
        ]

    def start_execution(self, contract_id: str, title: Optional[str] = None) -> str:
        exec_state = self._get_or_create_execution(contract_id, title)
        exec_state["status"] = "RUNNING"
        exec_state["started_at"] = datetime.now(timezone.utc).isoformat()
        exec_state["completed_at"] = None

        # Reset stages to clean state
        exec_state["stages"] = self._get_initial_stages()
        exec_state["events"] = []

        logger.info(f"Execution started for contract {contract_id} (ID: {exec_state['execution_id']})")
        return exec_state["execution_id"]

    async def emit_event(
        self,
        contract_id: str,
        event_type: str,
        society: str,
        agent: str,
        task: str,
        status: str = "RUNNING",
        result_summary: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        evidence: Optional[List[str]] = None,
        next_agent: Optional[str] = None,
        next_task: Optional[str] = None,
        waiting_reason: Optional[str] = None,
    ):
        """
        Emits a discrete execution event, updating the live execution model and notifying listeners.
        """
        exec_state = self._get_or_create_execution(contract_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        event_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"

        # 1. Update CURRENT step
        if status == "RUNNING":
            exec_state["current_step"] = {
                "society": society,
                "agent": agent,
                "task": task,
                "status": "Running",
                "started_at_ts": time.time(),
                "started_at": now_iso,
            }
            # Record in active operations for dashboard
            self._active_operations[contract_id] = {
                "contract_id": contract_id,
                "title": exec_state.get("title", f"Contract {contract_id}"),
                "society": society,
                "agent": agent,
                "task": task,
                "started_at_ts": time.time(),
                "status": "Running",
            }
        elif status in ("COMPLETED", "PAUSED_FOR_HUMAN", "FAILED"):
            if exec_state["current_step"] and exec_state["current_step"].get("agent") == agent:
                exec_state["current_step"]["status"] = status.capitalize()

            if status in ("COMPLETED", "FAILED"):
                # Remove or update active operation
                if contract_id in self._active_operations:
                    self._active_operations[contract_id]["status"] = status.capitalize()
                    self._active_operations[contract_id]["completed_at_ts"] = time.time()

        # 2. Update NEXT step
        if next_agent:
            exec_state["next_step"] = {
                "society": society,
                "agent": next_agent,
                "task": next_task or "Waiting to execute",
                "waiting_reason": waiting_reason or f"Waiting for {agent}",
            }
        elif status == "COMPLETED" and not exec_state.get("next_step"):
            exec_state["next_step"] = None

        # 3. Update matching stage and agent in the hierarchy
        for stage in exec_state["stages"]:
            if stage["society"].lower() in society.lower() or society.lower() in stage["society"].lower():
                if status == "RUNNING" and stage["status"] != "COMPLETED":
                    stage["status"] = "RUNNING"
                elif event_type == "society_completed":
                    stage["status"] = "COMPLETED"
                    for ag in stage["agents"]:
                        if ag["status"] != "COMPLETED":
                            ag["status"] = "COMPLETED"
                elif status == "COMPLETED" and all(a["status"] == "COMPLETED" for a in stage["agents"]):
                    stage["status"] = "COMPLETED"

                # Update agent
                for ag in stage["agents"]:
                    if ag["name"].lower() == agent.lower() or agent.lower() in ag["name"].lower():
                        ag["status"] = status
                        ag["task"] = task
                        if result_summary:
                            ag["result_summary"] = result_summary
                        if evidence:
                            ag["evidence"] = evidence
                        if details:
                            ag["details"] = details
                        ag["event_id"] = event_id

            # Check for transition stages
            if event_type == "director_routed" and stage["id"] == "transition_director_1":
                stage["status"] = "COMPLETED"
                stage["summary"] = task or stage["summary"]

            # Check for HITL
            if event_type == "hitl_required" and stage["id"] == "human_review":
                stage["status"] = "PAUSED_FOR_HUMAN"
                stage["summary"] = task or "Critical risk requires General Counsel approval."

            # Check for Fastn
            if event_type == "fastn_triggered" and stage["id"] == "fastn_automation":
                stage["status"] = "COMPLETED"
                stage["summary"] = result_summary or "Escalation delivered to external systems"

        # 4. Append to event trace
        event_obj = {
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": now_iso,
            "society": society,
            "agent": agent,
            "task": task,
            "status": status,
            "result_summary": result_summary,
            "evidence": evidence or [],
            "technical": {
                "eventId": event_id,
                "executionId": exec_state["execution_id"],
                "workflowId": details.get("workflow_id") if details else None,
                "timestamp": now_iso,
            }
        }
        exec_state["events"].append(event_obj)

        # 5. Push to SSE subscribers
        await self._broadcast_event(contract_id, event_obj, exec_state)

    async def complete_execution(self, contract_id: str, status: str = "COMPLETED"):
        exec_state = self._get_or_create_execution(contract_id)
        exec_state["status"] = status
        exec_state["completed_at"] = datetime.now(timezone.utc).isoformat()
        if exec_state["current_step"]:
            exec_state["current_step"]["status"] = status.capitalize()
        exec_state["next_step"] = None

        # Clean up active operation
        if contract_id in self._active_operations:
            del self._active_operations[contract_id]

        await self._broadcast_event(contract_id, {
            "event_type": "execution_completed",
            "status": status,
            "timestamp": exec_state["completed_at"],
        }, exec_state)

    async def _broadcast_event(self, contract_id: str, event_obj: Dict[str, Any], full_state: Dict[str, Any]):
        if contract_id in self._subscribers:
            dead_queues = []
            for q in self._subscribers[contract_id]:
                try:
                    payload = {
                        "event": event_obj,
                        "execution": full_state,
                    }
                    q.put_nowait(payload)
                except Exception:
                    dead_queues.append(q)
            for dq in dead_queues:
                self._subscribers[contract_id].remove(dq)

    def get_execution(self, contract_id: str) -> Optional[Dict[str, Any]]:
        return self._executions.get(contract_id)

    def get_active_operations(self) -> List[Dict[str, Any]]:
        now = time.time()
        ops = []
        for cid, op in self._active_operations.items():
            elapsed_sec = int(now - op.get("started_at_ts", now))
            ops.append({
                "contract_id": cid,
                "title": op.get("title", f"Contract {cid}"),
                "society": op.get("society", "Intelligence"),
                "agent": op.get("agent", "Specialist"),
                "task": op.get("task", "Analyzing"),
                "status": op.get("status", "Running"),
                "elapsed_seconds": elapsed_sec,
            })
        return ops

    async def subscribe_stream(self, contract_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        queue = asyncio.Queue()
        if contract_id not in self._subscribers:
            self._subscribers[contract_id] = []
        self._subscribers[contract_id].append(queue)

        # First emit existing state if present
        current = self.get_execution(contract_id)
        if current:
            yield {"event": {"event_type": "initial_state"}, "execution": current}

        try:
            while True:
                data = await queue.get()
                yield data
        except asyncio.CancelledError:
            pass
        finally:
            if contract_id in self._subscribers and queue in self._subscribers[contract_id]:
                self._subscribers[contract_id].remove(queue)


execution_tracker = ExecutionTracker()
