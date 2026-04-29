# Ether Deployment / Production Verification

This is the final Ether production gate for placing Ether before Circa Haus launch.

It combines deployment readiness, environment readiness, Supabase signal verification, provider readiness, webhook trust, Sentinel state, control-plane blockers, audit visibility, and cron/smoke checks into one go/no-go lane.

## Main routes

```text
GET  /health
GET  /health/deep
GET  /version
GET  /operations/production/gate
GET  /operations/production/checklist
GET  /operations/suite/status
POST /operations/suite/smoke
GET  /operations/cron/status
POST /operations/cron/signal
GET  /operations/signal/health
GET  /controls/blockers
GET  /providers/readiness/suite
GET  /sentinel/status
GET  /webhooks/status
```

All production verification routes beyond `/health`, `/health/deep`, `/version`, and `/` are internal-only and require the Ether internal token.

## Production gate

Route:

```text
GET /operations/production/gate
```

Expected launch result:

```json
{
  "decision": "go",
  "launch_ready": true,
  "blocker_count": 0
}
```

If the decision is:

```text
no-go
```

clear every listed blocker before placing Ether in front of Circa Haus.

## What the production gate checks

The production gate checks:

- required Ether server env
- Circa Haus Supabase signal env
- Exclusivity Supabase signal env
- Circa Haus provider webhook signature env
- project/provider control blockers
- provider readiness blockers
- Sentinel launch blockers
- verified signal health
- webhook rejection/signature blockers
- audit visibility snapshot

## Required production environment

### Core Ether

```text
ETHER_INTERNAL_TOKEN
ETHER_ALLOWED_SOURCES
```

### Circa Haus signal lane

```text
CIRCA_HAUS_SUPABASE_URL
CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY
CIRCA_HAUS_SIGNAL_RPC=ether_signal
CIRCA_HAUS_SIGNAL_TABLE=ether_signals
```

### Exclusivity signal lane

```text
EXCLUSIVITY_SUPABASE_URL
EXCLUSIVITY_SUPABASE_SERVICE_ROLE_KEY
EXCLUSIVITY_SIGNAL_RPC=ether_signal
EXCLUSIVITY_SIGNAL_TABLE=ether_signals
```

### Circa Haus live webhook trust

```text
CIRCA_HAUS_STRIPE_WEBHOOK_SECRET
CIRCA_HAUS_CANVA_WEBHOOK_SECRET
CIRCA_HAUS_APLIIQ_WEBHOOK_SECRET
CIRCA_HAUS_PRINTFUL_WEBHOOK_SECRET
```

Expected but not hard-blocking in all cases:

```text
CIRCA_HAUS_TWILIO_AUTH_TOKEN
CIRCA_HAUS_ETHER_SIGNAL_SECRET
EXCLUSIVITY_ETHER_SIGNAL_SECRET
```

## Required Supabase SQL

Apply this file to both connected Supabase projects:

```text
supabase/ether_signal_support.sql
```

Required projects:

```text
Circa Haus
Exclusivity
```

The gate requires verified signal activity, which means Ether must be able to write and read back rows from each project.

## Render deployment

Recommended Render web service settings:

```text
Runtime: Python
Build command: pip install -r requirements.txt
Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health check path: /health
```

Recommended service name:

```text
ether-backend
```

Recommended cron schedule after wiring:

```text
every 30 minutes
```

Cron runner:

```text
scripts/ether_cron_signal.py
```

Required cron env:

```text
ETHER_BASE_URL
ETHER_INTERNAL_TOKEN
ETHER_CRON_SOURCE=admin
ETHER_CRON_PROJECTS=circa_haus,exclusivity
ETHER_CRON_TIMEOUT_SECONDS=30
```

## Production smoke-test runner

Script:

```text
scripts/ether_production_smoke.py
```

Required local or Render shell env:

```text
ETHER_BASE_URL
ETHER_INTERNAL_TOKEN
ETHER_SMOKE_SOURCE=admin
ETHER_SMOKE_TIMEOUT_SECONDS=45
```

Run:

```bash
python scripts/ether_production_smoke.py
```

The smoke runner checks:

- health
- version
- production gate before smoke
- suite status
- cron status
- controls blockers
- provider readiness
- Sentinel status
- webhook status
- suite smoke
- cron signal
- signal health
- production gate after smoke

The script exits nonzero if the final production gate is not `go`.

## Manual wiring-day sequence

1. Deploy Ether to Render.
2. Confirm:

```text
GET /health
GET /version
```

3. Add all required Render env vars.
4. Apply Supabase SQL in Circa Haus and Exclusivity.
5. Check:

```text
GET /operations/production/checklist
```

6. Run:

```text
POST /operations/suite/smoke
```

7. Run:

```text
POST /operations/cron/signal
```

8. Check:

```text
GET /operations/signal/health
```

9. Check:

```text
GET /controls/blockers
GET /providers/readiness/suite
GET /sentinel/status
GET /webhooks/status
```

10. Final check:

```text
GET /operations/production/gate
```

Launch only if:

```text
decision = go
```

## Launch blockers

Do not place Ether in front of Circa Haus if any of these are true:

- `/operations/production/gate` returns `no-go`
- Ether internal token is missing
- Circa Haus Supabase signal env is missing
- Exclusivity Supabase signal env is missing
- signal SQL was not applied
- signal write/readback verification fails
- provider readiness has blockers
- webhook signature trust env is missing for live Circa Haus rails
- invalid webhook signatures are appearing after wiring
- Sentinel has open threats or active quarantines
- project/provider controls are disabled
- audit/control/signal stores are not initializing
- `/operations/suite/smoke` fails
- `/operations/cron/signal` fails after wiring

## What “go” means

A production gate `go` means Ether has no known blockers across the checks it can verify internally.

It does not mean external provider dashboards are configured correctly unless their live test events have been sent and accepted as trusted events.

Before live launch, confirm provider dashboards/webhooks independently:

- Stripe webhook endpoint points to Ether
- Canva webhook endpoint points to Ether, if used
- Apliiq webhook endpoint points to Ether, if available
- Printful webhook endpoint points to Ether
- Twilio webhook endpoint points to Ether, if used
- signed test events arrive as `accepted_verified`

## Final Ether-before-Circa-Haus standard

Ether is ready to sit in front of Circa Haus only when:

```text
GET /operations/production/gate
```

returns:

```text
decision = go
blocker_count = 0
launch_ready = true
```

and:

```text
POST /operations/suite/smoke
POST /operations/cron/signal
```

both succeed after real credentials and Supabase SQL are wired.
