import re
from typing import Dict, Any, List
from backend.core.security import SecurityGuardrails
from backend.core.logging import get_logger

logger = get_logger("DocumentParser")


class DocumentParser:
    """
    Normalizes raw contract text, identifies section boundaries,
    and removes noise while defending against prompt injection.
    """

    @staticmethod
    def parse_document(raw_text: str) -> Dict[str, Any]:
        sanitized_text, is_flagged, warnings = SecurityGuardrails.sanitize_contract_text(raw_text)
        if is_flagged:
            logger.warning(f"Security warnings in document parse: {warnings}")

        # Extract title
        lines = [line.strip() for line in sanitized_text.splitlines() if line.strip()]
        title = lines[0] if lines else "Untitled Contract"

        # Split into preliminary sections by Roman numerals, 'SECTION', or numbered headings
        section_pattern = r"(?:^|\n)(SECTION\s+\d+[:\.]?|[0-9]+\.[0-9]*\s+[A-Z][A-Za-z\s]+)"
        sections_split = re.split(section_pattern, sanitized_text)

        raw_sections = []
        if len(sections_split) > 1:
            for i in range(1, len(sections_split), 2):
                header = sections_split[i].strip()
                body = sections_split[i+1].strip() if i+1 < len(sections_split) else ""
                raw_sections.append({"header": header, "body": body})
        else:
            raw_sections.append({"header": "FULL_DOCUMENT", "body": sanitized_text})

        return {
            "title": title,
            "raw_text": sanitized_text,
            "char_count": len(sanitized_text),
            "line_count": len(lines),
            "raw_sections": raw_sections,
            "security_warnings": warnings
        }
