
## 1. Concept

Go Memory Allocation & Value Semantics — how data is stored, passed, and shared across functions and goroutines.

> **Naming trap**: The official "Go Memory Model" (go.dev/ref/mem) is about **happens-before ordering** across goroutines, not stack/heap allocation. If an interviewer hears "Go Memory Model," they'll expect you to talk about visibility guarantees. Use "memory allocation" or "value semantics" when discussing this topic.

---

## 2. Core Insight (TL;DR)

Go is **strictly pass-by-value**, and the **compiler (via escape analysis)** decides whether data lives on the **stack (fast)** or **heap (GC-managed)**.

---

## 3. Mental Model (Lock this in)

### Stack → "Your Desk"

- Private, fast, auto-cleaned
- Lives within function scope

### Heap → "Shared Storage"

- Used when data outlives function
- Managed by GC
- Slower due to allocation + scanning

### Pass-by-value → "Everything is copied"

- Even pointers are copied
- Sharing happens only via internal pointers

### Visual: Where does data live?

```
 ┌─────────────── PROCESS MEMORY ───────────────┐
 │                                               │
 │  ┌─── Goroutine 1 ──┐  ┌── Goroutine 2 ──┐  │
 │  │  STACK            │  │  STACK           │  │
 │  │  ┌─────────────┐  │  │  ┌────────────┐ │  │
 │  │  │ x := 42     │  │  │  │ y := 99    │ │  │
 │  │  │ buf [64]byte │  │  │  │ ptr *User  │─┼──┼──┐
 │  │  └─────────────┘  │  │  └────────────┘ │  │  │
 │  │  Private, fast     │  │  Private, fast  │  │  │
 │  │  Auto-freed on     │  │                 │  │  │
 │  │  function return   │  │                 │  │  │
 │  └────────────────────┘  └─────────────────┘  │  │
 │                                               │  │
 │  ┌──────────── HEAP (shared) ─────────────┐   │  │
 │  │                                        │   │  │
 │  │   ┌─────────┐   ┌──────────────────┐   │   │  │
 │  │   │ User{   │◄──┼──────────────────┼───┼───┘
 │  │   │  Name   │   │  []byte (big)    │   │   │
 │  │   │  Age    │   │                  │   │   │
 │  │   │ }       │   │                  │   │   │
 │  │   └─────────┘   └──────────────────┘   │   │
 │  │                                        │   │
 │  │   GC scans this entire region          │   │
 │  └────────────────────────────────────────┘   │
 └───────────────────────────────────────────────┘
```

---

## 4. Stack vs Heap (Real Rule)

> **Stack vs Heap decision is made entirely by escape analysis at compile time**

The programmer never explicitly chooses. `new()` and `&T{}` do NOT guarantee heap allocation — escape analysis decides.

---

## 5. Escape Analysis (Decision Engine)

### Mental Decision Tree

1. Returned from function? → **Heap**
2. Shared outside (goroutine, channel, global)? → **Heap**
3. Size unknown at compile time? → **Heap**
4. Very large allocation? → **Heap** (compiler heuristic, not a fixed threshold)
5. Stored in interface and value > pointer-sized? → **Often Heap**

> Escape analysis reasons about **lifetimes and reachability**, not size cutoffs. Large allocations tend to heap-allocate as a heuristic, but there's no hard 64KB rule.

### Example

```go
func foo() *int {
    x := 10
    return &x // x escapes — must outlive foo()
}
```

→ `x` escapes → heap

### Counter-example (stays on stack)

```go
func bar() int {
    x := 10
    p := &x   // p does NOT escape — used only within bar()
    return *p
}
```

→ `x` stays on stack

### Verify (non-negotiable skill)

```bash
go build -gcflags="-m"       # basic
go build -gcflags="-m -m"    # verbose (shows WHY something escapes)
```

### Visual: Escape Analysis Decision Flow

