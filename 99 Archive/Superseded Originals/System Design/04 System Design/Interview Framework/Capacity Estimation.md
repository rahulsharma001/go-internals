> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Back-of-the-Envelope Estimation]].

---
type: canonical
domain: system-design
topic: capacity-estimation
status: learning
source_conversations:
  - "System Design Practice Tips | 2025-05-04 | 681749e6-1698-8013-bb4c-22bcf122748c"
---
# Capacity Estimation

## Problem it solves

Estimation identifies which constraint changes the architecture: QPS, write volume, storage, bandwidth, fan-out, connections, or a hot key.

## Mental model and method

Use round assumptions and show units. Derive average operations/second from daily operations, then apply a labeled peak factor. Estimate payload bytes, retention, read/write ratio, concurrent connections, and replication overhead only when relevant. The result is an order of magnitude, not a forecast.

## Concrete example and dry run

Assume a notification system receives 100 million notification requests/day, 1 KB each, with a 5× peak. Average is about `100,000,000 / 86,400 ≈ 1,200 requests/s`; peak is about 6,000/s. Raw request payload is roughly 100 GB/day before indexes, replication, provider responses, or status history. If each request fans to two channels, downstream delivery attempts peak near 12,000/s.

The architectural consequences—not precision—matter: asynchronous buffering, partitioned workers, provider rate limits, retention tiers, and queue-age alerts. State that these are interview assumptions, not real production metrics.

## Success and failure scenarios

Success: one estimate justifies partition count, storage lifecycle, or CDN. Failure: ten minutes of arithmetic never influence a choice, or averages hide peaks. Recalculate only the dimension behind the suspected bottleneck.

## Scaling and production choices

Useful formulas: `QPS = operations / seconds`; `storage = writes × bytes × retention × replicas`; `bandwidth = QPS × payload`; `concurrency ≈ arrival rate × service time` (Little’s Law intuition). Technologies are examples: object storage for large immutable blobs, Kafka/Pub/Sub for durable event buffering, Redis for bounded hot state, relational/NoSQL stores according to invariants.

## Trade-offs and when not to use

More headroom costs money; compression trades CPU for bandwidth; batching improves throughput but adds latency; replication multiplies storage. Skip detailed estimates for tiny internal systems unless the interviewer asks—state why a single-node design is initially sufficient.

## Interview mistakes and follow-ups

Missing units, false precision, no peak factor, ignoring fan-out, and treating active users as QPS. Follow-ups: storage after three years? One celebrity/hot tenant? Connection count? Egress/CDN cost? Queue growth during a one-hour outage?

## Five-minute recall

Traffic → peak → payload → storage/retention/replicas → bandwidth → concurrency/fan-out → first bottleneck → architecture consequence.

Related: [[Requirements and Scope]], [[Scalability and Availability]], [[Partitioning and Sharding]].

## Source metadata

Method curated from the existing framework and source conversation; all numbers above are labeled examples.
