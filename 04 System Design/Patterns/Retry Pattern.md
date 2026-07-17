---
type: canonical
domain: system-design
topic: retry
status: learning
source_conversations:
  - "Kafka Deep Dive Guide | 2026-06-28 | 6a4107d3-19ac-83ee-a716-51fdbc569f3e"
  - "Scalable Approach Feedback | 2026-06-25 | 6a3d54ea-471c-83e8-953d-e26213c70a94"
---
# Retry Pattern

## Problem it solves

Retries recover from transient failure without requiring the caller to manually repeat work.

## Mental model and how it works

Retry only an operation classified as transient and safe/idempotent, within one end-to-end deadline and attempt budget. Use exponential backoff plus jitter, honor server hints, and stop on permanent errors, cancellation, or budget exhaustion. Retry at one responsible layer.

## Concrete example and dry run

Notification provider call has a 2-second attempt timeout and 8-second total deadline: attempt now, then after jittered 200 ms and 500 ms. HTTP 429 honors `Retry-After`; validation/auth errors do not retry. After budget exhaustion, the durable job moves to delayed retry or DLQ and exposes `DELIVERY_DELAYED`.

## Success and failure scenarios

Success: brief outage recovers without duplicate notification because `notification_id` is idempotent. Failure: every layer retries three times, turning one request into 27 calls; synchronized retries amplify recovery load. Centralize policy, use jitter, concurrency caps, circuit breaking, and retry budgets.

## Scaling and production choices

Client libraries/middleware can enforce deadlines; durable queues schedule long retries. Observe attempts/original request, recovered rate, terminal errors, budget exhaustion, retry queue age, and downstream saturation.

## Trade-offs and when not to use

Retries improve transient success but add load and tail latency. Do not retry deterministic validation, permission denial, overload without backoff, or non-idempotent side effects lacking a key/reconciliation plan.

## Interview mistakes and follow-ups

Fixed tight loop, no jitter/deadline, retry all 5xx forever, nested retries. Follow-ups: timeout ambiguity? 429? provider outage? poison message? budget propagation?

## Five-minute recall

Classify → idempotent? → attempt timeout → total deadline/budget → backoff+jitter → terminal path → metrics.

Related: [[Idempotency Pattern]], [[Circuit Breaker Pattern]], [[Timeouts Retries and Deadlines]].

## Source metadata

Generic technical content split from the sanitized sources; project details excluded.
