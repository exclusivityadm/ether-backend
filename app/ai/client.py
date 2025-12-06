import time
import logging
from typing import Optional

from openai import OpenAI
from app.core.config import get_settings
from app.models.ai_log import AILog
from sqlalchemy.orm import Session

logger = logging.getLogger("ether.ai")


class AIClient:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.OPENAI_API_KEY:
            self._client: Optional[OpenAI] = None
            logger.warning("OPENAI_API_KEY not configured; AI features will be disabled.")
        else:
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = settings.OPENAI_MODEL
        self._temperature = settings.OPENAI_TEMPERATURE

    def is_enabled(self) -> bool:
        return self._client is not None

    def chat(
        self,
        prompt: str,
        db: Optional[Session] = None,
        trace_id: Optional[str] = None,
        max_tokens: int = 512,
    ) -> tuple[str, dict]:
        if not self._client:
            raise RuntimeError("AI client not configured (missing OPENAI_API_KEY).")

        start = time.perf_counter()

        completion = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Ether, an internal assistant helping summarize and analyze receipts, "
                        "expenses, and merchant financial context. Keep answers short, clear, and focused."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=self._temperature,
        )

        latency_ms = int((time.perf_counter() - start) * 1000)
        choice = completion.choices[0]
        answer = choice.message.content or ""
        usage = completion.usage or None

        meta = {
            "model": self._model,
            "latency_ms": latency_ms,
            "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
            "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
        }

        if db is not None:
            log = AILog(
                model=self._model,
                prompt_preview=prompt[:500],
                input_tokens=meta["prompt_tokens"],
                output_tokens=meta["completion_tokens"],
                latency_ms=latency_ms,
                trace_id=trace_id,
            )
            db.add(log)
            db.commit()

        logger.info(
            "AI call finished: model=%s latency=%sms prompt_tokens=%s completion_tokens=%s",
            self._model,
            latency_ms,
            meta["prompt_tokens"],
            meta["completion_tokens"],
        )
        return answer, meta


_ai_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client
