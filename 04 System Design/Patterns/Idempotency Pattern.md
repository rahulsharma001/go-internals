---
type: canonical
domain: system-design
topic: idempotency-pattern
status: active
last_verified: 2026-07-17
---
# Idempotency Pattern

## 1. Problem it solves

Clients and workers retry after timeouts, so one logical command may arrive multiple times. Idempotency makes repeats return the same effect/result rather than duplicate side effects.

## 2. Simple mental model

Stable operation identity + durable ownership + payload conflict rule + stored outcome. Idempotency is not “check then act” in memory.

## 3. How it works

Client supplies key scoped to principal/operation. Service atomically inserts key with normalized request hash and operation/result. Winner executes or ties business state to same transaction. Duplicate same payload returns stored/pending result; different payload conflicts. Retain keys for retry horizon.

## 4. Concrete example

`POST /payments` with merchant+`checkout-9`; unique `(merchant,key)` row stores amount/currency hash and payment ID. Provider call uses stable provider idempotency/reference.

## 5. Detailed success flow

First command reserves key and creates intent. Retry sees same hash and returns intent/status. Only state machine can create one charge attempt per logical step.

## 6. Detailed failure flow

Service commits charge but response is lost. Retry returns/reconciles existing result instead of charging. If key exists with different amount, return conflict and alert suspicious reuse.

## 7. Scaling behaviour

Partition idempotency records with business owner/key; avoid global locks. TTL/archival follows maximum retry and audit needs. Hot clients need rate limits.

## 8. Data consistency implications

Key and business mutation should share a transaction when possible. Cross-system side effects require downstream idempotency and reconciliation; an API key alone cannot make external effects atomic.

## 9. Real implementation choices

Relational unique constraint, DynamoDB conditional put, Redis only if durability/eviction semantics are acceptable, provider-native idempotency plus local ledger.

## 10. Trade-offs

Storage and serialization versus safe retries. Long retention improves safety/audit but costs storage/privacy. `PENDING` handles concurrent duplicates but needs recovery.

## 11. When not to use it

Pure read operations may already be naturally idempotent. Do not use random server-generated keys the retrying client cannot reuse.

## 12. Common interview mistakes

In-memory map; check then insert race; key without principal/payload hash; key expires too soon; every retry gets new key; claiming exactly once.

## 13. How it appears inside larger systems

Payments, order creation/cancel, booking holds, notification sends, uploads, job execution, message producers/consumers.

## 14. Likely interviewer follow-ups

Scope? same key/different body? concurrent duplicate? crash after side effect? retention? downstream provider? pending/failed retry semantics?

## 15. Five-minute revision

Stable scoped key, normalized hash, atomic reservation+business state, stored pending/result, conflict on changed payload, retain for retry horizon, propagate downstream.

## 16. Related notes

[[Deduplication and Inbox Pattern]] · [[Retry Timeout and Deadline Pattern]] · [[Payment System]]

## 17. Verified further reading

- [AWS Builders’ Library: idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) — official production reasoning for retry-safe mutations.\n- [DynamoDB condition expressions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.OperatorsAndFunctions.html) — official conditional-put primitives.

