---
type: quick-revision
domain: go
topic: synchronization
canonical: "[[Mutexes and Data Race Safety]]"
---

# Synchronization - Quick Revision

## 30-second definition and mental model

A mutex protects an invariant over shared memory. A race is concurrent conflicting access without synchronization. Lock the whole invariant, not an arbitrary line.

Five facts: mutexes are not reentrant; do not copy after use; pointer receivers suit mutex-bearing types; RWMutex is not automatically faster; the race detector finds executed races, not all possible races.

Common trap: locking writes while leaving reads unsynchronized.

Production example: protect a multi-field cache invariant, while keeping network calls outside the critical section.

Interview answer: “I state the shared invariant and happens-before relationship, choose lock granularity, avoid copying, and verify with `go test -race` plus contention profiles.”

Active recall: implement a safe transfer with stable two-lock ordering.

Canonical: [[Mutexes and Data Race Safety]] · Related: [[Go Memory Model]]

Index: [[Quick Revision Index]]
