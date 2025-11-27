
from typing import List
from pydantic import BaseModel
from openai import OpenAI

_client = OpenAI()

class EmbedRequest(BaseModel):
    texts: List[str]
    model: str = "text-embedding-3-small"

class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    model: str

def generate_embeddings(req: EmbedRequest) -> EmbedResponse:
    resp = _client.embeddings.create(model=req.model, input=req.texts)
    return EmbedResponse(
        embeddings=[d.embedding for d in resp.data],
        model=resp.model
    )
