from typing import Optional

from app.services.logging.log_service import log_event


def extract_text_from_image(image_path: str) -> Optional[str]:
    """Stub OCR extractor.

    In v2 we leave this as a simple placeholder that pretends OCR succeeded.
    Later we can wire real OCR (Tesseract, AWS Textract, etc).
    """
    log_event("ocr_extracted_stub", {"image_path": image_path})
    # For now just return a friendly stub
    return f"STUB_OCR_TEXT for {image_path}"
