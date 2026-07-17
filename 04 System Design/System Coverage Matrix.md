---
type: curriculum-map
domain: system-design
status: active
---
# System Coverage Matrix

Use this matrix to choose the next system by **missing reasoning pattern**, not by brand recognition. A check means the concept materially changes the design or critical flow; it does not mean the system is the only place to learn it.

## System-to-challenge map

| Tier | System | Primary workload | Strictest invariant | Best first deep dive | Core concepts exercised |
| --- | --- | --- | --- | --- | --- |
| 1A | [[URL Shortener]] | high-read lookup | one code resolves predictably under the chosen reuse policy | code generation and redirects | caching, partitioning, replication, hot keys, abuse, multi-region reads |
| 1A | [[Rate Limiter System]] | admission on every request | one policy defines a bounded allowance and overshoot | distributed token accounting | caching, partitioning, atomic counters, consistency, skew, fail-open/closed |
| 1A | [[Notification System]] | high-write asynchronous delivery | a logical notification is not multiplied by redelivery | delivery state and provider uncertainty | queues, retries, idempotency, fan-out, rate control, observability |
| 1B | [[Order Processing System]] | transactional workflow | accepted state transitions and stock/payment effects remain reconcilable | saga and outbox | transactions, idempotency, outbox, CDC, queues, consistency |
| 1B | [[Payment System]] | money movement | ledger value is conserved and a command is not charged twice | ledger and idempotency | SQL transactions, ledger, reconciliation, provider uncertainty, security |
| 1B | [[Event Ticket Booking System]] | contested inventory | a seat cannot be sold twice | reservation lease and fencing | conditional writes, locking, TTL, idempotency, hot inventory, payment saga |
| 1C | [[News Feed System]] | high-read personalized fan-out | each feed item refers to an authorized, existing post | hybrid fan-out | caching, partitioning, queues, fan-out, celebrity skew, ranking |
| 1C | [[WebSocket Chat or Realtime System]] | long-lived realtime connections | durable message identity and per-conversation order are explicit | ordering and reconnect | WebSocket, presence, pub/sub, partitioning, dedupe, backpressure |
| 1C | [[Uber System Design]] | realtime geospatial matching | one driver cannot accept two active trips | nearby-driver matching | geospatial index, streaming, transactions, location freshness, multi-region |
| 1D | [[YouTube System Design]] | media upload and delivery | accepted upload remains durable before processing | transcoding pipeline | blob storage, CDN, queues, metadata, streaming, hot content |
| 1D | [[File Storage and Synchronization System]] | blob sync across clients | committed file versions never point to missing durable content | conflict resolution | chunking, object storage, metadata transactions, sync, dedupe, multi-region |
| 1E | [[Distributed Job Scheduler]] | timed distributed work | only the current fencing token may commit an attempt | leases and fencing | scheduling, queues, sharding, leader election, retries, fairness |
| 1E | [[Distributed Cache System]] | ultra-low-latency reads | cache is derived and old versions cannot replace new ones | membership and movement | consistent hashing, replication, eviction, hot keys, stampede, overload |
| 1E | [[Search Autocomplete System]] | prefix search under tight latency | published index versions are internally consistent | index construction and ranking | search indexing, caching, replication, streaming, personalization, abuse |
| 2 | [[Monitoring System]] | time-series ingest and alerting | missing data is explicit and one alert generation is logical | rule evaluation | TSDB, streaming, sharding, cardinality, leader election, SLOs |
| 2 | [[Logging and Metrics Pipeline]] | bursty telemetry write pipeline | accepted batches are durable and tenants are isolated | ingest backpressure | streaming, batching, tiered storage, indexing, cardinality, observability |
| 2 | [[Web Crawler System]] | network-bound high write | robots and per-host policy are enforced before fetch | polite frontier | queues, sharding, rate limits, blob storage, dedupe, security |
| 2 | [[API Gateway System]] | policy on every request | one config snapshot and no unsafe retry per request | config rollout | load balancing, rate limits, deadlines, bulkheads, security, multi-region |

## Concept-to-system index

| Dimension | Reconstruct these systems | Transfer question |
| --- | --- | --- |
| Caching | [[URL Shortener]], [[News Feed System]], [[Distributed Cache System]], [[Search Autocomplete System]] | What is the key/value, source of truth, staleness bound, invalidation, and miss behavior? |
| Partitioning | every Tier 1E system; [[WebSocket Chat or Realtime System]], [[Monitoring System]], [[Web Crawler System]] | Which ownership unit keeps related state together, and how is a request routed? |
| Replication | [[Distributed Cache System]], [[YouTube System Design]], [[Monitoring System]], [[File Storage and Synchronization System]] | Is the replica for availability, read scale, durability, or geography? |
| Queueing | [[Notification System]], [[Order Processing System]], [[YouTube System Design]], [[Distributed Job Scheduler]] | What commits before enqueue, what is replayed, and how are duplicates handled? |
| Streaming | [[Uber System Design]], [[Logging and Metrics Pipeline]], [[Monitoring System]], [[Web Crawler System]] | What ordering key and retention make replay useful? |
| Transactions | [[Order Processing System]], [[Payment System]], [[Event Ticket Booking System]] | Which invariant fits one state owner, and which crosses owners? |
| Idempotency | [[Payment System]], [[Order Processing System]], [[Notification System]], [[Distributed Job Scheduler]] | What identifies the logical operation and how is conflicting reuse rejected? |
| Realtime communication | [[WebSocket Chat or Realtime System]], [[Uber System Design]], [[Notification System]] | What is durable versus ephemeral, and how does reconnect catch up? |
| Blob storage | [[YouTube System Design]], [[File Storage and Synchronization System]], [[Web Crawler System]], [[Logging and Metrics Pipeline]] | Which metadata commits reference immutable bytes, and how are orphans reconciled? |
| Geospatial search | [[Uber System Design]] | How does cell size, freshness, movement, and hotspot expansion affect matching? |
| Search indexing | [[Search Autocomplete System]], [[Web Crawler System]], [[Logging and Metrics Pipeline]] | Is the index authoritative or rebuildable, and how is a version published? |
| Fan-out | [[News Feed System]], [[Notification System]], [[WebSocket Chat or Realtime System]] | Which side pays the cost, and what happens for a celebrity or offline user? |
| Scheduling | [[Distributed Job Scheduler]], [[Web Crawler System]], [[Monitoring System]] | What defines eligibility, ownership, lateness, and stale-worker fencing? |
| Consistency | [[Payment System]], [[Event Ticket Booking System]], [[File Storage and Synchronization System]], [[Distributed Cache System]] | Which read or write requires a strict guarantee and which can expose staleness? |
| Multi-region | [[URL Shortener]], [[Uber System Design]], [[YouTube System Design]], [[API Gateway System]] | Is write authority single-home, and how is split brain fenced? |
| Security | [[API Gateway System]], [[Payment System]], [[Web Crawler System]], [[File Storage and Synchronization System]] | What is the trust boundary, sensitive state, abuse path, and least-privilege owner? |
| Observability | every system; emphasize [[Monitoring System]] and [[Logging and Metrics Pipeline]] | Which user-level SLI reveals broken correctness before a component metric does? |

## Deliberate progression

1. Reconstruct one system from each Tier 1 row group before breadth systems.
2. When a rubric dimension scores below 70%, choose the next system from that concept row.
3. Repeat the same concept in a different workload and explain what transferred and what changed.
4. Record observed gaps only in [[Common Mistakes and Re-test Queue]].

Related: [[System Design Dashboard]] · [[README - How to Learn System Design]] · [[System Design Practice Tracker]].
