> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[System Pattern Selection Guide]].

---
type: quick-revision
domain: system-design
---

# Pattern Selection Guide

Start from the failure or invariant, not the pattern name.

- Expensive repeated read → cache; define owner, TTL/invalidation, staleness, stampede protection.
- Duplicate client/event → idempotency; stable key, durable result, payload conflict rule.
- Rare transient fault → retry; safe operation, deadline, exponential backoff+jitter, retry budget.
- Sustained dependency failure → circuit breaker; fail fast, half-open recovery, fallback semantics.
- One tenant/dependency exhausts shared resources → bulkhead; isolate pools/queues and reserve priority capacity.
- Producer faster than consumer → backpressure; bounded queue, admission control, shed/expire order.
- Protect capacity/fairness → rate limit; identify key, scope, algorithm, distributed consistency, reject/degrade policy.
- Cross-service transaction → saga; persisted state, idempotent participants, compensation/manual repair.
- Database update plus broker event → transactional outbox; CDC/poller and inbox/deduplication.
- Read/write models diverge materially → CQRS; authoritative write model, projection lag/rebuild.
- Cross-process exclusive action → first consider constraint/idempotency/partition ownership; otherwise lease + fencing lock.
- One coordinator → leader election; quorum, epoch fencing, election downtime.

Avoid pattern stacking. Walk one success and one failure; if you cannot explain state, ownership, repair, and signals, the pattern is not selected yet.

Canonical recall: [[Patterns Quick Revision]]

