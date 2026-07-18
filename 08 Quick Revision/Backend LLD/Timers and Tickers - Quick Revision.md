---
type: quick-revision
domain: backend-lld
topic: timers-and-tickers
review_time: under-5-minutes
---

# Timers and Tickers — Quick Revision

## Mental Model

time.Timer fires once; time.Ticker repeats until stopped. Prefer a timer when the next wake-up changes dynamically, such as a delayed queue or retry schedule. Reuse/reset patterns require careful Stop and channel draining; when clarity matters, create a fresh timer and stop it on every cancellation path. A ticker can leak resources or goroutines when not stopped. Never use wall-clock sleeps in deterministic unit tests for expiration logic when a Clock interface or manual trigger can control time.

## Go / Design Checklist

Time can move unexpectedly; comparisons should define expiry at now >= expiresAt. Store deadlines, not remaining durations, in owned state. For a heap scheduler, the earliest deadline owns the timer; inserting an earlier item must wake and reset the scheduler. Context cancellation should win without leaving an unread timer event that blocks cleanup. Tests should use a fake clock for refill/TTL math and minimal real timers only for context plumbing. Check zero/negative durations, deadline boundaries, timer reset after an earlier insertion, and shutdown while waiting.

## Explain Aloud

In 60–90 seconds: state the contract, name the invariant and owner, describe success and failure flow, identify cancellation/shutdown behavior, give complexity, and make one Decision → Reason → Cost → Alternative trade-off.

## Reconstruction Drill

Close this note. Sketch the public API and ownership diagram from memory, implement the smallest success path, add one boundary/failure test, then run go test and go test -race where concurrent. Record only observed mistakes and schedule the re-test in [[Backend LLD Practice Tracker]].

## Practice Links

[[TTL Cache]], [[Expiring Priority Queue]], [[Token-Bucket Rate Limiter]], [[Retry Executor]], [[Delayed Job Queue]], [[Cron-Like Scheduler]], [[Concurrent Batch Processor]]

