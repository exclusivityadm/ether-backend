# Circa Haus Credentialing Day Runbook

This runbook is for the credentialing window after the pre-credential foundation is staged.

## Purpose

Credentialing day should be provider verification, not foundational construction.

The current intended state is:

- Circa Haus UI boot stability is tested first.
- Ether is redeployed from latest `main`.
- Render environment variables are inserted only after keys are collected.
- Provider readiness endpoints become the primary verification surface.
- Payment UI is component-ready and not locked to one Stripe method.
- Platform fee is locked at 1.5 percent / 150 bps across money moving through the app.

## Stop conditions

Do not proceed deeper into provider credentialing if any of these are true:

- The mobile app cannot boot beyond splash.
- The Boot Guard shows a fatal UI error that has not been captured.
- Supabase leaked-password protection remains unaddressed for final launch hardening.
- Render is still running stale Ether code after the latest GitHub changes.
- Ether `/health` fails.
- Ether cannot reach Circa Haus Supabase after Supabase env values are inserted.
- A service-role key is accidentally placed into mobile/client environment.

## Credentialing order

### 1. Supabase

Owner actions:

- Confirm Circa Haus Supabase project and plan.
- Enable leaked-password protection in Auth security settings.
- Collect project URL.
- Collect client-safe publishable/anon key.
- Collect service-role key for Render only.

Render/server values:

```text
CIRCA_HAUS_SUPABASE_URL
CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY
```

Mobile/client values:

```text
EXPO_PUBLIC_SUPABASE_URL
EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY
EXPO_PUBLIC_SUPABASE_ANON_KEY only if publishable key is unavailable
```

Never put `CIRCA_HAUS_SUPABASE_SERVICE_ROLE_KEY` or any service-role key into the mobile app.

### 2. Render / Ether

Owner actions:

- Confirm Render service points to latest `ether-backend` GitHub `main`.
- Add core Ether env vars.
- Add Circa Haus Supabase env vars.
- Redeploy.

Verify:

```text
GET /health
GET /health/deep
GET /readiness
GET /readiness/circa_haus
GET /providers/circa_haus/readiness
```

Then verify signal bridge:

```text
POST /signal/handshake
POST /signal/heartbeat
```

Confirm Supabase receives signal rows:

```sql
select project_slug, lane, signal_type, status, received_at
from public.ether_signals
order by received_at desc
limit 10;
```

### 3. Stripe

Owner actions:

- Confirm account mode: test first, live later.
- Collect publishable key.
- Collect secret key for Render only.
- Configure Connect as required.
- Create webhook endpoint pointing to Ether.
- Copy webhook signing secret to Render.

Mobile/client value:

```text
EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY
```

Render/server values:

```text
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
STRIPE_CONNECT_CLIENT_ID if used
```

Verify:

- Provider readiness route reports Stripe configured.
- Test webhook event is received by Ether.
- Payment UI remains component-ready and pending/provider-ready states transition cleanly.

### 4. OpenAI / Saia

Owner actions:

- Confirm API billing.
- Collect API key for Render only.
- Confirm selected text model.
- Confirm selected image model for Saia merch ideation.

Render/server values:

```text
OPENAI_API_KEY
CIRCA_HAUS_OPENAI_TEXT_MODEL
CIRCA_HAUS_OPENAI_IMAGE_MODEL
```

Verify:

- Provider readiness route reports OpenAI configured.
- Saia guidance routes do not fail due to missing credentials.
- Saia merch ideation remains blocked from copying brands, logos, celebrities, characters, or existing merch designs.

### 5. ElevenLabs

Owner actions:

- Confirm API key.
- Confirm Talethia voice ID.
- Confirm Ava backup voice ID.

Render/server values:

```text
ELEVENLABS_API_KEY
ELEVENLABS_TALETHIA_VOICE_ID
ELEVENLABS_AVA_BACKUP_VOICE_ID
```

Verify:

- Provider readiness route reports voice provider configured.
- Voice remains optional until the app has explicit microphone consent.

### 6. Canva

Owner actions:

- Confirm official developer/partner credential path.
- Collect client ID and client secret if available.
- Configure callback/webhook URLs after Ether domain is final.

Render/server values:

```text
CANVA_CLIENT_ID
CANVA_CLIENT_SECRET
CANVA_WEBHOOK_SECRET if provided
```

Verify:

- Promo Studio shows pending/provider-ready state correctly.
- Canva provider readiness does not block unrelated launch surfaces unless marked required.

### 7. Apliiq / Printful

Owner actions:

- Confirm account/API access.
- Collect provider API keys/tokens for Render only.
- Configure webhook URLs if supported.

Render/server values:

```text
APLIIQ_API_KEY or provider-specific credential
PRINTFUL_API_TOKEN
APPLIIQ_WEBHOOK_SECRET if provided
PRINTFUL_WEBHOOK_SECRET if provided
```

Verify:

- Merch Studio provider readiness reports configured providers.
- Provider-safe print profiles are available.
- Publish readiness still requires creator approval, rights attestation, and preflight pass.

### 8. Cloudflare / domains

Owner actions:

Recommended domain model:

```text
circahaus.com  = public trust, marketing, legal, support
circahaus.app  = app/product, creator pages, QR routes, donation, campaigns, fan club, Creator Shop
circahaus.dev  = admin, security, Ether, Ghost Phantom, Phantom Core, operations
```

Render/server values if Cloudflare API automation is used later:

```text
CLOUDFLARE_ACCOUNT_ID
CLOUDFLARE_ZONE_ID
CLOUDFLARE_API_TOKEN
```

Verify:

- Public/legal/support URLs resolve.
- App/product URLs resolve.
- Admin/security surfaces stay protected behind Cloudflare Access or equivalent controls.

### 9. Communications

Potential providers:

- Twilio for SMS/phone.
- Amazon SES for outbound email.
- Google Workspace for support/admin inboxes.

Render/server values depend on final provider setup.

Verify:

- No communication credential is exposed to the mobile app.
- Support flows have clean pending/provider-ready states.

## After each provider

Run:

```text
GET /providers/circa_haus/readiness
GET /readiness/circa_haus
GET /operations/audit/recent
```

Record:

- Provider added.
- Values inserted into Render.
- Redeploy completed.
- Readiness result.
- Any error text.
- Whether the error is credential, config, provider, database, or UI.

## Final credentialing-day success definition

Credentialing day is successful when:

- Mobile app boots beyond splash.
- Ether is redeployed from latest GitHub `main`.
- Ether health and deep health pass.
- Circa Haus Supabase receives Ether heartbeat.
- Required provider readiness checks pass or have documented non-launch-blocking pending status.
- Payment UI remains component-ready and does not show fake card fields.
- Platform fee remains 1.5 percent across app money flows.
- No service-role/provider secret is present in client code or client env.
