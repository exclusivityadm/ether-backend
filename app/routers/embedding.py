
from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from app.embedding.service import EmbedRequest, EmbedResponse, generate_embeddings

router = APIRouter(prefix="/embedding", tags=["embedding"])

@router.post("/generate", response_model=EmbedResponse)
async def embed(req: EmbedRequest) -> EmbedResponse:
    try:
        return generate_embeddings(req)
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding error: {e}",
        )
