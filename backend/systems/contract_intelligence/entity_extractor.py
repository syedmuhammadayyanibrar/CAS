from typing import List, Optional
from pydantic import BaseModel, Field
from backend.core.gemini_service import gemini_service
from backend.core.security import SecurityGuardrails
from backend.models.graph import Party
from backend.core.logging import get_logger

logger = get_logger("EntityExtractor")


class ExtractedPartyDTO(BaseModel):
    name: str
    role: str  # e.g., "Customer", "Vendor", "Provider"
    jurisdiction: Optional[str] = None
    entity_type: Optional[str] = "Corporation"


class EntityExtractionResponse(BaseModel):
    parties: List[ExtractedPartyDTO] = Field(default_factory=list)
    governing_law: Optional[str] = None
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None


class EntityExtractor:
    """Agent specialized in identifying contracting parties, jurisdictions, and overarching dates."""

    @staticmethod
    async def extract_entities(contract_text: str) -> EntityExtractionResponse:
        prompt = (
            "You are the Entity & Party Extractor agent in a Contract Intelligence System.\n"
            "Extract all legal contracting parties from the text, their defined roles (Customer, Vendor, etc.), "
            "their state/jurisdiction of incorporation, the governing law, effective date, and expiration/initial term.\n"
        )
        wrapped_prompt = SecurityGuardrails.wrap_agent_context(prompt, contract_text)

        result: EntityExtractionResponse = await gemini_service.generate_structured(
            prompt=wrapped_prompt,
            response_model=EntityExtractionResponse,
            system_instruction="You are an expert contract metadata and entity recognition analyst."
        )

        logger.info(f"Extracted {len(result.parties)} parties. Governing Law: {result.governing_law}")
        return result
