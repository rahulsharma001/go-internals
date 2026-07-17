---
type: canonical
domain: system-design
topic: event-sourcing
status: active
last_verified: 2026-07-17
---
# Event Sourcing

## 1. Problem it solves

Some domains need an authoritative history of facts, temporal reconstruction, audit, and deterministic state derivation rather than storing only current state.

## 2. Simple mental model

The append-only event stream is truth; current state is a fold/projection. Events are immutable domain facts, not arbitrary logs or every table change.

## 3. How it works

Validate command against aggregate state/version; append new events with expected version; publish/project; snapshot periodically for load speed; evolve schemas/upcasters; correct with compensating events, not editing history.

## 4. Concrete example

Account stream: `PaymentIntentCreated`, `Authorized`, `Captured`, `RefundRequested`, `Refunded`; aggregate rejects invalid transition and projections build current status/audit.

## 5. Detailed success flow

01. Command handler loads the latest snapshot and all later events for the aggregate.
11. It rebuilds current state, validates the command against invariants, and proposes the next event.
21. Event store atomically appends at expected aggregate version N and rejects a concurrent mismatch.
31. Projectors consume the new event idempotently and update versioned read models
41. publisher exposes it to other owners.
51. API returns the new version or a conflict that the caller can safely resolve.

## 6. Detailed failure flow

01. Two writers append expected version 7
11. one wins, other gets conflict and reloads/rejects.
21. Broken projection rebuilds from immutable stream to new generation.

## 7. Scaling behaviour

Partition by aggregate ID; long streams need snapshots/archival; global queries require projections; event volume and replay time are major operations.

## 8. Data consistency implications

Strong per-aggregate append; projections eventual. Cross-aggregate invariant needs process/saga or different aggregate boundary. Event correction preserves history but complicates interpretation.

## 9. Real implementation choices

EventStoreDB, Kafka with careful retention/compaction limitations, relational append table, cloud event stores. Use schema registry and snapshots.

## 10. Trade-offs

Audit/time travel and flexible projections versus complex modeling, schema evolution, replay, storage, debugging, and privacy deletion.

## 11. When not to use it

Ordinary CRUD, team without event-model maturity, domains where erasure requirements conflict and benefits are weak. Outbox does not imply event sourcing.

## 12. Common interview mistakes

Events as CRUD diffs; mutable/deleted history; no version; replay side effects; no snapshot/evolution; Kafka retention assumed permanent truth; current table also uncontrolled truth.

## 13. How it appears inside larger systems

Ledgers/workflows/audit-heavy domains; scheduler history; occasionally collaborative files. Most systems need outbox, not full event sourcing.

## 14. Likely interviewer follow-ups

Aggregate boundary? concurrency? snapshot? schema evolution? GDPR/delete? replay external effects? temporal query? disaster recovery?

## 15. Five-minute revision

Immutable domain events as truth; expected-version append; fold/snapshot; projections eventual/rebuildable; never replay external side effects; pay schema/privacy cost.

## 16. Related notes

[[CQRS]] · [[Transactional Outbox Pattern]] · [[Saga Pattern]] · [[Consistency Models]]

## 17. Verified further reading

- [Microsoft event sourcing pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing) — vendor architecture guidance.
- [Apache Kafka log compaction](https://kafka.apache.org/documentation/#compaction) — official retention mechanics and limitations.
