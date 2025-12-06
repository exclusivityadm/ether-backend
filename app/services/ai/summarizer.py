from typing import Optional

from app.core.config import get_settings
from app.services.logging.log_service import log_event

settings = get_settings()


def summarize_text(text: str, focus: Optional[str] = None) -> str:
    """Stub summary engine.

    In v2 we keep this offline-friendly. If OpenAI_API_KEY is not set,
    we return a deterministic stitched summary instead of calling OpenAI.
    """
    log_event("ai_summarize_requested", {"focus": focus})

    if not settings.OPENAI_API_KEY:
        snippet = text[:400].replace("\n", " ")
        if focus:
            return f"(offline summary – focus: {focus}) {snippet}"
        return f"(offline summary) {snippet}"

    # Placeholder for future OpenAI wiring
    # We intentionally don't import openai here yet to avoid extra dependency.
    snippet = text[:800].replace("\n", " ")
    return f"(online summary placeholder) {snippet}"
