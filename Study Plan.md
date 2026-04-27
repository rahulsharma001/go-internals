# 8-Week Go Interview Battle Plan

> **Start date:** April 26, 2026
> **End date:** June 20, 2026
> **Daily time:** 1.5-2 hrs study + 15-20 min revision + 15-20 min interview prep
> **Morning warmup:** [[Daily Revision]] (15-20 min, every morning, non-negotiable)
> **Goal:** Crack a Senior Golang Developer role within notice period

---

## What Week Am I On?

| Week | Dates | Focus |
|------|-------|-------|
| 1 | Apr 26 - May 2 | Foundations: Pointers, Maps, Errors |
| 2 | May 3 - May 9 | Foundations: Defer/Panic, Interfaces |
| 3 | May 10 - May 16 | Concurrency Core: Goroutines, Scheduler, Channels |
| 4 | May 17 - May 23 | Concurrency Core: Select, Mutex, Context |
| 5 | May 24 - May 30 | Patterns + GC: Worker Pool, Fan-Out, Shutdown |
| 6 | May 31 - Jun 6 | Patterns + GC: Leaks, GC Deep Dive, GC Tuning |
| 7 | Jun 7 - Jun 13 | Production Go: net/http, gRPC, database/sql, Observability |
| 8 | Jun 14 - Jun 20 | Full Revision + Mock Interviews + Close Offers |

---

## How to Use This File

1. **Morning (15-20 min):** Open [[Daily Revision]], scroll top to bottom, do blurt checks
2. **Study session (1-1.5 hrs):** Come here, find your current week. Complete all **Prerequisites** first (short P-notes, ~15-25 min each). Then start the main **Topics**.
3. **Before each main topic:** Check which P-notes it needs (shown after `--`). If unchecked, do those first.
4. **Evening (15-20 min):** Do the week's "Interview Action" and try the self-test questions out loud
5. **After each prerequisite or topic:** Tick the checkbox here, then move to the next one

---

## Already Completed (Before This Plan)

These 6 topics are done. They're in your Daily Revision rotation already.

- [ ] [[T01 Go Type System & Value Semantics]] (~2 hrs)
- [ ] [[T02 Go Memory Allocation & Value Semantics]] (~2 hrs)
- [x] [[T03 Strings, Runes & UTF-8 Internals]] (~1.5 hrs)
- [x] [[T04 Arrays & Slice Internals]] (~2 hrs)
- [x] [[frameworks/T05 GIN Framework]] (~1.5 hrs)
- [ ] [[databases/T06 MongoDB]] (~2 hrs)

---

## Week 1-2: Complete Foundations + Start Applying

**Goal:** Fill the remaining foundation gaps so every later topic has solid ground to stand on.

**Prerequisites (complete these first):**

- [x] [[prerequisites/P01 Structs & Struct Memory Layout]] (~25 min)
- [ ] [[prerequisites/P02 Methods & Receivers]] (~25 min)
- [ ] [[prerequisites/P03 Mutex & Concurrency Safety Basics]] (~20 min)
- [x] [[prerequisites/P04 Hash Functions & Hashing Basics]] (~15 min)
- [ ] [[prerequisites/P05 Interfaces Basics]] (~20 min)
- [ ] [[prerequisites/P06 Function Call Stack]] (~15 min)

**Topics:**

- [x] [[T07 Pointers & Pointer Semantics]] (~1.5 hrs) -- needs P01, P02, P03
- [x] [[T08 Map Internals]] (~2 hrs) -- needs P01, P04
- [ ] [[T09 Error Handling Patterns]] (~1.5 hrs) -- needs P05
- [ ] [[T10 Defer, Panic & Recover Internals]] (~1.5 hrs) -- needs P06
- [ ] [[T11 Interface Internals (iface & eface)]] (~2 hrs) -- needs P01, P02, P05
- [ ] [[T12 Interface Design Principles]] (~1.5 hrs) -- needs T11

**Estimated total:** ~12 hrs across 14 days (~50 min/day study, includes prerequisites)

> **Status (Apr 28):** Week 1-2 is fully complete (all P-notes and T-notes checked). Move directly to Week 3-4.

**Interview Action:**
- Update resume with Go-specific bullet points
- Apply to 10-15 companies (LinkedIn, Naukri, direct)
- Schedule first interviews for week 3 (use early ones as practice)

**By end of week 2, you should be able to answer:**
1. "When should you use a pointer receiver vs a value receiver?" (T07)
2. "Why is Go's map not safe for concurrent use? What's the internal structure?" (T08)
3. "How do you wrap errors and check for specific error types?" (T09)
4. "What's the order of deferred calls? When are arguments evaluated?" (T10)
5. "What's the difference between iface and eface internally?" (T11)
6. "What does 'accept interfaces, return structs' mean and why?" (T12)

---

## Week 3-4: Concurrency Core (the 30-40% zone)

**Goal:** This is the most tested area in Go interviews. Master the primitives.

**Prerequisites (complete these first):**

