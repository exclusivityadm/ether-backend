from typing import Optional
from sqlalchemy.orm import Session
from .orchestrator import generate_reply


def nira_reply(
    db: Session,
    merchant_id: Optional[int],
    customer_id: Optional[int],
    user_message: str,
) -> str:
    return generate_reply(
        db=db,
        persona="nira",
        merchant_id=merchant_id,
        customer_id=customer_id,
        app_context="nirasova",
        user_message=user_message,
    )
