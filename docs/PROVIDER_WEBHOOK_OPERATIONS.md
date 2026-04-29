# Ether Provider / Webhook Operations

This is a full vertical operations capability for provider webhook intake.

It is not just a route. It provides durable webhook event storage, idempotency/replay detection, provider/project control awareness, audit integration, status visibility, and wiring-day diagnostics.

## Purpose

Ether should sit before Circa Haus launch. That means provider webhooks should have an internal operational layer that can answer:

- Did the webhook arrive?
- Which project/provider did it target?
- Was the provider enabled?
- Was the project/provider disabled by control plane?
- Was the event a duplicate?
- What event type was detected?
- Was a signature header present?
- What warnings need wiring attention?
- Was the event accepted, rejected, or accepted with warnings?

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

Duplicate events are idempotently accepted and marked as duplicates.

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

## Signature posture

At this stage Ether performs signature-header presence checks, not full cryptographic verification.

It records whether expected signature headers are present for:

- Stripe
- Twilio
- Canva
- Apliiq
- Printful

Full cryptographic verification should be added once provider webhook secrets are wired.

Until then, signature status is recorded as:

```text
presence-check-only-until-provider-secrets-are-wired
```

## Statuses

Possible statuses include:

- accepted
- accepted_with_warnings
- duplicate
- project_not_found
- project_disabled
- provider_disabled_by_control
- provider_not_enabled

## Control-plane integration

Webhook intake checks:

1. Project exists.
2. Project is not disabled.
3. Provider is not disabled by control plane.
4. Provider is enabled in the project registry.
5. Event is not a duplicate.

Rejected events are still stored so the operator can see what happened.

## Audit integration

Every webhook attempt writes an audit event:

```text
webhook.ingest
```

Audit includes:

- project slug
- provider
- result
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

3. Send test events to each intended provider route.

4. Confirm records appear:

```text
GET /webhooks/events?project_slug=circa_haus
```

5. Confirm audit events appear:

```text
GET /operations/audit/recent?action=webhook.ingest
```

## Provider-specific production follow-up

### Stripe

Add cryptographic verification using the Stripe webhook secret before trusting live financial events.

### Twilio

Add Twilio request signature validation before trusting SMS/call delivery events.

### Canva

Add Canva signature/OAuth validation once provider credentials are live.

### Apliiq

Add provider-specific webhook authentication based on Apliiq’s live account method.

### Printful

Add Printful signature validation based on configured webhook secret.

## Launch blocker posture

Provider webhook operations block launch if:

- required provider is disabled by control plane
- required provider is not enabled in project registry
- webhook events are rejected unexpectedly after wiring
- duplicate storms appear during testing
- Stripe webhook verification is not added before live financial reliance
- provider events cannot be audited or listed

## Current boundary

Completed now:

- durable webhook event store
- idempotency/replay detection
- provider/project control awareness
- status and event listing routes
- audit integration
- startup initialization
- runbook documentation

Still required after provider credentials:

- full cryptographic signature verification for each provider
- provider-specific event processing side effects
- routing accepted events into Circa Haus business functions where appropriate
