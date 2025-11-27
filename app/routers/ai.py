"""AI router for Ether.

This router exposes a simple, generic chat endpoint that:
- Accepts a list of messages (system/user/assistant)
- Delegates to the AIService
- Returns the model's reply as structured data

It is designed to be product-agnostic, so Sova, Exclusivity, and Nira
can all call the same endpoint with their own system prompts.
"""

from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from app.services.ai_service import ChatRequest, ChatResponse, ai_service

router = APIRouter(
    prefix="/ai",
    tags=["ai"],
)


@router.post("/chat", response_model=ChatResponse, summary="Generic AI chat endpoint")
async def ai_chat(payload: ChatRequest) -> ChatResponse:
    """Send a chat-style prompt to the AI engine and get a reply.

    This is intentionally generic so that:
    - Sova can send POS-related context
    - Exclusivity can send loyalty/commerce context
    - NiraSova OS can send system-wide context

    The responsibilities are:
    - Validate request structure
    - Delegate to AIService
    - Handle and surface any errors cleanly
    """
    try:
        return ai_service.chat(payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {exc}",
        )
