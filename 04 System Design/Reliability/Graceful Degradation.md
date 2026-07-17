---
status: learning
type: canonical
area: system-design
sources:
  - "Curated system-design synthesis"
---

# Graceful Degradation

## Problem it solves

When capacity or a dependency is lost, preserving every feature can collapse the essential path. Degradation retains a smaller truthful service.

## Mental model

Protect the core journey and spend remaining capacity by priority. A fallback is a product decision with correctness limits, not a hidden catch block.

## How it works

Classify features and traffic: critical, important, optional. Define triggers, allowed stale data, shed order, fallbacks, recovery hysteresis, and user messaging. Combine admission control, cached/static results, asynchronous acceptance, reduced fidelity, and feature flags with [[Bulkhead Pattern]] and [[Backpressure Pattern]].

## Concrete example and detailed dry run

During recommendation failure, video playback continues using cached subscriptions/popular items. Personalized ranking is disabled, analytics sampling is reduced, and upload remains available. A clear freshness marker prevents cached data from appearing current.

## Success scenario

Core operations stay within latency/error objectives; optional traffic is shed predictably; the degraded mode is visible to users/operators and exits gradually after recovery.

## Failure scenario

An overly stale inventory fallback accepts unavailable stock. The correct design forbids that fallback for a strict reservation invariant and instead returns pending/unavailable while degrading only recommendations or display data.

## Scaling considerations

Reserve capacity for critical traffic, enforce tenant/priority quotas, precompute fallbacks, test load-shed paths, and prevent simultaneous recovery from causing a cache/retry surge.

## Production technology choices

Feature-flag/control plane, gateway admission controls, cached snapshots, queue priority, CDN static responses, and client/server circuit breakers.

## Trade-offs

Degradation improves availability and containment but yields stale/incomplete UX, extra code paths, and risk that fallback semantics become incorrect or untested.

## When not to use it

Never silently degrade safety, authorization, payment correctness, consent, or other invariants. Prefer explicit failure/pending state.

## Common interview mistakes

Saying “use cache” without maximum staleness; degrading every tenant equally; no recovery rule; hiding degraded truth; not testing fallback.

## Interview questions and follow-ups

What is the minimum viable service? What is shed first? Which data may be stale? How is recovery prevented from surging?

## Five-minute recall

Prioritize core path; reserve capacity; define trigger + fallback + correctness boundary + user signal + hysteresis; test it.

## Related notes

[[Failure Handling Strategy]] · [[Caching Pattern]] · [[Backpressure Pattern]] · [[SLI SLO and Error Budgets]]

## Source metadata

Curated synthesis. Feature priorities and allowed staleness are product decisions and remain `status: needs-verification`.

