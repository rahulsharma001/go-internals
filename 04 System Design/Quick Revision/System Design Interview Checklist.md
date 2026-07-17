---
type: quick-revision
domain: system-design
canonical: "[[System Design Interview Framework]]"
---

# System Design Interview Checklist

## Before drawing

- Restate problem, users, core journey, non-goals.
- Clarify read/write mix, peak versus average, regions, retention, latency, availability, durability, and consistency.
- Mark every unknown as an assumption; do not invent scale.
- Identify the strictest invariant and acceptable stale views.

## Build the design

1. Core entities and ownership boundaries.
2. Essential APIs/events: inputs, outputs, errors, idempotency.
3. Source-of-truth data model, keys, indexes, status/version.
4. Smallest end-to-end architecture.
5. Complete success path from client to durable outcome.
6. One detailed partial-failure path, retry/repair, user-visible state.
7. First bottleneck, then scaling change and new trade-off.

## Required lenses

- Ordering, duplicates, concurrency, backpressure, poison work.
- Timeouts/deadlines, isolation, degradation, DR/multi-region.
- Metrics tied to user outcomes; trace IDs and repair visibility.
- Authentication, resource authorization, secrets/PII, abuse/limits.
- Concrete technology only after required semantics.

## Finish aloud

Summarize requirement → architecture → invariant → failure recovery → main trade-off. State what remains `needs-verification`.

## Traps

Boxes without flows; averages without peaks; “exactly once”; queue without age/retry/DLQ; cache without invalidation/staleness; two regions without write authority; JWT without object authorization; retries without idempotency/deadline.

Related: [[System Design 15-Minute Revision]] · [[System Design Trade-off Cheatsheet]]

