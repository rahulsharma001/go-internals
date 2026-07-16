---
type: quick-revision
domain: go
topic: go-memory-model
canonical: "[[Go Memory Model]]"
---

# Go Memory Model - Quick Revision

## 30-second definition and mental model

The memory model defines when writes in one goroutine are guaranteed visible to another. Program order plus synchronization creates happens-before; timing and sleeps do not.

Five facts: conflicting unsynchronized access is a race; mutex unlock/lock can order work; channel operations create specified ordering; atomics suit carefully scoped state; the race detector covers executed paths only.

Common trap: publishing data by setting a plain shared boolean.

Production example: close a ready channel after initialization and receive it before reading published state.

Interview answer: “I identify the shared invariant and exact synchronization edge. Race-free code is the baseline; contention optimization comes after correctness.”

Active recall: repair unsafe publication with channel, mutex, and atomic variants.

Canonical: [[Go Memory Model]] · Related: [[Mutexes and Data Race Safety]]

Index: [[Quick Revision Index]]
