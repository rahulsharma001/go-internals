# Go Internals & Interview Topics — Sequential Learning Roadmap

> This roadmap is ordered by **dependency** — each topic builds on the ones before it. Topics are grouped into phases. Within each phase, the order matters. Cross-phase, earlier phases are prerequisites for later ones.
>
> **Status legend**: ✅ Done | 🔄 In Progress | ⬜ Not Started

---

## Phase 1: Foundations (Language Core)

These are the building blocks. Every other topic assumes you know these cold.

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 1.1 | [[Go Type System & Value Semantics]] | ✅ | Pass-by-value, zero values, named types, type identity, assignability rules |
| 1.2 | [[Go Memory Allocation & Value Semantics]] | ✅ | Stack vs heap, escape analysis, GC basics — the foundation for everything |
| 1.3 | [[Pointers & Pointer Semantics]] | ⬜ | Pointer receivers vs value receivers, when to use which, nil pointer behavior |
| 1.4 | [[Strings, Runes & UTF-8 Internals]] | ✅ | String header (ptr + len), byte vs rune, range behavior, immutability, `len()` trap |
| 1.5 | [[Arrays & Slice Internals]] | ✅ | Slice header (ptr + len + cap), append mechanics, copy-on-grow, slice tricks, memory leaks |
| 1.6 | [[Map Internals]] | ⬜ | hmap struct, buckets, overflow chains, load factor 6.5, hash seed, evacuation, iteration randomness |
| 1.7 | [[Struct Layout & Memory Alignment]] | ⬜ | Padding rules, field ordering for minimal size, `unsafe.Sizeof`, cache-line awareness |

---

## Phase 2: Functions, Errors & Control Flow

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 2.1 | [[Functions, Closures & Anonymous Functions]] | ⬜ | Closure capture mechanics, escape analysis of captured variables, function values |
| 2.2 | [[Defer, Panic & Recover Internals]] | ⬜ | LIFO order, argument evaluation time, panic unwinding, recover() rules, goroutine isolation |
| 2.3 | [[Error Handling Patterns]] | ⬜ | Error wrapping (%w), errors.Is/As, sentinel errors, custom error types, error as values philosophy |
| 2.4 | [[Init Functions & Package Initialization]] | ⬜ | init() ordering, dependency graph, import side effects, blank identifier imports |

---

## Phase 3: Interfaces & Polymorphism

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 3.1 | [[Interface Internals (iface & eface)]] | ⬜ | iface struct (tab + data), eface struct (_type + data), itab caching, dynamic dispatch |
| 3.2 | [[Type Assertions & Type Switches]] | ⬜ | Runtime cost, itab Hash lookup, comma-ok pattern, performance of switch vs chain |
| 3.3 | [[Interface Design Principles]] | ⬜ | Small interfaces, implicit satisfaction, accept interfaces / return structs, interface pollution |
| 3.4 | [[Empty Interface (any) & Boxing]] | ⬜ | Heap allocation when boxing, when compiler avoids it, performance implications |

---

## Phase 4: Concurrency Primitives

This is the **most heavily tested** area in Go interviews (30-40% of questions).

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 4.1 | [[Goroutine Internals]] | ⬜ | Goroutine struct (g), stack growth/shrinking, states (runnable/running/waiting/dead), cost (~2KB) |
| 4.2 | [[GMP Scheduler]] | ⬜ | G-M-P model, local/global run queues, work stealing, handoff, GOMAXPROCS, syscall handling |
| 4.3 | [[Preemption (Cooperative & Asynchronous)]] | ⬜ | Go 1.14+ signal-based preemption, morestack checks, tight-loop starvation, safe points |
| 4.4 | [[Channel Internals]] | ⬜ | hchan struct, circular buffer, sudog queues, send/recv paths, direct copy optimization |
| 4.5 | [[Buffered vs Unbuffered Channels]] | ⬜ | Semantics difference, performance tradeoffs, when to use which, capacity as semaphore |
| 4.6 | [[Select Statement Internals]] | ⬜ | Random case selection, blocking vs default, compiler optimizations, poll order |
| 4.7 | [[Mutex & RWMutex Internals]] | ⬜ | State field, normal vs starvation mode, spin-lock fast path, reader/writer fairness |
| 4.8 | [[sync Package Deep Dive]] | ⬜ | WaitGroup, Once, Map, Pool, Cond — internals and correct usage patterns |
| 4.9 | [[Atomic Operations]] | ⬜ | sync/atomic, memory ordering, Compare-And-Swap, Load/Store, atomic.Value |
| 4.10 | [[Context Package Internals]] | ⬜ | Context tree, cancellation propagation, WithCancel/Timeout/Deadline/Value, goroutine-safe usage |

