---
type: quick-revision
domain: backend-lld
topic: context-and-cancellation
review_time: under-5-minutes
---

# Context and Cancellation — Quick Revision

## Mental Model

Context carries cancellation, deadline, and request-scoped values across an operation boundary. The caller creates and cancels it; a callee observes Done and returns ctx.Err when cancellation wins. Put context.Context first in method parameters and never store it as long-lived component state. Cancellation is cooperative: CPU loops and callbacks must check or receive context to stop. A context deadline does not automatically close channels, roll back state, or terminate a goroutine. Define whether an accepted operation finishes, drains, or is abandoned after cancellation.

## Go / Design Checklist

Every blocking channel send/receive should normally select on ctx.Done. Stop timers when cancellation wins and drain their channel only when required by the timer pattern. Preserve the causal error when wrapping. For admission APIs, cancellation before acceptance should leave state unchanged. After acceptance, decide whether the job uses the submission context or an independent lifecycle context. Test already-cancelled contexts, short deadlines, cancellation during backpressure, and goroutine completion after the caller times out.

## Explain Aloud

In 60–90 seconds: state the contract, name the invariant and owner, describe success and failure flow, identify cancellation/shutdown behavior, give complexity, and make one Decision → Reason → Cost → Alternative trade-off.

## Reconstruction Drill

Close this note. Sketch the public API and ownership diagram from memory, implement the smallest success path, add one boundary/failure test, then run go test and go test -race where concurrent. Record only observed mistakes and schedule the re-test in [[Backend LLD Practice Tracker]].

## Practice Links

[[Context Cancellation]], [[Semaphore With Context Cancellation]], [[Thread-Safe Bounded Queue]], [[Worker Pool]], [[Retry Executor]], [[Timeout and Deadline Budget]], [[Token-Bucket Rate Limiter]]

