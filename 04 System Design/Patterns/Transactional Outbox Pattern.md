---
type: canonical
domain: system-design
topic: transactional-outbox-pattern
status: active
last_verified: 2026-07-17
---
# Transactional Outbox Pattern

## 1. Problem it solves

A service must atomically change its database and publish an event, but a database and broker cannot safely commit as one ordinary transaction.

## 2. Simple mental model

Write business row and outbox row in the same local transaction. A separate relay publishes committed outbox rows. Duplicates remain possible, so consumers deduplicate.

## 3. How it works

Outbox row contains event ID, aggregate key/version, type/schema, payload/reference, time. Poller claims rows or CDC reads transaction log. Relay publishes keyed record and marks/observes progress. Consumers use inbox/local transaction.

## 4. Concrete example

Order transaction inserts `orders(o-42)` and `outbox(e-77,aggregate=o-42,type=OrderCreated.v1)`. Debezium routes committed row to Kafka keyed `o-42`.

## 5. Detailed success flow

DB commit makes state/event intent durable; relay publishes; consumer deduplicates and applies; outbox retention cleans only after safe horizon.

## 6. Detailed failure flow

Relay publishes then crashes before marking. It republishes; consumer inbox uniqueness ignores duplicate. If relay stalls, oldest unpublished age alerts and catch-up resumes.

## 7. Scaling behaviour

Partition/route by aggregate; index unpublished/created time; avoid large payloads; archive rows; monitor database log/poller load and broker backpressure.

## 8. Data consistency implications

Guarantees atomic local state+event intent, not exactly-once delivery or atomic consumer effect. Event ordering follows aggregate version/key if relay preserves it.

## 9. Real implementation choices

PostgreSQL outbox + Debezium Outbox Event Router; polling with `SKIP LOCKED`; application log tail; Kafka/SQS target.

## 10. Trade-offs

Reliability versus extra table/storage/relay operations. CDC lowers poll load/latency but adds connector/log retention/schema operations. Polling is simpler but can scan/lag.

## 11. When not to use it

If state is already broker-native/event-sourced or no broker event is required. Do not use as excuse for huge event payloads.

## 12. Common interview mistakes

Publish then DB write; outbox in second transaction; mark published before broker ack; no event ID/version/key; assuming no duplicates; deleting before consumers/replay horizon.

## 13. How it appears inside larger systems

Orders, payments, notifications, scheduler state, file metadata, feed post creation, cache/search projection updates.

## 14. Likely interviewer follow-ups

Poll or CDC? duplicates? ordering? cleanup? schema? relay outage? DB failover/log retention? consumer atomicity?

## 15. Five-minute revision

Business+outbox same transaction. Relay committed rows at least once keyed by aggregate. Consumer inbox/local transaction. Measure oldest unpublished, duplicates, cleanup/replay.

## 16. Related notes

[[Change Data Capture]] · [[Deduplication and Inbox Pattern]] · [[Saga Pattern]] · [[Order Processing System]]

## 17. Verified further reading

- [Debezium Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) — official schema and routing behavior.\n- [PostgreSQL SKIP LOCKED](https://www.postgresql.org/docs/current/sql-select.html) — official primitive often used by polling relays.

