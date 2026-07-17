---
status: learning
type: canonical
area: system-design
sources:
  - "ChatGPT: System Design Patterns (2026-07-05, 6a4aa703-f2d8-83ee-aac3-020aa67e9afb)"
---

# Saga Pattern

## Problem it solves

A business operation spans services that cannot share one ACID transaction. A saga coordinates local transactions and explicitly repairs partial completion.

## Mental model

It is a state machine with a forward action and, where possible, a compensating action for every committed step. Compensation is a new business operation, not a database rollback.

## How it works

- **Orchestration:** a saga coordinator commands each participant and records the current step. This is easier to inspect and change.
- **Choreography:** services react to events and publish the next event. This reduces central control but can hide the overall flow.
- Persist saga state, command/event IDs, attempts, deadlines, and terminal outcome.
- Make every participant idempotent. Use [[Transactional Outbox Pattern]] for durable publication and an inbox/deduplication record for consumption.

## Concrete example and detailed dry run

For order `o-42`, the coordinator stores `PENDING_PAYMENT`. Payment authorizes ₹1,000 and returns `payment-9`; the coordinator advances to `PENDING_INVENTORY`. Inventory reserves SKU `book-7`, then the saga marks the order `CONFIRMED` and requests notification. If inventory rejects the reservation, the coordinator sends `RefundPayment(payment-9)`, records the refund outcome, and marks the order `CANCELLED`.

## Success scenario

Every local transaction commits once, duplicate messages return the stored result, and the saga reaches a durable terminal state.

## Failure scenario

A worker crashes after payment commits but before acknowledging. The command is redelivered; payment's idempotency key returns the existing authorization. If inventory permanently fails, compensation is retried independently. An irrecoverable compensation moves to manual review rather than pretending the saga is complete.

## Scaling considerations

Partition saga commands by aggregate ID to preserve per-order ordering. Avoid one global coordinator instance; store state durably and scale stateless workers. Apply backpressure and cap concurrent sagas when dependencies degrade.

## Production technology choices

PostgreSQL for saga state and local transactions; Kafka for durable ordered streams; Temporal/Cadence for workflow semantics; Debezium for outbox relay. Choose based on operational maturity, not fashion.

## Trade-offs

Sagas preserve availability and service autonomy, but expose intermediate states, add compensation logic, and provide eventual rather than instantaneous cross-service consistency.

## When not to use it

Do not split a transaction into a saga when one database boundary is acceptable, or when the business action cannot tolerate intermediate visibility or define safe compensation.

## Common interview mistakes

- Calling compensation a rollback.
- Omitting idempotency, persisted state, deadlines, and manual-repair paths.
- Assuming every side effect is reversible.
- Choosing choreography without explaining event loops and observability.

## Interview questions and follow-ups

- What happens if compensation also fails?
- How do you prevent an old command from changing a completed saga?
- When would orchestration be clearer than choreography?

## Five-minute recall

1. Local transaction per service.
2. Durable saga state machine.
3. Idempotent commands and consumers.
4. Forward steps plus explicit compensation.
5. Timeouts, retries, terminal states, and manual repair.

## Related notes

[[Order Processing System]] · [[Transactional Outbox Pattern]] · [[Idempotency Pattern]] · [[Retry Pattern]] · [[Queues and Pub Sub]]

## Source metadata

Primary extracted source: *System Design Patterns*, 2026-07-05, conversation ID above. Technology behavior should be verified against current vendor documentation before implementation.

