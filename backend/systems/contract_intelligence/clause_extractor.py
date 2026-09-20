from typing import List
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.core.security import SecurityGuardrails
from backend.models.graph import Clause
from backend.core.logging import get_logger

logger = get_logger("ClauseExtractor")


class ExtractedClauseDTO(BaseModel):
    section_number: str
    title: str
    text: str
    clause_type: str = "OTHER"
    is_unusual: bool = False
    unusual_reason: str = ""
    summary: str = ""


class ClauseExtractionResponse(BaseModel):
    clauses: List[ExtractedClauseDTO] = Field(default_factory=list)


class ClauseExtractor:
    """Agent responsible for identifying and extracting all distinct legal clauses."""

    @staticmethod
    async def extract_clauses(contract_text: str) -> List[Clause]:
        prompt = (
            "You are the Clause Extractor agent in a Contract Intelligence System.\n"
            "Analyze the following contract text and extract every distinct clause or section.\n"
            "For each clause, provide:\n"
            "- section_number (e.g., 'Section 8.2' or '2.1')\n"
            "- title (e.g., 'Aggregate Liability Cap')\n"
            "- text (exact verbatim or key portion of the clause)\n"
            "- clause_type (one of: LIABILITY, INDEMNITY, TERMINATION, PAYMENT, CONFIDENTIALITY, IP, SLA, GOVERNING_LAW, RENEWAL, AUDIT, OTHER)\n"
            "- is_unusual (boolean flag if the clause contains aggressive, asymmetric, or non-standard terms)\n"
            "- unusual_reason (explanation if marked unusual)\n"
            "- summary (one sentence plain summary)\n"
        )
        wrapped_prompt = SecurityGuardrails.wrap_agent_context(prompt, contract_text)

        result: ClauseExtractionResponse = await gemini_service.generate_structured(
            prompt=wrapped_prompt,
            response_model=ClauseExtractionResponse,
            system_instruction="You are a legal contract clause extraction specialist."
        )

        clauses = []
        for idx, item in enumerate(result.clauses):
            clause_id = f"CLS-{idx+1:03d}"
            clauses.append(Clause(
                id=clause_id,
                section_number=item.section_number,
                title=item.title,
                text=item.text,
                clause_type=item.clause_type.upper(),
                is_unusual=item.is_unusual,
                unusual_reason=item.unusual_reason if item.is_unusual else None,
                summary=item.summary
            ))

        logger.info(f"Extracted {len(clauses)} clauses from contract.")
        return clauses
