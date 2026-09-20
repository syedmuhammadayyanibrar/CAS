from typing import List, Dict
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.systems.dispute_intelligence.ambiguity_detector import AmbiguousClauseDTO
from backend.core.logging import get_logger

logger = get_logger("PartyAInterpreter")


class PartyAInterpretationDTO(BaseModel):
    clause_reference: str
    customer_interpretation: str
    customer_argued_standard: str


class PartyAResponse(BaseModel):
    interpretations: List[PartyAInterpretationDTO] = Field(default_factory=list)


class PartyAInterpreter:
    """
    Intentionally interprets ambiguous contract clauses from Party A (Customer's)
    economic and operational perspective, maximizing customer protection and vendor duty.
    """

    @staticmethod
    async def interpret_clauses(ambiguities: List[AmbiguousClauseDTO], customer_name: str = "Customer") -> Dict[str, str]:
        ambiguities_str = "\n".join([
            f"- Ref: {a.clause_reference} | Text: '{a.clause_text}' | Vague Phrase: '{a.vague_phrase}'"
            for a in ambiguities
        ])

        prompt = (
            f"You are the litigation counsel for {customer_name} (Party A).\n"
            "Interpret each of the ambiguous clauses below in the way MOST FAVORABLE to Customer.\n"
            "Argue that implied warranties apply, that vendor's performance must be flawless, and that any "
            "vague standards must be construed strictly against the drafter (contra proferentem).\n\n"
            f"AMBIGUOUS CLAUSES:\n{ambiguities_str}\n"
        )

        result: PartyAResponse = await gemini_service.generate_structured(
            prompt=prompt,
            response_model=PartyAResponse,
            system_instruction=f"You are adversarial counsel representing {customer_name}."
        )

        lookup = {i.clause_reference: i.customer_interpretation for i in result.interpretations}
        logger.info(f"Party A Interpreter formulated {len(lookup)} customer interpretations.")
        return lookup
