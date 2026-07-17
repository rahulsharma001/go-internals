---
type: quick-revision
domain: system-design
review_time: 5-minutes
---
# Cache and Messaging Selection Guide

## Cache decision

State all eight: cached object, key, value, source of truth, TTL, invalidation, miss behavior, failure behavior.

| Pattern | Use when | Main risk |
| --- | --- | --- |
| cache-aside | application can own miss/fill | stale fill and stampede |
| read-through | shared cache layer owns loading | hidden source coupling |
| write-through | read freshness after cache-mediated writes | write latency and cache dependence |
| write-behind | loss/reordering is explicitly tolerated | cache becomes temporary authority |
| CDN | public/authorized edge-cacheable bytes | purge delay and cache-key/privacy errors |

Mitigate stampede with TTL jitter, one refresher, bounded stale-while-revalidate, and source load shedding.

## Messaging decision

| Need | Candidate | Ask next |
| --- | --- | --- |
| work distribution and per-message retry | SQS/RabbitMQ | visibility lease, DLQ, duplicate effect |
| ordered replay and many consumers | Kafka/Kinesis | partition key, retention, lag, reprocessing |
| transient broadcast | pub/sub | offline behavior and durability |

Never say the broker gives exactly-once external effects. Define commit-before-publish, idempotent consumer, ordering key, retry/DLQ, and backlog behavior. See [[Caching Pattern]] and [[Queues Streams and Pub Sub]].
