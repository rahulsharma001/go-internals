---
type: canonical
domain: system-design
topic: synchronous-vs-asynchronous-communication
status: active
last_verified: 2026-07-17
---
# Synchronous vs Asynchronous Communication

## 1. Problem it solves

Service interactions must choose whether the caller waits for completion or hands off durable work. The choice changes latency, coupling, state, and failure semantics.

## 2. Simple mental model

Synchronous is a live conversation requiring both parties now. Asynchronous is a durable note processed later. Async removes temporal coupling only if the handoff is durable and the product exposes intermediate state.

## 3. How it works

Sync HTTP/RPC carries deadline/cancellation and returns success/error. Async command/event is durably queued with stable identity; producer returns accepted/pending; workers process, publish results, and status/reconciliation closes the workflow.

## 4. Concrete example

`POST /orders` synchronously validates and commits `PENDING` order plus outbox, returning `202`. Payment and inventory proceed asynchronously. `GET /orders/{id}` reports progress. Email never blocks order confirmation.

## 5. Detailed success flow

Sync path has bounded dependencies and commits the acceptance point. Async handoff survives process failure; idempotent consumers advance a state machine; the user sees accurate status.

## 6. Detailed failure flow

Broker publish succeeds but response is lost; idempotency returns the same request. Consumer backlog grows; admission limits new optional work, critical priority is isolated, status shows delayed rather than false success.

## 7. Scaling behaviour

Sync fan-out multiplies tail latency and failure probability. Async buffers bursts and scales consumers, but backlog must fit retention and drain capacity. Batch where latency permits.

## 8. Data consistency implications

Sync does not guarantee strong consistency across services; async does not require chaos. Define authoritative state, transition order, stale views, duplicates, and completion.

## 9. Real implementation choices

HTTPS/gRPC for bounded queries/commands; Kafka/SQS/Pub/Sub for durable async; WebSocket for live delivery with durable catch-up; workflow engines for long stateful orchestration.

## 10. Trade-offs

Sync is simple/immediate but coupled to downstream availability and tail latency. Async improves resilience/throughput but adds lag, duplicate handling, status, debugging, and storage.

## 11. When not to use it

Do not make a tiny local operation async solely for fashion. Do not use sync chains for slow, bursty, or externally rate-limited side effects when accepted/pending semantics work.

## 12. Common interview mistakes

Queue after responding without durable handoff; `202` with no status; async claimed exactly-once; sync retry amplification; no deadline; event used as command with unclear owner.

## 13. How it appears inside larger systems

Payments, orders, notifications, media processing, analytics, search indexing, chat fan-out, and API composition.

## 14. Likely interviewer follow-ups

What does response mean? What if publish fails? How does user learn completion? What is max backlog? How cancel? Which layer retries? When does async not help?

## 15. Five-minute revision

Sync waits and couples; async hands off and exposes state. Define durable acceptance, deadline, identity, status, idempotent consumer, backlog bounds, and completion.

## 16. Related notes

[[Queues Streams and Pub Sub]] · [[Transactional Outbox Pattern]] · [[Retry Timeout and Deadline Pattern]] · [[Saga Pattern]]

## 17. Verified further reading

- [RFC 9110 HTTP semantics](https://www.rfc-editor.org/rfc/rfc9110) — authoritative HTTP method/status semantics.\n- [Debezium Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) — official durable database-to-event handoff.

