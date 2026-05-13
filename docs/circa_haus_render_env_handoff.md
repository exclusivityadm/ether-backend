# Circa Haus Render Environment Handoff

This file is the workstation checklist for bringing the deployed `ether-backend` Render service current for Circa Haus provider credentialing.

Do not paste real secrets into this file or commit secrets to GitHub. All real values belong in Render environment variables or the provider dashboards.

## Required sequence

1. Pull the latest `main` branch for `exclusivityadm/ether-backend`.
2. In Render, open the deployed `ether-backend` service.
3. Add/update the environment variables listed below.
4. Redeploy the service from the latest GitHub commit.
5. Verify `/health`, `/health/deep`, `/readiness`, `/readiness/circa_haus`, `/providers/readiness/circa_haus`, `/signal/handshake`, and `/signal/heartbeat`.
6. Confirm Circa Haus Supabase receives rows in `public.ether_signals`.

## Ether core

```text
ETHER_VERSION=2.2.0-circa-haus-precredential
ETHER_ENVIRONMENT=production
GIT_SHA=<latest deployed git sha>
ETHER_INTERNAL_TOKEN=<generate strong server-only token>
ETHER_ALLOWED_SOURCES=exclusivity,circa_haus,admin
ETHER_CORS_MODE=none
ETHER_CORS_ALLOW_ORIGINS=
ETHER_MAX_BODY_BYTES=1048576
ETHER_INGEST_RPM=120
ETHER_REPLAY_TTL_SECONDS=600
ETHER_ADMIN_AUDIT_LOG=true
ETHER_BOOTSTRAP_EXPOSE_PUBLIC_CONFIG=false
ETHER_PUBLIC_BASE_URL=<Render service URL or final Ether domain>
ETHER_CRON_SECRET=<generate strong cron-only token>
ETHER_PROJECT_REGISTRY_JSON=
ETHER_PROJECTS_JSON=
```

## Ghost Phantom / Phantom Core posture

```text
ETHER_SENTINEL_AI_ENABLED=false
ETHER_SENTINEL_AI_MODEL=gpt-5.5-thinking
PHANTOM_CORE_POLICY_VERSION=phantom-core-launch-v1
GHOST_PHANTOM_ENABLED=true
```

Keep Sentinel AI disabled until admin review controls and provider billing are verified.

## Circa Haus Supabase

```text
CIRCA_HAUS_SUPABASE_URL=<from Supabase project API settings>
CIRCA_HAUS_SUPABASE_ANON_KEY=<publishable/anon key from Supabase>
CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY=<server-only service role key>
CIRCA_HAUS_ETHER_SIGNAL_SECRET=<generate strong shared signal secret>
CIRCA_HAUS_SIGNAL_RPC=ether_signal
CIRCA_HAUS_SIGNAL_TABLE=ether_signals
```

The service role key must never go into Flutter, web frontend code, GitHub, or screenshots shared publicly.

## Stripe / payments

```text
CIRCA_HAUS_STRIPE_PUBLISHABLE_KEY=<Stripe publishable key>
CIRCA_HAUS_STRIPE_SECRET_KEY=<Stripe secret key>
CIRCA_HAUS_STRIPE_WEBHOOK_SECRET=<Stripe webhook signing secret>
CIRCA_HAUS_STRIPE_CONNECT_CLIENT_ID=<Stripe Connect client ID>
CIRCA_HAUS_STRIPE_PLATFORM_FEE_BPS=150
```

Webhook route to configure in Stripe after Ether redeploy:

```text
<ETHER_PUBLIC_BASE_URL>/webhooks/stripe/circa_haus
```

## Saia / OpenAI / image ideation

```text
CIRCA_HAUS_OPENAI_API_KEY=<server-only OpenAI API key>
CIRCA_HAUS_OPENAI_MODEL=gpt-5.5-thinking
CIRCA_HAUS_OPENAI_IMAGE_MODEL=<approved image model for merch ideation concepts>
CIRCA_HAUS_SAIA_RIGHTS_GUIDANCE_ENABLED=true
CIRCA_HAUS_SAIA_MERCH_IDEATION_ENABLED=true
```

Saia may assist with merch ideation and concept images, but products cannot publish without creator approval, rights warnings, provider-safe preflight, placement checks, and explicit confirmation.

## ElevenLabs voice

```text
CIRCA_HAUS_ELEVENLABS_API_KEY=<server-only ElevenLabs key>
CIRCA_HAUS_ELEVENLABS_TALETHIA_VOICE_ID=<Talethia voice id>
CIRCA_HAUS_ELEVENLABS_AVA_BACKUP_VOICE_ID=<Ava backup voice id>
```

## Licensed audio providers — conditional

Launch direction is verified licensed audio support, not native AI/music generation. Epidemic Sound and Artlist are planned/conditional until official API or partner access, licensing scope, costs, and creator usage-right verification are confirmed.

