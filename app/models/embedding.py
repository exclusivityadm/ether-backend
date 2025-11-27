from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.sql import func

from app.db import Base


class EntityEmbedding(Base):
    """Stores embeddings for any entity (customer, merchant, product, order, etc.)."""

    __tablename__ = "unify_entity_embeddings"

    id = Column(Integer, primary_key=True, index=True)

    entity_type = Column(String, index=True, nullable=False)
    entity_id = Column(String, index=True, nullable=False)
    namespace = Column(String, index=True, nullable=False, default="global")

    model = Column(String, nullable=False)
    dim = Column(Integer, nullable=False)

    # Comma-separated floats
    vector = Column(Text, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )


class GraphEdge(Base):
    """Lightweight memory graph edge between two logical nodes."""

    __tablename__ = "unify_memory_edges"

    id = Column(Integer, primary_key=True, index=True)

    source_type = Column(String, index=True, nullable=False)
    source_id = Column(String, index=True, nullable=False)

    target_type = Column(String, index=True, nullable=False)
    target_id = Column(String, index=True, nullable=False)

    relation_type = Column(String, index=True, nullable=False)
    weight = Column(Float, nullable=False, default=1.0)

    extra_data = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