- [x] [[prerequisites/P07 Functions, Closures & Variable Capture]] (~20 min)
- [x] [[prerequisites/P08 OS Threads vs Green Threads]] (~15 min)

> P03 (Mutex basics) and P06 (Call Stack) were completed in Week 1-2.

**Topics:**

- [ ] [[T13 Goroutine Internals]] (~2 hrs) -- needs P06, P07
- [ ] [[T14 GMP Scheduler]] (~2 hrs) -- needs P08
- [ ] [[T15 Channel Internals]] (~2 hrs)
- [ ] [[T16 Buffered vs Unbuffered Channels]] (~1 hrs)
- [ ] [[T17 Select Statement Internals]] (~1.5 hrs)
- [ ] [[T18 Mutex & RWMutex Internals]] (~1.5 hrs) -- needs P03
- [ ] [[T19 Context Package Internals]] (~1.5 hrs)

**Estimated total:** ~12 hrs across 14 days (~50 min/day study, includes prerequisites)

> **Pacing note:** P07/P08 are already done. 7 T-notes in 14 days = 1 note every 2 days. Start with T13/T14 (foundation for all concurrency topics) before moving to channels/select.

**Interview Action:**
- Give 2-3 interviews (these are calibration rounds, not your best shots)
- After each interview, log what was asked in the Interview Log section below
- Adjust study order if interviews reveal unexpected gaps

**By end of week 4, you should be able to answer:**
1. "How does Go's scheduler work? Explain G, M, and P." (T14)
2. "What happens internally when you send a value on a channel?" (T15)
3. "When would you use a buffered channel vs unbuffered?" (T16)
4. "How does select choose between multiple ready channels?" (T17)
5. "Explain starvation mode in sync.Mutex." (T18)
6. "How does context cancellation propagate through a goroutine tree?" (T19)

---

## Week 5-6: Concurrency Patterns + GC

**Goal:** Move from knowing primitives to applying them. Plus GC knowledge for the "production experience" signal.

**Prerequisites (complete these first):**

- [x] [[prerequisites/P09 GC Basics & Why It Matters]] (~20 min)

> All other prerequisites were completed in earlier weeks.

**Topics:**

- [ ] [[T20 Worker Pool Pattern]] (~1.5 hrs)
- [ ] [[T21 Fan-Out Fan-In Pattern]] (~1.5 hrs)
- [ ] [[T22 Graceful Shutdown]] (~1.5 hrs)
- [ ] [[T23 Goroutine Leak Prevention]] (~1.5 hrs)
- [ ] [[T24 Garbage Collector Deep Dive]] (~2 hrs) -- needs P09
- [ ] [[T25 GC Tuning (GOGC & GOMEMLIMIT)]] (~1.5 hrs)

**Estimated total:** ~9.8 hrs across 14 days (~42 min/day study, includes prerequisites)

**Interview Action:**
- Give 3-4 interviews (you should be noticeably better now)
- Focus on system design rounds -- use concurrency patterns in your designs
- Log all questions asked

**By end of week 6, you should be able to answer:**
1. "Implement a worker pool with bounded concurrency." (T20)
2. "How do you fan-out work to N goroutines and collect results?" (T21)
3. "Walk me through graceful shutdown of an HTTP server." (T22)
4. "How do you detect and prevent goroutine leaks?" (T23)
5. "Explain Go's tri-color mark-and-sweep GC." (T24)
6. "When would you tune GOGC vs GOMEMLIMIT?" (T25)

---

## Week 7: Production Go + System Design

**Goal:** Bridge Go knowledge into system design interviews. These topics show you've built real things.

**Topics:**

- [ ] [[T26 net/http Internals]] (~2 hrs)
- [ ] [[T27 gRPC with Go]] (~1.5 hrs)
- [ ] [[T28 database/sql & Connection Pooling]] (~1.5 hrs)
- [ ] [[T29 Observability (Logging, Metrics, Tracing)]] (~1.5 hrs)

**Estimated total:** ~6.5 hrs across 7 days (~1 hr/day study)

**Interview Action:**
- Schedule your top-choice company interviews this week or next
- Focus on system design rounds -- use net/http, gRPC, DB pooling knowledge
- 2-3 interviews

**By end of week 7, you should be able to answer:**
1. "How does net/http handle concurrent connections? Goroutine-per-request model?" (T26)
2. "Compare gRPC vs REST for microservice communication." (T27)
3. "How does database/sql connection pooling work? SetMaxOpenConns vs SetMaxIdleConns?" (T28)
4. "How would you set up observability in a Go microservice?" (T29)

---

## Week 8: Full Revision + Close Offers

**Goal:** No new topics. Consolidate everything and close deals.

**Daily routine this week:**

1. **Morning (30 min):** Full Daily Revision pass -- all topics
2. **Midday (45 min):** Pick 3 weak topics from the revision, open their revision cards, do the full recall grid
3. **Afternoon (30 min):** Mock interview -- pick 5 random questions from the Interview Gold Questions sections across all notes, answer them out loud with a timer (30 sec each)

**Interview Action:**
- Final round interviews with top-choice companies
- Negotiate offers
- Use verbal answers (Section 12) for last-minute prep before each call

