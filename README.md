# Ether v2 Backend

Ether is the internal control, signal, and security layer for the broader app suite. Its immediate launch purpose is to support Circa Haus, preserve Exclusivity, keep connected Supabase projects active through real, meaningful signal activity, and provide the protected Phantom Core safety floor for dangerous infrastructure operations.

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
- Phantom Core always-on gate for dangerous/sovereignty-critical writes
- Phantom emergency containment and recovery flow
- Phantom keepalive second safety lane
- SQLite dev database by default, Postgres-compatible for Supabase

## Launch Protocol Boundary

This branch is not an MVP branch. It is the Ether / Phantom Core launch-hardening branch for the current Circa Haus prelaunch sequence.

Locked launch doctrine:

- Phantom Core is absorbed into Ether as protected internal infrastructure.
- Phantom Core is not a public product, not a normal feature, and not casually disableable.
- Phantom Core remains always on for observation, audit, health, and dangerous-write gating.
- Emergency Containment / All Stop means activating containment mode, not turning Phantom Core off.
- Safe reads/status/support should remain available when practical.
- Dangerous writes, sovereignty-critical writes, ownership/key/config changes, provider controls, payout rails, and policy overrides must be gated.
- Circa Haus does not get a global collapse button; app-level operations should use maintenance, read-only, payment pause, payout pause, and incident banner modes.

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
- `GET /controls`
- `GET /controls/summary`
- `GET /controls/blockers`
- `GET /controls/impact/{project_slug}`
- `GET /controls/recovery/{project_slug}`
- `POST /controls/recover`
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
- `GET /operations/suite/status`
- `GET /operations/production/checklist`
- `GET /operations/production/gate`
- `GET /operations/cron/status`
- `POST /operations/cron/signal`

## Phantom Core

Phantom Core is Ether's protected internal safety floor. It is responsible for evaluating dangerous and sovereignty-critical operations before mutation.

Current Phantom modes:

- `normal`
- `degraded`
- `safe_mode`
- `owner_recovery`
- `emergency_containment`
- `locked`

Current gate decisions:

- `allow` — operation may proceed.
- `pause` — operation is contained before mutation and requires review/recovery.
- `deny` — operation cannot proceed in the current safety state.

Current severity classes:

- `read`
- `harmless_write`
- `reversible_write`
- `irreversible_write`
- `sovereignty_critical`

Phantom routes:

- `GET /phantom/status`
- `GET /phantom/health`
- `POST /phantom/gate`
- `POST /phantom/containment`
- `POST /phantom/recovery`
- `GET /phantom/events`
- `GET /phantom/invariants`

Phantom keepalive routes:

- `GET /phantom/keepalive/status`
- `POST /phantom/keepalive/run`
- `POST /phantom/keepalive/configure`

Phantom Core protects control mutations before state changes. These routes are currently gated before control-plane mutation:

- `POST /controls/recover`
- `POST /controls/project/disable`
- `POST /controls/project/enable`
- `POST /controls/provider/disable`
- `POST /controls/provider/enable`

If Phantom Core does not return `allow`, the route returns `ETHER_PHANTOM_CORE_PAUSED_ACTION` and no control-plane mutation should occur.

## Emergency Containment / All Stop

All Stop does not disable Phantom Core. It activates Emergency Containment.

During Emergency Containment:

- Phantom Core remains on.
- Observation continues.
- Health/status routes continue.
- Audit logging continues.
- Safe reads should remain available where practical.
- Dangerous writes are paused.
- Sovereignty-critical writes are paused.
- Recovery requires recorded authority context and audit trail.

No route should provide a casual permanent off-switch for Phantom Core observation or logging.

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

## Phantom Keepalive Lane

Phantom Keepalive is the second safety lane:

```text
Phantom Core -> Ether -> Supabase
```

Normal app/Ether signal lane remains separate:

```text
Circa Haus / Exclusivity / Sova -> Ether -> Supabase
```

The Phantom lane:

- runs through Ether's existing real Supabase signal mechanism
- uses `signal_kind: phantom_keepalive`
- uses `signal_source: phantom_core`
- uses `app_id: ether.phantom_core`
- uses `instance_id: phantom-core-primary`
- defaults to a 55-minute interval
- records not-configured or failed state visibly instead of crashing Ether
- is shown in `/phantom/keepalive/status`, `/operations/suite/status`, `/operations/cron/status`, and `/operations/production/gate`

Do not reduce the interval aggressively. The lane should provide meaningful activity without spamming Supabase.

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

## Production Gate / Wiring Day Checklist

Use these routes before placing Ether in front of Circa Haus launch traffic:

- `GET /operations/suite/status`
- `GET /operations/production/checklist`
- `GET /operations/production/gate`
- `GET /operations/cron/status`
- `POST /operations/suite/smoke`
- `POST /operations/cron/signal`
- `GET /phantom/status`
- `GET /phantom/events`
- `GET /phantom/invariants`
- `GET /phantom/keepalive/status`
- `POST /phantom/keepalive/run`
- `GET /controls/summary`
- `GET /controls/blockers`

Production gate must remain `no-go` if:

- required environment variables are missing
- provider readiness has launch blockers
- normal signal lane has not been verified
- control plane has disabled project/provider blockers
- Sentinel has unresolved threats/quarantines
- webhook signature/control failures are present
- Phantom Core is in `locked`, `degraded`, `safe_mode`, or `emergency_containment`
- Phantom Core has active containments
- Phantom keepalive is failing

## Current Completion Boundary

Ether now has:

- internal project registry
- Circa Haus launch-scope registry alignment
- signal handshake/heartbeat lanes
- real Supabase signal write attempts
- readiness endpoints
- Supabase SQL support for signal persistence
- env placeholders for Circa Haus, Exclusivity, and future Sova
- Phantom Core always-on gate
- Phantom emergency containment and recovery routes
- Phantom keepalive second safety lane
- Phantom status surfaced through controls, operations, cron, and production gate routes
- dangerous control mutations gated before mutation

Still required before production use:

- deploy to Render
- set real server-side environment values
- apply `supabase/ether_signal_support.sql` inside Circa Haus and Exclusivity Supabase projects
- verify `/readiness/circa_haus` and `/readiness/exclusivity`
- test `/signal/handshake` and `/signal/heartbeat`
- run `/operations/suite/smoke`
- run `/operations/cron/signal`
- run `/phantom/keepalive/run`
- confirm `/operations/production/gate` returns `decision=go`
- confirm signal rows appear in each connected Supabase project
- keep Sentinel AI disabled until admin controls and review flow are verified
