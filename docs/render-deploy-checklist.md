# Ether Render Deployment Checklist

Use this checklist when pushing Ether to Render.

## Do not paste these secrets into ChatGPT

Set these directly in Render only:

- `ETHER_INTERNAL_TOKEN`
- `CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY`
- `EXCLUSIVITY_SUPABASE_SERVICE_ROLE_KEY`
- `CIRCA_HAUS_ETHER_SIGNAL_SECRET`
- `EXCLUSIVITY_ETHER_SIGNAL_SECRET`
- provider API keys and webhook secrets

## Required Render environment values before signal verification

### Ether core

- `ETHER_ENVIRONMENT=production`
- `ETHER_VERSION=2.2.0-circa-haus-precredential`
- `ETHER_ALLOWED_SOURCES=exclusivity,circa_haus,admin`
- `ETHER_CORS_MODE=none`
- `ETHER_INTERNAL_TOKEN=<generate strong random value>`

### Circa Haus signal lane

- `CIRCA_HAUS_SUPABASE_URL=<project url>`
- `CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY=<service role key>`
- `CIRCA_HAUS_ETHER_SIGNAL_SECRET=<generate strong random value>`
- `CIRCA_HAUS_SIGNAL_RPC=ether_signal`
- `CIRCA_HAUS_SIGNAL_TABLE=ether_signals`

### Exclusivity signal lane

- `EXCLUSIVITY_SUPABASE_URL=<project url>`
- `EXCLUSIVITY_SUPABASE_SERVICE_ROLE_KEY=<service role key>`
- `EXCLUSIVITY_ETHER_SIGNAL_SECRET=<generate strong random value>`
- `EXCLUSIVITY_SIGNAL_RPC=ether_signal`
- `EXCLUSIVITY_SIGNAL_TABLE=ether_signals`

## Supabase SQL required in each connected project

Apply this file inside each Supabase project Ether should keep active:

```text
supabase/ether_signal_support.sql
```

Circa Haus already has an `ether_signals` table visible from the connected Supabase tool. Exclusivity still needs to be checked/applied from its own Supabase project dashboard if it is not connected here.

## Render deployment settings

The repo includes:

- `render.yaml`
- `runtime.txt`
- `requirements.txt`

Render should use:

```text
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health Check Path: /health
```

## Smoke checks after deploy

Replace `<ETHER_URL>` and `<ETHER_INTERNAL_TOKEN>`.

Public-safe checks:

```bash
curl <ETHER_URL>/health
curl <ETHER_URL>/version
```

Readiness checks:

```bash
curl -H "X-ETHER-INTERNAL-TOKEN: <ETHER_INTERNAL_TOKEN>" \
  -H "X-ETHER-SOURCE: admin" \
  <ETHER_URL>/readiness

curl -H "X-ETHER-INTERNAL-TOKEN: <ETHER_INTERNAL_TOKEN>" \
  -H "X-ETHER-SOURCE: admin" \
  <ETHER_URL>/readiness/circa_haus

curl -H "X-ETHER-INTERNAL-TOKEN: <ETHER_INTERNAL_TOKEN>" \
  -H "X-ETHER-SOURCE: admin" \
  <ETHER_URL>/readiness/exclusivity
```

Suite status:

```bash
curl -H "X-ETHER-INTERNAL-TOKEN: <ETHER_INTERNAL_TOKEN>" \
  -H "X-ETHER-SOURCE: admin" \
  <ETHER_URL>/operations/suite/status
```

Manual signal smoke test:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-ETHER-INTERNAL-TOKEN: <ETHER_INTERNAL_TOKEN>" \
  -H "X-ETHER-SOURCE: admin" \
  -d '{"project_slugs":["circa_haus","exclusivity"],"include_unconfigured":true,"signal_kind":"render_deploy_smoke","status":"ok"}' \
  <ETHER_URL>/operations/suite/smoke
```

Cron signal test:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-ETHER-INTERNAL-TOKEN: <ETHER_INTERNAL_TOKEN>" \
  -H "X-ETHER-SOURCE: admin" \
  -d '{"project_slugs":["circa_haus","exclusivity"],"signal_kind":"render_cron_test","status":"ok","include_unconfigured":false}' \
  <ETHER_URL>/operations/cron/signal
```

Signal health:

```bash
curl -H "X-ETHER-INTERNAL-TOKEN: <ETHER_INTERNAL_TOKEN>" \
  -H "X-ETHER-SOURCE: admin" \
  <ETHER_URL>/operations/signal/health
```

## Completion criteria

Ether is deploy-ready when:

- `/health` returns healthy.
- `/version` reports the expected version.
- `/readiness/circa_haus` shows Supabase URL + service role configured.
- `/readiness/exclusivity` shows Supabase URL + service role configured.
- `/operations/suite/smoke` verifies write + readback for both projects.
- `/operations/signal/health` has no launch-blocking signal issues.
- Signal rows appear in each project’s `public.ether_signals` table.

## Render Cron

After the web service is verified, add a Render Cron Job that calls:

```text
POST <ETHER_URL>/operations/cron/signal
```

Headers:

```text
Content-Type: application/json
X-ETHER-INTERNAL-TOKEN: <ETHER_INTERNAL_TOKEN>
X-ETHER-SOURCE: admin
```

Body:

```json
{"project_slugs":["circa_haus","exclusivity"],"signal_kind":"render_cron_keepalive","status":"ok","include_unconfigured":false}
```

Recommended cadence: every 10 to 15 minutes while protecting paused projects.
