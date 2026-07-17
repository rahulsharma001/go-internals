> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Change Data Capture]].

---
status: learning
type: canonical
area: system-design
sources:
  - "ChatGPT: System Design Patterns (2026-07-05, 6a4aa703-f2d8-83ee-aac3-020aa67e9afb)"
  - "Debezium documentation"
---

# Change Data Capture

## Problem it solves

Downstream systems need a reliable stream of committed database changes without application dual writes or repeated full-table scans.

## Mental model

CDC tails the database's durable commit journal and translates changes into an ordered event stream.

## How it works

A connector reads the WAL/binlog using a durable offset, takes an initial snapshot when configured, emits row changes, and resumes from its last position. Raw table CDC exposes storage shape; an outbox table exposes deliberate domain events and is safer for service contracts.

## Concrete example and detailed dry run

Transaction `T10` commits outbox rows `e-1` and `e-2`. PostgreSQL assigns log positions. Debezium reads them in commit order, transforms each row, publishes using `aggregate_id` as the Kafka key, then persists its source offset. After restart it resumes from the stored position. A duplicate near the checkpoint boundary is tolerated by consumer inbox records.

## Success scenario

Committed changes appear downstream with measurable lag, per-partition ordering, and enough retained history to recover a connector outage.

## Failure scenario

The connector is down longer than WAL retention. Its required position disappears and normal resume is impossible; operators must resnapshot or restore from a retained log while preventing duplicate side effects. Schema-breaking DDL can also stop deserialization and must be quarantined/rolled forward.

## Scaling considerations

Track source-log growth, connector lag, broker lag, snapshot load, partition-key skew, event size, and schema compatibility. One hot aggregate cannot be parallelized while preserving its strict order.

## Production technology choices

Debezium with PostgreSQL logical decoding/MySQL binlog and Kafka Connect is common. Managed database streams reduce operations but may constrain event transformation and retention.

## Trade-offs

CDC is low-latency and avoids polling load, but couples operations to database logs, introduces snapshot/recovery complexity, and may leak internal schemas if used carelessly.

## When not to use it

Avoid CDC for a tiny periodic export, for databases without dependable log access, or when an explicit application event is required but only raw row changes exist.

## Common interview mistakes

- Treating a row change as a stable domain contract.
- Ignoring snapshots, offsets, log retention, duplicates, and DDL.
- Assuming global ordering across partitions.

## Interview questions and follow-ups

- CDC versus polling?
- How do you recover after the source log is gone?
- How do you evolve schemas without breaking consumers?

## Five-minute recall

Commit log → connector offset → transform → partitioned stream → idempotent consumer. Watch source retention, lag, snapshots, DDL, and schema compatibility.

## Related notes

[[Transactional Outbox Pattern]] · [[Queues and Pub Sub]] · [[CQRS]] · [[Order Processing System]]

## Source metadata

Based on the extracted conversation and official Debezium concepts. Deployment-specific behavior is `status: needs-verification` until checked against the selected database and connector version.

