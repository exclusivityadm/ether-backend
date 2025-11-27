from typing import Optional
from sqlalchemy.orm import Session
from .orchestrator import generate_reply


def runa_reply(
    db: Session,
    merchant_id: Optional[int],
    customer_id: Optional[int],
    user_message: str,
) -> str:
    return generate_reply(
        db=db,
        persona="runa",
        merchant_id=merchant_id,
        customer_id=customer_id,
        app_context="sova",
        user_message=user_message,
    )
