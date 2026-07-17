---
type: quick-revision
domain: system-design
review_time: 5-minutes
---
# System Pattern Selection Guide

| Pressure or boundary | Consider | Mandatory question |
| --- | --- | --- |
| repeated read overwhelms owner | [[Caching Pattern]] | freshness, invalidation, miss/source capacity? |
| simultaneous expiry/hot key | [[Cache Invalidation and Stampede]] | one refresher, TTL jitter, stale limit? |
| retried command can duplicate effect | [[Idempotency Pattern]] | logical key, result retention, conflicting reuse? |
| database commit must emit event | [[Transactional Outbox Pattern]] + [[Change Data Capture]] | who relays, dedupes, and monitors lag? |
| consumer may receive duplicates | [[Deduplication and Inbox Pattern]] | inbox key and atomicity with effect? |
| workflow crosses state owners | [[Saga Pattern]] | compensation, irreversible step, reconciliation? |
| dependency overload/failure | [[Retry Timeout and Deadline Pattern]], [[Circuit Breaker Pattern]], [[Bulkhead Pattern]] | deadline, retry budget, isolation, probe? |
| producers exceed consumers | [[Backpressure and Load Shedding]] | queue bound, admission, priority, user outcome? |
| quota or abuse control | [[Rate Limiting Pattern]] | scope, algorithm, strictness, failure mode? |
| key ownership changes with nodes | [[Consistent Hashing Pattern]] | virtual shards, weights, movement, failure domains? |
| one current coordinator/worker | [[Leader Election]] or [[Distributed Locking]] | lease, fencing token, stale owner? |
| read/write shapes diverge | [[CQRS]] | rebuild, freshness, operational cost? |
| full event history is the product | [[Event Sourcing]] | schema evolution, replay, snapshots, audit need? |
| feed/notification recipients fan out | [[Fan-out on Write vs Fan-out on Read]] | celebrity/skew and freshness? |

Select a pattern only after naming the problem it solves and the new failure mode it creates.
