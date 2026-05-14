# Circa Haus Launch Blocker Decision Matrix

Use this matrix when a warning or error appears during pre-credential testing, credentialing, post-credential smoke tests, or store-readiness review.

The purpose is to decide quickly whether something blocks launch, blocks credentialing, can be fixed prelaunch, or can be accepted as non-launch-blocking.

## Decision labels

```text
LAUNCH_BLOCKER
CREDENTIALING_BLOCKER
PRELAUNCH_FIX
ACCEPTED_NON_LAUNCH_BLOCKER
DOCUMENTATION_ONLY
LATER_UPGRADE
```

## LAUNCH_BLOCKER

A launch blocker prevents public release or app-store submission readiness.

Automatically launch-blocking:

```text
Mobile app cannot boot beyond splash.
Payment fee is not 1.5%.
0.8% platform fee appears anywhere.
Service-role or provider secret is exposed in client code, mobile env, GitHub, logs, screenshots, or chat.
Money-moving records cannot be created or reconciled safely.
Stripe/payment path cannot produce trustworthy success/failure/receipt states.
Admin/security surfaces are publicly reachable without protection.
RLS is disabled or missing on user, money, rights, admin/security, or provider-sensitive tables.
Creator approval, rights attestation, or merch preflight can be bypassed for publishing.
Saia can silently publish or encourages copying protected brands, logos, celebrities, characters, or existing merch.
Terms, privacy, fee disclosure, or copyright process is missing from required public/app surfaces.
Supporter/creator account safety controls are broken.
```

Required action:

```text
Stop. Fix before launch or app-store submission.
```

## CREDENTIALING_BLOCKER

A credentialing blocker prevents moving to the next provider group during the credentialing session.

Examples:

```text
Supabase URL/service-role key is wrong.
Render cannot redeploy latest Ether code.
Ether /health fails.
Ether cannot write heartbeat into Supabase after Supabase env insertion.
Stripe webhook signature cannot verify.
Test/live Stripe values are mixed accidentally.
Provider dashboard cannot expose the required credential.
Credential destination is ambiguous.
```

Required action:

```text
Stop provider sequence. Fix the current provider group before adding the next one.
```

## PRELAUNCH_FIX

A prelaunch fix should be completed before public launch but does not necessarily block continuing credentialing.

Examples:

```text
Minor copy polish.
Non-critical UI spacing issue.
Pending provider state needs clearer wording.
A non-money analytics event is not recording.
Optional provider readiness copy is unclear.
Non-sensitive admin convenience view is incomplete.
```

Required action:

```text
Log it, keep credentialing if safe, fix before launch.
```

## ACCEPTED_NON_LAUNCH_BLOCKER

An accepted non-launch blocker is an issue deliberately allowed for launch because it is not required, not harmful, and not misleading.

Examples:

```text
Licensed audio provider remains conditional because official partner/API access is not confirmed.
Canva integration remains pending but Promo Studio has polished pending state.
Voice provider remains pending but text Saia is functional and voice is not falsely advertised as live.
Non-critical communications provider is pending while support email is available.
Optional domain is not purchased because price is unreasonable.
```

Required action:

```text
Record reason, owner, and future condition for revisiting.
```

## DOCUMENTATION_ONLY

Documentation-only items do not affect functionality or launch readiness directly.

Examples:

```text
Internal runbook wording improvements.
Optional checklist expansion.
Developer notes.
Non-customer-facing architecture explanation.
```

Required action:

```text
Update when convenient.
```

## LATER_UPGRADE

Later upgrades are intentionally out of launch scope and must not be presented as launch features.

Examples:

```text
Full Content ID-style audio fingerprinting.
Native AI/music generation.
Shopify-style theme marketplace.
POS system.
Marketplace syndication.
Broad plugin ecosystem.
Privately owned server migration.
Advanced AI security autonomy beyond current Ether/Ghost/Phantom launch scope.
```

Required action:

```text
Do not build for launch unless scope is explicitly reopened.
```

## High-risk areas that default to blocker

When unsure, default these areas to launch blocker until reviewed:

```text
money movement
platform fee calculation
Stripe webhooks
service-role/server secrets
creator payouts
account deletion/retention
copyright claims
rights attestations
admin/security access
RLS/grants/policies
Saia publish authority
provider fulfillment orders
```

## Low-risk areas that usually do not block launch

When isolated and not misleading, these are usually prelaunch fixes or accepted non-launch blockers:

```text
non-critical animation polish
copy refinement outside legal/payment surfaces
optional provider integrations with pending states
internal dashboard convenience widgets
non-money analytics events
optional visual variants
later marketing pages not required for app-store submission
```

## Required blocker record format

When something is classified as a blocker, record:

```text
Decision label:
Area:
Exact issue:
User-facing impact:
Security/compliance impact:
Revenue impact:
Provider involved:
Owner action needed:
Engineering action needed:
Can credentialing continue safely:
Required verification after fix:
```

## Fast decision questions

Ask these in order:

```text
1. Could this expose money, user data, admin access, or provider secrets?
2. Could this cause wrong fees, wrong receipts, wrong payouts, or wrong creator net?
3. Could this mislead a creator/supporter about payment, rights, or platform behavior?
4. Could this break app-store submission, legal pages, or policy requirements?
5. Could this prevent Ether/Supabase/Stripe from verifying the current provider group?
6. Is this visible to users or only internal documentation?
7. Is this required for launch or clearly optional with a pending state?
```

If yes to 1 through 5, treat as blocker until proven otherwise.
