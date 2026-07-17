---
type: canonical
domain: system-design
topic: cqrs
status: active
last_verified: 2026-07-17
---
# CQRS

## 1. Problem it solves

A single model can become awkward when writes enforce rich invariants while reads need different denormalized shapes, scale, or stores.

## 2. Simple mental model

Command model owns truth and invariants; query models are derived projections. CQRS means separated models/responsibilities, not necessarily separate services/databases.

## 3. How it works

Command validates and commits source+outbox. Projectors consume versioned events/CDC into read models. Queries read projection; rebuild from snapshot/events. Expose lag/read-your-writes strategy.

## 4. Concrete example

Order writes use normalized PostgreSQL. Customer order-history projection stores prejoined summaries keyed by customer; search projection supports filters. `GET /orders/{id}` can read truth when immediate.

## 5. Detailed success flow

Command commits version 4; event updates each projection only if newer; query returns fast denormalized result; rebuild can replace an index generation atomically.

## 6. Detailed failure flow

Projection consumer stalls. Lag metric marks data delayed; critical read falls back to truth or shows freshness. Replay from checkpoint/snapshot rebuilds without corrupting command state.

## 7. Scaling behaviour

Scale projections independently by query/use case; partition by read key. Write amplification and rebuild time grow with number/size of models.

## 8. Data consistency implications

Read models are eventual unless synchronously updated in same boundary. Define staleness, read-your-writes, version, deletion, and reconciliation.

## 9. Real implementation choices

PostgreSQL command model; Kafka/outbox; Redis/DynamoDB/OpenSearch read models; blue/green index generation.

## 10. Trade-offs

Fast tailored reads and independent scale versus more stores, lag, duplicate handling, schema evolution, and operational cost.

## 11. When not to use it

Simple CRUD where one relational model/index meets access patterns. Do not introduce because “microservices.”

## 12. Common interview mistakes

Projection becomes second writer; no rebuild; no version/idempotency; user sees stale after write without UX; one event schema tightly exposes DB; too many projections.

## 13. How it appears inside larger systems

Feeds, order history, dashboards, search/autocomplete, monitoring, API aggregation.

## 14. Likely interviewer follow-ups

How read-your-writes? rebuild? delete? projection lag? schema change? source truth outage? number of models/cost?

## 15. Five-minute revision

Command truth/invariants → outbox/event → versioned idempotent projections → query. Define lag/read-your-writes, rebuild generation, deletion/reconciliation.

## 16. Related notes

[[Change Data Capture]] · [[Event Sourcing]] · [[Fan-out on Write vs Fan-out on Read]]

## 17. Verified further reading

- [Microsoft CQRS pattern](https://learn.microsoft.com/azure/architecture/patterns/cqrs) — vendor architecture guidance.\n- [Debezium documentation](https://debezium.io/documentation/reference/stable/) — official change-stream mechanics for projections.

