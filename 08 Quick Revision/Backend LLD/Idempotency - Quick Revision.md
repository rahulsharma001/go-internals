---
type: quick-revision
domain: backend-lld
topic: idempotency
review_time: under-5-minutes
---

# Idempotency — Quick Revision

## Mental Model

Idempotency means repeating the same logical command does not create a second effect. It is not the same as deduping payloads: the client supplies a key scoped to an operation and identity. A store records in-progress, completed result, or failed/retryable state. Concurrent duplicates either wait for the first result or receive a defined conflict. The payload fingerprint prevents accidental reuse of one key for different commands. Expiry bounds memory but reopens the duplicate window after retention.

## Go / Design Checklist

Define when the key becomes authoritative: before the side effect, atomically with it, or after it. In-memory code cannot prove crash safety across an external side effect; state that limitation. Never hold a lock while executing the user operation. Use a per-key completion signal or singleflight-like record, and make its closing owner explicit. Tests cover concurrent same-key calls, same key/different payload, operation failure, waiter cancellation, expiry, and result replay. Production follow-ups include transactional storage, fencing, TTL policy, and observability for conflicts.

## Explain Aloud

In 60–90 seconds: state the contract, name the invariant and owner, describe success and failure flow, identify cancellation/shutdown behavior, give complexity, and make one Decision → Reason → Cost → Alternative trade-off.

## Reconstruction Drill

Close this note. Sketch the public API and ownership diagram from memory, implement the smallest success path, add one boundary/failure test, then run go test and go test -race where concurrent. Record only observed mistakes and schedule the re-test in [[Backend LLD Practice Tracker]].

## Practice Links

[[Idempotency-Key Store]], [[Singleflight Request Coalescer]], [[Inventory Reservation System]], [[Message Queue With Acknowledgements]], [[Resilient API Client]]

