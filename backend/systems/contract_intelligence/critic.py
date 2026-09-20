from typing import List
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.core.security import SecurityGuardrails
from backend.models.graph import ContractGraph
from backend.core.logging import get_logger

logger = get_logger("ContractCriticAgent")


class VerificationFinding(BaseModel):
    check_type: str  # MISSING_FIELD, MISATTRIBUTED_OBLIGATION, DATE_MISMATCH, CITATION_VERIFIED
    item_reference: str
    verified: bool
    notes: str


class CriticVerificationReport(BaseModel):
    is_valid: bool = True
    confidence_score: float = 0.95
    verified_clauses_count: int = 0
    discrepancies: List[VerificationFinding] = Field(default_factory=list)
    critic_summary: str = "Contract graph accurately captures key terms."


class ContractCriticAgent:
    """
    Critic & Verification Agent for Contract Intelligence.
    Adversarially cross-checks the assembled Contract Graph against the source text,
    verifying citations, party bindings, and temporal consistency.
    """

    @staticmethod
    async def verify_graph(graph: ContractGraph, raw_text: str) -> CriticVerificationReport:
        clauses_summary = "\n".join([f"[{c.id}] {c.section_number}: {c.title} ({c.clause_type})" for c in graph.clauses[:15]])
        obligations_summary = "\n".join([f"[{o.id}] {o.party_name} -> {o.title} (Due: {o.due_date})" for o in graph.obligations[:10]])

        prompt = (
            "You are the Verification & Critic Agent in a Contract Intelligence System.\n"
            "Your job is to rigorously audit the extracted Contract Graph against the source contract.\n"
            "Check for:\n"
            "1. Did we capture the primary parties correctly?\n"
            "2. Are key liability, indemnity, and termination clauses identified?\n"
            "3. Are obligations correctly attributed to the responsible party?\n"
            "4. Are there any hallucinations or misattributed terms?\n\n"
            f"EXTRACTED CLAUSES SUMMARY:\n{clauses_summary}\n\n"
            f"EXTRACTED OBLIGATIONS SUMMARY:\n{obligations_summary}\n"
        )
        wrapped_prompt = SecurityGuardrails.wrap_agent_context(prompt, raw_text[:4000])

        report: CriticVerificationReport = await gemini_service.generate_structured(
            prompt=wrapped_prompt,
            response_model=CriticVerificationReport,
            system_instruction="You are a meticulous legal audit critic."
        )

        logger.info(
            f"Critic verified graph for {graph.contract_id}: Valid={report.is_valid}, "
            f"Confidence={report.confidence_score:.2f}, Discrepancies={len(report.discrepancies)}"
        )
        return report
