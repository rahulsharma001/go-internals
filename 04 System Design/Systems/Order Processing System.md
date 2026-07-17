---
status: learning
type: system-design
area: system-design
sources:
  - "ChatGPT: System Design Patterns (2026-07-05, 6a4aa703-f2d8-83ee-aac3-020aa67e9afb)"
  - "Debezium Outbox Event Router documentation"
  - "Apache Kafka documentation"
---

# Order Processing System

## 1. Problem statement

Design an order workflow that accepts a purchase, coordinates payment and inventory across service boundaries, notifies the customer, and reaches an auditable terminal result despite duplicate messages and partial failure.

## 2. Functional requirements

- Create an order from validated items and a customer.
- Authorize/capture payment and reserve inventory.
- Expose order and step status.
- Notify on confirmed or cancelled outcome.
- Retry transient work and compensate permanent partial completion.
- Support operator investigation and safe replay.

Out of scope unless requested: catalogue search, fulfilment routing, returns, and accounting settlement.

## 3. Non-functional requirements

No lost accepted order; no duplicate business side effect; per-order event ordering; durable audit trail; bounded API latency; eventual cross-service consistency; controlled degradation when a dependency fails.

## 4. Scale assumptions

Obtain peak order writes, item count, payment latency, event retention, and recovery objectives from the interviewer. Size with variables: peak commands `W`, average events per order `E`, and event bytes `B`; broker ingress is approximately `W × E × B`. `status: needs-verification` until real requirements are supplied.

## 5. Core entities

`Order`, `OrderItem`, `Saga`, `Payment`, `InventoryReservation`, `OutboxEvent`, `ConsumerInbox`, and `Notification`.

Illustrative rows—not production data:

| Table | Key fields | Example row |
|---|---|---|
| orders | order_id, customer_id, status, total, version | `o-42, c-7, PENDING_PAYMENT, 1000 INR, 3` |
| saga | saga_id, order_id, step, status | `s-42, o-42, INVENTORY, RUNNING` |
| outbox | event_id, aggregate_id, type, payload, occurred_at | `e-77, o-42, OrderCreated.v1, {...}, t1` |
| consumer_inbox | consumer, event_id, result | `payment, e-77, payment-9` |

## 6. API design

```text
POST /v1/orders
Idempotency-Key: checkout-session-abc
{customerId, items:[{sku, quantity}], paymentMethodToken}
→ 202 {orderId:"o-42", status:"PENDING"}

GET /v1/orders/o-42
→ 200 {status, paymentStatus, inventoryStatus, version}

POST /v1/orders/o-42/cancel
Idempotency-Key: cancellation-xyz
```

The same idempotency key and normalized request return the stored response; the same key with a different payload is rejected.

## 7. Data model

Order, saga, and outbox rows share one PostgreSQL transaction. Service-owned payment and inventory databases remain separate. Optimistic `version` prevents lost updates. Money uses an integer minor unit plus currency. Events are immutable and versioned.

Outbox payload:

```json
{
  "eventId": "e-77",
  "eventType": "OrderCreated.v1",
  "aggregateType": "Order",
  "aggregateId": "o-42",
  "occurredAt": "illustrative-timestamp",
  "traceId": "trace-12",
  "payload": {"customerId":"c-7","totalMinor":100000,"currency":"INR"}
}
```

Kafka record:

```text
topic: order.events.v1
key: o-42
headers: event_id=e-77, event_type=OrderCreated.v1, schema_version=1, trace_id=trace-12
value: {customerId:c-7,totalMinor:100000,currency:INR}
```

## 8. High-level architecture

```text
Client → API Gateway → Order Service → PostgreSQL (Order + Saga + Outbox)
                                            │ committed WAL
                                            ▼
                                      Debezium CDC → Kafka
                                                     ├→ Payment Service
                                                     ├→ Inventory Service
                                                     └→ Notification Service
                                service results → Kafka → Saga worker → Order DB
```

See [[Saga Pattern]], [[Transactional Outbox Pattern]], [[Change Data Capture]], [[Idempotency Pattern]], [[Retry Pattern]], and [[Circuit Breaker Pattern]] for reusable mechanics.

## 9. Component responsibilities

- Gateway: authentication, request limits, idempotency header propagation.
- Order service: validates order-level invariants and exposes status.
- Saga worker: owns allowed transitions, timeouts, commands, and compensation.
- Debezium: publishes committed outbox rows; it does not supply business exactly-once.
- Kafka: durable delivery and per-key ordering within a partition.
- Participants: commit their local state and inbox/outbox atomically.

## 10. Complete request or event flow

`Client → API Gateway → Order Service → Order and Saga transaction → Transactional Outbox → Debezium CDC → Kafka → Payment → Inventory → Notification → Saga completion`.

