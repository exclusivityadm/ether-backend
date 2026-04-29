# Ether Provider / Webhook Operations

This is a full vertical operations capability for provider webhook intake.

It provides durable webhook event storage, idempotency/replay detection, provider/project control awareness, cryptographic signature verification where secrets are configured, audit integration, status visibility, and wiring-day diagnostics.

## Purpose

Ether should sit before Circa Haus launch. Provider webhooks need an internal operational layer that can answer:

- Did the webhook arrive?
- Which project/provider did it target?
- Was the provider enabled?
- Was the project/provider disabled by control plane?
- Was the event a duplicate?
- What event type was detected?
- Was a provider signature present?
- Was the provider signature configured and verified?
- What warnings need wiring attention?
- Was the event accepted, rejected, trusted, or accepted only as wiring-stage intake?

## Main routes

```text
GET  /webhooks/status
GET  /webhooks/events
POST /webhooks/{provider}/{project_slug}
```

Examples:

```text
GET /webhooks/status
GET /webhooks/status?project_slug=circa_haus
GET /webhooks/events?project_slug=circa_haus&provider=stripe
POST /webhooks/stripe/circa_haus
POST /webhooks/canva/circa_haus
POST /webhooks/apliiq/circa_haus
POST /webhooks/printful/circa_haus
POST /webhooks/twilio/circa_haus
```

## Durable storage

Webhook events are persisted to runtime SQLite by default.

Default path:

```text
ETHER_WEBHOOK_DB_PATH
```

Fallback path:

```text
ETHER_AUDIT_DB_PATH
```

Then:

```text
runtime/ether_audit.sqlite3
```

Runtime database files are ignored by Git.

## Stored fields

Each webhook record stores:

- internal event id
- event UID
- project slug
- provider
- event type
- provider event id
- status
- accepted flag
- duplicate flag
- payload hash
- payload JSON
- safe header metadata
- validation metadata
- received timestamp
- notes

## Idempotency / replay protection

Ether builds an event UID using:

```text
project_slug + provider + provider_event_id
```

If no provider event id can be found, Ether uses the canonical payload hash.

Duplicate events are idempotently accepted only after signature verification has not failed. If a provider signature secret is configured and the duplicate request has an invalid signature, Ether rejects it before duplicate acceptance.

## Provider event ID extraction

Current extraction behavior:

### Stripe

- `payload.id`
- `stripe-event-id` header fallback

### Twilio

- `MessageSid`
- `SmsSid`
- `CallSid`

### Canva

- `id`
- `event_id`
- `notification_id`

### Apliiq

- `id`
- `event_id`
- `order_id`

### Printful

- `id`
- `event_id`
- `data.id`

### Generic

- `id`
- `event_id`
- `eventId`

## Signature verification

Ether now supports provider signature verification.

### Stripe

Mode:

```text
stripe_v1_hmac_sha256
```

Expected header:

```text
stripe-signature
```

Env:

```text
CIRCA_HAUS_STRIPE_WEBHOOK_SECRET
```

Fallback generic env:

```text
STRIPE_WEBHOOK_SECRET
```

Behavior:

- validates timestamp
- uses 10-minute tolerance
- verifies v1 HMAC SHA-256 against raw request body
- rejects missing/invalid signatures once the secret is configured

### Twilio

Mode:

```text
twilio_hmac_sha1_url_params
```

Expected header:

```text
x-twilio-signature
```

Env:

```text
CIRCA_HAUS_TWILIO_AUTH_TOKEN
```

Fallback generic env:

```text
TWILIO_AUTH_TOKEN
```

Behavior:

- builds Twilio signature base string from request URL + sorted params
- verifies HMAC SHA-1 base64 signature
- rejects missing/invalid signatures once token is configured

Important: Twilio signature verification is sensitive to the public URL. If Render/Cloudflare rewrites host/protocol, set the provider webhook URL exactly to the public URL Ether receives.

### Canva

Mode:

```text
generic_hmac_sha256_raw_body
```

Expected header:

```text
x-canva-signature
```

Env:

```text
CIRCA_HAUS_CANVA_WEBHOOK_SECRET
```

Fallback in code:

```text
CIRCA_HAUS_CANVA_CLIENT_SECRET
```

### Apliiq

Mode:

```text
generic_hmac_sha256_raw_body
```

Expected header:

```text
x-apliiq-signature
```

Env:

```text
CIRCA_HAUS_APLIIQ_WEBHOOK_SECRET
```

Fallback in code:

```text
CIRCA_HAUS_APLIIQ_API_SECRET
```

### Printful

Mode:

```text
generic_hmac_sha256_raw_body
```

Expected header:

```text
x-pf-signature
```

Env:

```text
CIRCA_HAUS_PRINTFUL_WEBHOOK_SECRET
```

## Statuses

Possible statuses include:

- accepted
- accepted_verified
- accepted_with_warnings
- duplicate
- duplicate_verified
- signature_invalid
- project_not_found
- project_disabled
- provider_disabled_by_control
- provider_not_enabled

## Control-plane integration

Webhook intake checks:

1. Project exists.
2. Provider signature is not invalid when configured.
3. Event is not a duplicate, or is safely idempotent.
4. Project is not disabled.
5. Provider is not disabled by control plane.
6. Provider is enabled in the project registry.

Rejected events are still stored so the operator can see what happened.

## Provider readiness integration

Provider readiness now includes signature readiness for launch-sensitive Circa Haus rails:

- Stripe
- Twilio
- Canva
- Apliiq
- Printful

Check:

```text
GET /providers/circa_haus/readiness
GET /providers/readiness/suite
```

Missing webhook signature secrets are launch-blocking for those live rails because they affect money movement, user messaging, design publishing, or fulfillment.

## Audit integration

Every webhook attempt writes an audit event:

```text
webhook.ingest
```

Audit includes:

- project slug
- provider
- result
- trusted flag
- webhook event id
- event UID
- event type
- provider event id
- warnings
- configured route

Audit can be checked through:

```text
GET /operations/audit/recent
GET /operations/audit/summary
```

## Wiring-day provider checks

Before using live provider webhooks:

1. Confirm provider readiness:

```text
GET /providers/circa_haus/readiness
GET /providers/readiness/suite
```

2. Confirm webhook status starts clean:

```text
GET /webhooks/status?project_slug=circa_haus
```

3. Configure provider webhook secrets in Render.

4. Send signed test events from each provider dashboard/CLI.

5. Confirm records appear:

```text
GET /webhooks/events?project_slug=circa_haus
```

6. Confirm trusted events show:

```text
accepted_verified
```

7. Confirm invalid signature tests show:

```text
signature_invalid
```

8. Confirm audit events appear:

```text
GET /operations/audit/recent?action=webhook.ingest
```

## Launch blocker posture

Provider webhook operations block launch if:

- required provider is disabled by control plane
- required provider is not enabled in project registry
- required provider env vars are missing
- required provider webhook signature secret is missing
- webhook events are rejected unexpectedly after wiring
- duplicate storms appear during testing
- provider events cannot be audited or listed

## Current boundary

Completed now:

- durable webhook event store
- idempotency/replay detection
- provider/project control awareness
- provider signature verification utility
- Stripe signature verification
- Twilio signature verification path
- generic HMAC verification for Canva/Apliiq/Printful
- signature-aware rejection behavior
- trusted/verified webhook status behavior
- provider readiness launch-blocker integration
- status and event listing routes
- audit integration
- startup initialization
- runbook documentation

Still required after live credential wiring:

- provider-specific signed test events
- provider-specific business side effects after trusted events are accepted
- routing accepted events into Circa Haus business functions where appropriate
