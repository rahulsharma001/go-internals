---
type: canonical
domain: system-design
topic: saga-pattern
status: active
last_verified: 2026-07-17
---
# Saga Pattern

## 1. Problem it solves

A business workflow spans independently owned services/databases, so one ACID transaction cannot atomically update all participants.

## 2. Simple mental model

A saga is a persisted state machine of local transactions. Failure triggers semantic compensation where possible; compensation is a new business action, not rollback.

## 3. How it works

Orchestration has a coordinator issue idempotent commands and record results/timeouts. Choreography reacts to events without a central command owner. Every step has identity, expected state/version, retry classification, compensation/manual repair, and terminal states.

## 4. Concrete example

Order: create pending → authorize payment → reserve inventory → confirm. Inventory rejection triggers void/refund payment. Refund failure leaves `COMPENSATION_PENDING`, not falsely `CANCELLED`.

## 5. Detailed success flow

Saga commits current step+outbox, participant deduplicates command and commits result+outbox, coordinator advances expected version, final confirmed event publishes.

## 6. Detailed failure flow

Participant times out after commit. Coordinator retries same command/reconciles result. Permanent failure transitions to compensation. Compensation failure persists and escalates with operator tooling.

## 7. Scaling behaviour

Partition saga by aggregate/order ID; compact/archive terminal histories; timer service handles millions of deadlines; isolate compensation storms; avoid one global coordinator bottleneck.

## 8. Data consistency implications

Cross-service state is eventually consistent and exposes intermediate states. Local transactions preserve each service invariant. Events may duplicate/reorder; versions reject stale transitions.

## 9. Real implementation choices

Custom orchestrator with PostgreSQL/outbox; Temporal/Cadence/Camunda-like workflow engine; Kafka events. Engine does not remove idempotency/business compensation.

## 10. Trade-offs

Orchestration makes flow/repair visible but centralizes logic. Choreography decouples publishers but hides loops/ownership. Compensation may be incomplete/expensive.

## 11. When not to use it

If all state fits one database transaction, prefer it. Irreversible side effects may require reservation/authorization/manual approval rather than compensation.

## 12. Common interview mistakes

Calling compensation rollback; no persisted state; happy path only; no timeout/unknown outcome; service writes another DB; infinite retries; terminal repair state missing.

## 13. How it appears inside larger systems

Orders, payments, travel/booking, provisioning, file workflows, multi-step notifications.

## 14. Likely interviewer follow-ups

Step order? compensation? timeout after commit? cancellation race? orchestration vs choreography? repair/replay? schema/version? stuck workflow metrics?

## 15. Five-minute revision

Persist saga+step+version; local transaction+outbox; idempotent participants/inbox; bounded timeout/retry; semantic compensation; visible pending/manual repair; observe stuck duration.

## 16. Related notes

[[Transactional Outbox Pattern]] · [[Deduplication and Inbox Pattern]] · [[Order Processing System]] · [[Payment System]]

## 17. Verified further reading

- [Microsoft saga pattern](https://learn.microsoft.com/azure/architecture/reference-architectures/saga/saga) — vendor architecture guidance on orchestration/choreography.\n- [Debezium Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) — official local-transaction event handoff.

