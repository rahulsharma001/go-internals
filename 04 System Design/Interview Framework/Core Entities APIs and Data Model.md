---
type: canonical
domain: system-design
topic: entities-apis-data-model
status: learning
---
# Core Entities APIs and Data Model

## Problem it solves

It turns user flows into durable state boundaries and explicit contracts before architecture boxes obscure the domain.

## Mental model and method

Entities hold identity and lifecycle; APIs express commands/queries; events record facts. For each critical flow, define identifier, owner, state transitions, invariants, access patterns, transaction boundary, idempotency, pagination, authorization, and error semantics. Model from queries and consistency needs, not database fashion.

## Concrete example and dry run

Order entities: `Order`, `OrderItem`, `SagaInstance`, `OutboxEvent`; payment and inventory remain owned by their services. `POST /orders` accepts items and an `Idempotency-Key`, returning `202 Accepted` with `order_id` and `PENDING`. `GET /orders/{id}` returns current state. `OrderCreated` is a fact with `event_id`, `aggregate_id`, version, timestamp, and payload.

Dry run: duplicate POST hits a unique `(customer_id,idempotency_key)` record and returns the original order. The order row and outbox row commit together. A consumer deduplicates `(consumer,event_id)` in the same transaction as its business change.

## Success and failure scenarios

Success: ownership and unique constraints enforce the invariant. Failure: a retry creates two orders, offset pagination skips/duplicates under concurrent writes, or one service updates another service’s tables. Fix with stable keys, cursor pagination, and service-owned data.

## Scaling and production choices

Relational stores suit multi-row constraints and workflows; key-value/document stores suit known key access and horizontal partitioning; search indexes serve flexible text/filter queries; object stores own large blobs. Events are not a substitute for a source of truth.

## Trade-offs and when not to use

Normalized models reduce duplication but add joins; denormalized views improve reads but require reconciliation. Synchronous APIs give immediate status but couple latency; commands/events decouple work but expose intermediate states. Avoid creating an entity/service per noun.

## Interview mistakes and follow-ups

No idempotency, no state machine, vague JSON, missing authorization, shared database, and choosing Cassandra merely for “scale.” Follow-ups: schema evolution? deletion/privacy? hot partition? list consistency? version conflicts?

## Five-minute recall

Flow → entities/IDs → commands/queries/events → owner → invariant/transaction → access patterns/index → idempotency → pagination/errors → evolution.

Related: [[Data Storage Selection]], [[Idempotency Pattern]], [[Transactional Outbox Pattern]].

## Source metadata

Curated from the existing framework and sanitized order/event-pipeline material (`System Design Patterns`, 2026-07-05, `6a4aa703…`).
