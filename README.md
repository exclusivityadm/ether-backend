# Ether v2 Backend

Ether is the internal control, signal, and security layer for the broader app suite. Its immediate launch purpose is to support Circa Haus, preserve Exclusivity, and keep connected Supabase projects active through real, meaningful signal activity.

This is a clean, self-contained FastAPI backend for Ether v2 with:

- Internal-only control plane foundation
- Health and deep-health endpoints
- Project bootstrap and project registry resolution
- Readiness endpoints for provider/signal configuration
- Auth verification scaffold
- Provider and webhook routing scaffold
- Sentinel threat/quarantine scaffold
- Signal lane foundation for app authenticity handshake + keepalive sequencing
- Real Supabase project signal writes on accepted heartbeats
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
   - Readiness: http://127.0.0.1:8000/readiness

## Core Routes

Public-safe health/version routes:

- `GET /`
- `GET /health`
- `GET /health/deep`
- `GET /version`

Internal routes:

- `GET /projects`
- `GET /projects/{project_slug}`
- `POST /projects/bootstrap`
- `GET /readiness`
- `GET /readiness/{project_slug}`
- `POST /signal/handshake`
- `POST /signal/heartbeat`
- `GET /signal/lanes`
- `POST /controls/project/disable`
- `POST /controls/project/enable`
- `POST /controls/provider/disable`
- `POST /controls/provider/enable`
- `GET /providers/{project_slug}`
- `POST /webhooks/{provider}/{project_slug}`
- `POST /sentinel/events`
- `POST /sentinel/review`
- `POST /sentinel/quarantine`
- `GET /sentinel/quarantines`

## Signal Lane Foundation

Ether exposes the following internal-only Signal routes:

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

## Real Supabase Project Signal Writes

Accepted heartbeats now attempt real Supabase project activity.

Ether uses project-specific environment variables:

- `{PROJECT_SLUG}_SUPABASE_URL`
- `{PROJECT_SLUG}_SUPABASE_SERVICE_ROLE_KEY`
- `{PROJECT_SLUG}_SIGNAL_RPC`
- `{PROJECT_SLUG}_SIGNAL_TABLE`

Default RPC/table names:

- RPC: `ether_signal`
- Table: `ether_signals`

Behavior:

1. Accepted heartbeat builds a signal payload.
2. Ether attempts to call the project RPC first.
3. If the RPC is unavailable, Ether falls back to inserting into the project signal table.
4. Heartbeat response includes `project_signal` so wiring day can see whether real project activity succeeded.

Supabase SQL support is included at:

```text
supabase/ether_signal_support.sql
```

Apply that SQL inside each connected Supabase project that Ether should keep active.

## Readiness Endpoints

Ether exposes readiness routes so deployment/wiring can verify configuration without exposing secrets:

- `GET /readiness`
- `GET /readiness/{project_slug}`

Useful checks:

```text
/readiness/circa_haus
/readiness/exclusivity
```

These show:

- project status
- enabled providers
- feature flags
- whether Supabase URL is configured
- whether service role key is configured
- whether signal secret is configured
- RPC/table target names
- whether the project is ready for real Supabase signal activity

## Current Completion Boundary

Ether now has:

- internal project registry
- Circa Haus launch-scope registry alignment
- signal handshake/heartbeat lanes
- real Supabase signal write attempts
- readiness endpoints
- Supabase SQL support for signal persistence
- env placeholders for Circa Haus, Exclusivity, and future Sova

Still required before production use:

- deploy to Render
- set real server-side environment values
- apply `supabase/ether_signal_support.sql` inside Circa Haus and Exclusivity Supabase projects
- verify `/readiness/circa_haus` and `/readiness/exclusivity`
- test `/signal/handshake` and `/signal/heartbeat`
- confirm signal rows appear in each connected Supabase project
- keep Sentinel AI disabled until admin controls and review flow are verified