```text
CIRCA_HAUS_EPIDEMIC_SOUND_CLIENT_ID=<conditional>
CIRCA_HAUS_EPIDEMIC_SOUND_CLIENT_SECRET=<conditional>
CIRCA_HAUS_EPIDEMIC_SOUND_WEBHOOK_SECRET=<conditional>
CIRCA_HAUS_ARTLIST_CLIENT_ID=<conditional>
CIRCA_HAUS_ARTLIST_CLIENT_SECRET=<conditional>
CIRCA_HAUS_ARTLIST_WEBHOOK_SECRET=<conditional>
```

## Communications

```text
CIRCA_HAUS_TWILIO_ACCOUNT_SID=<Twilio account SID>
CIRCA_HAUS_TWILIO_MESSAGING_SERVICE_SID=<Twilio messaging service SID>
CIRCA_HAUS_TWILIO_AUTH_TOKEN=<Twilio auth token>
CIRCA_HAUS_TWILIO_WEBHOOK_SECRET=<Twilio webhook verification secret>

CIRCA_HAUS_SES_REGION=<AWS SES region>
CIRCA_HAUS_SES_ACCESS_KEY_ID=<SES access key id>
CIRCA_HAUS_SES_SECRET_ACCESS_KEY=<SES secret access key>
CIRCA_HAUS_SES_FROM_EMAIL=<verified SES sender>

CIRCA_HAUS_SUPPORT_EMAIL=<support inbox>
CIRCA_HAUS_ADMIN_EMAIL=<admin inbox>
CIRCA_HAUS_GOOGLE_WORKSPACE_DOMAIN=<workspace domain>
```

Twilio route to configure if enabled:

```text
<ETHER_PUBLIC_BASE_URL>/webhooks/twilio/circa_haus
```

## Promo Studio

```text
CIRCA_HAUS_CANVA_CLIENT_ID=<Canva client id>
CIRCA_HAUS_CANVA_CLIENT_SECRET=<Canva client secret>
CIRCA_HAUS_CANVA_WEBHOOK_SECRET=<Canva webhook secret>
```

Canva webhook route:

```text
<ETHER_PUBLIC_BASE_URL>/webhooks/canva/circa_haus
```

## Merch Studio + Creator Shop

```text
CIRCA_HAUS_APLIIQ_API_KEY=<Apliiq API key>
CIRCA_HAUS_APLIIQ_API_SECRET=<Apliiq API secret>
CIRCA_HAUS_APLIIQ_WEBHOOK_SECRET=<Apliiq webhook secret>
CIRCA_HAUS_PRINTFUL_API_TOKEN=<Printful API token>
CIRCA_HAUS_PRINTFUL_WEBHOOK_SECRET=<Printful webhook secret>
```

Provider webhook routes:

```text
<ETHER_PUBLIC_BASE_URL>/webhooks/apliiq/circa_haus
<ETHER_PUBLIC_BASE_URL>/webhooks/printful/circa_haus
```

## Cloudflare / domains / QR routing

```text
CIRCA_HAUS_CLOUDFLARE_ACCOUNT_ID=<Cloudflare account id>
CIRCA_HAUS_CLOUDFLARE_ZONE_ID=<Cloudflare zone id>
CIRCA_HAUS_CLOUDFLARE_API_TOKEN=<Cloudflare API token>
CIRCA_HAUS_PUBLIC_APP_DOMAIN=<public app/info domain>
CIRCA_HAUS_ADMIN_DOMAIN=<admin/support/security domain>
CIRCA_HAUS_QR_DOMAIN=<QR short-route domain>
```

## Optional project lanes

Keep these available for later reconnection without blocking Circa Haus credentialing.

```text
EXCLUSIVITY_SUPABASE_URL=
EXCLUSIVITY_SUPABASE_SERVICE_ROLE_KEY=
EXCLUSIVITY_ETHER_SIGNAL_SECRET=
EXCLUSIVITY_SIGNAL_RPC=ether_signal
EXCLUSIVITY_SIGNAL_TABLE=ether_signals

SOVA_SUPABASE_URL=
SOVA_SUPABASE_SERVICE_ROLE_KEY=
SOVA_ETHER_SIGNAL_SECRET=
SOVA_SIGNAL_RPC=ether_signal
SOVA_SIGNAL_TABLE=ether_signals
```

## Post-redeploy smoke checks

After env insertion and redeploy, check these routes in order:

```text
GET  <ETHER_PUBLIC_BASE_URL>/health
GET  <ETHER_PUBLIC_BASE_URL>/health/deep
GET  <ETHER_PUBLIC_BASE_URL>/readiness
GET  <ETHER_PUBLIC_BASE_URL>/readiness/circa_haus
GET  <ETHER_PUBLIC_BASE_URL>/providers/readiness/circa_haus
POST <ETHER_PUBLIC_BASE_URL>/signal/handshake
POST <ETHER_PUBLIC_BASE_URL>/signal/heartbeat
```

Then confirm in Circa Haus Supabase:

```sql
select project_slug, lane, signal_type, status, received_at
from public.ether_signals
order by received_at desc
limit 10;
```

Expected result: at least one accepted Circa Haus heartbeat row after the Render redeploy and signal test.

## Current manual-only item

Supabase Auth leaked-password protection is still a dashboard setting. Enable it in Supabase Auth settings before launch.