---

## Phase 5: Memory Management & GC

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 5.1 | [[Memory Allocator Internals]] | ⬜ | mcache → mcentral → mheap hierarchy, size classes, span management, tiny allocator |
| 5.2 | [[Garbage Collector Deep Dive]] | ⬜ | Tri-color mark-and-sweep, write barrier, mark assist, sweep/scavenge phases, GC pacing |
| 5.3 | [[GC Tuning (GOGC & GOMEMLIMIT)]] | ⬜ | GOGC ratio, GOMEMLIMIT soft cap, GC pacing algorithm, ballast trick (deprecated), tuning strategy |
| 5.4 | [[Escape Analysis Deep Dive]] | ⬜ | Compiler decision tree, -gcflags="-m", common escape patterns, optimization techniques |
| 5.5 | [[sync.Pool Internals]] | ⬜ | Per-P pool, victim cache, GC interaction, correct usage patterns, benchmarking impact |
| 5.6 | [[Stack Management]] | ⬜ | Contiguous stacks (Go 1.4+), growth/shrink, pointer adjustment, morestack, stack scanning |

---

## Phase 6: Go Memory Model (Happens-Before)

This is the **official** Go Memory Model — about concurrency safety, not allocation.

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 6.1 | [[Go Memory Model (Happens-Before)]] | ⬜ | Happens-before relation, visibility guarantees, channel communication ordering |
| 6.2 | [[Data Races & Race Detector]] | ⬜ | What constitutes a race, -race flag, ThreadSanitizer, race-free patterns |
| 6.3 | [[Memory Ordering & sync/atomic]] | ⬜ | Sequential consistency for atomics, relaxed ordering pitfalls, fences |

---

## Phase 7: Concurrency Patterns (Applied)

Build on Phase 4 primitives — these are the patterns interviewers expect you to implement.

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 7.1 | [[Worker Pool Pattern]] | ⬜ | Bounded concurrency, task distribution, graceful shutdown |
| 7.2 | [[Pipeline Pattern]] | ⬜ | Stage-based processing, channel chaining, cancellation propagation |
| 7.3 | [[Fan-Out / Fan-In Pattern]] | ⬜ | Parallel work distribution, result aggregation, error handling |
| 7.4 | [[Rate Limiter (Token Bucket & Leaky Bucket)]] | ⬜ | golang.org/x/time/rate, custom implementations, distributed rate limiting |
| 7.5 | [[Pub-Sub & Event-Driven Patterns]] | ⬜ | Channel-based pub-sub, broker pattern, event sourcing basics |
| 7.6 | [[Graceful Shutdown]] | ⬜ | Signal handling, context cancellation, drain connections, timeout strategies |
| 7.7 | [[Goroutine Leak Prevention]] | ⬜ | Common leak patterns, detection with pprof, done channels, context timeouts |

---

## Phase 8: Networking & I/O

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 8.1 | [[net/http Internals]] | ⬜ | Server lifecycle, handler chain, goroutine-per-request, connection pooling, timeouts |
| 8.2 | [[Network Poller (netpoll)]] | ⬜ | epoll/kqueue integration, goroutine parking on I/O, non-blocking sockets |
| 8.3 | [[io.Reader / io.Writer Patterns]] | ⬜ | Composability, streaming, buffered I/O, io.Pipe, zero-copy techniques |
| 8.4 | [[gRPC with Go]] | ⬜ | Protobuf, streaming, interceptors, connection management, deadlines |
| 8.5 | [[database/sql & Connection Pooling]] | ⬜ | Connection pool internals, prepared statements, transaction handling, context usage |

---

