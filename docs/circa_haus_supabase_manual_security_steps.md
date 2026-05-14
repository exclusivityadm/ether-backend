# Circa Haus Supabase Manual Security Steps

This checklist covers the Supabase steps that must be done manually in the dashboard or verified manually during credentialing.

## Purpose

Some Supabase security settings are not safely toggled by connector automation. These should be handled directly in the Supabase dashboard, then verified through the advisor and Ether readiness checks.

## Manual step 1 — Enable leaked-password protection

Location:

```text
Supabase dashboard
→ Circa Haus project
→ Authentication
→ Security
→ Leaked password protection
→ Enable
```

Why this matters:

- It reduces account-takeover risk from known-compromised passwords.
- It clears the remaining known Supabase security advisor warning.
- It improves app-store/security posture before launch.

Verification:

```text
Supabase dashboard
→ Advisors
→ Security
```

Expected:

```text
No leaked-password protection warning.
```

## Manual step 2 — Confirm API keys are separated correctly

Supabase key destinations:

```text
Project URL                    -> mobile/client and Render
Publishable or anon key         -> mobile/client only
Service-role key                -> Render/server only
```

Never place the service-role key in:

```text
mobile app env
frontend env
GitHub
ChatGPT
screenshots
support tickets
app store metadata
client logs
```

## Manual step 3 — Confirm RLS is enabled on launch tables

The current migrations are designed to enable RLS and policies, but this should still be verified.

Priority areas:

```text
profiles
creator/supporter relationship tables
donations
commerce checkout intents
merch orders
fan club memberships
rights/copyright tables
creator shop tables
provider readiness tables
launch readiness tables
ether signal/audit tables
admin/security tables
```

Expected posture:

```text
RLS enabled.
Explicit policies present.
Service role can perform server work.
Anon/authenticated access is limited by policy.
Missing grants are treated as configuration contract failures.
```

## Manual step 4 — Confirm storage buckets

Verify storage buckets used by Circa Haus exist and are not accidentally public unless intended.

Priority bucket categories:

```text
brand assets
creator uploads
QR assets
promo studio exports
merch concept assets
merch provider-safe artwork
receipts/reports if stored
policy/copyright evidence if stored
```

Expected posture:

```text
Public only where intentionally needed.
Private/signed where user, creator, legal, or provider content requires protection.
```

## Manual step 5 — Confirm fee doctrine records

Circa Haus platform fee must remain:

```text
1.5 percent
150 bps
0 fixed platform fee cents
```

Verification SQL:

```sql
select rule_key, platform_rate_bps, platform_fixed_cents, active, metadata
from public.fee_rules
where rule_key = 'circa_haus_platform_fee_all_money_v1';
```

Expected:

```text
platform_rate_bps = 150
platform_fixed_cents = 0
active = true
legacy_0_8_percent_disallowed = true
```

## Manual step 6 — Confirm Ether heartbeat after Render credentialing

After Render has the Circa Haus Supabase URL and service-role key, run Ether heartbeat checks, then verify Supabase received the signal.

Verification SQL:

```sql
select project_slug, lane, signal_type, status, received_at
from public.ether_signals
order by received_at desc
limit 10;
```

Expected:

```text
project_slug = circa_haus
recent received_at timestamp
status indicates success/accepted/verified depending on route implementation
```

## Manual step 7 — Confirm advisor state after credentialing

After the above steps:

```text
Supabase dashboard
→ Advisors
→ Security
→ Performance if desired
```

Record any remaining warnings as:

```text
launch_blocker
prelaunch_fix
accepted_non_launch_blocker
documentation_only
```

Do not ignore warnings silently. If they are not fixed before launch, they should have an explicit reason and owner.

## Hard stop conditions

Stop and fix before continuing if any of these are true:

```text
service-role key appears in mobile/client env
leaked-password protection remains disabled near final launch
RLS is disabled on money, rights, user, or admin/security tables
Ether cannot write heartbeat into Supabase after Render env insertion
fee_rules does not show 150 bps active Circa Haus platform fee
Supabase advisor reports a high-confidence launch-blocking security warning
```
