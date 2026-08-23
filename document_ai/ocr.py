from pathlib import Path
from typing import Any, Dict

try:
    from PIL import Image
except ImportError:
    Image = None


class ImageOCR:
    """OCR and Image Intelligence Engine."""

    @staticmethod
    def extract_text_from_image(file_path: Path) -> Dict[str, Any]:
        if Image is None:
            return {
                "page_count": 1,
                "full_text": f"[Image OCR unavailable - Pillow not installed: {file_path.name}]",
                "pages": [],
                "error": "Pillow not installed",
                "disclaimer": "FICTIONAL DEMO DOCUMENT — NOT A REAL LEGAL RECORD",
            }
        try:
            image = Image.open(file_path)
            width, height = image.size
            
            # Simulated clean OCR metadata preservation
            extracted_text = f"[Image Document Exhibit: {file_path.name} | Resolution: {width}x{height}]"
            
            return {
                "page_count": 1,
                "full_text": extracted_text,
                "pages": [
                    {
                        "page_number": 1,
                        "text": extracted_text,
                        "width": width,
                        "height": height,
                        "ocr_engine": "Vision-OCR",
                    }
                ],
                "image_metadata": {
                    "format": image.format,
                    "mode": image.mode,
                    "dimensions": f"{width}x{height}",
                },
                "disclaimer": "FICTIONAL DEMO DOCUMENT — NOT A REAL LEGAL RECORD",
            }
        except Exception as e:
            return {
                "page_count": 1,
                "full_text": f"[Failed to read image: {str(e)}]",
                "pages": [],
                "error": str(e),
                "disclaimer": "FICTIONAL DEMO DOCUMENT — NOT A REAL LEGAL RECORD",
            }
