> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Circuit Breaker Pattern]].

---
type: canonical
domain: system-design
topic: circuit-breaker
status: learning
source_conversations:
  - "Scalable Approach Feedback | 2026-06-25 | 6a3d54ea-471c-83e8-953d-e26213c70a94"
---
# Circuit Breaker Pattern

## Problem it solves

It stops repeated calls to a failing dependency so callers fail fast and the dependency gets recovery space.

## Mental model and how it works

Closed allows calls and measures relevant failures. Threshold opens the circuit and rejects/falls back. After a cooldown, half-open admits a small probe budget; success closes, failure reopens. Scope by dependency/operation/region so one failure does not block unrelated work.

## Concrete example and dry run

Pricing provider times out repeatedly. Breaker observes 20 calls with a high timeout ratio, opens for a bounded interval, and ride estimates use a conservative fallback labeled approximate. After cooldown, three probes run; two fail, so it reopens. Recovery probes later succeed and normal calls resume.

## Success and failure scenarios

Success: request threads and dependency capacity are protected while degradation is explicit. Failure: breaker opens on client validation errors, global breaker blocks every tenant, or half-open sends a traffic burst. Use meaningful error classification, rolling windows/minimum volume, limited probes, and per-operation isolation.

## Scaling and production choices

Client libraries, service proxies, or gateways can implement it, but ownership must be clear. Observe state transitions, rejected calls, fallback rate, probe success, downstream saturation, and SLO impact.

## Trade-offs and when not to use

Fail-fast may reject calls during partial recovery and hides problems if fallback is silent. Do not use as a substitute for timeouts, capacity planning, or retry policy; local deterministic dependencies may not need it.

## Interview mistakes and follow-ups

Calling it a retry mechanism; no half-open; one process-local state claimed as globally exact; fallback has no limit. Follow-ups: threshold? distributed instances? brownout? fallback correctness? recovery?

## Five-minute recall

Closed measure → open fail-fast → cooldown → limited half-open probes → close/reopen → observe fallback.

Related: [[Retry Pattern]], [[Bulkhead Pattern]], [[Graceful Degradation]].

## Source metadata

Sanitized source above; thresholds are workload-specific and intentionally not invented.
