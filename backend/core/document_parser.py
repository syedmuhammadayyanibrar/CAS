import io
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from backend.core.logging import get_logger

logger = get_logger("DocumentParser")


class DocumentParser:
    """
    Zero-external-dependency enterprise document parser for legal contracts.
    Natively supports:
    - Microsoft Word (.docx) via standard library zipfile + OpenXML ET
    - Plain text & Markdown (.txt, .md)
    - JSON structured contracts (.json)
    - PDF (.pdf) via pypdf or streaming text extraction fallback
    """

    @classmethod
    def extract_text_from_bytes(cls, filename: str, content_bytes: bytes) -> Dict[str, Any]:
        """
        Parses raw bytes from an uploaded contract file and extracts clean text,
        paragraph structure, word metrics, and preliminary contract metadata.
        """
        lower_name = filename.lower()
        extracted_text = ""
        file_type = "unknown"

        if lower_name.endswith(".docx"):
            file_type = "docx"
            extracted_text = cls._parse_docx(content_bytes)
        elif lower_name.endswith(".pdf"):
            file_type = "pdf"
            extracted_text = cls._parse_pdf(content_bytes)
        elif lower_name.endswith(".json"):
            file_type = "json"
            extracted_text = cls._parse_json(content_bytes)
        elif lower_name.endswith((".txt", ".md", ".rtf", ".csv")):
            file_type = "text"
            extracted_text = cls._parse_plain_text(content_bytes)
        else:
            # Fallback text decoder
            file_type = "text_fallback"
            extracted_text = cls._parse_plain_text(content_bytes)

        clean_text = extracted_text.strip()
        paragraphs = [p.strip() for p in clean_text.split("\n") if p.strip()]
        words = clean_text.split()
        word_count = len(words)
        char_count = len(clean_text)
        para_count = len(paragraphs)
        estimated_read_time = max(1, round(word_count / 200))  # standard 200 wpm

        title = cls._detect_title(filename, paragraphs)
        parties = cls._detect_parties(clean_text)

        logger.info(
            f"Successfully parsed document '{filename}' ({file_type}): "
            f"{char_count} chars, {word_count} words, {para_count} paragraphs."
        )

        return {
            "filename": filename,
            "file_type": file_type,
            "content": clean_text,
            "character_count": char_count,
            "word_count": word_count,
            "paragraph_count": para_count,
            "estimated_read_time_minutes": estimated_read_time,
            "detected_title": title,
            "detected_parties": parties,
        }

    @classmethod
    def _parse_docx(cls, content_bytes: bytes) -> str:
        """Parses Microsoft Word (.docx) files using standard library zipfile and XML."""
        try:
            with zipfile.ZipFile(io.BytesIO(content_bytes)) as zf:
                if "word/document.xml" not in zf.namelist():
                    raise ValueError("Document does not contain standard word/document.xml.")
                
                xml_data = zf.read("word/document.xml")
                root = ET.fromstring(xml_data)
                
                # Standard OpenXML namespace for WordprocessingML
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                
                paragraphs = []
                for p in root.iterfind(".//w:p", ns):
                    runs = []
                    for t in p.iterfind(".//w:t", ns):
                        if t.text:
                            runs.append(t.text)
                    para_text = "".join(runs).strip()
                    if para_text:
                        paragraphs.append(para_text)
                
                return "\n\n".join(paragraphs)
        except zipfile.BadZipFile:
            logger.debug("File with .docx extension is not a valid zip container. Falling back to plain text decoding.")
            return cls._parse_plain_text(content_bytes)
        except Exception as e:
            logger.warning(f"Error parsing .docx file ({e}). Falling back to plain text.")
            return cls._parse_plain_text(content_bytes)

    @classmethod
    def _parse_pdf(cls, content_bytes: bytes) -> str:
        """Parses PDF documents using pypdf if available, or native stream parser."""
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content_bytes))
            pages_text = []
            for idx, page in enumerate(reader.pages):
                txt = page.extract_text()
                if txt and txt.strip():
                    pages_text.append(txt.strip())
            if pages_text:
                return "\n\n".join(pages_text)
        except Exception as e:
            logger.debug(f"pypdf extraction failed or not available ({e}), falling back to stream parsing.")

        # Fallback: extract text blocks from PDF stream
        try:
            raw = content_bytes.decode("latin-1", errors="ignore")
            # Extract PDF parenthesized text elements inside text objects (Tj / TJ)
            matches = re.findall(r"\(([\w\s\.,\-\'\":;?!@#$%&*+=\[\]{}()<>/\\]{3,})\)\s*(?:Tj|'|\")", raw)
            if matches:
                # Clean escaped chars
                cleaned = [m.replace("\\(", "(").replace("\\)", ")").replace("\\r", "\n") for m in matches]
                return "\n".join(cleaned)
            
            # General text heuristics
            readable_blocks = re.findall(r"[A-Za-z0-9\s,.\-\'\"\:\;\/\(\)]{20,}", raw)
            if readable_blocks:
                return "\n\n".join(b.strip() for b in readable_blocks[:80])
        except Exception as e:
            logger.error(f"Stream PDF extraction error: {e}")

        # Final graceful fallback to plain text
        return cls._parse_plain_text(content_bytes)

    @classmethod
    def _parse_plain_text(cls, content_bytes: bytes) -> str:
        """Parses plain text with multi-encoding fallback."""
        for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252", "ascii"):
            try:
                return content_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        return content_bytes.decode("utf-8", errors="replace")

    @classmethod
    def _parse_json(cls, content_bytes: bytes) -> str:
        """Parses JSON contract files or returns pretty-printed contract content."""
        import json
        text = cls._parse_plain_text(content_bytes)
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                # If JSON has 'content', 'raw_text', or 'text', use that directly
                for key in ("content", "raw_text", "text", "contract_text"):
                    if key in data and isinstance(data[key], str):
                        return data[key]
            return json.dumps(data, indent=2)
        except Exception:
            return text

    @classmethod
    def _detect_title(cls, filename: str, paragraphs: List[str]) -> str:
        """Infers an appropriate contract title from first headings or filename."""
        if paragraphs:
            first = paragraphs[0].strip()
            # If the first paragraph is short and looks like a title
            if 5 < len(first) < 100 and not first.endswith("."):
                return first
        
        # Clean filename
        clean_name = re.sub(r"\.[^.]+$", "", filename)
        clean_name = clean_name.replace("_", " ").replace("-", " ").title()
        return clean_name or "Enterprise Commercial Agreement"

    @classmethod
    def _detect_parties(cls, text: str) -> List[str]:
        """Detects potential contracting parties mentioned in preamble."""
        preamble = text[:1500]
        # Match patterns like: Acme Corp ("Customer") and NovaCloud Inc ("Vendor")
        parties = []
        matches = re.findall(r"([A-Z][A-Za-z0-9\s,\.]{2,40}?)\s*\((?:\"|')(?:Customer|Vendor|Client|Provider|Licensor|Licensee|Party A|Party B)(?:\"|')\)", preamble)
        for m in matches:
            clean = m.strip(" ,")
            if clean and clean not in parties:
                parties.append(clean)
        return parties
