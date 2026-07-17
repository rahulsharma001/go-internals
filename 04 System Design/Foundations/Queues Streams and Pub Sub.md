---
type: canonical
domain: system-design
topic: queues-streams-and-pub-sub
status: active
last_verified: 2026-07-17
---
# Queues Streams and Pub Sub

## 1. Problem it solves

Synchronous callers should not absorb all burst, processing time, or downstream failure. Queues distribute work; streams preserve ordered retained records; pub/sub broadcasts transient or durable events depending on product.

## 2. Simple mental model

A queue is a work inbox; a stream is a replayable ordered log split into partitions; pub/sub is a delivery relationship. Always define producer, consumer, key, retention, acknowledgement, retry, ordering, and backpressure.

## 3. How it works

Producer durably publishes a job/event. Broker partitions/routes it. Consumer processes and acknowledges/checkpoints. At-least-once delivery requires idempotency. Visibility timeout or consumer offsets enable reclaim. DLQ/quarantine is an investigation state, not recovery completion.

## 4. Concrete example

Order outbox events enter a Kafka topic keyed by order ID; each consumer group has independent offsets and per-order order within a partition. A thumbnail job can use SQS-like queue with visibility timeout.

## 5. Detailed success flow

01. After business commit, producer publishes
11. broker replicates
21. consumer owns a partition/job, performs an idempotent transaction, then advances offset/ack.
31. Lag and age remain within SLO.

## 6. Detailed failure flow

01. Consumer commits side effect then crashes before ack.
11. Redelivery finds inbox/event ID and returns stored result.
21. Poison work retries only transient faults, then quarantines with replay tooling and operator-visible state.

## 7. Scaling behaviour

Increase partitions/queues for parallelism, but key ordering limits one key to one partition. Batch/prefetch improves throughput; observe lag/oldest age. More consumers cannot fix a saturated downstream.

## 8. Data consistency implications

Brokers do not make cross-system business exactly-once. Ordering is usually per partition/key, not global. Events may be stale/out of order across topics; include versions and idempotency.

## 9. Real implementation choices

Kafka/Pulsar/Kinesis for retained partitioned streams; SQS/RabbitMQ for work queues; cloud pub/sub for managed fan-out; Redis Pub/Sub only for disposable live messages, not durable history.

## 10. Trade-offs

Async decouples and buffers but adds lag, duplicates, state machines, and operations. Long retention enables replay but costs storage. More partitions improve throughput but weaken ordering scope and increase overhead.

## 11. When not to use it

Do not add a broker for a simple low-volume synchronous operation without burst/failure/decoupling need. Do not queue work whose caller requires immediate completion unless status semantics are explicit.

## 12. Common interview mistakes

Queue without bounds/age; DLQ as fix; claiming exactly once; bytes/media in messages; no partition key; ack before side effect; retrying permanent errors; no schema evolution.

## 13. How it appears inside larger systems

Order/payment events, notification delivery, video transcodes, analytics/logging pipelines, crawlers, schedulers, and feed fan-out.

## 14. Likely interviewer follow-ups

Queue or stream? Delivery guarantee? Partition key/order? Ack point? Retention/replay? Poison work? Backpressure? Schema evolution? Regional failure?

## 15. Five-minute revision

Producer → durable broker → key/partition → consumer → local idempotent commit → ack/offset. Define duplicates, order, retry/quarantine, lag/age, retention, and replay.

## 16. Related notes

[[Synchronous vs Asynchronous Communication]] · [[Backpressure and Load Shedding]] · [[Deduplication and Inbox Pattern]] · [[Transactional Outbox Pattern]]

## 17. Verified further reading

- [Apache Kafka documentation](https://kafka.apache.org/documentation/) — official partitions, consumers, delivery, and operations.
- [Redis use cases](https://redis.io/docs/latest/develop/use-cases/) — official examples distinguishing job queues, pub/sub, and streams.

