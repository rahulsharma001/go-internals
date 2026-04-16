# Go Memory Allocation & Value Semantics — Interview Questions

> Comprehensive interview Q&A bank for [[Go Memory Allocation & Value Semantics]].
> Sorted by frequency at top tech companies (Google, Amazon, Meta, Uber, Stripe, Cloudflare).
> Tags: `[COMMON]` = asked frequently, `[ADVANCED]` = deep understanding expected, `[TRICKY]` = gotcha/trap question

---

## Q1: Explain Go's escape analysis. How does the compiler decide stack vs heap? [COMMON]

**Answer:**
Escape analysis is the compiler's static data-flow analysis that determines whether a variable can safely live on the stack or must be allocated on the heap. The compiler builds a directed graph of variable assignments and checks two invariants: (1) pointers to stack objects cannot be stored on the heap, and (2) pointers to stack objects cannot outlive those objects. If either is violated, the variable "escapes" to the heap. Common escape triggers: returning a pointer from a function, sending data to a goroutine or channel, storing in a global variable, or allocating with a size unknown at compile time. You can inspect decisions with `go build -gcflags="-m"`.

**Interview tip:** The interviewer is testing whether you understand that `new()` and `&T{}` do NOT guarantee heap allocation — it's the compiler that decides. Mention the `-gcflags="-m"` flag to show you've used it in practice.

---

## Q2: What's the difference between `new()` and `make()`? Does `new()` always heap-allocate? [COMMON]

**Answer:**
`new(T)` allocates zeroed memory for type T and returns a `*T` pointer. `make(T)` is only for slices, maps, and channels — it initializes the internal data structure and returns the type itself (not a pointer). `new()` does NOT always heap-allocate; escape analysis decides. If the returned pointer never leaves the function scope, the compiler can allocate it on the stack. `make` for slices with a constant size can also be stack-allocated. The key distinction is `new` returns a pointer to zeroed memory, while `make` returns an initialized, ready-to-use value of a reference type.

**Interview tip:** The interviewer wants to confirm you know Go's memory allocation is compiler-decided, not programmer-decided. Mentioning that `new` can stay on the stack separates you from mid-level candidates.

---

## Q3: How would you reduce GC pressure in a high-throughput Go service? [COMMON]

**Answer:**
First, profile with `GODEBUG=gctrace=1` and `go tool pprof -alloc_space` to find allocation hotspots. Then apply these techniques in order of impact: (1) Use `sync.Pool` for frequently allocated buffers in hot paths like HTTP handlers and serialization. (2) Prefer value semantics for small structs (< ~128 bytes) to keep them on the stack. (3) Pre-allocate slices with `make([]T, 0, knownCap)` to avoid repeated append reallocation. (4) Avoid interface boxing in tight loops — each boxing of a value larger than pointer-size triggers a heap allocation. (5) Use `[]byte` instead of `string` in parsing-heavy code to avoid immutability copies. (6) Tune `GOMEMLIMIT` (Go 1.19+) to set a memory budget and let the runtime adjust GC pacing, potentially with a high GOGC value. The chain: fewer heap allocs → fewer live objects → shorter mark phase → less mark assist → better p99 latency.

**Interview tip:** The interviewer is checking if you have a systematic approach (profile first) rather than premature optimization. Mentioning GOMEMLIMIT shows awareness of modern Go (1.19+).

---

## Q4: Is Go pass-by-value or pass-by-reference? Explain with slices and maps. [COMMON]

**Answer:**
Go is strictly pass-by-value — always, no exceptions. When you pass a variable to a function, Go copies the value. However, some types contain internal pointers: a slice is a 24-byte header (pointer + length + capacity), a map is a pointer to the runtime hmap struct, and an interface is a two-field struct (type + data pointer). When these are copied by value, the copy shares the same underlying data via the internal pointer. So modifying a slice's elements inside a function IS visible to the caller (shared backing array), but appending beyond capacity creates a new backing array that the caller doesn't see. Maps always share because a map variable IS a pointer under the hood.

**Interview tip:** Saying "slices are reference types" is a common incorrect answer. The precise answer is: "The slice header is a value that contains a pointer." This distinction matters.

---

## Q5: What is the difference between stack and heap allocation in Go? When does each happen? [COMMON]

**Answer:**
Stack allocation is per-goroutine, automatic, and extremely fast (~1-2ns). Memory is freed instantly when the function returns — no GC involvement. Each goroutine starts with a ~2-8 KB stack that grows as needed via contiguous stack copying. Heap allocation is shared across all goroutines, costs ~25-50ns, and requires garbage collection to free — every heap object is an edge the GC must traverse. The compiler decides placement via escape analysis: variables that outlive their function scope, are shared across goroutines, or have unknown size at compile time go to the heap. Everything else stays on the stack.

