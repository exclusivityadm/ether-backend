from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class EmbeddingUpsertRequest(BaseModel):
    entity_type: str = Field(..., description="e.g. customer, merchant, product, order")
    entity_id: str = Field(..., description="Stable ID for the entity")
    text: str = Field(..., description="Content to embed")
    namespace: str = Field("global", description="Logical app/tenant namespace")
    model: str = Field("text-embedding-3-large", description="Embedding model name")


class EmbeddingRead(BaseModel):
    id: int
    entity_type: str
    entity_id: str
    namespace: str
    model: str
    dim: int

    model_config = ConfigDict(from_attributes=True)


class EmbeddingSearchRequest(BaseModel):
    entity_type: str = Field(..., description="Type of entity to search over")
    namespace: str = Field("global", description="Namespace to restrict search to")
    query_text: str = Field(..., description="Natural language query to embed and search with")
    top_k: int = Field(10, ge=1, le=100, description="Max results")


class EmbeddingSearchResult(BaseModel):
    embedding: EmbeddingRead
    score: float


class GraphEdgeCreate(BaseModel):
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    relation_type: str
    weight: float = 1.0
    extra_data: Optional[str] = Field(
        None,
        description="Optional JSON/text payload with additional context",
    )


class GraphEdgeRead(GraphEdgeCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class NeighborRead(BaseModel):
    edge: GraphEdgeRead
    neighbor_type: str
    neighbor_id: str
