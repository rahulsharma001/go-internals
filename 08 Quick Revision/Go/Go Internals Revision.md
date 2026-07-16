---
type: quick-revision
domain: go
topic: go-internals
status: deferred
canonical: "[[Go Runtime Overview]]"
---

# Go Internals Revision

This is a retrieval card, not an active Week 1 task.

| Topic | Recall in one line |
|---|---|
| [[Go Scheduler]] | G is work, M is an OS thread, P enables Go execution; diagnose with measurements, never assumed fairness. |
| [[Go Memory Model]] | Cross-goroutine visibility needs a defined synchronization relationship; timing is not synchronization. |
| [[Go Memory Allocation and Escape Analysis]] | Go passes values; the compiler chooses placement from lifetime and escape analysis. |
| [[Go Garbage Collector]] | GC cost follows reachable heap shape, allocation rate, and retention; profile before tuning. |
| [[Go Slice Internals]] | A copied descriptor may share backing storage; append may reuse or replace it. |
| [[Go Map Internals]] | Hashing gives expected fast access; order and runtime layout are not stable contracts. |
| [[Go Interface Internals]] | An interface is nil only when both its dynamic type and dynamic value are absent. |
| [[Go Channel Internals]] | Sends and receives rendezvous or use a bounded buffer; blocked goroutines can be parked. |

## Interview boundary

State the language contract first, name version-sensitive implementation details, and connect internals to a real correctness or diagnostic question. If there is no such question, return to implementation practice.

Overview: [[Go Runtime Overview]] · Sprint boundary: [[Deferred Backlog]] · Index: [[Quick Revision Index]]
