---
status: learning
type: canonical
area: system-design
sources:
  - "ChatGPT: System Design Patterns (2026-07-05, 6a4aa703-f2d8-83ee-aac3-020aa67e9afb)"
---

# Timeouts Retries and Deadlines

## Problem it solves

Without bounded waiting, one slow dependency consumes caller resources and violates the end-to-end latency objective; careless retries then amplify the failure.

## Mental model

A deadline is a shrinking end-to-end budget. Each hop gets only a portion; retries spend the same budget rather than resetting the clock.

## How it works

Choose connect, per-attempt, and total timeouts from observed latency plus business objective. Propagate the earlier caller deadline. Retry only transient errors and safe/idempotent operations, with exponential backoff, jitter, cap, attempt limit, and retry budget. Cancel abandoned downstream work where supported.

## Concrete example and detailed dry run

A request arrives with 800 ms remaining. The service reserves response/processing margin, allows a 250 ms payment attempt, then one jittered retry only if enough budget remains. If the first timeout has an unknown outcome, payment idempotency/reconciliation decides whether another attempt is safe.

## Success scenario

A brief network fault recovers on a second attempt inside the deadline; downstream sees the same idempotency key; total latency stays bounded.

## Failure scenario

The dependency is overloaded. A retry budget is exhausted, the circuit opens, and callers fail fast or return a truthful pending/degraded response. Queued attempts expire rather than execute after user interest is gone.

## Scaling considerations

Retries multiply offered load: approximate attempts as original load × average attempts. Coordinate client/server limits, use hedging only for idempotent requests with spare capacity, and observe retry amplification by dependency.

## Production technology choices

Go `context.Context` deadlines; gRPC deadline propagation; HTTP client connect/header/overall timeouts; resilience libraries/service meshes only when ownership and metrics are clear.

## Trade-offs

Short timeouts reduce resource occupancy but increase false failure; long timeouts improve slow success but worsen tail collapse. Retries improve availability for rare faults but harm overloaded systems.

## When not to use it

Do not automatically retry non-idempotent side effects, permanent validation/auth errors, overload responses without policy, or operations lacking enough remaining deadline.

## Common interview mistakes

One timeout for everything; resetting timeout per hop; retrying every error; synchronized backoff; ignoring unknown outcomes and server cancellation.

## Interview questions and follow-ups

How is the timeout chosen? Which errors retry? How are retries budgeted? What happens after the client disconnects?

## Five-minute recall

Propagate deadline; reserve margin; bound each attempt; retry only safe/transient work; exponential backoff + jitter + cap; budget retries; reconcile unknown results.

## Related notes

[[Retry Pattern]] · [[Circuit Breaker Pattern]] · [[Idempotency Pattern]] · [[Failure Handling Strategy]]

## Source metadata

Based on extracted patterns material. Numeric timeout values are intentionally omitted until measured objectives exist.

