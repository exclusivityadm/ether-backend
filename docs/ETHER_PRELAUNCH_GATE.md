# Ether Prelaunch Gate

Ether should be placed before Circa Haus launches. That makes Ether a prelaunch gate, not later infrastructure.

Circa Haus should not go live until Ether can prove the suite is reachable, configured, and able to perform real Supabase signal activity for the core projects.

## Gate purpose

Ether protects launch by proving:

- Ether deploys successfully
- Ether is sealed behind internal-token access
- Circa Haus is registered and signal-ready
- Exclusivity is registered and signal-ready
- real Supabase signal activity can be written into each connected project
- cron/manual keepalive operations work
- operations/audit visibility exists
- Sentinel remains disabled until admin controls are verified

## Required before Circa Haus launch

### 1. Ether deploys on Render

Required checks:

```text
GET /health
GET /health/deep
GET /version
```

Expected result:

- `/health` returns ok
- `/version` returns current Ether version
- `/health/deep` does not expose secrets

### 2. Ether internal access is sealed

Required checks:

- Internal routes reject requests with no internal token
- Internal routes reject invalid internal token
- Allowed sources are limited to launch needs
- Public-safe routes are only health/version/root

Internal routes include:

```text
/projects
/readiness
/operations/suite/status
/operations/suite/smoke
/operations/cron/status
/operations/cron/signal
/signal/handshake
/signal/heartbeat
```

### 3. Supabase SQL support is applied in connected projects

Apply this file inside both Circa Haus and Exclusivity Supabase projects:

```text
supabase/ether_signal_support.sql
```

This creates:

- `ether_signals` table
- supporting indexes
- RLS enabled with no client-facing policies
- `ether_signal(payload jsonb)` RPC

### 4. Render env is wired for Circa Haus and Exclusivity

Ether needs server-side project variables for both projects:

```text
CIRCA_HAUS_SUPABASE_URL
CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY
CIRCA_HAUS_ETHER_SIGNAL_SECRET
CIRCA_HAUS_SIGNAL_RPC
CIRCA_HAUS_SIGNAL_TABLE

EXCLUSIVITY_SUPABASE_URL
EXCLUSIVITY_SUPABASE_SERVICE_ROLE_KEY
EXCLUSIVITY_ETHER_SIGNAL_SECRET
EXCLUSIVITY_SIGNAL_RPC
EXCLUSIVITY_SIGNAL_TABLE
```

The service role keys must exist only in Ether/Render/server-side settings. They must never be placed in Flutter, web clients, or public code.

### 5. Readiness passes

Check:

```text
GET /operations/suite/status
GET /operations/cron/status
GET /readiness/circa_haus
GET /readiness/exclusivity
```

Required result:

- Circa Haus ready for real signal
- Exclusivity ready for real signal
- core_ready_for_cron = true
- no missing core projects

### 6. Manual suite smoke test passes

Run:

```text
POST /operations/suite/smoke
```

Required result:

- ok = true
- signal ok_count equals total
- Circa Haus signal write succeeds
- Exclusivity signal write succeeds
- audit snapshot shows the smoke test and project signal events

Then confirm inside each Supabase project:

```text
select * from public.ether_signals order by received_at desc limit 10;
```

### 7. Cron signal path passes

Run:

```text
POST /operations/cron/signal
```

Required result:

- ok = true
- Circa Haus signal row appears in its Supabase project
- Exclusivity signal row appears in its Supabase project
- audit summary shows cron signal event

### 8. Render Cron is configured

Use the script:

```text
scripts/ether_cron_signal.py
```

Recommended schedule:

```text
every 30 minutes
```

The cron job should call Ether's internal cron signal operation and verify success by status code + response body.

### 9. Sentinel remains gated

Before Circa Haus launch:

```text
ETHER_SENTINEL_AI_ENABLED=false
```

Do not enable AI Sentinel until:

- admin access controls are verified
- audit visibility is adequate
- quarantine/review behavior is understood
- no user-facing route exposes Sentinel internals

## Prelaunch gate pass/fail

Ether prelaunch gate passes only when:

- Ether deploys
- internal routes are protected
- Circa Haus readiness passes
- Exclusivity readiness passes
- suite smoke test succeeds
- cron signal succeeds
- rows appear in both Supabase projects
- no service-role key is exposed to client code
- Sentinel remains disabled until safe

## Launch blockers

Do not launch Circa Haus if:

- Ether cannot deploy
- Ether internal token is missing
- internal routes are public
- Circa Haus project is not signal-ready
- Exclusivity project is not signal-ready
- Supabase SQL support was not applied
- service-role keys are unavailable or exposed incorrectly
- `/operations/suite/smoke` fails after wiring
- `/operations/cron/signal` fails after wiring
- signal rows do not appear in Supabase
- Sentinel AI is enabled prematurely

## Why this matters

Ether in front of Circa Haus means the suite has a living operational spine before users arrive. The app is not just launched; it is watched, signaled, and kept alive from the start.
