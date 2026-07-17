> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[15-Minute Interview Launchpad]].

---
type: quick-revision
domain: system-design
canonical: "[[System Design Interview Framework]]"
---

# System Design 15-Minute Revision

## Minute 0–2: frame

Clarify core users/actions, non-goals, correctness invariant, scale dimensions, latency/availability/durability, consistency, retention, and regions. Mark assumptions; never invent product scale.

## Minute 2–5: contract and state

- Entities, ownership, lifecycle/status.
- API/event inputs, outputs, errors, pagination, idempotency.
- Source of truth, key/index, constraints/version.
- Which views may be stale?

## Minute 5–8: smallest architecture

Client → edge/gateway → stateless service → authoritative storage. Add cache, queue/stream, workers, search/read model, CDN, or regions only for a stated requirement. Name component responsibility and data direction.

## Minute 8–11: prove flows

Success: entry → validation → commit point → side effects → response/event → observable completion.

Failure: dependency timeout/unknown outcome → deadline → idempotent bounded retry → circuit/isolation → pending/degraded result → reconciliation/compensation/manual repair.

Also test duplicate request/event, race, poison work, slow consumer, stale cache, and hot key.

## Minute 11–13: scale and operate

Find the first bottleneck. Explain partition key, skew/hot spot, replication/failover, queue bounds/backpressure, cache invalidation, restore/replay. Observe latency/errors/traffic/saturation plus backlog age, lag, stuck workflow, compensation, and business correctness.

## Minute 13–15: secure and conclude

AuthN, resource AuthZ, transport encryption, secret/PII minimization, abuse/rate limits, audit. Summarize architecture, invariant, failure recovery, and one central trade-off.

Answer pattern: “Requirement X needs semantic Y, so I choose Z. It costs C; I contain it with M and monitor N.”

Companions: [[System Design Interview Checklist]] · [[Pattern Selection Guide]] · [[Database Selection Guide]]

