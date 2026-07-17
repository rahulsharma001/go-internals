---
type: canonical
domain: system-design
topic: backpressure
status: learning
source_conversations:
  - "System Design Patterns | 2026-07-05 | 6a4aa703-f2d8-83ee-aac3-020aa67e9afb"
  - "MQ vs Pub/Sub vs Kafka | 2026-03-07 | 69abdd63-3e90-8322-bd0e-1d00aacc12c9"
---
# Backpressure Pattern

## Problem it solves

When producers are faster than consumers, backpressure prevents unbounded queues, memory growth, timeouts, and downstream collapse.

## Mental model and how it works

Capacity is finite. Signal or enforce limits upstream through bounded queues, blocked/paused reads, demand/credits, concurrency caps, rate limits, admission control, batching, or load shedding. Queueing delays work; it does not create capacity.

## Concrete example and dry run

Kafka order consumer handles 5,000/s but receives 8,000/s. Lag grows 3,000/s. Autoscale only up to partition count and DB capacity. If DB is saturated, pause partitions, reduce batch/concurrency, shed optional analytics, and reject/throttle new low-priority producers before retention/deadline is exhausted.

## Success and failure scenarios

Success: lag stabilizes and core work meets deadline. Failure: unbounded buffer hides overload until OOM, or retries add more traffic. Use oldest-age alerts, bounded retention, retry budget, DLQ/quarantine, priority lanes, and capacity protection.

## Scaling and production choices

Broker consumer pause/resume, bounded worker pools, HTTP 429/503 with hints, TCP/stream flow control, and queue quotas. Observe arrival/service rate, queue depth and age, saturation, rejection, drop reason, retry amplification, and completion latency.

## Trade-offs and when not to use

Blocking propagates latency; shedding loses/delays work; more buffer absorbs bursts but worsens stale backlog. Do not use a large queue as the only response to sustained overload.

## Interview mistakes and follow-ups

“Kafka handles it”; autoscale past partitions; no user-visible policy; no oldest age. Follow-ups: producer cannot slow? priority? DB bottleneck? retention expires? reconnect storm?

## Five-minute recall

Arrival > service → measure lag/age → bound buffer/concurrency → slow/pause/reject/shed → protect dependency → recover/replay.

Related: [[Rate Limiting Pattern]], [[Bulkhead Pattern]], [[Queues and Pub Sub]], [[Failure Handling Strategy]].

## Source metadata

Sanitized sources above; capacities are illustrative only.
