---
type: canonical
domain: system-design
topic: api-data-model
status: active
---
# API and Data Model Design

## Purpose

APIs expose commands and queries; data models enforce ownership, access paths, lifecycle, and invariants. Design them together before architecture boxes.

## Interview-sized API contract

For each important operation state:

- method/path or RPC and semantic action;
- request identifiers, required fields, validation, and authentication;
- response and what success means;
- idempotency key and duplicate-payload conflict rule for mutations;
- cursor pagination and stable ordering for lists;
- expected errors: validation, authorization, conflict, rate limit, unavailable, unknown/pending;
- async status/event if completion outlives the request.

Example:

```text
POST /v1/payments
Authorization: Bearer …
Idempotency-Key: checkout-9
{merchantId, orderId, amountMinor, currency, paymentMethodToken}
→ 202 {paymentId, status:"PROCESSING"}
409 if the same key is reused with a different normalized payload
```

## Model from access patterns

For every authoritative table/store record specify primary key, partition key, indexes, source of truth, retention, consistency, and reads/writes. Add a `version` or state transition guard where concurrent mutation matters.

Representative payment rows:

```text
payment_intents(payment_id PK, merchant_id, order_id, amount_minor,
  currency, status, version, idempotency_key, payload_hash, created_at)
UNIQUE(merchant_id, idempotency_key)

payment_attempts(attempt_id PK, payment_id, provider, provider_ref,
  status, error_class, created_at)
INDEX(payment_id, created_at)
```

Money uses integer minor units plus currency; time uses explicit semantics; state transitions are enumerated. Large blobs live in [[Blob Object and File Storage]], not automatically in relational rows.

## Ownership and derived data

One service owns writes to each authoritative dataset. Search indexes, caches, feeds, analytics, and materialized views are derived and rebuildable. Cross-service changes use APIs/events, not direct table writes. Events include stable `event_id`, aggregate key, version, schema version, timestamp, and trace ID.

## Pagination

Prefer cursor pagination on a stable sort key such as `(created_at,id)`; offset pagination becomes slow and inconsistent under concurrent writes. Define whether deleted/inserted items may alter a traversal.

## Schema evolution and deletion

Use additive event changes, tolerant readers, explicit versions, dual read/write only during migrations, and backfill observability. Retention/deletion must cover authoritative rows, derived indexes, caches, object storage, backups, and events according to supplied policy.

## Common mistakes

No uniqueness/idempotency, unbounded list/array, shared database ownership, random partition key, search/cache as sole truth, storing secrets/PII in events, vague status string, no authorization, and list endpoints without pagination.

## Follow-ups

How does cancellation race with completion? How do schema versions coexist? What query becomes cross-partition? How is a deleted object removed from derived stores? What happens when a duplicate key has a different payload?

## Five-minute revision

Journey → commands/queries → auth/idempotency/errors/pagination → entities/lifecycle → owner → PK/partition/index → constraint/version → derived views → retention/evolution.

Related: [[Database and Storage Selection]] · [[Invariants and Critical Paths]] · [[Transactional Outbox Pattern]] · [[API and Data Model Checklist]].

