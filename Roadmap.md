# Go Internals & Interview Topics — Sequential Learning Roadmap

> This roadmap is ordered by **dependency** — each topic builds on the ones before it. Topics are grouped into phases. Within each phase, the order matters. Cross-phase, earlier phases are prerequisites for later ones.
>
> **Status legend**: ✅ Done | 🔄 In Progress | ⬜ Not Started | ⏭ SKIP (see reason)
>
> **Battle plan:** ~30 topics are active; SKIP topics stay skipped unless your interview log proves otherwise. See [[Study Plan]] for the **80/20 Senior Go track** (what to finish first, daily revision bands, application gates).

---

## Phase 1: Foundations (Language Core)

These are the building blocks. Every other topic assumes you know these cold.

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 1.1 | [[T01 Go Type System & Value Semantics]] | ✅ | Pass-by-value, zero values, named types, type identity, assignability rules |
| 1.2 | [[T02 Go Memory Allocation & Value Semantics]] | ✅ | Stack vs heap, escape analysis, GC basics — the foundation for everything |
| 1.3 | [[T07 Pointers & Pointer Semantics]] | ✅ | Pointer receivers vs value receivers, when to use which, nil pointer behavior |
| 1.4 | [[T03 Strings, Runes & UTF-8 Internals]] | ✅ | String header (ptr + len), byte vs rune, range behavior, immutability, `len()` trap |
| 1.5 | [[T04 Arrays & Slice Internals]] | ✅ | Slice header (ptr + len + cap), append mechanics, copy-on-grow, slice tricks, memory leaks |
| 1.6 | [[T08 Map Internals]] | ✅ | hmap struct, buckets, overflow chains, load factor 6.5, hash seed, evacuation, iteration randomness |
| 1.7 | [[Struct Layout & Memory Alignment]] | ⏭ SKIP | Rarely asked; know "field ordering affects padding" is enough |

---

## Phase 2: Functions, Errors & Control Flow

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 2.1 | [[prerequisites/P07 Functions, Closures & Variable Capture]] | ✅ | Covered as a prerequisite P-note (not a standalone T-note). First-class functions, closure capture by reference, loop variable trap, middleware factories |
| 2.2 | [[T10 Defer, Panic & Recover Internals]] | ✅ | LIFO order, argument evaluation time, panic unwinding, recover() rules, goroutine isolation |
| 2.3 | [[T09 Error Handling Patterns]] | ✅ | Error wrapping (%w), errors.Is/As, sentinel errors, custom error types, error as values philosophy |
| 2.4 | [[Init Functions & Package Initialization]] | ⏭ SKIP | Rarely asked; know "init runs before main, avoid side effects" is enough |

---

## Phase 3: Interfaces & Polymorphism

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 3.1 | [[T11 Interface Internals (iface & eface)]] | ✅ | iface struct (tab + data), eface struct (_type + data), itab caching, dynamic dispatch |
| 3.2 | [[Type Assertions & Type Switches]] | ⏭ SKIP | Covered within Interface Internals (T11) |
| 3.3 | [[T12 Interface Design Principles]] | ✅ | Small interfaces, implicit satisfaction, accept interfaces / return structs, interface pollution |
| 3.4 | [[Empty Interface (any) & Boxing]] | ⏭ SKIP | Covered within Interface Internals (T11) |

---

## Phase 4: Concurrency Primitives

