---
type: quick-revision
domain: go
topic: go-scheduler
canonical: "[[Go Scheduler]]"
---

# Go Scheduler - Quick Revision

## 30-second definition and mental model

G is a goroutine, M an OS thread, and P the runtime resource needed to execute Go code. `GOMAXPROCS` controls P count, while many goroutines may be runnable, running, or waiting.

Five facts: local/global runnable queues exist; idle Ps can steal work; channel/mutex waits park goroutines; syscall and netpoll paths help keep other work moving; exact fairness/layout is not a stable contract.

Common trap: equating goroutine count with threads or CPU parallelism.

Production example: use traces and block profiles before changing runtime settings; bound CPU work to the actual bottleneck.

Interview answer: “The runtime multiplexes Gs over Ms using Ps; work stealing and parking keep resources utilized, while `GOMAXPROCS` bounds simultaneous Go execution.”

Active recall: explain 10,000 goroutines with four Ps.

Canonical: [[Go Scheduler]] · Foundation: [[Goroutines and Lifecycle]]

Index: [[Quick Revision Index]]