**Interview tip:** Mention that Go's stack is contiguous and can grow (unlike C's fixed-size stack) and that this is why Go bans pointer arithmetic — stack addresses change when the stack is relocated.

---

## Q6: Explain Go's garbage collector. What are its characteristics? [COMMON]

**Answer:**
Go uses a concurrent, non-generational, tri-color mark-and-sweep garbage collector. Tri-color means objects are classified as white (unreached), grey (reached but children unscanned), or black (fully scanned). The GC runs concurrently with your program, with two very brief Stop-The-World (STW) pauses (typically sub-100 microseconds) for bookkeeping. The real performance cost isn't STW pauses — it's **mark assist**: when a goroutine tries to allocate during a GC cycle, the runtime forces it to help with marking before the allocation proceeds, causing tail latency spikes. Go's GC is non-generational (unlike Java's), meaning it scans all live objects every cycle, which makes reducing total live heap size more impactful than in generational collectors.

**Interview tip:** Saying "STW pauses are the bottleneck" is an outdated answer. The modern answer is "mark assist is the real latency killer." This shows you understand production Go behavior.

---

## Q7: What are GOGC and GOMEMLIMIT? How do you tune them in production? [ADVANCED]

**Answer:**
GOGC (default 100) controls the GC trigger ratio: when heap grows by GOGC% since last collection, a new cycle triggers. GOGC=100 means GC at 2x live heap. Higher GOGC → less frequent GC → more throughput, more memory. Lower GOGC → more frequent GC → less memory, more CPU overhead. GOMEMLIMIT (Go 1.19+) is a soft memory cap — the runtime adjusts GC pacing to stay under this budget. The modern production strategy: set GOMEMLIMIT to ~90% of your container memory limit and set GOGC high (200-500) or even `GOGC=off`. This lets the limit drive GC pacing instead of the ratio, preventing both OOM kills and excessive GC CPU. Always monitor with `GODEBUG=gctrace=1` and pprof before tuning.

**Interview tip:** Mentioning GOMEMLIMIT shows you're current with Go 1.19+ best practices. The old "GOGC ballast trick" is deprecated — GOMEMLIMIT replaces it.

---

## Q8: How does the `append` trap work with slices? Why does the caller sometimes not see the new element? [COMMON]

**Answer:**
A slice is a 24-byte header: {pointer to backing array, length, capacity}. When passed to a function, the header is copied by value — both copies point to the same backing array. If `append` is called and there's enough capacity, the new element is written into the shared array and the local header's length updates — but the caller's header still has the old length. If `append` exceeds capacity, Go allocates a brand new, larger array and copies data over. Now the local header points to the new array while the caller's header still points to the old one. In both cases the caller's header is stale. Fix: always return the new slice from the function and reassign at the call site.

**Interview tip:** This is one of the most commonly asked Go gotcha questions. Be ready to draw the before/after memory layout showing both headers and both backing arrays.

---

## Q9: What is a memory leak in Go? How do you detect and fix them? [ADVANCED]

**Answer:**
Go has garbage collection, so traditional leaks (forgetting to free) don't exist. But Go has retention leaks — data that's still reachable but no longer needed. Common causes: (1) Sub-slice of a large slice holds a reference to the entire backing array — fix with `copy()`. (2) Goroutine leaks — goroutines blocked forever on channels or I/O, holding references to heap objects. (3) Growing maps that never shrink — even after deleting keys, the map's bucket array doesn't shrink. (4) Forgotten `time.Ticker` without `Stop()`. Detection: use `go tool pprof -inuse_space` for heap profiling, `runtime.NumGoroutine()` for goroutine count trending, and `GODEBUG=gctrace=1` for GC behavior. In production, expose a pprof endpoint (`net/http/pprof`) and monitor goroutine count and heap inuse over time.

**Interview tip:** The interviewer is checking if you know that GC doesn't prevent all memory issues. The sub-slice leak and goroutine leak are the two most common production Go memory problems.

---

## Q10: Explain the write barrier in Go's GC. Why does it exist? [ADVANCED]

**Answer:**
The write barrier is a hidden runtime check on every pointer write to the heap during a GC cycle. It exists to maintain the tri-color invariant: a black (fully-scanned) object must never point directly to a white (unvisited) object, because the white object would be missed and incorrectly freed. When your code writes a new pointer value to a heap object during concurrent marking, the write barrier intercepts this write and ensures the pointed-to object is marked grey (so the GC will eventually scan it). This is the cost of concurrent GC — pointer writes are slightly more expensive during a GC cycle. Write barriers are NOT active between GC cycles, only during the concurrent mark phase.