This is the **most heavily tested** area in Go interviews (30-40% of questions).

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 4.1 | [[T13 Goroutine Internals]] | ⬜ | Goroutine struct (g), stack growth/shrinking, states (runnable/running/waiting/dead), cost (~2KB) |
| 4.2 | [[T14 GMP Scheduler]] | ⬜ | G-M-P model, local/global run queues, work stealing, handoff, GOMAXPROCS, syscall handling |
| 4.3 | [[Preemption (Cooperative & Asynchronous)]] | ⏭ SKIP | Know "Go 1.14 added async preemption via signals" — one sentence is enough |
| 4.4 | [[T15 Channel Internals]] | ✅ | hchan struct, circular buffer, sudog queues, send/recv paths, direct copy optimization |
| 4.5 | [[T16 Buffered vs Unbuffered Channels]] | ⬜ | Semantics difference, performance tradeoffs, when to use which, capacity as semaphore |
| 4.6 | [[T17 Select Statement Internals]] | ⬜ | Random case selection, blocking vs default, compiler optimizations, poll order |
| 4.7 | [[T18 Mutex & RWMutex Internals]] | ⬜ | State field, normal vs starvation mode, spin-lock fast path, reader/writer fairness |
| 4.8 | [[sync Package Deep Dive]] | ⏭ SKIP | WaitGroup/Once covered in concurrency topics; sync.Map/Pool rarely asked in depth |
| 4.9 | [[Atomic Operations]] | ⏭ SKIP | Know "use sync/atomic for lock-free counters" — details rarely asked |
| 4.10 | [[T19 Context Package Internals]] | ⬜ | Context tree, cancellation propagation, WithCancel/Timeout/Deadline/Value, goroutine-safe usage |

---

## Phase 5: Memory Management & GC

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 5.1 | [[Memory Allocator Internals]] | ⏭ SKIP | mcache/mcentral/mheap covered in T02; deeper detail rarely asked |
| 5.2 | [[T24 Garbage Collector Deep Dive]] | ⬜ | Tri-color mark-and-sweep, write barrier, mark assist, sweep/scavenge phases, GC pacing |
| 5.3 | [[T25 GC Tuning (GOGC & GOMEMLIMIT)]] | ⬜ | GOGC ratio, GOMEMLIMIT soft cap, GC pacing algorithm, ballast trick (deprecated), tuning strategy |
| 5.4 | [[Escape Analysis Deep Dive]] | ⏭ SKIP | Basics covered in T02; "use -gcflags='-m'" is the practical answer |
| 5.5 | [[sync.Pool Internals]] | ⏭ SKIP | Know "per-P pool, cleared on GC" — implementation details rarely asked |
| 5.6 | [[Stack Management]] | ⏭ SKIP | Know "contiguous stacks, auto-grow from 2KB" — covered in goroutine internals |

---

## Phase 6: Go Memory Model (Happens-Before)

This is the **official** Go Memory Model — about concurrency safety, not allocation.

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 6.1 | [[Go Memory Model (Happens-Before)]] | ⏭ SKIP | Academic; practical rules covered in mutex/channel topics |
| 6.2 | [[Data Races & Race Detector]] | ⏭ SKIP | Know "-race flag" and "two goroutines, one writing, no sync" — covered in concurrency topics |
| 6.3 | [[Memory Ordering & sync/atomic]] | ⏭ SKIP | Academic; rarely asked beyond "use sync/atomic" |

---

## Phase 7: Concurrency Patterns (Applied)

Build on Phase 4 primitives — these are the patterns interviewers expect you to implement.

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 7.1 | [[T20 Worker Pool Pattern]] | ⬜ | Bounded concurrency, task distribution, graceful shutdown |
| 7.2 | [[Pipeline Pattern]] | ⏭ SKIP | Covered as a variant within Fan-Out/Fan-In (T21) |
| 7.3 | [[T21 Fan-Out / Fan-In Pattern]] | ⬜ | Parallel work distribution, result aggregation, error handling |
| 7.4 | [[Rate Limiter (Token Bucket & Leaky Bucket)]] | ⏭ SKIP | System design topic; know "golang.org/x/time/rate" is enough |
| 7.5 | [[Pub-Sub & Event-Driven Patterns]] | ⏭ SKIP | Architecture pattern; not Go-specific enough for Go interviews |
| 7.6 | [[T22 Graceful Shutdown]] | ⬜ | Signal handling, context cancellation, drain connections, timeout strategies |
| 7.7 | [[T23 Goroutine Leak Prevention]] | ⬜ | Common leak patterns, detection with pprof, done channels, context timeouts |

---

## Phase 8: Networking & I/O

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 8.1 | [[T26 net/http Internals]] | ⬜ | Server lifecycle, handler chain, goroutine-per-request, connection pooling, timeouts |
| 8.2 | [[Network Poller (netpoll)]] | ⏭ SKIP | Deep runtime internals; know "epoll-based, goroutine parks on I/O" is enough |
| 8.3 | [[io.Reader / io.Writer Patterns]] | ⏭ SKIP | Know the interfaces; composability rarely tested in depth |
| 8.4 | [[T27 gRPC with Go]] | ⬜ | Protobuf, streaming, interceptors, connection management, deadlines |
| 8.5 | [[T28 database/sql & Connection Pooling]] | ⬜ | Connection pool internals, prepared statements, transaction handling, context usage |

