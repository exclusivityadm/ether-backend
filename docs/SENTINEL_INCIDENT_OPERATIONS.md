# Ether Sentinel Incident Operations

This is a full operational capability, not just a scaffold.

Sentinel incident operations provide durable security/safety event intake, scoring, quarantine, review, release, audit, and launch-blocker visibility for Ether-connected projects.

## Purpose

Sentinel exists to help Ether notice and respond to operational risk across Circa Haus, Exclusivity, and future projects.

It supports:

- threat event intake
- risk scoring
- durable threat records
- durable quarantine records
- automatic actor quarantine for critical events
- optional project/provider disable through the control plane
- manual admin quarantine
- manual review
- quarantine release
- AI/admin review summary scaffold
- launch-blocker status
- audit integration

## Storage

Sentinel uses the runtime SQLite store by default.

Default path comes from:

```text
ETHER_SENTINEL_DB_PATH
```

If unset, it falls back to:

```text
ETHER_AUDIT_DB_PATH
```

Then:

```text
runtime/ether_audit.sqlite3
```

Runtime database files are ignored by Git.

## Main routes

```text
GET  /sentinel/status
POST /sentinel/events
GET  /sentinel/events
POST /sentinel/review
POST /sentinel/review/manual
POST /sentinel/quarantine
POST /sentinel/quarantine/release
GET  /sentinel/quarantines
```

All Sentinel routes are internal-only and require Ether internal-token access.

## Event intake

Route:

```text
POST /sentinel/events
```

Example body:

```json
{
  "project_slug": "circa_haus",
  "event_type": "auth_replay_detected",
  "severity": "critical",
  "actor_id": "user-or-system-id",
  "source_ip": "optional-source-ip",
  "details": {
    "replay_detected": true,
    "cross_project_attempt": false,
    "provider": "stripe",
    "auto_disable_provider": false,
    "auto_disable_project": false
  }
}
```

Risk scoring considers:

- severity
- replay detection
- cross-project attempts
- provider abuse
- credential exposure
- payment abuse
- QR abuse
- auth-related event type

Disposition:

- risk below 70: allow / observed
- risk 70 to 89: review
- risk 90+: quarantine

## Quarantine

Automatic quarantine:

- critical risk events can auto-quarantine the actor if `actor_id` is present.

Manual quarantine:

```text
POST /sentinel/quarantine
```

Example body:

```json
{
  "project_slug": "circa_haus",
  "target_type": "actor",
  "target_id": "user-or-system-id",
  "reason": "Suspicious credential replay pattern",
  "details": {
    "source": "manual_admin_review"
  }
}
```

Release quarantine:

```text
POST /sentinel/quarantine/release
```

Example body:

```json
{
  "quarantine_id": 1,
  "reason": "Reviewed and cleared"
}
```

## Manual review

Manual review marks a persisted threat with an admin status and notes.

Route:

```text
POST /sentinel/review/manual
```

Example body:

```json
{
  "threat_id": 1,
  "status": "reviewed",
  "review_notes": "False positive after provider log comparison."
}
```

Recommended statuses:

- reviewed
- dismissed
- escalated
- resolved
- monitoring

## AI/admin review scaffold

Route:

```text
POST /sentinel/review
```

This uses the current admin AI reviewer scaffold and should remain admin-only.

Before production AI review is enabled, keep:

```text
ETHER_SENTINEL_AI_ENABLED=false
```

## Status and launch blockers

Route:

```text
GET /sentinel/status
GET /sentinel/status?project_slug=circa_haus
```

Launch-blocking conditions:

- open Sentinel threats
- active quarantines
- quarantine-level incidents

Circa Haus should not launch if Sentinel status reports unresolved launch blockers that affect Circa Haus or the suite.

## Control-plane integration

Threat event details may request automatic control actions:

```json
{
  "auto_disable_project": true
}
```

or:

```json
{
  "provider": "stripe",
  "auto_disable_provider": true
}
```

These should be used sparingly. They are powerful because control-plane state is now persistent.

## Audit integration

Sentinel writes audit events for:

- threat intake
- quarantine creation
- quarantine release
- manual review
- auto project/provider disable side effects

Audit can be inspected through:

```text
GET /operations/audit/recent
GET /operations/audit/summary
```

## Prelaunch use

Before Circa Haus launch:

1. Start Ether.
2. Confirm Sentinel store initializes.
3. Submit a test low event.
4. Submit a test critical event with a harmless actor ID.
5. Confirm threat records persist.
6. Confirm auto quarantine appears.
7. Release the test quarantine.
8. Manually review the test threat.
9. Confirm `/sentinel/status` clears launch blockers.
10. Confirm audit entries exist.

## Production cautions

- Keep Sentinel internal-only.
- Do not expose Sentinel routes to users.
- Keep AI review disabled until admin identity, logging, and review controls are verified.
- Do not auto-disable projects/providers for noisy events until thresholds are tested.
- Move persistent storage to managed Postgres/Supabase when production scale requires it.
