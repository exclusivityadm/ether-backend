import logging
from typing import Any, Dict, Optional

from openai import OpenAI

from app.core.config import get_settings

logger = logging.getLogger("ether.ai")


def get_client() -> Optional[OpenAI]:
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set; AI endpoints will return 503.")
        return None
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def run_chat(prompt: str, context: Optional[Dict[str, Any]] = None) -> dict[str, Any]:
    """Call OpenAI chat completion with a very small, safe wrapper.

    If there is any config or network error, we catch it and return a structured
    error instead of crashing the API.
    """
    settings = get_settings()
    client = get_client()
    if client is None:
        return {
            "ok": False,
            "error": "OPENAI_API_KEY not configured",
        }

    system_parts = ["You are Ether, a receipt and document intelligence engine."]
    if context:
        system_parts.append(f"Context: {context}")
    system_prompt = "\n".join(system_parts)

    try:
        completion = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        message = completion.choices[0].message.content or ""
        return {
            "ok": True,
            "result": message,
            "model": completion.model,
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error calling OpenAI: %s", exc)
        return {
            "ok": False,
            "error": str(exc),
        }
