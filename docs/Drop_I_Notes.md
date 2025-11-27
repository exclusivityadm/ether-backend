# Drop I — AI Engine Implementation (Ether)

This drop turns Ether from a purely structural API into a system with
a functional AI engine that Sova, Exclusivity, and Nira can call.

## What this drop includes

### 1. `app/services/ai_service.py`

A centralized AI service layer that:

- Wraps the `openai.OpenAI` client
- Defines `ChatMessage`, `ChatRequest`, and `ChatResponse` Pydantic models
- Exposes an `AIService` class with a `chat()` method
- Creates a shared `ai_service` instance for reuse across the app

It uses:

- `OPENAI_API_KEY` from the environment (already loaded via `load_dotenv()` in `app.main`)
- The `chat.completions.create` API for broad compatibility

### 2. `app/routers/ai.py`

A full replacement for the AI router that:

- Mounts under the `/ai` prefix
- Exposes a single `POST /ai/chat` endpoint
- Accepts a `ChatRequest` payload
- Returns a `ChatResponse` payload
- Delegates all logic to `ai_service.chat()`

This keeps the router thin and the service layer rich.

## Installation

1. Unzip this Drop I archive somewhere convenient.

2. Drag the **`app`** folder from the drop into your Ether project root:

   `C:/Users/pinks/Desktop/ether`

3. When prompted by Windows:

   - Choose **Merge** for folders
   - Choose **Replace** for:
     - `app/routers/ai.py`
     - `app/services/ai_service.py` (overwriting the earlier scaffold from Drop F)

After that, your project will contain:

```text
ether/
  app/
    routers/
      ai.py          # New, fully implemented AI router
    services/
      ai_service.py  # New, fully implemented AI service
```

## Behaviour

Once installed and with `OPENAI_API_KEY` set, you can:

- Start the server:
  ```bash
  uvicorn app.main:app --reload
  ```

- Call the AI endpoint (for example via curl or a REST client):

  ```bash
  POST http://localhost:8000/ai/chat
  Content-Type: application/json

  {
    "messages": [
      {"role": "system", "content": "You are Ether, a helpful assistant."},
      {"role": "user", "content": "Say hello in one short sentence."}
    ],
    "model": "gpt-4.1-mini",
    "temperature": 0.2
  }
  ```

- Receive a structured `ChatResponse` with:
  - `content`: the model's reply
  - `model`: the actual model used
  - `finish_reason`: if provided by the API

This makes Ether "AI-complete enough" for:

- Sova to start delegating assistant-style queries
- Exclusivity to later send loyalty/commerce prompts
- NiraSova OS to leverage a shared AI subsystem

## Notes

- No other routers or modules are modified by this drop.
- No new dependencies are introduced beyond the existing `openai` package you already have installed.
- Future drops (Embeddings, CRM, Merchant system) will build on this foundation.
