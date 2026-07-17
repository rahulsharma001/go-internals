---
type: canonical
domain: system-design
topic: circuit-breaker-pattern
status: active
last_verified: 2026-07-17
---
# Circuit Breaker Pattern

## 1. Problem it solves

Repeated calls to a failing/slow dependency consume threads, connections, retries, and latency, spreading failure upstream.

## 2. Simple mental model

Like an electrical breaker: closed allows calls, open fails fast, half-open probes recovery. It is a local protection state, not health truth or a retry replacement.

## 3. How it works

Track qualifying failures/slow calls over a window. Open after threshold; return fallback/error without call. After cool-down admit limited half-open probes; close on sustained success or reopen. Scope by dependency/operation/region and combine with timeout/bulkhead.

## 4. Concrete example

Pricing enrichment fails. Checkout circuit opens for optional price recommendation and uses last known/omits it; payment authorization has no unsafe fallback and returns pending/unavailable.

## 5. Detailed success flow

Healthy calls flow; isolated failures remain below threshold. Recovery probes gradually restore traffic and slow-start prevents flood.

## 6. Detailed failure flow

Dependency is down. Circuit opens and preserves upstream capacity. If all instances synchronize probes, jitter/limited global rate prevents a thundering herd. Alert on user impact and open duration.

## 7. Scaling behaviour

Per-instance circuits can be sufficient and avoid shared-state dependency, but aggregate traffic may still overwhelm recovery. Limit half-open concurrency and use provider/global quotas.

## 8. Data consistency implications

Fallback may be stale or semantically different; explicitly restrict it. Never use stale authorization/inventory/charge result as success.

## 9. Real implementation choices

Resilience4j/Polly/Envoy or simple client wrapper. Use latency/error classification, rolling window, open duration, probe count, and observable state.

## 10. Trade-offs

Fails fast and isolates but can reject calls after dependency recovers or hide partial failure. Shared breaker coordinates but adds dependency/complexity.

## 11. When not to use it

Local deterministic errors, CPU overload in same process, or as a substitute for deadline/admission control. Critical writes may need pending rather than fallback.

## 12. Common interview mistakes

Circuit without timeout; same fallback for every operation; retries continue while open; global circuit lets one tenant trip all; fixed thresholds with no traffic minimum; no half-open limit.

## 13. How it appears inside larger systems

Payment/provider calls, notification adapters, maps/geocoding, search enrichment, object origin, internal RPC.

## 14. Likely interviewer follow-ups

Scope? qualifying failures? fallback correctness? half-open herd? low traffic? observability? interaction with retries/load shedding?

## 15. Five-minute revision

Timeout first. Closed measures; open fails fast; half-open bounded probes. Scope narrowly, define safe fallback/pending, jitter recovery, observe state and user impact.

## 16. Related notes

[[Retry Timeout and Deadline Pattern]] · [[Bulkhead Pattern]] · [[Backpressure and Load Shedding]]

## 17. Verified further reading

- [Microsoft circuit breaker pattern](https://learn.microsoft.com/azure/architecture/patterns/circuit-breaker) — vendor architecture guidance and state transitions.\n- [AWS reliability guidance](https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_mitigate_interaction_failure.html) — official dependency-failure mitigation.

