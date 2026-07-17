---
type: canonical
domain: system-design
topic: latency-throughput-and-capacity
status: active
last_verified: 2026-07-17
---
# Latency Throughput and Capacity

## 1. Problem it solves

Designs fail when latency, throughput, concurrency, and capacity are treated as synonyms. They describe response time, completed work per unit time, simultaneous work, and sustainable resource limits.

## 2. Simple mental model

A pipe has width (throughput), travel time (latency), water currently inside (concurrency), and a safe maximum (capacity). Tail latency matters because a fan-out request is gated by its slowest dependencies.

## 3. How it works

Budget end-to-end latency across network, queue, service, and storage. Measure p50/p95/p99 rather than averages. Use batching/pipelining for throughput, concurrency limits for protection, caching/locality for latency, and queueing for burst absorption.

## 4. Concrete example

At 2,000 requests/s and 200 ms average in-flight time, concurrency is roughly 400. If one request fans to 20 shards, its tail rises with the slowest shard; reducing shard fan-out may beat adding CPU.

## 5. Detailed success flow

01. Admission accepts work within capacity
11. queues remain bounded
21. each dependency consumes a known deadline slice
31. the response meets tail target
41. optional work completes asynchronously.

## 6. Detailed failure flow

01. As utilization approaches saturation, queue time and tail latency climb.
11. Retries add load and cause collapse.
21. Admission control rejects/degrades early, cancels expired work, sheds optional traffic, and alarms on saturation and error-budget burn.

## 7. Scaling behaviour

Scale on saturation and queue age, not CPU alone. Batching reduces overhead but adds waiting latency. Parallelism lowers latency until coordination/resource contention dominates. Account for connection pools, file descriptors, IOPS, memory, network, and provider quota.

## 8. Data consistency implications

Lower latency through replicas/caches often serves older state. Quorum or leader coordination improves freshness but adds network delay. State which operation accepts the trade.

## 9. Real implementation choices

Use histograms for latency; bounded worker pools; connection pooling; CDN/cache for repeated immutable reads; Kafka/SQS for bursty async work. Benchmark safe per-instance capacity rather than inventing it.

## 10. Trade-offs

Batch size versus latency; parallel fan-out versus resource amplification; headroom versus cost; timeout shortness versus false failures; local replica latency versus freshness.

## 11. When not to use it

Do not add asynchronous processing when the caller needs immediate correctness, or parallelize cheap work whose coordination dominates.

## 12. Common interview mistakes

Average latency only; active users as QPS; no peak/skew; infinite concurrency; autoscaling after saturation; retries excluded from capacity; queue depth without age/rates.

## 13. How it appears inside larger systems

Video transcoding, monitoring ingest, chat connections, notification provider quotas, search fan-out, and cache hit/miss paths.

## 14. Likely interviewer follow-ups

What is p99? What happens at 80–90% utilization? How much backlog accrues in an outage? Which dependency owns the deadline? What is the drain time?

## 15. Five-minute revision

Latency=time, throughput=rate, concurrency=in flight, capacity=safe ceiling. Budget tail, account amplification, bound queues/concurrency, keep headroom, measure saturation.

## 16. Related notes

[[Back-of-the-Envelope Estimation]] · [[Finding Bottlenecks]] · [[Backpressure and Load Shedding]] · [[Retry Timeout and Deadline Pattern]]

## 17. Verified further reading

- [AWS Builders’ Library: timeouts, retries, and backoff](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) — explains latency-driven timeout and retry design.
- [OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/) — official definitions for metrics and traces used to measure latency.

