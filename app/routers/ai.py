from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.context.deps import get_db, get_current_merchant
from app.ai import get_ai_client, build_merchant_context
from app.schemas.ai import AIPrompt, AIResponse
from app.models.merchant import Merchant

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/assist", response_model=AIResponse)
def assist(
    payload: AIPrompt,
    db: Session = Depends(get_db),
    merchant: Merchant = Depends(get_current_merchant),
) -> AIResponse:
    client = get_ai_client()
    if not client.is_enabled():
        raise HTTPException(
            status_code=503,
            detail="AI is not configured (OPENAI_API_KEY not set).",
        )

    context = build_merchant_context(db, merchant)
    prompt = f"""Context:
{context}

User question:
{payload.query}
"""

    answer, meta = client.chat(prompt, db=db)
    return AIResponse(
        answer=answer,
        model=meta.get("model", ""),
        prompt_tokens=meta.get("prompt_tokens"),
        completion_tokens=meta.get("completion_tokens"),
    )
