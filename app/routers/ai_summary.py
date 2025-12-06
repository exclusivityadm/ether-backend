from fastapi import APIRouter

from app.schemas.ai import SummaryRequest, SummaryResponse
from app.services.ai.summarizer import summarize_text

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/summary", response_model=SummaryResponse)
def create_summary(payload: SummaryRequest) -> SummaryResponse:
    summary = summarize_text(payload.text, focus=payload.focus)
    return SummaryResponse(summary=summary, model="stub-or-openai")
