---
type: canonical
domain: system-design
topic: sync-async-communication
status: learning
source_conversations:
  - "System Design Patterns | 2026-07-05 | 6a4aa703-f2d8-83ee-aac3-020aa67e9afb"
---
# Synchronous vs Asynchronous Communication

## Problem it solves

It chooses whether a caller waits for downstream work or durably hands it off for later processing.

## Mental model and how it works

Synchronous calls give immediate answers and simple control flow but couple latency and availability. Asynchronous commands/events buffer bursts and decouple consumers but require durable acceptance, intermediate states, idempotency, ordering, and reconciliation. The question is completion semantics, not REST versus Kafka branding.

## Concrete example and dry run

Order creation synchronously validates/authenticates and commits order plus outbox; it returns `202 PENDING`. Payment, inventory, and notifications run asynchronously. `GET /orders/o1` exposes progress. If synchronous validation fails, no durable work exists. If a consumer is down, Kafka retains work and queue age rises without blocking order acceptance until a configured backlog limit.

## Success and failure scenarios

Success: user knows whether acceptance or completion was confirmed. Failure: fire-and-forget loses work, unbounded queues hide overload, or synchronous retry storms collapse a dependency. Use durable queues, deadlines, retry budgets, idempotency, backpressure, and explicit status.

## Scaling and production choices

HTTP/gRPC suit queries and immediate commands; queues/streams suit buffering, fan-out, replay, and independent consumers. Observe end-to-end latency, queue age/depth, consumer lag, retry/DLQ, and business completion—not only API latency.

## Trade-offs and when not to use

Async improves isolation but adds eventual consistency and operational complexity. Do not introduce a broker for a fast, reliable, required response with no need for buffering/fan-out.

## Interview mistakes and follow-ups

“Async is faster”; no durable acknowledgment; no backlog policy; events used for queries. Follow-ups: what does 202 mean? duplicate delivery? ordering? poison message? provider outage?

## Five-minute recall

User completion → coupling budget → durable handoff → status → idempotency/order → overload → observe business completion.

Related: [[Queues and Pub Sub]], [[Transactional Outbox Pattern]], [[Backpressure Pattern]], [[Timeouts Retries and Deadlines]].

## Source metadata

Curated from source conversation listed above and Apache Kafka documentation; product versions require verification.
