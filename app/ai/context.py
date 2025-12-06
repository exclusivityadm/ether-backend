from sqlalchemy.orm import Session
from app.models.merchant import Merchant
from app.models.receipt import Receipt


def build_merchant_context(db: Session, merchant: Merchant) -> str:
    receipts = (
        db.query(Receipt)
        .filter(Receipt.merchant_id == merchant.id)
        .order_by(Receipt.created_at.desc())
        .limit(10)
        .all()
    )
    lines: list[str] = [
        f"Merchant: {merchant.name} ({merchant.email or 'no-email'})",
        "",
        "Recent receipts:",
    ]
    if not receipts:
        lines.append("  - None yet.")
    else:
        for r in receipts:
            line = f"  - #{r.id} vendor={r.vendor_name or 'unknown'} total={r.total_amount or 'n/a'} status={r.status}"
            lines.append(line)
    return "\n".join(lines)
