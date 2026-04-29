# Ether Admin Control Plane

The Admin Control Plane is Ether's internal command center for disabling, enabling, diagnosing, and recovering project/provider rails.

This is a full vertical capability, not just disable/enable endpoints.

## Purpose

Ether sits before Circa Haus launch. The control plane must help the operator answer:

- What is currently disabled?
- Why is it disabled?
- Was the disable linked to an incident?
- Which project/provider rails are launch-blocking?
- What is the operational impact?
- What must be checked before recovery?
- What happened historically?
- Did recovery clear the blocker?

## Main routes

```text
GET  /controls
GET  /controls/summary
GET  /controls/blockers
GET  /controls/history
GET  /controls/impact/{project_slug}
GET  /controls/recovery/{project_slug}
POST /controls/recover
POST /controls/project/disable
POST /controls/project/enable
POST /controls/provider/disable
POST /controls/provider/enable
```

All routes are internal-only.

## Durable state

Control state persists to runtime SQLite.

Default path:

```text
ETHER_CONTROL_DB_PATH
```

Fallback:

```text
ETHER_AUDIT_DB_PATH
```

Then:

```text
runtime/ether_audit.sqlite3
```

Runtime DB files are ignored by Git.

## Durable control history

Every project/provider enable/disable also writes a control history event.

Control history records:

- control type
- action
- project slug
- provider
- reason
- actor/source
- incident id
- details
- created timestamp

Check history:

```text
GET /controls/history
GET /controls/history?project_slug=circa_haus
GET /controls/history?project_slug=circa_haus&provider=stripe
GET /controls/history?incident_id=INC-001
```

## Project disable

Route:

```text
POST /controls/project/disable
```

Example:

```json
{
  "project_slug": "circa_haus",
  "reason": "Launch hold while Stripe webhook signature is being verified",
  "incident_id": "INC-STRIPE-001",
  "details": {
    "source": "admin",
    "expected_recovery": "verify signed webhook test"
  }
}
```

Effect:

- persists disabled project state
- writes control history event
- writes audit event
- project becomes launch-blocking
- protected project routes should honor control state where integrated

## Project enable

Route:

```text
POST /controls/project/enable
```

Use only after recovery checks are complete.

## Provider disable

Route:

```text
POST /controls/provider/disable
```

Example:

```json
{
  "project_slug": "circa_haus",
  "provider": "stripe",
  "reason": "Webhook signature mismatch detected during test",
  "incident_id": "INC-STRIPE-002",
  "details": {
    "observed_status": "signature_invalid"
  }
}
```

Effect:

- persists disabled provider state
- writes control history event
- writes audit event
- provider becomes launch-blocking
- webhook intake rejects that provider while disabled
- provider readiness reports the blocker

## Provider enable

Route:

```text
POST /controls/provider/enable
```

Use only after validating provider readiness and test events.

## Recovery workflow

Route:

```text
GET /controls/recovery/{project_slug}
```

This gives readiness notes before recovery.

Route:

```text
POST /controls/recover
```

Example:

```json
{
  "project_slug": "circa_haus",
  "reason": "Stripe signed webhook test passed and provider readiness is clear",
  "incident_id": "INC-STRIPE-002",
  "enable_project": false,
  "providers": ["stripe"],
  "details": {
    "verified_event_status": "accepted_verified"
  }
}
```

This can recover a project, one or more providers, or both in one action.

## Impact view

Route:

```text
GET /controls/impact/circa_haus
```

Impact view includes:

- current project control state
- provider control state
- provider readiness
- Sentinel snapshot
- signal verification snapshot
- webhook snapshot
- recent control events
- launch blockers

This is the main “why is this blocked?” operator view.

## Blockers

Route:

```text
GET /controls/blockers
```

Shows:

- launch blocking state
- project/provider control blockers
- provider readiness blockers
- operator notes

## Summary

Route:

```text
GET /controls/summary
```

Shows a suite-level control center snapshot including:

- controls
- provider readiness
- signal verification
- audit summary
- per-project impact rows

## Audit integration

Every control action writes audit entries, including:

```text
controls.project.disable
controls.project.enable
controls.provider.disable
controls.provider.enable
controls.project.recover
controls.provider.recover
```

Check:

```text
GET /operations/audit/recent?action=controls.provider.disable
GET /operations/audit/summary
```

## Sentinel linkage

Control actions support:

```text
incident_id
```

Sentinel-triggered or manually reviewed incidents can be tied to disable/recovery actions through this field.

## Prelaunch use

Before Circa Haus launch:

1. Confirm no control blockers:

```text
GET /controls/blockers
```

2. Confirm suite summary is clear:

```text
GET /controls/summary
```

3. Confirm Circa Haus impact is clear:

```text
GET /controls/impact/circa_haus
```

4. If a provider was disabled, run recovery diagnostics:

```text
GET /controls/recovery/circa_haus
```

5. Recover only after provider readiness, Sentinel, webhooks, and signal checks are clear.

## Launch blockers

Do not launch Circa Haus while:

- project control state is disabled
- required provider control state is disabled
- recovery diagnostics show active Sentinel threats/quarantines
- provider readiness remains blocked
- signal verification remains unverified
- signed provider webhook tests are failing

## Current boundary

Completed now:

- persistent project/provider controls
- persistent control event history
- incident-linked control actions
- blocker summary
- impact diagnostics
- recovery diagnostics
- bundled recovery action
- provider readiness integration
- Sentinel snapshot integration
- signal verification integration
- webhook status integration
- audit integration
- operator runbook

Still useful later:

- a visual admin dashboard built on top of these routes
- identity-aware admin roles beyond source/token-level internal access
- approval workflows for high-risk recovery actions
