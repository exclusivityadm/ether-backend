# Circa Haus Post-Credential Smoke-Test Checklist

This checklist is for the first verification pass after each credential group is inserted.

The goal is to prove one layer at a time without destabilizing multiple systems at once.

## Testing rule

Run the smallest meaningful test after each provider group.

```text
Add one provider group.
Redeploy or rebuild only what changed.
Run the matching smoke test.
Classify any error.
Fix before moving to the next provider group.
```

## Baseline before provider tests

Do these first:

```text
1. Pull latest mobile app.
2. Confirm app boots beyond splash.
3. Confirm Boot Guard does not show a fatal UI error.
4. Confirm Ether Render deploy is latest main.
5. Confirm no service-role or provider secret exists in mobile/client env.
```

## Ether baseline smoke tests

Run after Render redeploy:

```text
GET /health
GET /health/deep
GET /version
GET /readiness
GET /readiness/circa_haus
GET /providers/circa_haus/readiness
GET /operations/audit/recent
```

Expected:

```text
/health returns online.
/deep health returns structured status.
/readiness routes return structured readiness, even if some providers are pending.
/provider readiness shows missing providers as missing configuration, not generic failure.
```

## Supabase bridge smoke tests

Run after Supabase env values are inserted into Render:

```text
POST /signal/handshake
POST /signal/heartbeat
```

Then verify in Supabase:

```sql
select project_slug, lane, signal_type, status, received_at
from public.ether_signals
order by received_at desc
limit 10;
```

Expected:

```text
project_slug = circa_haus
recent timestamp
successful/accepted signal status
```

Failure classes:

```text
Missing env value
Wrong Supabase URL
Wrong service-role key
RLS/grant/policy issue
Ether route bug
Network/deploy issue
```

## Mobile boot smoke test

Run:

```powershell
flutter clean
flutter pub get
flutter run -d chrome --web-port 8080
```

Expected:

```text
Splash appears.
App moves beyond splash.
Choose/entry surface appears.
No blank screen.
No fatal Boot Guard panel.
```

If Boot Guard appears:

```text
Capture screenshot.
Copy terminal error.
Do not continue deeper into credentialing until boot path is fixed.
```

## Payment UI smoke tests

After payment routes are wired into the app route map:

```text
/payments/donation
/payments/campaign
/payments/fan-club
/payments/creator-premium
/payments/merch
/payments/post-donation-upgrade
/payments/receipt
```

Expected before Stripe is live:

```text
Each surface renders a branded Circa Haus payment shell.
Each surface shows pending-provider state.
No fake card-entry fields appear.
No redirect-only assumption appears.
Payment review shows Circa Haus platform fee (1.5%).
```

Expected after Stripe test-mode configuration:

```text
Provider readiness reports Stripe configured.
Payment UI can transition from pending-provider state to provider-ready state.
Provider result states can show success, failed, canceled, and requires-action without rebuilding the shell.
```

## Stripe smoke tests

After Stripe values are inserted into Render:

```text
GET /providers/circa_haus/readiness
POST /webhooks/stripe/circa_haus with Stripe dashboard test event
GET /webhooks/events if available
GET /operations/audit/recent
```

Expected:

```text
Stripe readiness shows configured.
Webhook signature validates.
Webhook event is stored or recorded.
Payment event classification is clear.
```

Hard stop if:

```text
Stripe secret key is in mobile env.
Webhook signature cannot be verified.
Test/live mode is mixed without explicit intent.
Platform fee is not 1.5%.
```

## OpenAI / Saia smoke tests

After OpenAI values are inserted into Render:

```text
GET /providers/circa_haus/readiness
POST /circa/premium/saia/merch-briefs with test payload
POST /circa/merch/ideation/sessions with test payload if route is ready
GET /operations/audit/recent
```

Expected:

```text
OpenAI readiness reports configured.
Saia surfaces do not fail due to missing API key.
Saia guidance remains copyright-aware.
Saia merch ideation does not encourage copying protected brands, logos, celebrities, characters, or existing merch.
```

## ElevenLabs smoke tests

After ElevenLabs values are inserted into Render:

```text
GET /providers/circa_haus/readiness
GET /operations/audit/recent
```

Expected:

```text
Voice provider readiness reports configured.
Talethia primary voice ID is present.
Ava backup voice ID is present.
Mobile app still requests microphone only after user action.
```

Hard stop if:

```text
The app requests mic permission on first launch before user taps/chooses voice.
Voice key appears in mobile env.
```

## Canva smoke tests

After Canva values are available:

```text
GET /providers/circa_haus/readiness
GET /operations/audit/recent
```

Expected:

```text
Canva readiness reports configured or intentionally pending.
Promo Studio remains polished in pending state if Canva access is not ready.
No unrelated launch surface is blocked solely because Canva is pending unless explicitly marked required.
```

## Apliiq / Printful smoke tests

After merch provider values are inserted into Render:

```text
GET /providers/circa_haus/readiness
POST /circa/merch/preflight-reviews with safe test payload
POST /circa/premium/merch/publish-ready with test listing id if available
GET /operations/audit/recent
```

Expected:

```text
Merch provider readiness is clear.
Creator Shop can show provider-pending or provider-ready state.
Publish readiness still requires creator approval, rights attestation, and preflight pass.
No product can be silently published by Saia.
```

## Cloudflare/domain smoke tests

After domains are purchased and configured:

```text
https://circahaus.com
https://circahaus.com/legal/privacy
https://circahaus.com/legal/terms
https://circahaus.com/support
https://circahaus.app
https://circahaus.dev
```

Expected:

```text
.com public trust/legal/support routes work.
.app product/app route works.
.dev is protected for admin/security use before sensitive dashboards go live.
```

Hard stop if:

```text
Admin/security routes are publicly accessible without protection.
```

## Communications smoke tests

After communications providers are configured:

```text
GET /providers/circa_haus/readiness
GET /operations/audit/recent
```

Expected:

```text
Support/admin inbox values are known.
SMS/email providers are configured or clearly pending.
No communication secret appears in mobile/client env.
```

## Final post-credential smoke success

The first post-credential pass is successful when:

```text
Mobile boots beyond splash.
Ether health and readiness pass.
Ether heartbeat reaches Supabase.
Supabase security dashboard has no ignored launch-blocking warning.
Stripe minimum readiness is verified.
Payment UI remains component-ready.
Platform fee remains 1.5%.
Saia provider readiness is clear or isolated.
Merch/Promo/Voice/Comms providers are either verified or explicitly marked non-launch-blocking pending.
No server secret appears in client code/env/logs.
```
