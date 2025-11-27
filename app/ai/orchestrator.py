from typing import Optional

from sqlalchemy.orm import Session

from .ai_client import run_chat_completion
from .prompts import PERSONA_PROMPTS
from .memory import store_memory, load_memory


def generate_reply(
    *,
    db: Session,
    persona: str,
    merchant_id: Optional[int],
    customer_id: Optional[int],
    app_context: Optional[str],
    user_message: str,
) -> str:
    """Central orchestration function for Ether AI.

    - Picks the right system prompt for the persona
    - Optionally loads prior context from memory
    - Calls OpenAI
    - Stores the latest exchange in memory
    """
    persona_key = persona or "global"
    system_prompt = PERSONA_PROMPTS.get(persona_key, PERSONA_PROMPTS["global"])

    history_snippet = load_memory(
        db=db,
        persona=persona_key,
        merchant_id=merchant_id,
        customer_id=customer_id,
        app_context=app_context,
        key="last_turn",
    )

    messages = []
    if history_snippet:
        messages.append(
            {
                "role": "assistant",
                "content": f"Previous context summary: {history_snippet}",
            }
        )

    messages.append({"role": "user", "content": user_message})

    reply = run_chat_completion(
        messages=messages,
        system_prompt=system_prompt,
    )

    # Store short summary of the latest exchange
    compact = f"User: {user_message[:500]} | Assistant: {reply[:500]}"
    store_memory(
        db=db,
        persona=persona_key,
        merchant_id=merchant_id,
        customer_id=customer_id,
        app_context=app_context,
        key="last_turn",
        value=compact,
    )

    return reply
