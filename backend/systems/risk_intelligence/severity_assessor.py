from typing import List, Dict
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.systems.risk_intelligence.counterargument import DebatedRiskDTO
from backend.systems.risk_intelligence.evidence_verifier import VerifiedEvidenceDTO
from backend.core.logging import get_logger

logger = get_logger("SeverityAssessor")


class NetSeverityDTO(BaseModel):
    clause_reference: str
    net_severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    severity_rationale: str
    uncertainty: float = 0.1
    recommend_human_review: bool = False


class SeverityAssessmentResponse(BaseModel):
    assessments: List[NetSeverityDTO] = Field(default_factory=list)


class SeverityAssessor:
    """
    Arbitration and scoring agent in the Adversarial Debate.
    Weighs the Hunter's indictment against the Counterargument's defense and
    the textual evidence to determine objective Net Severity and uncertainty.
    """

    @staticmethod
    async def assess_severity(
        debated_risks: List[DebatedRiskDTO],
        evidence_lookup: Dict[str, VerifiedEvidenceDTO]
    ) -> List[NetSeverityDTO]:
        debate_transcript = []
        for d in debated_risks:
            ev = evidence_lookup.get(d.clause_reference)
            ev_status = "VERIFIED VERBATIM" if (ev and ev.is_grounded_in_text) else "UNVERIFIED/QUESTIONABLE"
            debate_transcript.append(
                f"CLAUSE: {d.clause_reference} ({d.clause_title})\n"
                f"  Evidence Status: {ev_status}\n"
                f"  Hunter Claim: {d.hunter_claim}\n"
                f"  Counterargument: {d.counterargument} (Strength: {d.counterargument_strength})\n"
                f"  Mitigations: {d.mitigating_factors}\n"
            )

        prompt = (
            "You are the Severity Assessor in an Adversarial Risk Intelligence System.\n"
            "You must impartially judge the adversarial debate between the Risk Hunter and the Counterargument Agent.\n"
            "Rules for scoring:\n"
            "1. If the counterargument is STRONG and grounded in real commercial reality, DOWNGRADE the severity.\n"
            "2. If the risk is truly dangerous (e.g. uncapped indemnity or asymmetric liability) and cannot be reasonably excused, "
            "assign HIGH or CRITICAL and recommend human review.\n"
            "3. If evidence is unverified or ambiguous, increase uncertainty.\n"
            "Assign: net_severity (LOW, MEDIUM, HIGH, CRITICAL), severity_rationale, uncertainty (0.0 to 1.0), "
            "and recommend_human_review (bool).\n\n"
            f"DEBATE TRANSCRIPTS:\n" + "\n".join(debate_transcript)
        )

        result: SeverityAssessmentResponse = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=SeverityAssessmentResponse,
            system_instruction="You are an impartial judicial arbitrator evaluating legal risk debates."
        )

        logger.info(f"Severity Assessor calibrated {len(result.assessments)} risk verdicts.")
        return result.assessments