**Mock Interview Protocol:**
1. Open any topic's Interview Questions file
2. Read just the question (cover the answer)
3. Set a 60-second timer
4. Answer out loud -- structure: "The key insight is... Internally... The gotcha is..."
5. Uncover the answer, compare
6. Score yourself: 3 = nailed it, 2 = close, 1 = missed key points
7. Topics scoring 1 get extra revision tomorrow

---

## What I Skipped and Why

These topics are marked SKIP in the [[Roadmap]]. They're either rarely asked, too academic, or covered enough by the topics you ARE studying.

| # | Topic | Why Skipped |
|---|-------|-------------|
| 1.7 | Struct Layout & Memory Alignment | Rarely asked; know "field ordering affects padding" is enough |
| 2.1 | Functions, Closures & Anonymous Functions | Covered as P07 prerequisite note (not a standalone T-note) |
| 2.4 | Init Functions & Package Initialization | Rarely asked; know "init runs before main, avoid side effects" is enough |
| 3.2 | Type Assertions & Type Switches | Covered within Interface Internals (T11) |
| 3.4 | Empty Interface (any) & Boxing | Covered within Interface Internals (T11) |
| 4.3 | Preemption (Cooperative & Asynchronous) | Know "Go 1.14 added async preemption via signals" -- one sentence is enough |
| 4.8 | sync Package Deep Dive | WaitGroup/Once covered in concurrency topics; sync.Map/Pool rarely asked in depth |
| 4.9 | Atomic Operations | Know "use sync/atomic for lock-free counters" -- details rarely asked |
| 5.1 | Memory Allocator Internals | mcache/mcentral/mheap covered in T02; deeper detail rarely asked |
| 5.4 | Escape Analysis Deep Dive | Basics covered in T02; "use -gcflags='-m'" is the practical answer |
| 5.5 | sync.Pool Internals | Know "per-P pool, cleared on GC" -- implementation details rarely asked |
| 5.6 | Stack Management | Know "contiguous stacks, auto-grow from 2KB" -- covered in goroutine internals |
| 6.1 | Go Memory Model (Happens-Before) | Academic; practical rules covered in mutex/channel topics |
| 6.2 | Data Races & Race Detector | Know "-race flag" and "two goroutines, one writing, no sync" -- covered in concurrency topics |
| 6.3 | Memory Ordering & sync/atomic | Academic; rarely asked beyond "use sync/atomic" |
| 7.2 | Pipeline Pattern | Covered as a variant within Fan-Out/Fan-In (T21) |
| 7.4 | Rate Limiter (Token Bucket & Leaky Bucket) | System design topic; know "golang.org/x/time/rate" is enough |
| 7.5 | Pub-Sub & Event-Driven Patterns | Architecture pattern; not Go-specific enough for Go interviews |
| 8.2 | Network Poller (netpoll) | Deep runtime internals; know "epoll-based, goroutine parks on I/O" is enough |
| 8.3 | io.Reader / io.Writer Patterns | Know the interfaces; composability rarely tested in depth |
| 9.1 | Reflection Internals | Rarely asked; know "reflect.Type/Value, slow, avoid in hot paths" |
| 9.2 | unsafe Package | Know "unsafe.Pointer for type punning, bypasses safety" -- details rarely asked |
| 9.3 | Generics (Type Parameters) | Still new; interviews test basic syntax at most |
| 9.4 | Code Generation & go generate | Build tooling, not interview material |
| 10.1 | Testing Patterns in Go | Practical skill; you already know table-driven tests |
| 10.2 | Benchmarking & Performance Profiling | Know "testing.B, pprof" -- practical skill, not theory-heavy |
| 10.3 | Fuzzing | Rarely asked; know "native fuzzing in Go 1.18" |
| 10.4 | Race Detector & Debugging Tools | Covered in concurrency topics |
| 11.1 | Go Compiler Pipeline | Academic; rarely asked beyond "SSA-based" |
| 11.2 | Inlining & Compiler Optimizations | Know "inlining budget, //go:noinline" -- one-line answers |
| 11.3 | Linker & Binary Layout | Academic; not interview material |
| 11.4 | Build Tags, Cross-Compilation & CGO | Practical skill; rarely asked in interviews |
| 12.2 | Configuration & Feature Flags | Not Go-specific |
| 12.3 | Dependency Injection in Go | Know "constructor injection" -- patterns vary by team |
| 12.4 | Microservices Patterns in Go | Architecture topic; not Go-specific enough |
| 12.5 | High-Performance Go | Advanced optimization; covered partially in GC tuning |

---

## Interview Log

Track what companies actually ask. Update this after every interview.

| Date | Company | Round | Topics Asked | How I Did (1-3) | Notes |
|------|---------|-------|--------------|-----------------|-------|
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |

**Pattern tracker:** After 5+ interviews, tally which topics appear most. If something appears 3+ times that you haven't studied, bump it up.

---

> See [[Roadmap]] for the full topic list with SKIP markers.
> See [[Daily Revision]] for your morning warmup.
