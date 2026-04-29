# Ether Sentinel Enforcement / Recovery

Sentinel Enforcement / Recovery upgrades Sentinel from incident storage into an operational decision layer.

It answers:

- Is this actor/target/provider/project quarantined?
- Should this action be allowed, reviewed, or blocked?
- Which quarantine caused the block?
- What must be reviewed before recovery?
- Did recovery clear launch blockers?
- Does control-plane recovery still need to happen after Sentinel recovery?

## Main routes

```text
GET  /sentinel/status
POST /sentinel/enforce
GET  /sentinel/recovery/{project_slug}
POST /sentinel/recovery
POST /sentinel/events
GET  /sentinel/events
POST /sentinel/quarantine
POST /sentinel/quarantine/release
GET  /sentinel/quarantines
POST /sentinel/review/manual
```

All routes are internal-only.

## Enforcement checks

Route:

```text
POST /sentinel/enforce
```

Example actor check:

```json
{
  "project_slug": "circa_haus",
  "action": "donation",
  "actor_id": "supporter-123",
  "details": {
    "provider": "stripe"
  }
}
```

Example target check:

```json
{
  "project_slug": "circa_haus",
  "action": "message",
  "actor_id": "supporter-123",
  "target_type": "creator",
  "target_id": "creator-456"
}
```

Example provider check:

```json
{
  "project_slug": "circa_haus",
  "action": "webhook",
  "details": {
    "provider": "stripe"
  }
}
```

Possible dispositions:

```text
allow
review
block
```

Hard blocks occur when active quarantines match:

- actor
- target
- project
- provider

Review disposition occurs when related open threats exist and risk remains high enough for human/admin review.

## Quarantine target types

Supported operational target types include:

```text
actor
creator
supporter
project
provider
campaign
message_thread
qr_code
storefront
product
admin
```

The engine treats `actor`, `project`, and `provider` as first-class enforcement scopes now. Other target types are supported through target lookups when caller supplies `target_type` and `target_id`.

## Recovery diagnostics

Route:

```text
GET /sentinel/recovery/circa_haus
```

Returns:

- active quarantines
- open threats
- launch blockers
- readiness to recover
- guidance for next action

Do not recover if active quarantines/open threats are not understood.

## Bundled recovery

Route:

```text
POST /sentinel/recovery
```

Example:

```json
{
  "project_slug": "circa_haus",
  "release_quarantine_ids": [1, 2],
  "review_threat_ids": [4, 5],
  "review_status": "resolved",
  "reason": "Reviewed signed provider logs; test incident cleared.",
  "details": {
    "operator": "admin",
    "evidence": "Stripe dashboard test event matched Ether webhook history"
  }
}
```

This can release quarantines and mark threats reviewed/resolved in one recovery operation.

## Control-plane relationship

Sentinel recovery does not automatically re-enable disabled projects/providers.

That is intentional.

Correct sequence:

1. Resolve Sentinel threats/quarantines.
2. Check:

```text
GET /sentinel/status?project_slug=circa_haus
```

3. If Sentinel is clear but control-plane blockers remain, check:

```text
GET /controls/recovery/circa_haus
GET /controls/impact/circa_haus
```

4. Recover controls only after Sentinel and provider readiness are clear:

```text
POST /controls/recover
```

## Auto control actions

When recording a critical Sentinel event, callers may request automatic control actions:

```json
{
  "details": {
    "auto_disable_project": true
  }
}
```

or:

```json
{
  "details": {
    "provider": "stripe",
    "auto_disable_provider": true
  }
}
```

These are powerful because control-plane state is persistent. Use sparingly.

Auto-disabled controls are linked to the Sentinel threat id using:

```text
sentinel-threat-{threat_id}
```

## Launch blocking

Sentinel blocks launch when:

- open threats exist
- active quarantines exist
- quarantine-level incidents are recorded

Check:

```text
GET /sentinel/status
GET /sentinel/status?project_slug=circa_haus
```

## Audit integration

Sentinel writes audit events for:

```text
sentinel.enforce
sentinel.event
sentinel.quarantine
sentinel.quarantine.release
sentinel.recovery
sentinel.recovery.quarantine_release
sentinel.recovery.threat_review
sentinel.threat.review_manual
```

Check:

```text
GET /operations/audit/recent?action=sentinel.enforce
GET /operations/audit/summary
```

## Prelaunch test flow

1. Add a harmless quarantine:

```text
POST /sentinel/quarantine
```

2. Check enforcement blocks that actor/target/provider:

```text
POST /sentinel/enforce
```

3. Confirm status shows launch blockers:

```text
GET /sentinel/status?project_slug=circa_haus
```

4. Release the quarantine:

```text
POST /sentinel/recovery
```

5. Confirm status clears:

```text
GET /sentinel/status?project_slug=circa_haus
```

6. Confirm audit history:

```text
GET /operations/audit/recent?action=sentinel.recovery
```

7. Run suite smoke test:

```text
POST /operations/suite/smoke
```

## Current boundary

Completed now:

- active quarantine enforcement lookup
- target/action enforcement decision engine
- actor/provider/project quarantine blocking
- related open-threat review behavior
- enforcement route
- recovery diagnostics
- bundled Sentinel recovery
- launch-blocker visibility
- control-plane incident linkage
- audit integration
- route visibility
- runbook documentation

Still useful later:

- automatic enforcement calls from every app business action
- role-aware admin identity beyond internal token/source
- richer severity policy tuning after live traffic
- a visual admin dashboard built on top of these routes
