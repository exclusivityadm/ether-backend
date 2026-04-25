# Ether v2 Backend

This is a clean, self-contained FastAPI backend for Ether v2 with:

- Internal-only control plane foundation
- Health and deep-health endpoints
- Project bootstrap and project registry resolution
- Auth verification scaffold
- Provider and webhook routing scaffold
- Sentinel threat/quarantine scaffold
- Signal lane foundation for app authenticity handshake + keepalive sequencing
- SQLite dev database by default, Postgres-compatible for Supabase

## Local Dev Quickstart

1. Create and activate venv:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on `.env.example`.

4. Run:

   ```bash
   uvicorn app.main:app --reload
   ```

5. Visit:

   - API docs: http://127.0.0.1:8000/docs
   - Health: http://127.0.0.1:8000/health
   - Deep health: http://127.0.0.1:8000/health/deep

## Signal Lane Foundation

Ether now exposes the following internal-only Signal routes:

- `POST /signal/handshake`
- `POST /signal/heartbeat`
- `GET /signal/lanes`

Each project can optionally configure a per-project signal secret using either:

- `{PROJECT_SLUG}_ETHER_SIGNAL_SECRET`
- `{PROJECT_SLUG}_SIGNAL_SECRET`

Examples:

- `CIRCA_HAUS_ETHER_SIGNAL_SECRET`
- `EXCLUSIVITY_ETHER_SIGNAL_SECRET`
- `SOVA_ETHER_SIGNAL_SECRET`

Behavior:

- If no project signal secret is configured, Ether accepts the lane in `pending-secret` mode.
- If a project signal secret is configured, Ether requires proof-based verification for the lane to be accepted.
- Accepted heartbeats rotate the server nonce, giving the lane an evolving sequence for future proof checks.

## Current Completion Boundary

The Signal foundation is server-side ready.
What remains later is app-side wiring, real project secrets, and runtime verification from the workstation.
