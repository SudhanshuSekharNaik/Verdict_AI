import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import pymupdf
except ImportError:
    pymupdf = None


class DocumentParser:
    """Document AI Parser supporting PDF, Images, Plain Text, and DOCX."""

    @staticmethod
    def calculate_hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def parse_pdf(file_path: Path) -> Dict[str, Any]:
        if pymupdf is None:
            return DocumentParser.parse_text(file_path)
        doc = pymupdf.open(file_path)
        pages_data: List[Dict[str, Any]] = []
        full_text_list: List[str] = []

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            text = page.get_text()
            rect = page.rect
            pages_data.append({
                "page_number": page_idx + 1,
                "text": text,
                "char_count": len(text),
                "width": rect.width,
                "height": rect.height,
            })
            full_text_list.append(text)

        full_text = "\n\n".join(full_text_list)
        return {
            "page_count": len(doc),
            "full_text": full_text,
            "pages": pages_data,
            "disclaimer": "FICTIONAL DEMO DOCUMENT — NOT A REAL LEGAL RECORD",
        }

    @staticmethod
    def parse_text(file_path: Path) -> Dict[str, Any]:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        return {
            "page_count": 1,
            "full_text": text,
            "pages": [{"page_number": 1, "text": text, "char_count": len(text)}],
            "disclaimer": "FICTIONAL DEMO DOCUMENT — NOT A REAL LEGAL RECORD",
        }

    @staticmethod
    def parse_file(file_path: Path, mime_type: Optional[str] = None) -> Dict[str, Any]:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf" or mime_type == "application/pdf":
            return DocumentParser.parse_pdf(file_path)
        elif suffix in [".txt", ".md", ".json", ".csv"]:
            return DocumentParser.parse_text(file_path)
        elif suffix in [".png", ".jpg", ".jpeg"]:
            # Image OCR Fallback
            from document_ai.ocr import ImageOCR
            return ImageOCR.extract_text_from_image(file_path)
        else:
            return DocumentParser.parse_text(file_path)
