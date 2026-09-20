from typing import List, Optional
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.core.security import SecurityGuardrails
from backend.models.findings import ObligationItem
from backend.core.logging import get_logger

logger = get_logger("ObligationItemExtractor")


class DetailedObligationDTO(BaseModel):
    party: str
    title: str
    description: str
    due_date_or_interval: Optional[str] = None
    notice_days: Optional[int] = 14
    obligation_type: str = "DELIVERABLE"  # PAYMENT, DELIVERABLE, RENEWAL, REPORTING, SLA
    recurring: bool = False
    frequency: str = "ONE_TIME"  # ONE_TIME, MONTHLY, QUARTERLY, ANNUAL


class DetailedObligationResponse(BaseModel):
    obligations: List[DetailedObligationDTO] = Field(default_factory=list)


class ObligationItemExtractor:
    """
    Identifies all post-signature operational commitments, recurring payments,
    reporting milestones, renewal notice windows, and SLA deliverables.
    """

    @staticmethod
    async def extract_all_obligations(contract_text: str) -> List[ObligationItem]:
        prompt = (
            "You are the Obligation Extractor in an Event-Driven Obligation Intelligence System.\n"
            "Extract all post-signature operational, financial, legal, and delivery commitments in this contract.\n"
            "Ensure you extract:\n"
            "- Payment terms, due dates, billing frequency, and penalties\n"
            "- Uptime SLA requirements and credit request windows\n"
            "- Non-renewal notice windows (e.g., 60 days prior to expiration)\n"
            "- Reporting or audit obligations\n"
            "- Confidentiality or data return upon termination\n"
        )
        wrapped_prompt = SecurityGuardrails.wrap_agent_context(prompt, contract_text[:4000])

        result: DetailedObligationResponse = await gemini_service.generate_structured(
            prompt=wrapped_prompt,
            response_model=DetailedObligationResponse,
            system_instruction="You are a post-signature contract obligation and SLA operations specialist."
        )

        items = []
        for idx, dto in enumerate(result.obligations):
            ob_id = f"OBL-RUN-{idx+1:03d}"
            items.append(ObligationItem(
                obligation_id=ob_id,
                party=dto.party,
                title=dto.title,
                description=dto.description,
                due_date=dto.due_date_or_interval,
                notice_days=dto.notice_days,
                type=dto.obligation_type.upper(),
                status="PENDING",
                escalation_level="NONE"
            ))

        logger.info(f"Obligation Extractor identified {len(items)} post-signature commitments.")
        return items
