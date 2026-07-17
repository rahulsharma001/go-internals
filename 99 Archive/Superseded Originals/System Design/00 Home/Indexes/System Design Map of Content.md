> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[System Design Map of Content]].

---
type: moc
domain: system-design
status: active
---

# System Design Map of Content

Start: [[System Design Dashboard]]

## Interview method and revision

- [[System Design Interview Framework]] · [[Requirements and Scope]] · [[Capacity Estimation]] · [[Core Entities APIs and Data Model]] · [[Architecture Presentation Strategy]] · [[Trade-off Communication]]
- [[System Design 15-Minute Revision]] · [[System Design Interview Checklist]] · [[System Design Trade-off Cheatsheet]]

## Foundations

[[Scalability and Availability]] · [[Consistency Models]] · [[CAP and PACELC]] · [[Load Balancing]] · [[Consistent Hashing]] · [[Partitioning and Sharding]] · [[Replication]] · [[Stateless and Stateful Services]] · [[Synchronous vs Asynchronous Communication]] · [[Queues and Pub Sub]] · [[Data Storage Selection]]

## Reusable patterns

[[Caching Pattern]] · [[Idempotency Pattern]] · [[Retry Pattern]] · [[Circuit Breaker Pattern]] · [[Bulkhead Pattern]] · [[Backpressure Pattern]] · [[Rate Limiting Pattern]] · [[Saga Pattern]] · [[Transactional Outbox Pattern]] · [[Change Data Capture]] · [[CQRS]] · [[Distributed Locking]] · [[Leader Election]]

## Representative systems

[[Order Processing System]] · [[Uber System Design]] · [[YouTube System Design]] · [[Notification System]] · [[WebSocket Chat or Realtime System]] · [[Monitoring System]] · [[URL Shortener]]

## Production lenses

- Reliability: [[Failure Handling Strategy]] · [[Timeouts Retries and Deadlines]] · [[Graceful Degradation]] · [[Disaster Recovery]] · [[Multi Region Architecture]]
- Observability: [[Logs Metrics and Traces]] · [[SLI SLO and Error Budgets]] · [[Alerting Strategy]]
- Security: [[Authentication and Authorization]] · [[OAuth JWT OIDC and mTLS]] · [[API Security]]

## Adjacent existing material

- Databases: [[MongoDB with Go]]
- Go-local reliability/concurrency building blocks: [[Worker Pool]], [[Context Cancellation]], [[Go Channels]]

The System Design canonicals are learning material, not evidence of personal production ownership. Product/version-specific statements marked `needs-verification` must be checked before implementation.

Revision: [[Quick Revision Index]] · Interview navigation: [[Interview Preparation Index]]