---

## Phase 9: Reflection, Unsafe & Generics

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 9.1 | [[Reflection Internals]] | ⏭ SKIP | Rarely asked; know "reflect.Type/Value, slow, avoid in hot paths" |
| 9.2 | [[unsafe Package]] | ⏭ SKIP | Know "unsafe.Pointer for type punning, bypasses safety" — details rarely asked |
| 9.3 | [[Generics (Type Parameters)]] | ⏭ SKIP | Still new; interviews test basic syntax at most |
| 9.4 | [[Code Generation & go generate]] | ⏭ SKIP | Build tooling, not interview material |

---

## Phase 10: Testing & Profiling

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 10.1 | [[Testing Patterns in Go]] | ⏭ SKIP | Practical skill; you already know table-driven tests |
| 10.2 | [[Benchmarking & Performance Profiling]] | ⏭ SKIP | Know "testing.B, pprof" — practical skill, not theory-heavy |
| 10.3 | [[Fuzzing]] | ⏭ SKIP | Rarely asked; know "native fuzzing in Go 1.18" |
| 10.4 | [[Race Detector & Debugging Tools]] | ⏭ SKIP | Covered in concurrency topics |

---

## Phase 11: Compiler & Linker

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 11.1 | [[Go Compiler Pipeline]] | ⏭ SKIP | Academic; rarely asked beyond "SSA-based" |
| 11.2 | [[Inlining & Compiler Optimizations]] | ⏭ SKIP | Know "inlining budget, //go:noinline" — one-line answers |
| 11.3 | [[Linker & Binary Layout]] | ⏭ SKIP | Academic; not interview material |
| 11.4 | [[Build Tags, Cross-Compilation & CGO]] | ⏭ SKIP | Practical skill; rarely asked in interviews |

---

## Phase 12: Production Go (System Design Ready)

These topics bridge Go knowledge with real-world system design interviews.

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 12.1 | [[Error Handling in Distributed Systems]] | ⬜ | Circuit breakers, retries with backoff, bulkhead pattern, error budgets |
| 12.2 | [[T29 Observability (Logging, Metrics, Tracing)]] | ⬜ | Structured logging (slog), Prometheus metrics, OpenTelemetry tracing, correlation IDs |
| 12.3 | [[Configuration & Feature Flags]] | ⏭ SKIP | Not Go-specific |
| 12.4 | [[Dependency Injection in Go]] | ⏭ SKIP | Know "constructor injection" — patterns vary by team |
| 12.5 | [[Microservices Patterns in Go]] | ⏭ SKIP | Architecture topic; not Go-specific enough |
| 12.6 | [[High-Performance Go]] | ⏭ SKIP | Advanced optimization; covered partially in GC tuning |

---

## Quick Reference: Interview Weight by Topic

Based on research across Reddit (r/golang, r/ExperiencedDevs), YouTube interviews, and FAANG-level interview guides (2025-2026):

| Topic Area | Interview Weight | Phase |
|---|---|---|
| **Concurrency (goroutines, channels, patterns)** | 30-40% | 4, 7 |
| **Memory & GC (allocation, escape analysis, tuning)** | 15-20% | 1, 5 |
| **Interface design & internals** | 10-15% | 3 |
| **Error handling & production patterns** | 10% | 2, 12 |
| **System design with Go specifics** | 15-20% | 8, 12 |
| **Data structures (slice, map internals)** | 5-10% | 1 |
| **Testing & profiling** | 5-10% | 10 |
| **Compiler, reflection, generics** | 5% | 9, 11 |

---

## Sources

Synthesized from: r/golang, r/ExperiencedDevs, r/cscareerquestions, CodeForGeek, SecondTalent, GankInterview, Interviewing.io, Reintech, Go official docs, YouTube (Alex Hyett, Fireship, Exponent), Medium (Go internals series), and Go runtime source (go.dev/src/runtime).

---