1. Order service atomically inserts `Order(PENDING_PAYMENT)`, `Saga(RUNNING)`, and `OrderCreated` outbox.
2. CDC publishes with key `o-42`.
3. Payment consumes `e-77`; in one local transaction it inserts inbox `e-77`, records authorization, and writes `PaymentAuthorized` to its outbox.
4. The saga consumes that result, transitions to `PENDING_INVENTORY`, and emits `ReserveInventory`.
5. Inventory similarly deduplicates, reserves units, and emits `InventoryReserved`.
6. Saga changes the order to `CONFIRMED`, emits `OrderConfirmed`, and notification records its delivery request.
7. Notification delivery is asynchronous; order confirmation does not depend on email/SMS success.

## 11. Detailed success path

The API transaction returns `202` only after the order, saga, and first outbox row commit. CDC may publish twice, but inbox uniqueness makes each participant return its stored result. Payment and inventory results advance only the expected saga version. The final transaction sets `CONFIRMED` and writes the final event. `GET` shows step state throughout; trace/event IDs join the timeline.

## 12. At least one detailed failure path

**Inventory unavailable after payment:** inventory retries only transient failures with exponential backoff, jitter, and a deadline. On a permanent rejection or exhausted deadline it emits `InventoryRejected`. The saga changes to `COMPENSATING_PAYMENT` and issues `RefundPayment(payment-9)` with a stable command ID. Payment deduplicates, records the refund, and emits `PaymentRefunded`. The saga atomically marks `CANCELLED` and publishes `OrderCancelled`; notification informs the customer. A failed refund remains `COMPENSATION_PENDING`, pages/queues operator review, and never masquerades as cancelled-complete.

**Crash after payment commit:** redelivery finds `consumer_inbox(payment,e-77)` and returns `payment-9`; there is no second charge.

## 13. Bottlenecks

Hot product reservations, payment-provider latency, skewed Kafka partitions, database write contention, CDC lag, oversized payloads, and compensation storms.

## 14. Scaling strategy

Partition events by `order_id`; independently scale consumer groups; isolate hot SKU inventory ownership; batch only where latency allows; keep payloads compact; apply [[Backpressure Pattern]]; archive old outbox/inbox rows without destroying audit requirements.

## 15. Reliability and disaster recovery

Use multi-AZ databases and broker replication, point-in-time recovery, tested restore procedures, replayable events, poison-event quarantine, and recovery objectives agreed with the business. Reconciliation jobs compare non-terminal sagas with participant state; they do not silently force success.

## 16. Observability

Propagate `trace_id`, `order_id`, `saga_id`, and `event_id`. Measure API errors/latency, oldest unpublished outbox age, CDC/Kafka lag, saga duration by step, retry/duplicate rate, compensation rate, stuck saga count, and notification delivery outcomes. Alert on user-impacting symptoms and exhausted compensations.

## 17. Security

Authenticate clients; authorize ownership of order reads/cancellation; tokenize payment instruments and avoid storing raw card data; encrypt in transit/at rest; minimize PII in events; restrict topic/database access; audit operator actions; validate event schemas and sizes.

## 18. Concrete technology choices

PostgreSQL for order/saga/outbox ACID state; Debezium for log-based outbox relay; Kafka for durable events; Redis only for non-authoritative caching/rate limiting; OpenTelemetry-compatible telemetry. Payment provider choice and compliance controls are `status: needs-verification`.

## 19. Trade-offs

Orchestrated saga makes flow and repair visible but centralizes workflow logic. Choreography reduces coordinator commands but obscures the whole state machine. CDC reduces polling load but adds connector/log operations. Eventual consistency preserves availability but exposes intermediate states.

## 20. Interview follow-up questions

- Reserve inventory before payment, or payment before inventory?
- How are price changes handled between cart and order?
- How are events evolved and replayed?
- What happens when cancellation races with confirmation?
- How do reconciliation and manual repair work?

## 21. Five-minute revision

Order/saga/outbox commit together. CDC publishes to Kafka. Participants use inbox + local state + outbox. Saga advances by versioned results. Inventory failure triggers idempotent payment compensation. Observe lag, stuck steps, retries, and compensation. Never claim end-to-end exactly-once.

## Related notes

[[Data Storage Selection]] · [[Consistency Models]] · [[Timeouts Retries and Deadlines]] · [[Logs Metrics and Traces]] · [[API Security]]

## Source metadata

Core flow synthesized from *System Design Patterns* (2026-07-05, ID above) and verified conceptually against official Debezium/Kafka documentation. Example identifiers and rows are explicitly illustrative, not personal or production claims.
