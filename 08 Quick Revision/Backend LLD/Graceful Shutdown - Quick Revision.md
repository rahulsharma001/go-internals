---
type: quick-revision
domain: backend-lld
topic: graceful-shutdown
review_time: under-5-minutes
---

# Graceful Shutdown — Quick Revision

## Mental Model

Graceful shutdown has phases: stop admission, signal owned workers, finish or cancel accepted work according to policy, release resources, and report completion. State transitions must be idempotent because multiple callers may close concurrently. The component that owns a work channel closes it only after no sender can race with closure. A WaitGroup counts owned goroutines; Add happens before launch, Done is deferred, and Wait must not race with new Add operations. A caller deadline limits waiting but should not leave shutdown ownership undefined.

## Go / Design Checklist

Choose drain versus abort explicitly. Drain gives accepted work a completion guarantee but can exceed a caller deadline; abort reduces latency but requires idempotency/retry semantics. Reject new work with a stable error after shutdown begins. Unblock producers, consumers, and timer waiters. Do not close result channels before workers finish. Tests should cover empty close, double close, close during blocked submit, accepted work completion, deadline expiry, no goroutine leak, and race detector execution. Explain who continues cleanup if Close(ctx) returns early.

## Explain Aloud

In 60–90 seconds: state the contract, name the invariant and owner, describe success and failure flow, identify cancellation/shutdown behavior, give complexity, and make one Decision → Reason → Cost → Alternative trade-off.

## Reconstruction Drill

Close this note. Sketch the public API and ownership diagram from memory, implement the smallest success path, add one boundary/failure test, then run go test and go test -race where concurrent. Record only observed mistakes and schedule the re-test in [[Backend LLD Practice Tracker]].

## Practice Links

[[Goroutines and Lifecycle]], [[Worker Pool]], [[Thread-Safe Bounded Queue]], [[Delayed Job Queue]], [[Cron-Like Scheduler]], [[Connection Pool]], [[Message Queue With Acknowledgements]]