```
            ┌──────────────────────┐
            │  Variable declared   │
            └──────────┬───────────┘
                       ▼
            ┌──────────────────────┐
            │ Returned / stored in │──── YES ──▶ HEAP
            │ outliving location?  │
            └──────────┬───────────┘
                       │ NO
                       ▼
            ┌──────────────────────┐
            │ Sent to goroutine /  │──── YES ──▶ HEAP
            │ channel / global?    │
            └──────────┬───────────┘
                       │ NO
                       ▼
            ┌──────────────────────┐
            │ Size unknown at      │──── YES ──▶ HEAP
            │ compile time?        │
            └──────────┬───────────┘
                       │ NO
                       ▼
            ┌──────────────────────┐
            │ Stored in interface  │──── YES ──▶ OFTEN HEAP
            │ (value > ptr size)?  │         (impl-specific)
            └──────────┬───────────┘
                       │ NO
                       ▼
                    ┌───────┐
                    │ STACK │
                    └───────┘
```

---

## 6. Stack Internals (Critical Detail)

- Starts small (~2–8 KB per goroutine, varies by Go version)
- **Grows dynamically** (contiguous stack model since Go 1.4)
- Growth = allocate **new larger stack** + **copy old data** + **update all pointers**

### Visual: Stack Growth

```
  BEFORE GROWTH                 AFTER GROWTH
  ┌────────────┐               ┌────────────────────────┐
  │ frame: C() │               │                        │
  │ frame: B() │  ── copy ──▶  │ frame: C()             │
  │ frame: A() │               │ frame: B()             │
  └────────────┘               │ frame: A()             │
     2 KB                      │                        │
                               │    (room to grow)      │
                               └────────────────────────┘
                                  4 KB (doubled)

  All internal pointers are ADJUSTED to new addresses.
```

### Senior Insight:

> Go pointers are **movable**

When stack grows:
- Memory shifts to a new contiguous block
- **All pointers pointing into the old stack are rewritten**

This is why:
> Go disallows pointer arithmetic (unlike C) — because addresses can change under you

---

## 7. Heap + GC Reality

- **Tri-color concurrent mark-and-sweep** GC (since Go 1.5)
- STW phases exist but are typically **sub-millisecond** (often < 100μs)

### Visual: Tri-Color Mark and Sweep

```
  ┌─────────────────────────────────────────────┐
  │          Tri-Color Marking                  │
  │                                             │
  │  WHITE = unvisited (candidates for sweep)   │
  │  GREY  = visited, children not yet scanned  │
  │  BLACK = visited, all children scanned      │
  │                                             │
  │  Step 1: All objects start WHITE            │
  │  Step 2: Roots marked GREY                  │
  │  Step 3: Pick GREY → scan children → BLACK  │
  │  Step 4: Repeat until no GREY left          │
  │  Step 5: Sweep all remaining WHITE          │
  │                                             │
  │   ○ WHITE    ◐ GREY     ● BLACK             │
  │                                             │
  │   root ──▶ ● ──▶ ● ──▶ ◐ ──▶ ○            │
  │                   │            ↑             │
  │                   └──▶ ● ─────┘             │
  │                                             │
  │   After marking: ○ = garbage → freed        │
  └─────────────────────────────────────────────┘
```

### The REAL cost: Mark Assist (not STW)

> The actual latency killer in production is **mark assist** — when goroutines allocating during a GC cycle are forced to help with marking work before their allocation proceeds. This is what causes tail latency spikes.

### Write Barrier

During a GC cycle, every **pointer write to the heap** goes through a **write barrier** — a hidden runtime check ensuring the GC doesn't miss newly reachable objects (preserves the tri-color invariant).

> **Pointer writes are more expensive than value writes** during GC because of the write barrier overhead.

### Key rules:

> More heap → more GC scan → more latency
> More pointers = more GC work (each pointer is a potential edge in the object graph)

---

## 8. Pass-by-Value (Strict, No Exceptions)

### Primitive

```go
func update(x int) {
    x = 20  // modifies local copy only
}
```

### Pointer

```go
func update(x *int) {
    *x = 20  // modifies original via dereferencing
}
```

> Pointer is copied, underlying data is shared

### Visual: Pass-by-Value with Pointer

```
  CALLER                          CALLEE
  ┌──────────────┐               ┌──────────────┐
  │ p *int ──────┼───┐           │ x *int ──────┼───┐
  └──────────────┘   │           └──────────────┘   │
                     │   (same address, copied)     │
                     ▼                               ▼
                  ┌──────┐
                  │  42  │  ◄── both point here
                  └──────┘
                  (heap or stack)
```

---

## 9. Reference-like Types (Actual Truth)

### Slice (Most Important)

