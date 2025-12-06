# Ether v2 Backend (A1–A10 Drop)

This is a clean, self-contained FastAPI backend for Ether v2 with:

- Health endpoint
- Merchant CRUD (minimal)
- Receipt ingestion + stub OCR + storage (local folder)
- AI summary stub
- Simple KPI aggregation from receipts
- Background scheduler with keepalive / OCR / metrics ticks
- CORS configured for localhost + Vercel by default
- SQLite dev database by default, Postgres-compatible for Supabase

## Local Dev Quickstart

1. Create and activate venv (you already did this):

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # on Windows
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Create a `.env` file based on `.env.example`.

4. Run:

   ```bash
   uvicorn app.main:app --reload
   ```

5. Visit:

   - API docs: http://127.0.0.1:8000/docs
   - Health:   http://127.0.0.1:8000/health
   - Example:  GET http://127.0.0.1:8000/api/merchants/me
