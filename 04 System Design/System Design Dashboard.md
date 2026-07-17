---
type: dashboard
domain: system-design
status: active
---
# System Design Dashboard

Use this as the entry point for Senior Backend and Google/FAANG design practice. Notes provide reference knowledge; interview readiness requires a dated, timed design attempt and re-test.

## Interview sequence

[[Requirements and Scope]] → [[Capacity Estimation]] → [[Core Entities APIs and Data Model]] → [[Architecture Presentation Strategy]] → success flow → failure flow → bottleneck → reliability/security → [[Trade-off Communication]].

Primary owner: [[System Design Interview Framework]] · 15-minute revision: [[System Design 15-Minute Revision]] · checklist: [[System Design Interview Checklist]].

## Foundations

[[Scalability and Availability]] · [[Consistency Models]] · [[CAP and PACELC]] · [[Load Balancing]] · [[Consistent Hashing]] · [[Partitioning and Sharding]] · [[Replication]] · [[Stateless and Stateful Services]] · [[Synchronous vs Asynchronous Communication]] · [[Queues and Pub Sub]] · [[Data Storage Selection]]

## Reusable patterns

[[Caching Pattern]] · [[Idempotency Pattern]] · [[Retry Pattern]] · [[Circuit Breaker Pattern]] · [[Bulkhead Pattern]] · [[Backpressure Pattern]] · [[Rate Limiting Pattern]] · [[Saga Pattern]] · [[Transactional Outbox Pattern]] · [[Change Data Capture]] · [[CQRS]] · [[Distributed Locking]] · [[Leader Election]]

Selection aid: [[Pattern Selection Guide]] · quick recall: [[Patterns Quick Revision]].

## Representative systems

| System | Core interview depth |
| --- | --- |
| [[Order Processing System]] | Saga, outbox, Debezium CDC, Kafka, inbox/idempotency, compensation |
| [[Uber System Design]] | geospatial location, matching consistency, hot regions, realtime trip flow |
| [[YouTube System Design]] | chunked upload, asynchronous transcoding, object storage, CDN |
| [[Notification System]] | preferences, fan-out, providers, retries, delivery status |
| [[WebSocket Chat or Realtime System]] | connection routing, presence, ordering, offline delivery |
| [[Monitoring System]] | scheduling, distributed probes, state transitions, alert dedupe |
| [[URL Shortener]] | key generation, read path, cache, abuse and expiry |

## Production decision lenses

- Reliability: [[Failure Handling Strategy]], [[Timeouts Retries and Deadlines]], [[Graceful Degradation]], [[Disaster Recovery]], [[Multi Region Architecture]].
- Observability: [[Logs Metrics and Traces]], [[SLI SLO and Error Budgets]], [[Alerting Strategy]].
- Security: [[Authentication and Authorization]], [[OAuth JWT OIDC and mTLS]], [[API Security]].
- Data choice: [[Database Selection Guide]].

## Evidence boundary

No personal scale, incident, ownership, metric, or production technology is asserted here. Example scale assumptions are interview inputs, explicitly labeled as assumptions. Canonical content is `learning`; mock outcomes remain unrecorded until performed.

Sources and migration decisions: [[MIGRATION_REPORT_04_SYSTEM_DESIGN]].
