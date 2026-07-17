> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Reliability and Failure Analysis]].

---
status: learning
type: canonical
area: system-design
sources:
  - "ChatGPT: System Design Patterns (2026-07-05, 6a4aa703-f2d8-83ee-aac3-020aa67e9afb)"
---

# Failure Handling Strategy

## Problem it solves

Distributed calls fail partially and ambiguously. A strategy decides how to contain, retry, repair, expose, and learn from failure without multiplying it.

## Mental model

Prevent → detect → contain → recover → reconcile. Every operation needs an owner, deadline, idempotency rule, terminal state, and observable outcome.

## How it works

Classify failures as transient, permanent, overload, dependency, corrupt input, or unknown outcome. Apply [[Timeouts Retries and Deadlines]], bounded [[Retry Pattern|retries]], [[Circuit Breaker Pattern|circuits]], [[Bulkhead Pattern|bulkheads]], [[Backpressure Pattern|backpressure]], fallback/degradation, durable queues, quarantine, reconciliation, and manual repair where appropriate.

## Concrete example and detailed dry run

Checkout calls payment with a propagated deadline and idempotency key. A connection timeout makes outcome unknown. It does not charge again blindly: it queries/reconciles by key, retries only if safe, then advances or leaves a visible pending state. Sustained provider errors open the circuit and protect the request pool.

## Success scenario

Transient faults recover within budget; user-visible state is truthful; unrelated tenants/features retain capacity; every accepted asynchronous operation reaches a terminal or operator-visible repair state.

## Failure scenario

Unbounded retries amplify an outage until thread pools and queues saturate. Correct handling stops new work, sheds optional traffic, expires stale work, and alerts on user impact/backlog age rather than flooding logs.

## Scaling considerations

Set capacity and retry budgets per dependency/tenant/priority. Bound queues, concurrency, message age, and fan-out. Design regional/cellular isolation and recovery capacity before traffic grows.

## Production technology choices

Client deadline support, service-mesh/client circuits, Kafka/SQS-style durable queues, DLQ/quarantine, workflow engines, database reconciliation queries, and OpenTelemetry-compatible telemetry.

## Trade-offs

Fast failure protects capacity but rejects more work; queues absorb bursts but increase latency/staleness; fallback preserves availability but may reduce correctness/freshness.

## When not to use it

Do not add every resilience mechanism indiscriminately. In-process pure functions and single-transaction database operations need simpler handling.

## Common interview mistakes

“Retry three times” without safety or budget; treating timeout as failure rather than unknown; no queue bound; no poison-message path; no reconciliation/manual repair.

## Interview questions and follow-ups

Which failures are safe to retry? What is shed first? How is unknown outcome reconciled? What proves recovery completed?

## Five-minute recall

Classify → deadline → idempotency → bounded retry → isolate → backpressure/shed → durable repair → reconcile → observe.

## Related notes

[[Graceful Degradation]] · [[Disaster Recovery]] · [[Alerting Strategy]] · [[Idempotency Pattern]]

## Source metadata

Synthesized from the extracted patterns conversation; thresholds must be verified from real service objectives.

