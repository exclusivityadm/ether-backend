# Circa Haus Render Env Template — No Secrets

This is a no-secrets template for the Render `ether-backend` service.

Use this during credentialing to know which values belong in Render. Do not paste actual values into GitHub, ChatGPT, screenshots, or this document.

## How to use

For each line:

```text
1. Find the value in the provider dashboard.
2. Paste the real value only into Render environment variables.
3. Save.
4. Redeploy only when the current provider group is ready to test.
5. Run the readiness check for that provider before moving on.
```

## Core Ether

```text
ETHER_ENV=production
ETHER_VERSION=<current Ether version>
ETHER_INTERNAL_TOKEN=<server-only internal token>
ETHER_ALLOWED_SOURCES=circa_haus,exclusivity,sova
ETHER_CORS_MODE=allowlist
ETHER_CORS_ALLOW_ORIGINS=https://circahaus.app,https://circahaus.com,https://circahaus.dev
```

## Circa Haus Supabase

```text
CIRCA_HAUS_SUPABASE_URL=<Circa Haus Supabase project URL>
CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY=<Circa Haus Supabase service-role key>
```

## Stripe

```text
STRIPE_SECRET_KEY=<Stripe secret key>
STRIPE_WEBHOOK_SECRET=<Stripe webhook signing secret>
STRIPE_CONNECT_CLIENT_ID=<Stripe Connect client ID if used>
STRIPE_MODE=test
```

Keep Stripe in test mode first. Switch to live only after test-mode flows are stable.

## OpenAI / Saia

```text
OPENAI_API_KEY=<OpenAI server API key>
CIRCA_HAUS_OPENAI_TEXT_MODEL=<selected text model>
CIRCA_HAUS_OPENAI_IMAGE_MODEL=<selected image model>
SAIA_COPYRIGHT_AWARE=true
SAIA_NATIVE_MUSIC_GENERATION=false
```

## ElevenLabs

```text
ELEVENLABS_API_KEY=<ElevenLabs server API key>
ELEVENLABS_TALETHIA_VOICE_ID=<Talethia voice ID>
ELEVENLABS_AVA_BACKUP_VOICE_ID=<Ava backup voice ID>
```

## Canva / Promo Studio

```text
CANVA_CLIENT_ID=<Canva client ID if applicable>
CANVA_CLIENT_SECRET=<Canva client secret if applicable>
CANVA_WEBHOOK_SECRET=<Canva webhook secret if applicable>
```

## Merch providers

```text
APPLIIQ_API_KEY=<Apliiq API key if provided>
APPLIIQ_API_SECRET=<Apliiq API secret if provided>
APPLIIQ_WEBHOOK_SECRET=<Apliiq webhook secret if provided>
PRINTFUL_API_TOKEN=<Printful API token>
PRINTFUL_WEBHOOK_SECRET=<Printful webhook secret if provided>
```

## Licensed audio providers

Launch direction is verified licensed audio support, not native AI/music generation.

Only add these if official access, licensing scope, cost, and usage-right verification are confirmed.

```text
EPIDEMIC_SOUND_CLIENT_ID=<if official access is confirmed>
EPIDEMIC_SOUND_CLIENT_SECRET=<if official access is confirmed>
ARTLIST_CLIENT_ID=<if official access is confirmed>
ARTLIST_CLIENT_SECRET=<if official access is confirmed>
LICENSED_AUDIO_PROVIDER_MODE=conditional
```

## Communications

```text
TWILIO_ACCOUNT_SID=<Twilio account SID>
TWILIO_AUTH_TOKEN=<Twilio auth token>
TWILIO_FROM_NUMBER=<Twilio number>
AWS_ACCESS_KEY_ID=<AWS SES access key ID if used>
AWS_SECRET_ACCESS_KEY=<AWS SES secret access key if used>
AWS_REGION=<AWS SES region>
SES_FROM_EMAIL=<approved sender email>
GOOGLE_WORKSPACE_SUPPORT_EMAIL=<support inbox>
GOOGLE_WORKSPACE_ADMIN_EMAIL=<admin inbox>
```

## Cloudflare / domains

```text
CLOUDFLARE_ACCOUNT_ID=<Cloudflare account ID if automation is used>
CLOUDFLARE_ZONE_ID=<Cloudflare zone ID if automation is used>
CLOUDFLARE_API_TOKEN=<Cloudflare API token if automation is used>
CIRCA_PUBLIC_DOMAIN=circahaus.com
CIRCA_APP_DOMAIN=circahaus.app
CIRCA_ADMIN_DOMAIN=circahaus.dev
```

## Security / Phantom / Ghost

```text
GHOST_PHANTOM_SECRET=<server-only secret if used>
PHANTOM_CORE_SECRET=<server-only secret if used>
PHANTOM_CORE_POLICY_VERSION=circa-haus-launch-v1
MISSING_GRANTS_CLASSIFICATION=configuration_contract_failure
```

## Verification after each provider group

After each provider group is inserted and Render is redeployed, run:

```text
GET /health
GET /health/deep
GET /readiness/circa_haus
GET /providers/circa_haus/readiness
GET /operations/audit/recent
```

For Supabase/Ether bridge specifically, also run:

```text
POST /signal/handshake
POST /signal/heartbeat
```

Then verify Supabase:

```sql
select project_slug, lane, signal_type, status, received_at
from public.ether_signals
order by received_at desc
limit 10;
```

## Values that never go in Render

Render does not need mobile-only public flags such as:

```text
EXPO_PUBLIC_APP_NAME
EXPO_PUBLIC_APP_ENV
EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY
EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY
EXPO_PUBLIC_ENABLE_QR
```

Those belong in the mobile/client environment, not Ether.
