---
type: canonical
domain: system-design
topic: backpressure-and-load-shedding
status: active
last_verified: 2026-07-17
---
# Backpressure and Load Shedding

## 1. Problem it solves

When producers create work faster than consumers/downstream can complete it, latency, memory, queues, and retries grow until the system collapses.

## 2. Simple mental model

Backpressure tells upstream to slow down; load shedding refuses/expires lower-value work to protect useful work. A bounded system chooses what not to do.

## 3. How it works

Bound queues, buffers, concurrency, payload, and deadlines. Expose 429/503/retry-after, pause consumers/producers, use credits/flow control, prioritize, expire stale work, sample/drop optional events, and admission-control before scarce resources.

## 4. Concrete example

Chat gateway drops typing/presence first, then closes a slow socket and relies on durable history catch-up. It never lets per-connection buffers grow unbounded.

## 5. Detailed success flow

01. Arrival ≤ service or short bursts fit bounded buffer
11. producers adapt
21. queue age meets SLO
31. critical work uses reserved capacity.

## 6. Detailed failure flow

01. Downstream slows.
11. Oldest age rises
21. admission rejects new bulk work, consumers do not retry storm, optional data sheds, and critical state remains recoverable.
31. Recovery drains with a controlled rate.

## 7. Scaling behaviour

Observe arrival, completion, age, saturation, retries, and drain time. Autoscale only if downstream/headroom exists. Partition by cost/tenant/priority and cap expensive requests.

## 8. Data consistency implications

Dropped work must be explicitly disposable. Durable accepted commands cannot be silently shed; reject before acceptance or persist with visible delayed/expired state.

## 9. Real implementation choices

Bounded channels/worker pools, HTTP 429/503, queue max/TTL, Kafka pause, gRPC flow control, token buckets, fair queues, priority topics.

## 10. Trade-offs

Protects availability but denies/degrades users. Large buffers absorb bursts but increase stale latency; strict priority can starve bulk; fairness reduces peak utilization.

## 11. When not to use it

Do not drop correctness-critical accepted writes. Backpressure alone cannot fix permanently under-provisioned capacity.

## 12. Common interview mistakes

Infinite queue; depth without age; autoscale consumers against saturated DB; retry on overload; no expiry; dropping after acknowledging; all traffic same priority.

## 13. How it appears inside larger systems

Logging/metrics, notifications, chat sockets, API gateways, transcoding, crawlers, schedulers, caches, search queries.

## 14. Likely interviewer follow-ups

What is shed first? accepted semantics? bounds? retry-after? fairness? drain time? downstream saturated? client behavior? recovery burst?

## 15. Five-minute revision

Bound everything. Measure arrival/service/oldest age. Slow/reject before scarce resource, reserve priority, expire/drop only disposable work, controlled drain and clear user outcome.

## 16. Related notes

[[Bulkhead Pattern]] · [[Rate Limiting Pattern]] · [[Queues Streams and Pub Sub]] · [[Retry Timeout and Deadline Pattern]]

## 17. Verified further reading

- [AWS Well-Architected: fail fast and limit queues](https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_mitigate_interaction_failure_fail_fast.html) — official overload containment.
- [Google SRE Book: handling overload](https://sre.google/sre-book/handling-overload/) — public primary guidance.

