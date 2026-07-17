---
type: quick-revision
domain: system-design
---

# Patterns Quick Revision

| Symptom | Pattern | Non-negotiable caveat |
|---|---|---|
| repeated expensive reads | [[Caching Pattern]] | staleness, invalidation, stampede |
| duplicated command/event | [[Idempotency Pattern]] | durable key + request identity |
| rare transient failure | [[Retry Pattern]] | safe operation, budget, jitter |
| failing dependency consumes capacity | [[Circuit Breaker Pattern]] | not a retry replacement |
| one dependency/tenant starves others | [[Bulkhead Pattern]] | capacity fragmentation |
| producer outruns consumer | [[Backpressure Pattern]] | bounded queue and shed policy |
| caller exceeds fair budget | [[Rate Limiting Pattern]] | key/scope and failure policy |
| cross-service business transaction | [[Saga Pattern]] | compensation is not rollback |
| database commit plus event | [[Transactional Outbox Pattern]] | relay duplicates; consumer inbox |
| stream committed DB changes | [[Change Data Capture]] | log retention, offsets, schemas |
| writes and reads need different models | [[CQRS]] | projection lag and rebuild |
| narrow cross-process exclusion | [[Distributed Locking]] | lease + fencing token |
| one active coordinator | [[Leader Election]] | quorum + epoch fencing |

Selection order: state the failure/invariant → choose the smallest pattern → walk success → walk failure → name operational cost and signals.

Related: [[Pattern Selection Guide]]

