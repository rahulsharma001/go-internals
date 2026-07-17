> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Rate Limiting Pattern]].

---
type: canonical
domain: system-design
topic: rate-limiting
status: learning
source_conversations:
  - "Security Protocols Deep Dive | 2026-06-26 | 6a3e58e8-4470-83e8-aadc-8775e79a5656"
---
# Rate Limiting Pattern

## Problem it solves

Rate limiting protects capacity, fairness, cost, and sensitive business flows by bounding admitted operations.

## Mental model and how it works

Define identity, scope, unit, limit/window, burst, decision location, and rejection response. Token bucket allows bursts up to bucket capacity and refills at a steady rate; leaky bucket smooths output; fixed/sliding windows trade simplicity and precision. Distributed decisions require atomic shared state or deliberate local approximation.

## Concrete example and dry run

`POST /rides` allows five requests/minute per authenticated rider with burst two. A Redis-side atomic token update deducts one token; when empty, gateway returns 429 with retry metadata. Separate limits protect IP login attempts, tenant-wide provider quota, and internal payment calls. User ID—not IP alone—drives business fairness.

## Success and failure scenarios

Success: abuse/traffic spikes shed before expensive work. Failure: Redis outage blocks all traffic or fail-open overloads backend; NAT makes IP unfair; clock/window boundary doubles burst. Choose fail-open/closed per endpoint, local emergency limits, and monitoring.

## Scaling and production choices

Gateway/service limiters, Redis atomic scripts, or managed quota systems. Observe allowed/rejected by reason/scope, limiter latency/error, hot keys, backend saturation, and false positives. Shard keys and bound cardinality.

## Trade-offs and when not to use

Central accuracy adds latency/dependency; local limits overshoot globally. Rate limits do not replace authorization, backpressure, or autoscaling. Avoid one universal limit for endpoints with different costs.

## Interview mistakes and follow-ups

IP-only, no burst semantics, racey counters, no outage policy, 429 without retry behavior. Follow-ups: multi-region? clock skew? premium tenant? distributed atomicity? provider quota?

## Five-minute recall

Who/what → cost unit → algorithm/burst → atomic scope → 429/degrade → outage policy → metrics.

Related: [[Backpressure Pattern]], [[API Security]], [[Uber System Design]].

## Source metadata

Generic technical sections only from sanitized source; current OWASP/API guidance should be verified before implementation.
