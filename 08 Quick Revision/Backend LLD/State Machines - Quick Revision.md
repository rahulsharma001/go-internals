---
type: quick-revision
domain: backend-lld
topic: state-machines
review_time: under-5-minutes
---

# State Machines — Quick Revision

## Mental Model

A state machine makes legal transitions explicit instead of scattering booleans across methods. Define states, events/commands, guards, side effects, and terminal states. A transition either commits completely or leaves state unchanged with a stable error. Keep transition validation close to state ownership. For concurrent services, one lock can protect the state and version, but external callbacks or persistence must not run under it; capture the transition result, unlock, then emit. Consider how callback failure affects the already-committed transition.

## Go / Design Checklist

Use typed string or integer states and a transition table or switch that is easy to review. Do not add states merely to mirror implementation steps. Commands should include identifiers needed for idempotency. Tests enumerate every legal transition, representative illegal transitions, terminal behavior, and concurrent duplicate commands. For distributed follow-ups, discuss optimistic version checks, outbox/event publication, and reconciliation without pretending the in-memory exercise provides durability. Explain the invariant in domain language before showing structs.

## Explain Aloud

In 60–90 seconds: state the contract, name the invariant and owner, describe success and failure flow, identify cancellation/shutdown behavior, give complexity, and make one Decision → Reason → Cost → Alternative trade-off.

## Reconstruction Drill

Close this note. Sketch the public API and ownership diagram from memory, implement the smallest success path, add one boundary/failure test, then run go test and go test -race where concurrent. Record only observed mistakes and schedule the re-test in [[Backend LLD Practice Tracker]].

## Practice Links

[[Circuit Breaker]], [[Food-Delivery Order State Machine]], [[Inventory Reservation System]], [[Elevator Controller]], [[Idempotency-Key Store]], [[Durable Job Scheduler Simulation]]

