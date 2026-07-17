---
type: canonical
domain: system-design
topic: invariants-critical-paths
status: active
---
# Invariants and Critical Paths

## Purpose

An invariant is a statement that must remain true across concurrency, retry, and failure. A critical path is the minimum sequence whose latency or correctness determines the user-visible result. Senior designs protect invariants narrowly instead of applying strong consistency everywhere.

## Derivation method

1. State the user journey in one sentence.
2. Ask what outcome would be unacceptable: double charge, oversold seat, lost acknowledged upload, two drivers, or message reorder.
3. Write the invariant as a testable statement.
4. Find the smallest authoritative state and transaction/conditional boundary enforcing it.
5. Mark derived views that may lag.
6. Define completion: accepted, committed, delivered, or reconciled.

## Examples

| System | Strict invariant | Relaxed state |
| --- | --- | --- |
| payment | one logical payment intent causes at most one charge | analytics and receipt email |
| ticketing | one seat has at most one active confirmed booking | search availability |
| ride matching | one driver has at most one active trip | displayed location/ETA |
| video | acknowledged source object remains durable | search index/view count |
| chat | accepted message is durable and ordered per conversation | presence/typing/global order |
| scheduler | one logical run result is committed per schedule occurrence | duplicate worker execution may occur |

## Critical-path worksheet

Number: caller → validation/auth → idempotency → authoritative read/conditional write → durable commit → response. Move notifications, analytics, indexing, and optional enrichment off the path unless requirements demand them. Each synchronous dependency consumes latency budget and availability.

## Concurrency tools

- unique constraint for “one key, one record”;
- compare-and-set/version for state transition;
- row transaction for related invariant state;
- partition ownership for ordered per-key mutation;
- idempotency key for duplicate commands;
- lease plus fencing token when exclusive external work is unavoidable.

Locks are not the first answer; database constraints and deterministic ownership are easier to reason about.

## Failure reasoning

A timeout is an unknown outcome, not proof of failure. Ask whether state may have committed. Retry with the same identity, query authoritative state, or reconcile. Never compensate based only on a client timeout. State machines need valid transitions and terminal/manual-repair states.

## Interview phrases

- “I need strong consistency only for the final claim; candidate discovery may be stale.”
- “The response confirms durable acceptance, not completion of asynchronous side effects.”
- “This projection can lag because the authoritative row and version remain queryable.”

## Common mistakes

Vague “data consistency,” no commit point, more than one writer, global ordering without need, queue treated as truth, cache mutation before source commit, and a success response before durable acceptance.

## Five-minute revision

Journey → unacceptable outcome → invariant → owner → enforcement boundary → completion semantics → derived stale state → timeout/duplicate behavior.

Related: [[Consistency Models]] · [[Idempotency Pattern]] · [[API and Data Model Design]] · [[Reliability and Failure Analysis]].

