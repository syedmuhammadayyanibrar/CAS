from typing import List, Optional
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.core.security import SecurityGuardrails
from backend.models.graph import Deadline
from backend.core.logging import get_logger

logger = get_logger("DeadlineExtractor")


class ExtractedDeadlineDTO(BaseModel):
    title: str
    due_date_or_window: str
    is_critical: bool = False
    reminder_days: int = 14
    description: Optional[str] = None


class DeadlineExtractionResponse(BaseModel):
    deadlines: List[ExtractedDeadlineDTO] = Field(default_factory=list)


class DeadlineExtractor:
    """Agent specialized in extracting exact calendar deadlines, notice windows, and milestone targets."""

    @staticmethod
    async def extract_deadlines(contract_text: str) -> List[Deadline]:
        prompt = (
            "You are the Date & Deadline Extractor agent in a Contract Intelligence System.\n"
            "Extract every time-bound deadline, payment schedule, notice window (e.g., non-renewal notice), "
            "cure period, and expiration date.\n"
            "Flag if a deadline is critical (e.g., failure to provide notice results in auto-renewal or breach).\n"
        )
        wrapped_prompt = SecurityGuardrails.wrap_agent_context(prompt, contract_text)

        result: DeadlineExtractionResponse = await gemini_service.generate_structured(
            prompt=wrapped_prompt,
            response_model=DeadlineExtractionResponse,
            system_instruction="You are a legal timeline and deadline scheduling expert."
        )

        deadlines = []
        for idx, dto in enumerate(result.deadlines):
            dl_id = f"DLN-{idx+1:03d}"
            deadlines.append(Deadline(
                id=dl_id,
                title=dto.title,
                due_date=dto.due_date_or_window,
                is_critical=dto.is_critical,
                reminder_days=dto.reminder_days,
                description=dto.description
            ))

        logger.info(f"Extracted {len(deadlines)} deadlines.")
        return deadlines
