from typing import List, Optional

from pydantic import BaseModel


class SummaryRequest(BaseModel):
    text: str
    focus: Optional[str] = None


class SummaryResponse(BaseModel):
    summary: str
    model: str


class KPIInsight(BaseModel):
    title: str
    description: str


class KPIResponse(BaseModel):
    time_range: str
    total_receipts: int
    total_spend: float
    by_category: dict
    insights: List[KPIInsight]