```go
type slice struct {
    ptr *T    // pointer to underlying array
    len int   // number of elements in use
    cap int   // total capacity of underlying array
}
```

### Visual: Slice Header vs Underlying Array

```
  SLICE HEADER (24 bytes, passed by value)
  ┌───────────────────────────────────┐
  │ ptr ──────────┐   len: 3  cap: 5 │
  └───────────────┼───────────────────┘
                  ▼
  UNDERLYING ARRAY (heap-allocated)
  ┌─────┬─────┬─────┬─────┬─────┐
  │  10 │  20 │  30 │     │     │
  └─────┴─────┴─────┴─────┴─────┘
    [0]   [1]   [2]   [3]   [4]
           ▲                 ▲
           │                 │
         len=3             cap=5
       (visible)       (available)
```

> Passing a slice = copying the 24-byte header. Both caller and callee see the same underlying array.

### Slice Behaviors

```go
func modify(s []int) {
    s[0] = 100  // ✅ visible outside — same underlying array
}

func grow(s []int) {
    s = append(s, 4)  // ❌ NOT visible outside if realloc happens
}
```

### Visual: The Append Trap

```
  BEFORE append (cap=3, len=3 — full)
  caller.s ──▶ [10, 20, 30]

  INSIDE grow():
    s = append(s, 4)
    // cap exceeded! Go allocates NEW array
    // local s now points to NEW array
    // caller's s still points to OLD array

  AFTER:
  caller.s ──▶ [10, 20, 30]         ← unchanged!
  local s  ──▶ [10, 20, 30, 4]      ← new allocation, lost on return
```

**Fix**: return the new slice, or pass `*[]int`.

---

### Map

```go
// map variable is a pointer to runtime.hmap
m := make(map[string]int)
// m is of type *runtime.hmap under the hood
```

