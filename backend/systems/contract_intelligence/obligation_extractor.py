from typing import List, Optional
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.core.security import SecurityGuardrails
from backend.models.graph import Obligation
from backend.core.logging import get_logger

logger = get_logger("ObligationExtractor")


class ExtractedObligationDTO(BaseModel):
    party_name: str
    clause_section: str
    title: str
    description: str
    obligation_type: str = "DELIVERABLE"  # PAYMENT, DELIVERABLE, REPORTING, NOTICE, RENEWAL, SERVICE_LEVEL, CONFIDENTIALITY
    frequency: str = "ONE_TIME"  # ONE_TIME, MONTHLY, QUARTERLY, ANNUAL, ON_EVENT
    due_date_or_trigger: Optional[str] = None
    notice_days: Optional[int] = None
    penalty_summary: Optional[str] = None


class ObligationExtractionResponse(BaseModel):
    obligations: List[ExtractedObligationDTO] = Field(default_factory=list)


class ObligationExtractor:
    """Agent responsible for identifying all contractual obligations, commitments, and performance duties."""

    @staticmethod
    async def extract_obligations(contract_text: str) -> List[Obligation]:
        prompt = (
            "You are the Obligation Extractor agent in a Contract Intelligence System.\n"
            "Extract every affirmative and negative obligation placed upon either party in this contract.\n"
            "Identify: which party is bound, the relevant section, obligation type (PAYMENT, DELIVERABLE, RENEWAL, NOTICE, etc.), "
            "frequency, due dates or triggers, notice requirements, and penalties for breach.\n"
        )
        wrapped_prompt = SecurityGuardrails.wrap_agent_context(prompt, contract_text)

        result: ObligationExtractionResponse = await gemini_service.generate_structured(
            prompt=wrapped_prompt,
            response_model=ObligationExtractionResponse,
            system_instruction="You are an expert contract obligation analysis specialist."
        )

        obligations = []
        for idx, dto in enumerate(result.obligations):
            ob_id = f"OBL-{idx+1:03d}"
            obligations.append(Obligation(
                id=ob_id,
                party_name=dto.party_name,
                clause_id=dto.clause_section,
                title=dto.title,
                description=dto.description,
                obligation_type=dto.obligation_type.upper(),
                frequency=dto.frequency.upper(),
                due_date=dto.due_date_or_trigger,
                notice_days=dto.notice_days,
                penalty_summary=dto.penalty_summary
            ))

        logger.info(f"Extracted {len(obligations)} obligations.")
        return obligations
