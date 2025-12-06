from __future__ import annotations
from typing import Dict, Any
import json
import logging
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger("ether.receipt_ai")

def extract_from_image(image_path: str) -> Dict[str, Any]:
    """
    Placeholder for AI-powered receipt extraction.

    Today:
      - Returns a dummy structure so the pipeline works end-to-end.

    Future:
      - Plug in OpenAI vision / OCR stack here.
    """
    settings = get_settings()
    logger.info("Running dummy AI extraction on %s", image_path)

    # Minimal stub result; adapt as needed
    result: Dict[str, Any] = {
        "vendor": None,
        "purchase_date": None,
        "total_amount": None,
        "currency": "USD",
        "category": None,
        "raw_text": f"AI parsing not yet implemented for {Path(image_path).name}",
        "items": [],
    }

    # If you later wire OpenAI, you can enrich `result` here.
    if settings.OPENAI_API_KEY:
        logger.info("OPENAI_API_KEY detected – ready for real integration when desired.")

    return result
