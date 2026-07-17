---
type: canonical
domain: system-design
topic: deduplication-and-inbox-pattern
status: active
last_verified: 2026-07-17
---
# Deduplication and Inbox Pattern

## 1. Problem it solves

At-least-once event delivery can repeat after consumer crash, broker retry, replay, or producer duplicate. Consumers need durable duplicate recognition tied to their business effect.

## 2. Simple mental model

An inbox is a consumer’s receipt ledger. Insert `(consumer,event_id)` and business change in one local transaction; duplicate insert returns the prior outcome.

## 3. How it works

Validate schema/key/version; begin transaction; conditional inbox insert; if new, apply state transition and write outbox; commit; then acknowledge offset/message. Duplicate skips/reuses stored result. Retain for replay horizon and scope by consumer.

## 4. Concrete example

Inventory consumes `ReserveInventory command c-9`; transaction inserts `inventory-inbox,c-9`, decrements available with condition, writes `InventoryReserved`, commits, then acks.

## 5. Detailed success flow

New event applies once locally; ack follows commit. Redelivery finds inbox row and produces no second decrement.

## 6. Detailed failure flow

Crash after commit before ack. Broker redelivers; inbox uniqueness absorbs it. If inbox expired before late replay, duplicate may reapply—retention/reconciliation must cover horizon.

## 7. Scaling behaviour

Partition inbox with business owner; batch and archive terminal entries; bloom/cache may optimize but durable store decides. Large global inbox becomes hotspot if key wrong.

## 8. Data consistency implications

Inbox and business mutation must share atomic boundary. Broker transactions alone cannot cover arbitrary database/provider effect. Event version guards stale/out-of-order updates.

## 9. Real implementation choices

Relational unique constraint; DynamoDB conditional transaction; consumer-specific table; state store in stream processor when semantics cover output.

## 10. Trade-offs

Storage/write amplification versus safe replay. Long retention costs more; short risks duplicates. Storing result supports deterministic reply but increases data.

## 11. When not to use it

Naturally idempotent commutative operation may use version/event set instead, but identity is still useful for audit. External side effects need provider idempotency/reconcile too.

## 12. Common interview mistakes

Mark processed before effect; in-memory set; ack before commit; one inbox shared key without consumer; event ID regenerated on retry; TTL shorter than retention/replay.

## 13. How it appears inside larger systems

Outbox consumers, payment/inventory commands, notification delivery, analytics aggregation, feed fan-out, job results.

## 14. Likely interviewer follow-ups

Atomic with business state? retention? replay? out-of-order? result storage? external provider? partition/hot key? cleanup?

## 15. Five-minute revision

Stable event ID → consumer-scoped inbox + business effect + outbox same transaction → ack after commit → version guard → retain through replay horizon.

## 16. Related notes

[[Idempotency Pattern]] · [[Transactional Outbox Pattern]] · [[Queues Streams and Pub Sub]]

## 17. Verified further reading

- [Debezium Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) — official producer-side complement.\n- [PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html) — official atomic transaction semantics.