- Always behaves like shared structure (it's already a pointer)
- No need to pass `*map` — the map value IS a pointer

---

### Interface (Senior-Level Detail)

```go
type iface struct {       // interface with methods
    tab  *itab            // type info + method table
    data unsafe.Pointer   // pointer to actual value
}

type eface struct {       // empty interface (any)
    _type *_type
    data  unsafe.Pointer
}
```

### Visual: Interface Layout

```
  var r io.Reader = &os.File{...}

  ┌─────────────────────────┐
  │ iface                   │
  │  tab ──▶ itab{          │
  │           inter: *io.Reader type info
  │           _type: *os.File type info
  │           fun:   [Read method ptr]
  │          }              │
  │  data ──▶ os.File{...}  │  ◄── on heap
  └─────────────────────────┘

  Copying interface = copying this 16-byte struct
  The data it points to is NOT copied
```

### When interfaces cause heap allocation:

- Value assigned to interface **larger than pointer size** → must heap-allocate to store behind `unsafe.Pointer`
- Small scalar types (int, bool) may avoid allocation (compiler optimization, version-specific)

---

## 10. Closure Escape (Gap Filled)

```go
func makeAdder(n int) func(int) int {
    return func(x int) int {
        return x + n  // n is captured — escapes to heap
    }
}
```

> The closure captures `n`, forcing it to heap-allocate. The returned function outlives `makeAdder`, so `n` must survive too.

### Visual: Closure Capture

```
  makeAdder(5) returns:
  ┌──────────────────────┐
  │ func closure {       │
  │   code: func(x int)  │
  │   env ──▶ ┌───────┐  │
  │           │ n = 5 │  │  ◄── heap-allocated
  │           └───────┘  │
  │ }                    │
  └──────────────────────┘
```

---

## 11. sync.Pool (Gap Filled — Interview Essential)

`sync.Pool` amortizes heap allocation cost on hot paths by reusing objects.

```go
var bufPool = sync.Pool{
    New: func() any { return new(bytes.Buffer) },
}

func handler(w http.ResponseWriter, r *http.Request) {
    buf := bufPool.Get().(*bytes.Buffer)
    buf.Reset()
    defer bufPool.Put(buf)

    // use buf...
}
```

### Key insight:

> `sync.Pool` is a **cache, not a free list** — objects can be collected at any GC cycle. Never store critical state in a Pool.

### When to use:

- High-frequency allocations of same-shaped objects (buffers, structs)
- HTTP handlers, serialization paths, encoding loops

---

## 12. GOGC and GOMEMLIMIT (Gap Filled — Interview Essential)

### GOGC (default: 100)

Controls GC frequency: ratio of new heap allocations to live heap size.
- `GOGC=100` → GC triggers when heap doubles
- `GOGC=50` → GC triggers sooner (less memory, more CPU)
- `GOGC=200` → GC triggers later (more memory, less CPU)
- `GOGC=off` → disables GC entirely

### GOMEMLIMIT (Go 1.19+)

Soft memory ceiling. The runtime adjusts GC frequency to stay within the budget.

```bash
GOMEMLIMIT=512MiB ./myserver
```

### Interview line:

> "GOGC trades throughput for memory. GOMEMLIMIT (Go 1.19+) is the modern approach — set a memory budget and the runtime adjusts GC pacing automatically. In production, we typically set GOMEMLIMIT and use a high GOGC (or off) to let the memory limit drive GC behavior."

### Visual: GOGC Effect

```
  GOGC=100 (default)         GOGC=50
  ┌────────────┐             ┌────────────┐
  │ live: 100MB│             │ live: 100MB│
  │ trigger at │             │ trigger at │
  │   200MB    │             │   150MB    │
  │ ▓▓▓▓░░░░░░│             │ ▓▓▓▓░░░░░░│
  │ ▓▓▓▓▓▓▓▓░░│ ← GC here  │ ▓▓▓▓▓▓░░░░│ ← GC here (sooner)
  └────────────┘             └────────────┘
  Less CPU, more memory      More CPU, less memory
```

---

## 13. Channel Internals & Memory (Gap Filled)

```go
type hchan struct {
    buf      unsafe.Pointer // circular buffer (heap-allocated)
    dataqsiz uint           // buffer capacity
    elemsize uint16         // size of each element
    // ... lock, sendq, recvq, etc.
}
```

### Key memory facts:

- Buffered channels have an internal **circular buffer** (heap-allocated)
- **Sending a value copies it** into the channel buffer (pass-by-value again)
- Sending a pointer shares the underlying data — same GC implications
- Unbuffered channels do **direct goroutine-to-goroutine copy** (no buffer)

### Visual: Buffered Channel

```
  ch := make(chan int, 4)

  ┌──── hchan ─────────────────────────┐
  │ buf ──▶ ┌────┬────┬────┬────┐      │
  │         │ 42 │ 77 │    │    │      │
  │         └────┴────┴────┴────┘      │
  │           ▲              ▲         │
  │         recvx          sendx       │
  │  dataqsiz: 4  qcount: 2           │
  │  sendq: [blocked goroutines...]    │
  │  recvq: [blocked goroutines...]    │
  └────────────────────────────────────┘
```

---

## 14. Why This Design Exists

- Stack → fast, cache-friendly, zero GC overhead
- Heap → flexible but GC-heavy
- Compiler handles allocation → simpler than C/C++ manual memory management
- Write barrier + concurrent GC → safe concurrent access without programmer burden

Goal:
> Performance + simplicity balance — the programmer thinks in values, the compiler optimizes placement

---

## 15. Tradeoffs (What matters in real systems)

### Value types

- ✅ Better cache locality (contiguous memory)
- ✅ Less GC pressure (no pointers to scan)
- ✅ Predictable performance
- ❌ Expensive to copy for large structs (> ~128 bytes, benchmark to confirm)

### Pointer types

- ✅ Avoid copying large data
- ✅ Enable shared mutation
- ❌ Increase GC scanning (every pointer is an edge in the object graph)
- ❌ Hurt cache locality (pointer chasing = cache misses)
- ❌ Can trigger escapes → heap allocation

### Rule of thumb:

> For structs ≤ ~128 bytes with read-heavy access patterns, prefer value semantics. For large structs or write-heavy shared state, consider pointers — but always measure.

---

## 16. GC Tax (Non-Negotiable Insight)

> Heap allocations are not free — they create **future GC work**

- GC must **traverse every pointer** on the heap (mark phase)
- **Mark assist** forces allocating goroutines to help GC during active cycles
- More objects → longer mark phase → tail latency spikes
- Write barrier adds overhead to **every pointer store** during GC

### The chain reaction:

```
More heap allocs → more live objects → more pointers to scan
  → longer mark phase → more mark assist → goroutine latency spikes
    → p99 latency degrades under load
```

---

## 17. Critical Edge Cases

### Slice append trap

```go
func modify(s []int) {
    s = append(s, 4)  // may allocate new backing array
}                      // caller never sees the change
```

**Fix**: `func modify(s []int) []int` and return the new slice.

### Loop variable trap (UPDATED)

```go
for _, v := range arr {
    go func() {
        fmt.Println(v)  // Pre-1.22: captures same variable — race/bug
    }()
}
```

**Pre-Go 1.22**: Same variable reused across iterations → all goroutines see final value.

**Go 1.22+**: Loop variable is **per-iteration** at compiler level.

> "This was fixed in Go 1.22. The loop variable is now scoped per-iteration, so closures capture the correct value without needing `v := v`."

### Interface nil trap

```go
var p *MyStruct = nil
var i interface{} = p
fmt.Println(i == nil) // false!
```

> An interface is nil only when **both** tab/type AND data are nil. Wrapping a nil pointer in an interface makes it non-nil.

---

## 18. Common Misconceptions

| Misconception | Reality |
|---|---|
| Go is pass-by-reference | **WRONG** — strictly pass-by-value |
| Pointer = always faster | **WRONG** — adds GC pressure, hurts locality |
| Slice is a reference type | **HALF TRUE** — slice header is a value containing a pointer |
| `new()` always allocates on heap | **WRONG** — escape analysis decides |
| Map values are addressable | **WRONG** — `&m["key"]` is illegal |
| STW pauses are the GC bottleneck | **OUTDATED** — mark assist is the real latency killer |

Correct mental model:
> Everything is pass-by-value. Some values contain internal pointers that enable shared access to underlying data.

---

## 19. Real-world Impact

- Heap-heavy systems → GC latency spikes (especially p99)
- Pointer-heavy design → slower under load due to GC + cache misses
- Value semantics → better performance at scale
- `sync.Pool` → critical for hot-path allocation reduction
- `GOMEMLIMIT` → modern GC tuning knob for production systems

---

## 20. Interview Gold Questions

### Q1: `map[string]User` vs `map[string]*User` for 10M users?

**Nuanced answer:**

| Factor | `map[string]User` | `map[string]*User` |
|---|---|---|
| GC pressure | ✅ Low (no extra pointers) | ❌ High (10M pointer edges) |
| Map growth/rehash | ❌ Expensive (copies all values) | ✅ Cheap (copies pointers) |
| Mutation | ❌ Copy-out, modify, copy-back | ✅ Direct mutation via pointer |
| `&m["key"]` | ❌ Illegal | ✅ Already a pointer |
| Cache locality | ✅ Values contiguous in buckets | ❌ Pointer chasing |

> **For small structs (< ~128 bytes) with read-heavy access**: `map[string]User` — fewer pointers, less GC work.
> **For large structs or write-heavy workloads**: `map[string]*User` — cheaper rehash, direct mutation.
> **Advanced**: Use `map[string]int32` as index into `[]User` slice — best of both worlds (dense values, cheap map ops).

### Q2: How would you reduce GC pressure in a high-throughput HTTP service?

> "I'd profile with `GODEBUG=gctrace=1` and `pprof` to find the allocation hotspots. Then: (1) use `sync.Pool` for frequently allocated buffers, (2) prefer value semantics for small structs, (3) pre-allocate slices with known capacity, (4) avoid unnecessary interface boxing, (5) tune `GOMEMLIMIT` to give the GC a memory budget rather than relying solely on GOGC."

---

## 21. Final Verbal Answer

> "Go is strictly pass-by-value. The compiler uses escape analysis to decide whether variables are allocated on the stack or heap. Stack allocation is fast and automatically managed, while heap allocation introduces garbage collection overhead. The GC is a concurrent tri-color mark-and-sweep collector — STW pauses are sub-millisecond, but the real cost is mark assist, where allocating goroutines are forced to help with GC work, causing tail latency spikes. Types like slices, maps, and interfaces appear reference-like because they contain internal pointers, but they are still passed by value. In high-performance systems, minimizing heap allocations and pointer usage is critical — using value semantics, sync.Pool, pre-allocated buffers, and GOMEMLIMIT tuning to keep GC pressure under control."

---
