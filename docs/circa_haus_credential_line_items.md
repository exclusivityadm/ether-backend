# Circa Haus Line-by-Line Credential Tracker

Use this tracker during credentialing. The goal is to add one provider group at a time, redeploy only when needed, test immediately, and avoid destabilizing multiple systems at once.

## Absolute rule

Do not paste actual secret values into this document, GitHub, ChatGPT, screenshots, support tickets, or any mobile/client environment.

This document tracks the existence, destination, and verification status of credentials only.

## Status meanings

```text
not_started      = not collected yet
collected        = owner has found/copyable value in provider dashboard
inserted         = value has been placed in its correct destination
redeployed       = Render/app has been restarted or rebuilt after insertion
verified         = readiness/smoke test passed
blocked          = provider/dashboard/action needed
not_required_now = not needed for launch or intentionally deferred
```

## Phase 0 — UI boot proof before deeper credentialing

| Item | Destination | Status | Verification |
| --- | --- | --- | --- |
| Pull latest `circa-haus-mobile` main | Workstation | not_started | `git pull origin main` |
| Flutter dependency refresh | Workstation | not_started | `flutter pub get` |
| Chrome boot test | Workstation | not_started | `flutter run -d chrome --web-port 8080` |
| App moves beyond splash | Workstation | not_started | No blank screen / no fatal Boot Guard |
| Boot Guard error captured if present | Workstation | not_started | Screenshot or terminal output saved |

## Phase 1 — Supabase

| Item | Destination | Status | Verification |
| --- | --- | --- | --- |
| Confirm Circa Haus project and plan | Supabase dashboard | not_started | Project visible and active |
| Enable leaked-password protection | Supabase Auth Security | not_started | Security advisor warning clears |
| Project URL | Render + mobile env | not_started | Readiness check can see Supabase URL |
| Publishable/anon key | Mobile env only | not_started | App initializes Supabase client safely |
| Service-role key | Render only | not_started | Ether can query/write server-side tables |
| Security advisor recheck | Supabase dashboard | not_started | Only acceptable non-launch blockers remain |

## Phase 2 — Render / Ether

| Item | Destination | Status | Verification |
| --- | --- | --- | --- |
| Render service points to latest `ether-backend` main | Render | not_started | Latest deploy uses current GitHub commit |
| Core Ether env inserted | Render env | not_started | `/health` and `/version` respond |
| Circa Haus Supabase env inserted | Render env | not_started | `/health/deep` sees Supabase |
| Render redeploy completed | Render | not_started | Service restarted after env updates |
| Ether health check | Browser/API | not_started | `GET /health` passes |
| Deep health check | Browser/API | not_started | `GET /health/deep` passes or reports precise missing providers |
| Project readiness check | Browser/API | not_started | `GET /readiness/circa_haus` returns structured status |
| Provider readiness check | Browser/API | not_started | `GET /providers/circa_haus/readiness` returns provider matrix |
| Signal handshake | Browser/API | not_started | `POST /signal/handshake` passes |
| Signal heartbeat | Browser/API | not_started | `POST /signal/heartbeat` passes |
| Supabase signal row verified | Supabase SQL | not_started | `public.ether_signals` has latest row |

## Phase 3 — Stripe

| Item | Destination | Status | Verification |
| --- | --- | --- | --- |
| Stripe publishable key | Mobile env | not_started | Client can identify Stripe publishable config |
| Stripe secret key | Render only | not_started | Provider readiness reports Stripe server configured |
| Stripe Connect client ID if used | Render only | not_started | Connect readiness passes |
| Stripe webhook endpoint created | Stripe dashboard | not_started | Endpoint points to Ether webhook route |
| Stripe webhook signing secret | Render only | not_started | Test event verifies signature |
| Stripe test event sent | Stripe dashboard | not_started | Ether receives webhook event |
| Payment UI pending state verified | Mobile app | not_started | Payment shell renders without fake card fields |
| Payment provider-ready state verified | Mobile app + Ether | not_started | Payment surface transitions cleanly after Stripe config |

## Phase 4 — OpenAI / Saia

