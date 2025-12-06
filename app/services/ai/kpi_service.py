from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session

from app.db.models.receipt import Receipt
from app.schemas.ai import KPIInsight, KPIResponse


def compute_basic_kpis(db: Session) -> KPIResponse:
    receipts: List[Receipt] = db.query(Receipt).all()

    total_receipts = len(receipts)
    total_spend = float(
        sum((r.total or Decimal("0.00")) for r in receipts)
    )
    by_category = {}
    for r in receipts:
        cat = r.category or "uncategorized"
        by_category.setdefault(cat, 0.0)
        by_category[cat] += float(r.total or 0.0)

    insights = [
        KPIInsight(
            title="Receipt volume",
            description=f"You currently have {total_receipts} receipts stored.",
        ),
        KPIInsight(
            title="Total spend",
            description=f"Your tracked total spend is approximately {total_spend:.2f}.",
        ),
    ]

    return KPIResponse(
        time_range="all_time",
        total_receipts=total_receipts,
        total_spend=total_spend,
        by_category=by_category,
        insights=insights,
    )
