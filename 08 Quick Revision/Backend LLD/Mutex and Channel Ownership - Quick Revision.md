---
type: quick-revision
domain: backend-lld
topic: mutex-and-channel-ownership
review_time: under-5-minutes
---

# Mutex and Channel Ownership — Quick Revision

## Mental Model

Use a mutex when several goroutines share state with an invariant spanning multiple fields. Use channels when values or ownership move between goroutines and queueing/lifecycle are part of the contract. A mutex protects data, not code; document the exact fields and keep critical sections small. Never invoke user callbacks while holding an internal lock because re-entry or slow work can deadlock and inflate tail latency. A channel must have one closing owner. Receivers normally do not close it, and multiple producers require a coordinator to close after all senders finish.

## Go / Design Checklist

For each design, answer: who creates the channel, who sends, who closes, and what unblocks a blocked send/receive on shutdown? Closing broadcasts completion but does not cancel already-running callbacks. A mutex plus a replaced-and-closed notification channel can wake context-aware queue waiters without sync.Cond. With RWMutex, do not hold a read lock across arbitrary work; it delays shutdown writers. Preserve lock ordering if more than one lock exists. Run race tests with many callers and shutdown overlap, not only sequential happy paths.

## Explain Aloud

In 60–90 seconds: state the contract, name the invariant and owner, describe success and failure flow, identify cancellation/shutdown behavior, give complexity, and make one Decision → Reason → Cost → Alternative trade-off.

## Reconstruction Drill

Close this note. Sketch the public API and ownership diagram from memory, implement the smallest success path, add one boundary/failure test, then run go test and go test -race where concurrent. Record only observed mistakes and schedule the re-test in [[Backend LLD Practice Tracker]].

## Practice Links

[[Mutexes and Data Race Safety]], [[Go Channels]], [[Thread-Safe Bounded Queue]], [[Worker Pool]], [[In-Process Pub Sub Broker]], [[Connection Pool]]