**Interview tip:** This is a deep question testing GC internals. Connecting it to the tri-color invariant and explaining that it's only active during marking shows real understanding.

---

## Q11: What is `sync.Pool` and when should you use it? [COMMON]

**Answer:**
`sync.Pool` is a concurrent-safe pool of temporary objects that can be reused to reduce heap allocations. It's designed for objects that are frequently allocated and discarded — like byte buffers in HTTP handlers or JSON encoders. Objects in the pool may be silently removed by the GC at any time (during every GC cycle), so you can't rely on persistence. Use it when profiling shows a specific allocation is a hot path bottleneck. Don't use it for objects that need to persist or for connection pools (use a channel or dedicated pool for that). The pattern: `Get()` retrieves (or creates) an object, use it, `Reset()` it, then `Put()` it back.

**Interview tip:** The key nuance is that sync.Pool is NOT a cache — objects are evicted on GC. Mentioning this distinction shows you understand the GC interaction.

---

## Q12: Value semantics vs pointer semantics — when do you choose each? [COMMON]

**Answer:**
Use value semantics (value receivers, pass by value) for: small structs under ~128 bytes, immutable data, read-heavy access patterns, and when you want cache-friendly contiguous memory. Use pointer semantics for: large structs where copy cost matters, when methods need to mutate the receiver, when sharing state between goroutines (with proper synchronization), and for types containing non-copyable fields like `sync.Mutex`. Bill Kennedy's consistency rule: if ANY method on a type needs a pointer receiver, ALL methods should use pointer receiver. The tradeoff: values are stack-friendly and GC-friendly (no pointer edges to trace), but expensive to copy when large. Pointers are cheap to pass (8 bytes) but can trigger escape to heap and add GC scan work.

**Interview tip:** Don't just give the rule — explain the tradeoff. "It depends on struct size, mutation needs, and GC impact" is the senior answer.

---

## Q13: How does Go's stack work differently from C's stack? [ADVANCED]

**Answer:**
Go uses contiguous stacks (since Go 1.4) that start small (~2-8 KB per goroutine) and grow dynamically. When a function call would exceed the current stack size, Go allocates a new, larger stack (typically 2x), copies the entire old stack to the new location, and rewrites ALL pointers that pointed into the old stack. This is why Go bans pointer arithmetic — if you calculated `base + offset`, that address would be invalid after a stack relocation. C stacks are fixed-size (typically 1-8 MB per thread), set at thread creation, and never move. Go's approach allows creating millions of goroutines (each starting at 2KB vs 1MB per thread), at the cost of occasional stack copy overhead.

**Interview tip:** This question tests whether you understand the goroutine cost model. The link between "contiguous stack" → "stack can move" → "no pointer arithmetic" is the key chain of reasoning.

---

## Q14: What is mark assist and why is it the real GC bottleneck? [TRICKY]

**Answer:**
Mark assist is a mechanism where goroutines that allocate heap memory during an active GC cycle are forced to help with the marking phase before their allocation proceeds. It's the GC's way of ensuring marking keeps pace with allocation. The problem: if your service allocates heavily during a GC cycle, goroutines experience unpredictable pauses (not the brief STW pauses, but variable-length assist pauses proportional to allocation rate). This causes p99 latency spikes that are hard to diagnose because they don't show up as "GC pause time" in typical monitoring. The fix is the same as reducing GC pressure in general: fewer allocations, sync.Pool, value semantics, pre-allocated buffers. You can see mark assist time in `GODEBUG=gctrace=1` output and pprof traces.

**Interview tip:** Most candidates say "STW pauses" when asked about GC bottlenecks. The correct modern answer is "mark assist." This single answer can differentiate you from other candidates.

---

## Q15: How would you investigate a Go service that's using more memory than expected? [ADVANCED]

**Answer:**
Systematic approach: (1) Enable `GODEBUG=gctrace=1` to see GC cycle frequency and heap sizes. (2) Run `go tool pprof -inuse_space` to see what's currently alive on the heap — this finds retention leaks. (3) Run `go tool pprof -alloc_space` to see total allocations — this finds allocation hotspots even if objects are short-lived. (4) Check `runtime.NumGoroutine()` trending — goroutine leaks are a common hidden memory consumer. (5) Look for sub-slice leaks with pprof's source view — functions retaining large backing arrays. (6) Check for map bloat — maps don't shrink their bucket array even after deleting keys. (7) In production, use continuous profiling (Datadog, Pyroscope, or pprof endpoints) to compare heap profiles over time. The differential shows what's growing.

**Interview tip:** This is a practical "how would you debug" question. Having a numbered, systematic approach (rather than guessing) is what marks a senior engineer.

---

> Back to main note → [[Go Memory Allocation & Value Semantics]]
