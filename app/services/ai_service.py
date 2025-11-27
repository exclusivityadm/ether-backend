
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY missing")

_client=OpenAI(api_key=OPENAI_API_KEY)

class ChatRequest(BaseModel):
    messages:list[dict]
    model:str="gpt-4o-mini"

class ChatResponse(BaseModel):
    response_text:str
    model:str

def ai_service(payload:ChatRequest)->ChatResponse:
    completion=_client.chat.completions.create(
        model=payload.model,
        messages=payload.messages
    )
    reply=completion.choices[0].message["content"]
    return ChatResponse(response_text=reply, model=payload.model)