## Phase 9: Reflection, Unsafe & Generics

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 9.1 | [[Reflection Internals]] | ⬜ | reflect.Type/Value, Kind, struct tag parsing, performance cost, when to use |
| 9.2 | [[unsafe Package]] | ⬜ | unsafe.Pointer, Sizeof/Alignof/Offsetof, pointer conversion rules, real-world uses |
| 9.3 | [[Generics (Type Parameters)]] | ⬜ | Type constraints, type inference, stenciling vs dictionary approach, performance implications |
| 9.4 | [[Code Generation & go generate]] | ⬜ | When codegen beats reflection, stringer, mockgen, wire |

---

## Phase 10: Testing & Profiling

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 10.1 | [[Testing Patterns in Go]] | ⬜ | Table-driven tests, subtests, test helpers, testify, golden files, integration tests |
| 10.2 | [[Benchmarking & Performance Profiling]] | ⬜ | testing.B, pprof (CPU/memory/block/goroutine), trace tool, flame graphs |
| 10.3 | [[Fuzzing]] | ⬜ | Native fuzzing (Go 1.18+), corpus management, finding edge cases |
| 10.4 | [[Race Detector & Debugging Tools]] | ⬜ | -race flag, GODEBUG settings, delve debugger, runtime/debug package |

---

## Phase 11: Compiler & Linker

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 11.1 | [[Go Compiler Pipeline]] | ⬜ | Lexing → parsing → type checking → SSA → machine code, compiler directives (//go:) |
| 11.2 | [[Inlining & Compiler Optimizations]] | ⬜ | Inlining budget, //go:noinline, bounds check elimination, dead code elimination |
| 11.3 | [[Linker & Binary Layout]] | ⬜ | Static linking, symbol resolution, build modes (shared, plugin, c-archive) |
| 11.4 | [[Build Tags, Cross-Compilation & CGO]] | ⬜ | Build constraints, GOOS/GOARCH, CGO_ENABLED=0, C interop costs |

---

## Phase 12: Production Go (System Design Ready)

These topics bridge Go knowledge with real-world system design interviews.

| # | Topic | Status | Why It Matters |
|---|-------|--------|----------------|
| 12.1 | [[Error Handling in Distributed Systems]] | ⬜ | Circuit breakers, retries with backoff, bulkhead pattern, error budgets |
| 12.2 | [[Observability (Logging, Metrics, Tracing)]] | ⬜ | Structured logging (slog), Prometheus metrics, OpenTelemetry tracing, correlation IDs |
| 12.3 | [[Configuration & Feature Flags]] | ⬜ | Env vars, config files, remote config, feature flag patterns |
| 12.4 | [[Dependency Injection in Go]] | ⬜ | Constructor injection, wire, fx, interface-based testing |
| 12.5 | [[Microservices Patterns in Go]] | ⬜ | Service discovery, API gateways, saga pattern, event-driven architecture |
| 12.6 | [[High-Performance Go]] | ⬜ | Memory pooling, zero-alloc patterns, string interning, buffer reuse, struct-of-arrays |

---

## Quick Reference: Interview Weight by Topic

Based on research across Reddit (r/golang, r/ExperiencedDevs), YouTube interviews, and FAANG-level interview guides (2025-2026):

| Topic Area | Interview Weight | Phase |
|---|---|---|
| **Concurrency (goroutines, channels, patterns)** | ★★★★★ (30-40%) | 4, 7 |
| **Memory & GC (allocation, escape analysis, tuning)** | ★★★★☆ (15-20%) | 1, 5 |
| **Interface design & internals** | ★★★★☆ (10-15%) | 3 |
| **Error handling & production patterns** | ★★★☆☆ (10%) | 2, 12 |
| **System design with Go specifics** | ★★★★☆ (15-20%) | 8, 12 |
| **Data structures (slice, map internals)** | ★★★☆☆ (5-10%) | 1 |
| **Testing & profiling** | ★★★☆☆ (5-10%) | 10 |
| **Compiler, reflection, generics** | ★★☆☆☆ (5%) | 9, 11 |

---

## Sources

Synthesized from: r/golang, r/ExperiencedDevs, r/cscareerquestions, CodeForGeek, SecondTalent, GankInterview, Interviewing.io, Reintech, Go official docs, YouTube (Alex Hyett, Fireship, Exponent), Medium (Go internals series), and Go runtime source (go.dev/src/runtime).

---
