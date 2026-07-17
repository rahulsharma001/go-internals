---
type: canonical
domain: system-design
topic: failure-analysis
status: active
---
# Reliability and Failure Analysis

## Method: fail every arrow and state transition

For each dependency ask: timeout before/after possible commit, connection reset, slow response, corrupt/invalid result, partial batch, duplicate, reordering, total outage, recovery. For each store ask: unavailable, replica lag, lost quorum, disk/full quota, restore, region loss. For each queue ask: duplicate, poison message, lag, retention expiry, consumer crash.

## Failure-flow template

1. **Detection:** timeout, health/circuit signal, checksum, version conflict, lag/SLO alert.
2. **Immediate behavior:** fail fast, pending response, stale fallback, queue, shed, or isolate.
3. **Retry policy:** only transient/safe work; end-to-end deadline, exponential backoff, jitter, cap, budget.
4. **Idempotency/deduplication:** stable command/event identity and durable stored result.
5. **Recovery:** replay, reconcile, compensate, restore, fail over/fail back, manual repair.
6. **User-visible result:** unavailable, pending, degraded, conflict, or safely completed.
7. **Observability:** business correctness plus technical symptoms.

## Unknown outcomes

A timeout after sending a mutation does not say whether it committed. Query by idempotency key/provider reference, return `PENDING`, or reconcile before repeating. The same principle protects payments, bookings, uploads, notifications, and distributed jobs.

## Overload is a failure mode

Bound queues, concurrency, buffers, and retry budgets. Preserve critical work by priority/isolation; shed optional analytics, typing, thumbnails, or bulk notifications first. Retries can amplify overload, so coordinate them at one layer.

## Redundancy is not recovery

Replication handles some live faults; backups and restore handle deletion/corruption. Define RPO (acceptable data loss) and RTO (acceptable recovery time), test restore and failback, and reconcile data after recovery. Multi-region requires an authority/conflict policy.

## Graceful degradation examples

- serve stale product metadata but never stale inventory confirmation;
- keep chat history/catch-up while dropping presence/typing;
- accept video upload while delaying optional renditions;
- preserve redirects while shedding analytics;
- pause new jobs while letting owned leases complete safely.

## Common mistakes

“Retry three times,” DLQ as the end of recovery, no deadline, compensating an unknown outcome, multi-region without fencing, alerting only CPU, unbounded backlog, and declaring exactly-once without application state.

## Five-minute revision

Fail arrow → detect → immediate behavior → deadline/retry → identity → recovery/repair → user state → signal. Then zone/region, backup/restore, failback, and post-recovery consistency.

Related: [[Retry Timeout and Deadline Pattern]] · [[Circuit Breaker Pattern]] · [[Bulkhead Pattern]] · [[Backpressure and Load Shedding]] · [[Multi-Region Design]] · [[Observability and SLOs]].

