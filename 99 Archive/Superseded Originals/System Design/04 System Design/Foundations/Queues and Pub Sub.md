> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Queues Streams and Pub Sub]].

---
type: canonical
domain: system-design
topic: queues-pub-sub
status: learning
source_conversations:
  - "MQ vs Pub/Sub vs Kafka | 2026-03-07 | 69abdd63-3e90-8322-bd0e-1d00aacc12c9"
  - "Kafka Deep Dive Guide | 2026-06-28 | 6a4107d3-19ac-83ee-a716-51fdbc569f3e"
---
# Queues and Pub Sub

## Problem it solves

Messaging buffers work, distributes it to workers, or broadcasts events to independent subscribers.

## Mental model and how it works

A work queue typically gives one message to one worker group; pub/sub gives each subscription a copy; a durable log/stream retains ordered partition records that consumer groups read by offset. Define retention, acknowledgment, visibility/lease, delivery guarantee, ordering scope, replay, and poison-message handling.

## Concrete example and dry run

`OrderConfirmed` keyed by `order_id` enters a Kafka partition. Payment and notification use separate consumer groups, so both see it. Inside the notification group only one instance owns that partition. The consumer writes business change plus inbox key, then commits offset. Crash after DB commit but before offset commit redelivers; inbox makes it safe.

## Success and failure scenarios

Success: workers scale to partition/queue parallelism and lag recovers. Failure: poison event blocks a partition, hot key overloads one partition, or producer outruns consumers. Apply bounded retries, quarantine/DLQ, schema validation, partition-key review, backpressure/load shedding, and replay tooling.

## Scaling and production choices

Examples: Kafka/Pulsar for replayable streams; SQS/RabbitMQ for work queues; cloud pub/sub for managed fan-out. Kafka ordering is within a partition; consumers beyond partition count add no same-group parallelism. Observe publish failures, broker health, oldest age/lag, processing latency, retries, DLQ, skew, and business outcomes.

## Trade-offs and when not to use

Replayable logs cost storage and operations; queues simplify work dispatch but may not support long replay; pub/sub duplicates delivery cost. Do not add messaging to hide an unclear transaction boundary.

## Interview mistakes and follow-ups

Claiming global order or blanket exactly-once; offset commit before work; no idempotency; no retention. Follow-ups: consumer crash? rebalance? schema change? one hot customer? replay side effects?

## Five-minute recall

Queue vs fan-out vs log → ack/offset → delivery → order scope → partition key → retry/DLQ → replay → lag/skew.

Related: [[Idempotency Pattern]], [[Backpressure Pattern]], [[Change Data Capture]], [[Order Processing System]].

## Source metadata

Sanitized sources above plus current Apache Kafka introduction: https://kafka.apache.org/documentation/.
