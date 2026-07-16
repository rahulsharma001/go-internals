---
type: learning-path
domain: go
status: active
---

# Go Learning Path

Advanced material is a follow-up. Move forward from evidence: explain → blank-editor implementation → edge cases → modification → production trade-off → re-test.

## Level 1 — Syntax and executable fundamentals

1. Collections: [[Go Slices]], [[Go Maps]], [[Collection Transformations in Go]].
2. Data modeling: [[Go Structs and Constructors]], [[Go Methods and Receivers]], [[Go Method Sets]].
3. Abstraction: [[Go Interfaces]], [[Interface Design in Go]], [[Struct Embedding and Composition]].
4. Control and errors: [[Complete Go Programs]], [[Go Error Handling]].
5. Supporting syntax: [[Go Types and Value Semantics]], [[Pointers in Go]], [[Strings Bytes Runes and UTF-8]], [[Functions and Closures]].
6. Drills: [[Coding Drill Index]].

Exit evidence: complete runnable programs, normal and edge cases, one timed change, and recorded re-test.

## Level 2 — Practical Go

- Error/resource boundaries: [[Defer Panic and Recover]].
- Cancellation: [[Context Cancellation]].
- HTTP framework source: [[Gin HTTP Services]]; learn standard `net/http`, JSON, packages, testing, and database access before claiming this level complete.
- Database driver/application material: [[MongoDB with Go]].

Coverage warning: packages, standard-library HTTP/JSON, `database/sql`, and testing do not yet have source-backed canonical notes.

## Level 3 — Concurrency

1. [[Goroutines and Lifecycle]]
2. [[Go Channels]]
3. [[Select in Go]]
4. [[Mutexes and Data Race Safety]]
5. [[Worker Pool]] and [[Worker Pool with Cancellation - Drill]]

Exit evidence: ownership, cancellation, error propagation, boundedness, race reasoning, and shutdown.

## Level 4 — Runtime internals

- [[Go Scheduler]]
- [[Go Memory Model]]
- [[Go Memory Allocation and Escape Analysis]]
- [[Go Garbage Collector]]
- [[Go Map Internals]]
- [[Go Interface Internals]]

These notes support debugging and deeper interviews; they do not replace Levels 1–3.

## Level 5 — Production and senior engineering

Connect Go decisions to API contracts, observability, resilience, storage, distributed systems, performance profiles, and explicit trade-offs through [[System Design Map of Content]]. Source-backed coverage is currently limited.

Navigation: [[Go Map of Content]] · [[Quick Revision Index]] · [[Google Engineering Roadmap]]

