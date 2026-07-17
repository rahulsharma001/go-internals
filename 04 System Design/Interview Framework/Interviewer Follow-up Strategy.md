---
type: canonical
domain: system-design
topic: followups
status: active
---
# Interviewer Follow-up Strategy

## Treat follow-ups as changed constraints

Pause, restate the change, identify the affected invariant or flow, compare options, modify the smallest branch, and summarize the new downside. Do not defend the original diagram reflexively.

## Response loop

1. “The new constraint is __.”
2. “It affects __ on the critical path; invariant __ remains/changes.”
3. “Options are A and B.”
4. “I choose B because __; diagram change is __.”
5. “The new risk is __, contained/observed by __.”

## Common branches

| Follow-up | First questions | Typical diagram change |
| --- | --- | --- |
| 100× traffic | which dimension and skew? | partition/cache/batch/admission at first limit |
| region fails | write authority, RPO/RTO? | failover epoch, replicated truth, degraded mode |
| stronger consistency | which operation/invariant? | conditional transaction/quorum/single writer |
| lower cost | dominant compute/storage/egress? | tiering, batching, downsampling, fewer replicas |
| celebrity hotspot | one key or many? | request coalescing, hot replication, hybrid fan-out |
| dependency unreliable | unknown outcome? | deadline, circuit/bulkhead, pending/reconcile |
| global users | reads or writes? residency? | edge/read replicas/home-region ownership |
| delete/privacy | authoritative and derived copies? | deletion workflow, tombstones, audit/reconciliation |

## Clarifying without stalling

Ask one question that changes the choice, then make a labelled assumption. A senior candidate can proceed under ambiguity. Avoid responding with five questions or redesigning unrelated components.

## When challenged

Explain the invariant and evidence, not authority: “A queue improves buffering, but the payment timeout is an unknown outcome, so I still need provider idempotency/reconciliation.” If the interviewer supplies a new fact, update the design explicitly.

## Five-minute revision

Restate changed constraint → locate branch/invariant → alternatives → minimal change → new trade-off/failure/signal → revised summary.

Related: [[README - How to Learn System Design#Level 4 — Adversarial practice|Adversarial practice]] · [[System Design Evaluation Rubric]] · [[Common Interview Traps]].
