# Circa Haus Error Classification Guide

Use this during UI testing, Render redeploys, credentialing, and post-credential smoke tests. Every failure should be classified before fixing so we do not make broad changes under pressure.

## Error classes

```text
UI_BOOT_ERROR
UI_ROUTE_ERROR
MOBILE_ENV_ERROR
RENDER_DEPLOY_ERROR
ETHER_RUNTIME_ERROR
SUPABASE_CONFIG_ERROR
SUPABASE_RLS_GRANT_ERROR
PROVIDER_CREDENTIAL_ERROR
PROVIDER_WEBHOOK_ERROR
STRIPE_MODE_ERROR
PAYMENT_DOCTRINE_ERROR
SAIA_PROVIDER_ERROR
MERCH_PROVIDER_ERROR
DOMAIN_DNS_ERROR
ADMIN_SECURITY_EXPOSURE
SECRET_EXPOSURE
POLICY_COMPLIANCE_ERROR
UNKNOWN_NEEDS_TRIAGE
```

## UI_BOOT_ERROR

Symptoms:

```text
Blank screen after splash.
Boot Guard fatal panel appears.
Flutter terminal shows uncaught build/init error.
App never reaches choose/entry surface.
```

First action:

```text
Capture Boot Guard screenshot and the first terminal error. Do not proceed deeper into credentialing until boot is stable.
```

## UI_ROUTE_ERROR

Symptoms:

```text
App boots, but tapping a button crashes.
Named route not found.
Payment, Fan Club, Merch, or Admin screen route fails.
```

First action:

```text
Fix route registration, import, constructor, or button destination.
```

## MOBILE_ENV_ERROR

Symptoms:

```text
App boots but cannot initialize Supabase, Stripe, or Ether client-side.
Public key missing.
Feature flag not behaving.
```

First action:

```text
Confirm only public or publishable values are in mobile env. Run flutter clean and rebuild.
```

## RENDER_DEPLOY_ERROR

Symptoms:

```text
Render deploy fails.
Service does not restart.
Old code still appears live.
Health route unavailable.
```

First action:

```text
Read Render deploy log first error and confirm service points to latest ether-backend main.
```

## ETHER_RUNTIME_ERROR

Symptoms:

```text
/health fails.
/deep health fails unexpectedly.
Readiness route crashes.
Operations or audit route fails.
```

First action:

```text
Check /health, Render logs, then /health/deep.
```

## SUPABASE_CONFIG_ERROR

Symptoms:

```text
Ether cannot connect to Supabase.
Wrong project queried.
Tables not found.
Service-role key rejected.
```

First action:

```text
Verify project URL and service-role key belong to the Circa Haus Supabase project.
```

## SUPABASE_RLS_GRANT_ERROR

Symptoms:

```text
Table exists but write/read fails.
Permission denied.
Missing grant.
RLS blocks expected server operation.
```

First action:

```text
Classify as configuration or migration contract failure, not hostile outage. Review grants, policies, and role used.
```

## PROVIDER_CREDENTIAL_ERROR

Symptoms:

```text
Provider readiness says missing key.
Provider API rejects request.
Provider route returns unauthorized.
```

First action:

```text
Verify value in provider dashboard and destination env. Do not paste secrets into chat or GitHub.
```

## PROVIDER_WEBHOOK_ERROR

Symptoms:

```text
Webhook rejects signature.
Provider dashboard says endpoint failed.
Event never appears in Ether.
```

First action:

```text
Confirm endpoint URL, signing secret, and provider mode.
```

## STRIPE_MODE_ERROR

Symptoms:

```text
Test key with live webhook.
Live key with test checkout.
Connected-account mismatch.
Webhook events do not match expected mode.
```

First action:

```text
Stay in test mode until test smoke passes. Never mix test and live values accidentally.
```

## PAYMENT_DOCTRINE_ERROR

Symptoms:

```text
Platform fee is not 1.5%.
0.8% appears anywhere.
Receipts disagree with database.
Creator net calculation mismatch.
```

First action:

```text
Treat as launch blocker. Platform fee must be 150 bps across app money flows.
```

## SAIA_PROVIDER_ERROR

Symptoms:

```text
Saia routes fail after OpenAI credentials.
Merch ideation fails.
Copyright guidance does not render.
```

First action:

```text
Verify OpenAI readiness and route payload. Keep Saia copyright-aware and no native music generation at launch.
```

## MERCH_PROVIDER_ERROR

Symptoms:

```text
Apliiq or Printful readiness fails.
Preflight route cannot validate provider profile.
Publish-readiness check fails unexpectedly.
```

First action:

```text
Confirm provider access and keep publish gate strict: creator approval, rights attestation, and preflight.
```

## DOMAIN_DNS_ERROR

Symptoms:

```text
Domain does not resolve.
HTTPS unavailable.
Callback URL rejected.
QR route unavailable.
```

First action:

```text
Check Cloudflare DNS, host mapping, and HTTPS status.
```

## ADMIN_SECURITY_EXPOSURE

Symptoms:

```text
Admin/security route publicly accessible.
.dev surface not protected.
Internal dashboard reachable without gate.
```

First action:

```text
Hard stop. Protect before continuing.
```

## SECRET_EXPOSURE

Symptoms:

```text
Secret appears in mobile env, GitHub, screenshot, log, chat, or support ticket.
Service-role key exposed.
```

First action:

```text
Stop using exposed secret. Rotate or revoke it. Replace Render value. Redeploy. Record incident.
```

## POLICY_COMPLIANCE_ERROR

Symptoms:

```text
Terms, privacy, fees, or copyright copy missing.
Receipt lacks fee clarity.
Copyright claim flow absent.
User consent or acknowledgment missing.
```

First action:

```text
Treat payment, rights, consent, and account safety issues as launch blockers unless explicitly classified otherwise.
```

## UNKNOWN_NEEDS_TRIAGE

Use only when no other class fits.

First action:

```text
Capture exact error, exact route/action, latest commit/deploy timestamp, and logs. Do not make broad changes until classified.
```

## Minimum error report format

```text
Class:
Where it happened:
Exact action:
Exact route/screen:
Provider involved:
Latest deploy/rebuild:
Visible error:
Terminal/log excerpt:
Screenshot available:
Immediate next action:
```
