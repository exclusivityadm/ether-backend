# Ether Trust Ratchet, Agent Kernel, and Web Intelligence

## Non-negotiable boundary

Ether is the privileged custodian for every registered application. Applications and agents request capabilities from Ether; they do not receive Supabase service-role credentials or provider secrets simply because they are trusted clients.

## Rotating trust lane

For projects with a configured signal secret, each authenticated transition uses:

- project identity
- lane identity
- app/instance identity
- ratchet generation
- fresh Ether server nonce
- fresh client nonce
- HMAC-SHA256 proof derived over the complete context

A successful verification advances the generation and rotates the server nonce before the next interaction. Previously observed proof material is therefore not a reusable bearer credential.

The server returns the next public challenge nonce, never the shared secret or a future proof. Clients independently derive the next proof only when the next interaction occurs.

## Latency doctrine

AI reasoning is not permitted in the ordinary authentication/database fast path.

Fast path:

1. resolve project/lane
2. verify deterministic cryptographic proof
3. apply deterministic control/security policy
4. retrieve or mutate the minimum authorized data
5. reduce/filter response for the requesting project
6. return result

Agent path:

- observe external changes
- maintain compact verified memory
- analyze security/operational telemetry
- prepare provider capability state
- recommend optimization/recovery actions

Agent work should precompute state consumed by the fast path rather than make ordinary user requests wait for model inference.

## Agent authority

The Agent Kernel issues short-lived capability leases scoped to:

- agent identity
- project slug
- explicit capabilities
- expiration

A lease does not contain database or provider credentials. Privileged execution remains an Ether Core responsibility.

Built-in agent classes:

- `web_intelligence`
- `sentinel`
- `optimization`
- `provider_intelligence`
- `recovery`
- `memory`

## Web intelligence boundary

Web content is hostile/untrusted input. The Web Intelligence registry stores registered source metadata, compact fingerprints, evidence references, and change observations. Browser/fetch executors remain separate from privileged data access.

Execution path policy starts with the cheapest safe class:

1. `http_fetch` for non-JavaScript public sources
2. `lightweight_browser` for JavaScript-rendered sources
3. `isolated_browser` for interactive or authenticated browsing

No browser executor receives Supabase service-role credentials.

## Performance instrumentation

Ether records request latency in-memory and exposes internal summaries at `/intelligence/latency` with p50/p95/p99/max measurements by method/path.

Initial engineering targets (to validate under production-like load rather than assume):

- cryptographic/security compute: single-digit milliseconds on ordinary paths
- avoid AI/model calls on ordinary reads/writes
- keep Ether intermediary overhead below user-perceptible thresholds wherever network topology allows
- prioritize correctness over latency for payouts, admin recovery, destructive operations, and active security incidents

## Next production hardening

Before merging a client-breaking ratchet change:

- update each client handshake implementation to derive `ether-ratchet-v1` proof material
- add durable/distributed lane state for multi-instance Ether deployment
- define bounded resynchronization/recovery behavior for interrupted rotations
- benchmark handshake/heartbeat and end-to-end DB request p50/p95/p99
- persist Web Intelligence source/change state in an Ether-owned store
- add outbound domain/network policy before automated fetching/browser execution
- add production background scheduling/queueing for agent jobs
