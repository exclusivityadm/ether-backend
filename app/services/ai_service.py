from typing import Optional

from openai import OpenAI

from app.core.config import get_settings
from app.schemas.ai import ChatRequest, ChatResponse


settings = get_settings()


class AIService:
    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            self.client: Optional[OpenAI] = None
        else:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def is_configured(self) -> bool:
        return self.client is not None

    async def chat(self, payload: ChatRequest) -> ChatResponse:
        if not self.client:
            return ChatResponse(content="AI is not configured.")

        messages = [{"role": m.role, "content": m.content} for m in payload.messages]

        response = await self.client.chat.completions.create(  # type: ignore[attr-defined]
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=settings.OPENAI_TEMPERATURE,
        )

        content = response.choices[0].message.content or ""
        return ChatResponse(content=content)


ai_service = AIService()