| Item | Destination | Status | Verification |
| --- | --- | --- | --- |
| OpenAI API key | Render only | not_started | Provider readiness reports OpenAI configured |
| Text model selected | Render env | not_started | Saia text route/config check passes |
| Image model selected | Render env | not_started | Saia merch ideation route/config check passes |
| Saia rights guidance check | App/Ether | not_started | Guidance can render or return provider-ready state |
| Saia merch ideation guardrails check | App/Ether | not_started | Protected-brand/copyright warning path present |

## Phase 5 — ElevenLabs

| Item | Destination | Status | Verification |
| --- | --- | --- | --- |
| ElevenLabs API key | Render only | not_started | Provider readiness reports voice configured |
| Talethia voice ID | Render env | not_started | Voice config check recognizes primary voice |
| Ava backup voice ID | Render env | not_started | Voice config check recognizes backup voice |
| Voice consent flow remains gated | App | not_started | Mic permission is not requested until user action |

## Phase 6 — Canva / Promo Studio

| Item | Destination | Status | Verification |
| --- | --- | --- | --- |
| Canva developer/partner path confirmed | Canva dashboard | not_started | Credential path is known |
| Canva client ID | Render only if needed | not_started | Provider readiness reports configured if available |
| Canva client secret | Render only if needed | not_started | Provider readiness reports configured if available |
| Canva webhook/callback configured | Canva dashboard | not_started | Callback uses approved public Ether/app URL |
| Promo Studio pending state verified | App | not_started | Surface is polished if Canva not live yet |

## Phase 7 — Apliiq / Printful / Merch Studio

| Item | Destination | Status | Verification |
| --- | --- | --- | --- |
| Apliiq credential/access confirmed | Apliiq dashboard | not_started | Provider readiness reports available/configured |
| Printful token/access confirmed | Printful dashboard | not_started | Provider readiness reports available/configured |
| Merch webhook URLs configured if supported | Provider dashboards | not_started | Ether webhook route receives test event if available |
| Provider print profiles visible | Supabase/App | not_started | Apliiq/Printful profile records available |
| Publish-readiness gate tested | App/Ether | not_started | Creator approval + rights + preflight required |

## Phase 8 — Cloudflare / Domains

| Item | Destination | Status | Verification |
| --- | --- | --- | --- |
| `circahaus.app` purchased if affordable | Cloudflare | not_started | Domain visible in Cloudflare |
| `circahaus.dev` purchased if affordable | Cloudflare | not_started | Domain visible in Cloudflare |
| `circahaus.com` purchased if normal price | Cloudflare | not_started | Domain visible in Cloudflare |
| Public routes planned | DNS/app host | not_started | `.com` for trust/legal/support, `.app` for product |
| Admin/security protection planned | Cloudflare Access | not_started | `.dev` protected before sensitive surfaces go live |

## Phase 9 — Communications

| Item | Destination | Status | Verification |
| --- | --- | --- | --- |
| Google Workspace support/admin inboxes | Google Workspace | not_started | Support/admin email works |
| Twilio account/number if used | Twilio dashboard | not_started | Provider readiness/pending status known |
| SES sender/domain if used | AWS SES | not_started | Email sending status known |
| No comms secrets in client | Mobile repo/env | not_started | Static scan remains clear |

## One-provider-at-a-time verification loop

For each provider:

```text
1. Collect value in provider dashboard.
2. Place it only in the correct destination.
3. Redeploy/rebuild only if necessary.
4. Run the matching readiness check.
5. Capture exact error if it fails.
6. Fix that provider before moving on.
```

## Final credentialing success definition

Credentialing is successful when:

- Mobile app boots beyond splash.
- Ether is running latest code.
- Ether health/deep health pass.
- Ether writes a verified Circa Haus heartbeat into Supabase.
- Stripe minimum readiness passes.
- Saia/OpenAI readiness passes or is clearly isolated.
- Required provider readiness checks pass or are explicitly non-launch-blocking.
- Payment UI remains component-ready.
- Platform fee remains 1.5 percent everywhere.
- No secret/server credential appears in mobile/client code or env.
