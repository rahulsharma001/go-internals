---
type: canonical
domain: system-design
topic: change-data-capture
status: active
last_verified: 2026-07-17
---
# Change Data Capture

## 1. Problem it solves

Systems need a reliable ordered feed of committed database changes for indexes, caches, events, migrations, or analytics without dual-writing in application code.

## 2. Simple mental model

CDC follows the database commit log, checkpoints a position, converts changes to records, and delivers them downstream. It exposes physical/row change unless an outbox shapes business events.

## 3. How it works

Connector snapshots initial state, then streams log records with table/key/operation/before-after/position. Store offsets durably; apply schemas; partition; consumers idempotently materialize. Handle DDL, log retention, resnapshot, and deletes/tombstones.

## 4. Concrete example

Debezium reads only `outbox` table, turns each insert into an event keyed by aggregate, and Kafka consumers build search/cache views.

## 5. Detailed success flow

Transaction commits; log record becomes visible; connector publishes in order for source partition; consumer applies version and checkpoints; lag remains bounded.

## 6. Detailed failure flow

Connector offline beyond WAL/binlog retention loses position. Alert before exhaustion; retain logs, restore connector, resnapshot/backfill, then resume and reconcile versions.

## 7. Scaling behaviour

Snapshot load, database log I/O, connector tasks, broker partitions, schema registry, and consumer lag. Large transactions create bursts; split/route by stable key.

## 8. Data consistency implications

CDC is after commit and usually at-least-once. Cross-table transaction ordering may require metadata. Downstream views lag and need version/delete semantics; CDC does not enforce business intent.

## 9. Real implementation choices

Debezium for PostgreSQL/MySQL/Mongo etc.; cloud database streams; Kafka Connect; native logical replication. Outbox for domain events; raw CDC for replication/materialization.

## 10. Trade-offs

Low application coupling and replay versus connector/log/schema operations and exposure of storage schema. Polling is simpler but less efficient/timely.

## 11. When not to use it

Do not expose raw table changes as stable public business events without a compatibility contract. Small workloads may use polling.

## 12. Common interview mistakes

No snapshot plan; log retention ignored; schema/DDL unhandled; PII leaked into broker; duplicate/order assumed away; delete not propagated; CDC called exactly-once.

## 13. How it appears inside larger systems

Transactional outbox relay, cache prefill, search indexing, analytics, database migration, audit/replication.

## 14. Likely interviewer follow-ups

Snapshot+stream boundary? offsets? retention? schema evolution? transaction order? deletes? resnapshot? source load? PII?

## 15. Five-minute revision

Snapshot → log position → committed changes → schema/key/partition → idempotent versioned consumer → lag/retention alert → resnapshot/reconcile.

## 16. Related notes

[[Transactional Outbox Pattern]] · [[CQRS]] · [[Event Sourcing]] · [[Caching Pattern]]

## 17. Verified further reading

- [Debezium documentation](https://debezium.io/documentation/reference/stable/) — official connectors, snapshots, offsets, and schemas.\n- [Debezium Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) — domain-event specialization.

