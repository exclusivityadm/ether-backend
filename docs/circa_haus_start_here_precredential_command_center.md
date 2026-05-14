# Circa Haus — Start Here Pre-Credential Command Center

This is the master index for the next phase. Use this document first when returning to the workstation or entering provider credentialing.

## Current operating principle

Credentialing should be line-by-line, provider-by-provider, with verification after each group.

Do not add multiple providers at once. Do not move to the next provider group until the current group is verified or clearly classified.

## Current stop line

Before deeper credentialing:

```text
1. Pull latest mobile app.
2. Run Flutter locally.
3. Confirm app boots beyond splash.
4. Capture any Boot Guard error if present.
5. Fix UI boot path before inserting live provider credentials.
```

## Master order

```text
0. UI boot proof
1. Supabase manual security + keys
2. Render / Ether redeploy
3. Ether health/readiness/heartbeat
4. Stripe test-mode credentials
5. OpenAI / Saia credentials
6. ElevenLabs voice credentials
7. Canva / Promo Studio credentials if available
8. Apliiq / Printful credentials
9. Cloudflare / domains
10. Communications providers
11. Post-credential smoke tests
12. Launch-blocker review
```

## Critical docs

### Credentialing execution

```text
docs/circa_haus_credentialing_day_runbook.md
docs/circa_haus_credential_line_items.md
docs/circa_haus_render_env_template_no_secrets.md
docs/circa_haus_supabase_manual_security_steps.md
```

### Testing and triage

```text
docs/circa_haus_post_credential_smoke_tests.md
docs/circa_haus_error_classification_guide.md
docs/circa_haus_launch_blocker_decision_matrix.md
```

### Mobile-side companion docs

In the `circa-haus-mobile` repo:

```text
docs/workstation_ui_stability_and_ether_checklist.md
docs/precredential_ui_authority_plan.md
docs/payment_ui_component_ready_handoff.md
docs/mobile_env_credential_safety_checklist.md
```

## Non-negotiables

```text
No service-role key in mobile/client env.
No provider secret in mobile/client env.
No secret values in GitHub or ChatGPT.
No fake card-entry UI.
No redirect-only payment assumption.
No 0.8% platform fee.
Circa Haus platform fee is 1.5% / 150 bps across app money flows.
Ether must be verified with health, readiness, and heartbeat before trusting provider flow.
Missing grants are configuration/migration contract failures, not generic outages or hostile events.
```

## First workstation commands

```powershell
cd C:\Users\pinks\Desktop\circa-haus-mobile-fresh
git pull origin main
flutter clean
flutter pub get
flutter run -d chrome --web-port 8080
```

If the folder needs to be recloned:

```powershell
cd C:\Users\pinks\Desktop
git clone https://github.com/exclusivityadm/circa-haus-mobile.git circa-haus-mobile-fresh
cd .\circa-haus-mobile-fresh
flutter clean
flutter pub get
flutter run -d chrome --web-port 8080
```

## First expected result

```text
Splash appears.
App moves beyond splash.
Choose/entry surface appears.
No blank screen.
No fatal Boot Guard panel.
```

If Boot Guard appears:

```text
1. Screenshot it.
2. Copy the first terminal error.
3. Classify as UI_BOOT_ERROR.
4. Fix before credentialing.
```

## Supabase first manual steps

```text
1. Open Circa Haus Supabase project.
2. Enable leaked-password protection.
3. Confirm project URL.
4. Confirm publishable/anon key for mobile.
5. Confirm service-role key for Render only.
6. Rerun security advisor.
```

## Render / Ether first verification

After env insertion and redeploy:

```text
GET /health
GET /health/deep
GET /readiness
GET /readiness/circa_haus
GET /providers/circa_haus/readiness
POST /signal/handshake
POST /signal/heartbeat
```

Then Supabase:

```sql
select project_slug, lane, signal_type, status, received_at
from public.ether_signals
order by received_at desc
limit 10;
```

## Payment doctrine reminder

Platform fee:

```text
1.5 percent
150 basis points
0 fixed Circa Haus platform fee cents
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

## Payment UI doctrine reminder

```text
Payment surfaces are component-ready.
Provider zone is replaceable.
No fake card fields.
No redirect-only assumption.
Stripe method can be selected safely after credentialing.
```

## Hard stop conditions

Stop if any of these happen:

```text
Mobile app cannot boot beyond splash.
Service-role key is exposed in mobile/client env.
Provider secret is exposed in GitHub, chat, screenshot, or client logs.
Ether /health fails after Render redeploy.
Ether cannot write heartbeat into Supabase.
Stripe test/live credentials are mixed accidentally.
Platform fee is not 1.5%.
Admin/security route is public without protection.
RLS/grants fail on money, rights, user, or admin/security tables.
```

## Completion definition for this phase

The pre-credential preparation phase is complete when:

```text
All safe docs/checklists are staged.
Mobile payment shell is staged.
Payment surfaces are route-ready but not force-wired into fragile boot path.
Fee doctrine is locked in Supabase.
Supabase manual security steps are known.
Render env template is ready.
Error classification and launch-blocker rules are ready.
Next work is either workstation boot proof or real credential insertion.
```
