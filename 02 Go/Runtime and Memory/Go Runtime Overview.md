---
type: overview
domain: go
topic: go-runtime
status: deferred
---

# Go Runtime Overview

Use this page to route a runtime question to one focused canonical. It is not an active 30-day sprint curriculum and does not replace implementation-first Go study.

| Question | Canonical note |
|---|---|
| How do goroutines share execution resources? | [[Go Scheduler]] |
| When is a cross-goroutine read guaranteed to observe a write? | [[Go Memory Model]] |
| Why does a value use local or heap-backed storage? | [[Go Memory Allocation and Escape Analysis]] |
| What drives tracing and reclamation work? | [[Go Garbage Collector]] |
| How do backing arrays, aliasing, growth, and retention interact? | [[Go Slice Internals]] |
| How do hashing, collision handling, growth, and ordering constraints interact? | [[Go Map Internals]] |
| How do dynamic type/value pairs explain typed nil and dispatch? | [[Go Interface Internals]] |
| How are rendezvous, buffering, waiting, and wake-up coordinated? | [[Go Channel Internals]] |

## Study boundary

Start from the language-level notes—[[Go Slices]], [[Go Maps]], [[Go Interfaces]], and [[Go Channels]]—then open an internals note for a concrete interview follow-up or measured diagnostic need. Exact runtime layouts and policies may change across Go versions; application correctness belongs to the language and library contracts.

Five-minute retrieval: [[Go Internals Revision]] · Sprint boundary: [[Deferred Backlog]] · Parent: [[Go Map of Content]]
