from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func, BigInteger
from app.db.base_class import Base


class AILog(Base):
    __tablename__ = "ai_logs"

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=True)

    model = Column(String(100), nullable=False)
    prompt_preview = Column(Text, nullable=True)
    input_tokens = Column(BigInteger, nullable=True)
    output_tokens = Column(BigInteger, nullable=True)
    latency_ms = Column(BigInteger, nullable=True)
    trace_id = Column(String(64), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
