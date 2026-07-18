---
type: quick-revision
domain: backend-lld
topic: retry-and-backoff
review_time: under-5-minutes
---

# Retry and Backoff — Quick Revision

## Mental Model

Retry only failures likely to be transient and only when the operation is safe to repeat. Set a maximum attempt count and a total deadline budget; per-attempt timeouts must fit inside it. Exponential backoff reduces pressure, and jitter prevents synchronized clients from retrying together. Honor server Retry-After when appropriate. Preserve the final error plus attempt context. Do not retry validation, authentication, deterministic not-found, or context cancellation errors. Retrying inside multiple layers multiplies load and latency.

## Go / Design Checklist

Accept a policy or small classifier only when substitution is useful. Sleep with a timer selected against context, not time.Sleep. Clamp backoff to a maximum and guard duration overflow. Record attempts, latency, final outcome, and exhausted budget without high-cardinality labels. Tests inject a clock/sleeper or deterministic jitter, covering immediate success, eventual success, permanent error, budget expiry, cancellation during backoff, and maximum attempts. Explain interaction with idempotency, circuit breakers, rate limits, and bulkheads; ordering these policies changes behavior.

## Explain Aloud

In 60–90 seconds: state the contract, name the invariant and owner, describe success and failure flow, identify cancellation/shutdown behavior, give complexity, and make one Decision → Reason → Cost → Alternative trade-off.

## Reconstruction Drill

Close this note. Sketch the public API and ownership diagram from memory, implement the smallest success path, add one boundary/failure test, then run go test and go test -race where concurrent. Record only observed mistakes and schedule the re-test in [[Backend LLD Practice Tracker]].

## Practice Links

[[Retry Executor]], [[Resilient API Client]], [[Circuit Breaker]], [[Bulkhead Executor]], [[Timeout and Deadline Budget]], [[Idempotency-Key Store]]

