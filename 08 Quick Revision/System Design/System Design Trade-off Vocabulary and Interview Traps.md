---
type: quick-revision
domain: system-design
---

# System Design Trade-off Vocabulary and Interview Traps

## Useful vocabulary

Authoritative vs derived; durable vs ephemeral; strict vs bounded-stale; availability vs correctness; throughput vs latency; average vs tail; fan-out-on-write vs read; synchronous coupling vs asynchronous lag; horizontal scale vs coordination; single writer vs conflict resolution; hot path vs control plane; recovery point vs recovery time; isolation vs utilization; safety vs liveness.

Use: “I choose X because requirement Y needs semantic Z. The downside is C. I bound it with M and observe N.”

## Common traps

- Drawing before agreeing on scope/invariants.
- Inventing traffic numbers or calculating dimensions that change nothing.
- Naming Kafka/Redis/Kubernetes without a responsibility.
- Claiming exactly-once end to end; omit idempotent consumer/inbox.
- Queue without bounds, backlog age, retry/DLQ, ordering or poison path.
- Cache without source of truth, staleness, invalidation or stampede.
- Retry without deadline, jitter, safety or retry budget.
- Sharding without access pattern, key skew, rebalancing or cross-shard query.
- Two regions without write authority, partition behavior, fencing or failback.
- “JWT secures it” without object authorization, expiry/audience, abuse limits, PII/secrets.
- Metrics without SLI/user outcome; alerts without owner/action/runbook.
- Failure path ends at “send to DLQ” instead of repair and terminal state.
- Making unsupported personal production/scale claims.

Finish by restating the invariant, complete flow, primary bottleneck, recovery, and deliberate compromise.
