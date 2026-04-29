# Ether Signal / Keepalive Verification

This is the verified keepalive capability for Ether.

It upgrades Ether from “attempting a signal write” to proving that a signal was written and then visible through readback.

## Purpose

Ether should sit before Circa Haus launches. Its keepalive/signaling layer must prove:

- the project is configured
- the signal write succeeds
- the signal can be read back from Supabase
- the verified run is stored locally
- cron status can show last success/failure
- launch can be blocked when core projects have no verified signal

Core projects:

```text
circa_haus
exclusivity
```

## Main routes

```text
GET  /operations/signal/health
GET  /operations/signal/history
GET  /operations/cron/status
POST /operations/cron/signal
POST /operations/suite/smoke
POST /operations/signal/all
POST /operations/signal/{project_slug}
POST /signal/heartbeat
```

## Verification flow

For every accepted manual/cron/smoke signal and every accepted heartbeat:

1. Ether builds a signal payload.
2. Ether attempts Supabase RPC write through `ether_signal(payload)`.
3. If RPC fails, Ether falls back to table insert into `ether_signals`.
4. If write succeeds, Ether reads back from the project `ether_signals` table.
5. If a matching row is found, the run is marked verified.
6. Ether persists the run in the local signal run store.
7. Operations status exposes last success and last failure per project.

## Required Supabase support

Apply this file inside every connected Supabase project Ether should keep active:

```text
supabase/ether_signal_support.sql
```

That creates:

- `ether_signals` table
- indexes
- RLS enabled with no client-facing policies
- `ether_signal(payload jsonb)` RPC

## Required server env

For Circa Haus:

```text
CIRCA_HAUS_SUPABASE_URL
CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY
CIRCA_HAUS_SIGNAL_RPC=ether_signal
CIRCA_HAUS_SIGNAL_TABLE=ether_signals
```

For Exclusivity:

```text
EXCLUSIVITY_SUPABASE_URL
EXCLUSIVITY_SUPABASE_SERVICE_ROLE_KEY
EXCLUSIVITY_SIGNAL_RPC=ether_signal
EXCLUSIVITY_SIGNAL_TABLE=ether_signals
```

Service role keys must remain server-side in Ether/Render only.

## Local signal run storage

Signal verification runs persist locally through:

```text
ETHER_SIGNAL_DB_PATH
```

Fallback:

```text
ETHER_AUDIT_DB_PATH
```

Then:

```text
runtime/ether_audit.sqlite3
```

Runtime files are ignored by Git.

## Health and launch blockers

Check suite signal health:

```text
GET /operations/signal/health
```

Check project-specific signal health:

```text
GET /operations/signal/health?project_slug=circa_haus
GET /operations/signal/health?project_slug=exclusivity
```

Launch-blocking conditions:

- no verified signal run for Circa Haus
- no verified signal run for Exclusivity
- write succeeds but readback fails
- Supabase env is missing
- Supabase SQL support is missing
- service role permissions fail

## History

List recent runs:

```text
GET /operations/signal/history
GET /operations/signal/history?project_slug=circa_haus
GET /operations/signal/history?verified_ok=false
```

Each run stores:

- project slug
- signal kind
- lane id
- status
- write result
- readback result
- verified result
- error
- payload summary
- recorded timestamp

## Cron flow

Check readiness:

```text
GET /operations/cron/status
```

Run cron signal manually:

```text
POST /operations/cron/signal
```

Expected after real wiring:

- `ok = true`
- `cron_ready_after_run = true`
- both core projects have verified signal runs
- `/operations/signal/health` has no launch blockers

## Smoke test flow

Run:

```text
POST /operations/suite/smoke
```

Expected:

- before summary included
- write + readback signal attempt included
- after summary included
- signal verification snapshot included
- audit snapshot included

## App heartbeat flow

App authenticity lanes use:

```text
POST /signal/handshake
POST /signal/heartbeat
```

Accepted heartbeats now also perform write + readback verification and persist the run.

## Failure diagnostics

If write fails:

- check Supabase URL
- check service role key
- check SQL/RPC exists
- check network/provider availability

If readback fails:

- check `ether_signals` table exists
- check table columns match the support SQL
- check service role permissions
- check that RPC/table fallback wrote the expected lane id and heartbeat count

If cron status is ready but not verified:

- run `/operations/cron/signal`
- inspect `/operations/signal/history?verified_ok=false`

## Prelaunch requirement

Before Circa Haus launches, Ether must show:

```text
GET /operations/signal/health
```

with no launch blockers for:

- Circa Haus
- Exclusivity

This proves Ether is not only deployed, but actively writing and verifying real signal activity into both connected Supabase projects.
