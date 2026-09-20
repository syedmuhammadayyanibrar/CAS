from typing import List, Dict
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.systems.dispute_intelligence.ambiguity_detector import AmbiguousClauseDTO
from backend.core.logging import get_logger

logger = get_logger("PartyBInterpreter")


class PartyBInterpretationDTO(BaseModel):
    clause_reference: str
    vendor_interpretation: str
    vendor_argued_standard: str


class PartyBResponse(BaseModel):
    interpretations: List[PartyBInterpretationDTO] = Field(default_factory=list)


class PartyBInterpreter:
    """
    Intentionally interprets ambiguous contract clauses from Party B (Vendor's)
    economic and operational perspective, maximizing vendor discretion and liability shields.
    """

    @staticmethod
    async def interpret_clauses(ambiguities: List[AmbiguousClauseDTO], vendor_name: str = "Vendor") -> Dict[str, str]:
        ambiguities_str = "\n".join([
            f"- Ref: {a.clause_reference} | Text: '{a.clause_text}' | Vague Phrase: '{a.vague_phrase}'"
            for a in ambiguities
        ])

        prompt = (
            f"You are the litigation counsel for {vendor_name} (Party B).\n"
            "Interpret each of the ambiguous clauses below in the way MOST FAVORABLE to Vendor.\n"
            "Argue that Vendor has broad operational discretion, that liability caps and disclaimers are absolute, "
            "that 'commercially reasonable' means minimal industry effort, and that Customer assumed the risk.\n\n"
            f"AMBIGUOUS CLAUSES:\n{ambiguities_str}\n"
        )

        result: PartyBResponse = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=PartyBResponse,
            system_instruction=f"You are adversarial counsel representing {vendor_name}."
        )

        lookup = {i.clause_reference: i.vendor_interpretation for i in result.interpretations}
        logger.info(f"Party B Interpreter formulated {len(lookup)} vendor interpretations.")
        return lookup
