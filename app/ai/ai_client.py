from typing import List, Dict, Optional
from openai import OpenAI

from app.config import settings

# Single shared OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)


def run_chat_completion(
    messages: List[Dict[str, str]],
    system_prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: int = 1024,
) -> str:
    """Thin wrapper around OpenAI Chat Completions API (sync).

    Uses GPT-5.1 'latest' model by default, but allows override via settings.
    """
    model_name = model or getattr(settings, "OPENAI_MODEL_NAME", None) or "gpt-4.1-mini"

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "system", "content": system_prompt}] + messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # Standard Chat Completions response shape
    content = response.choices[0].message.content
    return content.strip() if content else ""
