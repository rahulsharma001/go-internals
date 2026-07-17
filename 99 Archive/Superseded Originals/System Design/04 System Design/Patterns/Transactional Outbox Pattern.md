> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Transactional Outbox Pattern]].

---
status: learning
type: canonical
area: system-design
sources:
  - "ChatGPT: System Design Patterns (2026-07-05, 6a4aa703-f2d8-83ee-aac3-020aa67e9afb)"
  - "Debezium Outbox Event Router documentation"
---

# Transactional Outbox Pattern

## Problem it solves

A service must update its database and publish an event without losing one side or performing an unsafe dual write.

## Mental model

Write the business change and a sealed envelope in the same local transaction. A separate relay delivers the envelope later.

## How it works

Within one database transaction, update the aggregate and insert an outbox row. A polling relay or [[Change Data Capture|CDC]] reads committed rows and publishes them. Consumers deduplicate by event ID. Publication is normally at-least-once; atomic creation does not mean exactly-once processing.

Suggested fields: `event_id`, `aggregate_type`, `aggregate_id`, `event_type`, `payload`, `occurred_at`, `schema_version`, plus relay status only when polling.

## Concrete example and detailed dry run

An order transaction inserts `orders(o-42, PENDING)` and `outbox(e-77, OrderCreated, o-42, {...})`. A crash immediately after commit is safe: both rows remain. Debezium observes the WAL entry, routes the outbox row to Kafka, and the payment consumer inserts `inbox(e-77, payment)` before authorizing. If Kafka redelivers `e-77`, the inbox uniqueness constraint prevents a second charge.

## Success scenario

Business state and intent-to-publish commit atomically; the relay eventually publishes; consumers process once from the business perspective.

## Failure scenario

The relay publishes and crashes before recording progress, so the event is published again. Stable IDs plus consumer idempotency make the duplicate harmless. Malformed payloads go to quarantine/DLQ with an alert; they are not silently discarded.

## Scaling considerations

Partition topics by aggregate ID, index polling columns, bound batch size, retain enough CDC log, archive processed rows, monitor oldest unpublished age, and version schemas compatibly.

## Production technology choices

PostgreSQL transaction + outbox table; Debezium Outbox Event Router for log-based CDC; Kafka for delivery. A `FOR UPDATE SKIP LOCKED` poller is simpler at modest volume but adds polling load and cleanup state.

## Trade-offs

It removes the dual-write gap and gives auditability, but adds storage, relay operations, duplicates, schema evolution, and publication lag.

## When not to use it

Avoid it when no external event is needed, a single transactional database already owns the whole workflow, or a managed platform already provides an equivalent atomic mechanism.

## Common interview mistakes

- Claiming exactly-once end to end.
- Marking an outbox row before broker acknowledgement.
- Omitting consumer inbox/idempotency.
- Ignoring retention, ordering, and schema evolution.

## Interview questions and follow-ups

- Polling or CDC, and why?
- How do you replay without duplicating side effects?
- What metric reveals a stuck relay?

## Five-minute recall

Atomic DB transaction → committed outbox → relay/CDC → broker → idempotent inbox consumer. Monitor lag and duplicates; version events.

## Related notes

[[Change Data Capture]] · [[Idempotency Pattern]] · [[Order Processing System]] · [[Queues and Pub Sub]]

## Source metadata

Synthesized from the extracted conversation above and the official Debezium Outbox Event Router documentation. No production ownership claim is implied.

