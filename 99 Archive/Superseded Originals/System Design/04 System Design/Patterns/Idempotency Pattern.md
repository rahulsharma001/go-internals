> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Idempotency Pattern]].

---
type: canonical
domain: system-design
topic: idempotency
status: learning
source_conversations:
  - "System Design Patterns | 2026-07-05 | 6a4aa703-f2d8-83ee-aac3-020aa67e9afb"
---
# Idempotency Pattern

## Problem it solves

Retries and at-least-once delivery can repeat an operation. Idempotency makes repeated execution produce one business effect.

## Mental model and how it works

Give one logical operation a stable key. Atomically claim the key with the business change, store outcome/status, and return/replay that outcome for duplicates. Scope keys by caller/operation and retain them longer than the retry/redelivery window. Natural idempotency (`set status`) is safer than non-idempotent increments.

## Concrete example and dry run

Payment command uses `payment:order:o1:authorize:1`. Consumer transaction inserts `(consumer,event_id)` and payment attempt with unique idempotency key. First delivery creates `AUTHORIZED`; crash occurs before offset commit. Redelivery hits the unique inbox row and skips the side effect, then commits offset. Concurrent duplicates race; the unique constraint chooses one winner.

## Success and failure scenarios

Success: timeout/retry returns the original result. Failure: key is marked done before business change, Redis key expires too early, payload changes under the same key, or third-party side effect lacks its own idempotency. Put claim and local change in one transaction; store request fingerprint; reconcile ambiguous external calls.

## Scaling and production choices

Relational unique constraints/inbox tables give durable atomicity; conditional writes work in key-value stores; Redis may suit short-lived low-risk dedupe but must not silently become the only durable proof. Observe duplicate rate, key conflicts, in-progress age, retention, and reconciliation.

## Trade-offs and when not to use

Storage and contention cost; exactly replaying large responses may be expensive. Do not create random keys per retry or use idempotency to hide incorrect state transitions.

## Interview mistakes and follow-ups

Check-then-act race; dedupe separate from business transaction; assuming Kafka exactly-once covers payments/SMS. Follow-ups: concurrent duplicates? key reuse? timeout ambiguity? retention? multi-region?

## Five-minute recall

Stable key → atomic claim + effect → stored outcome → duplicate replay/skip → retention → external reconciliation.

Related: [[Transactional Outbox Pattern]], [[Retry Pattern]], [[Order Processing System]].

## Source metadata

Curated from source above; no personal Redis/payment claim.
