---
type: quick-revision
domain: system-design
review_time: 4-minutes
---
# Reliability Checklist

For the critical path, cover:

- end-to-end deadline and shorter per-hop timeout
- retryable conditions, maximum attempts, exponential backoff, jitter, retry budget
- idempotency key/event ID and conflicting-reuse behavior
- circuit breaker and half-open probe
- concurrency limit, queue bound, load shedding priority
- replica placement and failover authority/fencing
- backup, restore test, RPO, RTO
- cache/index/queue rebuild from source of truth
- partial-write/ambiguous-outcome reconciliation
- user-visible degraded behavior

For each failure say: detection → immediate behavior → retry → dedupe → recovery → user outcome → metric/alert.

Do not retry overload indefinitely. Do not fail over writes before fencing the old authority. See [[Reliability and Failure Analysis]].
