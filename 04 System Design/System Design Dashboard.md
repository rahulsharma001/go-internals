---
type: dashboard
domain: system-design
status: active
---
# System Design Dashboard

## Current operating rule

Designs are learned by reconstruction. Note completeness never changes personal readiness. Use [[README - How to Learn System Design]] and preserve every timed attempt before comparison.

## Start a session

1. Open [[15-Minute Interview Launchpad]] and choose a system from [[System Coverage Matrix]].
2. Use [[System Design Blank Interview Template]] and [[45-Minute System Design Playbook]].
3. Score with [[System Design Mock Rubric]].
4. Update [[System Design Practice Tracker]].
5. Add only observed failures to [[Common Mistakes and Re-test Queue]].

## Curriculum layers

- Interview method: [[45-Minute System Design Playbook]] · [[Requirements Clarification Framework]] · [[Back-of-the-Envelope Estimation]] · [[Invariants and Critical Paths]] · [[API and Data Model Design]] · [[Building the HLD Incrementally]]
- Decisions and failure: [[Choosing Databases and Storage]] · [[Finding Bottlenecks]] · [[Reliability and Failure Analysis]] · [[Trade-off Communication]] · [[Interviewer Follow-up Strategy]]
- Foundations: [[Scalability Availability and Reliability]] · [[Latency Throughput and Capacity]] · [[Consistency Models]] · [[Partitioning and Sharding]] · [[Queues Streams and Pub Sub]] · [[Multi-Region Design]]
- Pattern selection: [[System Pattern Selection Guide]] · [[Caching Pattern]] · [[Idempotency Pattern]] · [[Transactional Outbox Pattern]] · [[Backpressure and Load Shedding]]

## System sequence

| Tier | Systems | Why now |
| --- | --- | --- |
| 1A | [[URL Shortener]], [[Rate Limiter System]], [[Notification System]] | scope, cache, rate control, async delivery |
| 1B | [[Order Processing System]], [[Payment System]], [[Event Ticket Booking System]] | invariants, transactions, idempotency, concurrency |
| 1C | [[News Feed System]], [[WebSocket Chat or Realtime System]], [[Uber System Design]] | fan-out, realtime, ordering, geospatial matching |
| 1D | [[YouTube System Design]], [[File Storage and Synchronization System]] | blob lifecycle, CDN, async processing, conflict resolution |
| 1E | [[Distributed Job Scheduler]], [[Distributed Cache System]], [[Search Autocomplete System]] | ownership, leases/fencing, partitioning, indexes |
| 2 | [[Monitoring System]], [[Logging and Metrics Pipeline]], [[Web Crawler System]], [[API Gateway System]] | streaming, high write, control/data planes, fairness |

Full mapping: [[System Coverage Matrix]].

## Readiness snapshot

All systems begin `not-started` in [[System Design Practice Tracker]]. Canonical notes are complete curriculum assets, not evidence of a mock, re-test, or interview readiness.

## Five-minute launch

`Users → journey → invariant → scale → APIs/state → owner → basic HLD → bottleneck → failure → trade-off → summary`

Quick pack: [[45-Minute Timeline Cheatsheet]] · [[Requirements Checklist]] · [[HLD Drawing Checklist]] · [[Reliability Checklist]] · [[Common Interview Traps]].

