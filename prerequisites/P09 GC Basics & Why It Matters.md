# P09 GC Basics & Why It Matters

> **Prerequisite note** — complete this before starting [[T24 Garbage Collector Deep Dive]].
> Estimated time: ~20 min

---

## 1. Concept

**Garbage collection (GC)** means the runtime frees heap memory you are not using anymore. You never call `free`. Go tracks what is still **reachable** from your running program. Everything else can be recycled.

Think of a **janitor** in an office: most of the time they work around you. Sometimes they need the hallway for a moment and everyone waits briefly. You need cleaning. Cleaning has a cost.

---

## 2. Core Insight (TL;DR)

**Go's GC finds everything your program still uses and frees the rest.** It only cares about **heap** objects — things that outlive a single function call because the compiler had to put them somewhere stable.

**For your job:** high **allocation rate** (lots of new heap objects per second) means the GC runs more often and burns more CPU. That shows up as **tail latency**: your p50 looks fine while p99 spikes.

**The practical lever:** fewer heap allocations → less GC work → more predictable latency. Profile first, then fix hot paths.

---

## 3. Mental Model (Lock this in)

Your service is a loop: **request in → work → response out**. Every time you `make` a slice, grow a string badly, or marshal JSON into a fresh buffer, you add **heap churn**. Short-lived objects are fine in isolation; **millions** of them per minute are not.

**Reachable** means: "Could my code still get to this value through a pointer chain from globals, stacks, or other heap objects?" If not, it is garbage.

**What triggers GC:** you do not call it by hand for normal code. **Allocation** drives it. The runtime tracks how big the live heap is getting. When it crosses the pacing threshold (related to **GOGC**, default 100), a cycle starts. More allocations → more cycles → more background work and occasional pauses.

```
  Your handler                    Heap                         GC
  ┌───────────────┐    alloc    ┌──────────────────────┐
  │ make([]Order)  │ ─────────→ │ []Order backing array │
  │ json.Marshal() │ ─────────→ │ []byte buffer         │     ┌─────────┐
  │ fmt.Sprintf()  │ ─────────→ │ string temp           │     │ Mark:   │
  │ ... response   │            │                        │ ←── │ walk    │
  └───────────────┘            │ (all short-lived)      │     │ roots   │
                                └──────────────────────┘     │         │
  Handler returns →              All unreachable →           │ Sweep:  │
  stack frame gone               GC frees them               │ reclaim │
                                                              └─────────┘
  The more you allocate per request, the more often the GC runs.
  The more often it runs, the more CPU it burns — you see it as p99 spikes.
```

### The mistake that teaches you

```go
package main

import (
	"fmt"
	"runtime"
	"time"
)

func allocHeavy() {
	for i := 0; i < 1_000_000; i++ {
		_ = fmt.Sprintf("order-%d", i) // heap alloc every iteration
	}
}

func main() {
	var before, after runtime.MemStats
	runtime.ReadMemStats(&before)
	start := time.Now()

	allocHeavy()

	runtime.ReadMemStats(&after)
	fmt.Printf("Time:     %v\n", time.Since(start))
	fmt.Printf("GC runs:  %d\n", after.NumGC-before.NumGC)
	fmt.Printf("Total alloc: %.1f MB\n", float64(after.TotalAlloc-before.TotalAlloc)/1e6)
}
```

**What you'd expect:** A million `fmt.Sprintf` calls should be fast — each string is tiny.

**What actually happens:** The program allocates ~50-80 MB total (each `Sprintf` creates a new string on the heap). The GC runs 10-20+ times during the loop. On a hot API path at 5k RPS, this kind of allocation pattern turns into sustained GC pressure and p99 latency spikes.

**Why:** Each `fmt.Sprintf` allocates a new string on the heap. The string is immediately unreachable after `_ =` discards it, but the GC still had to track it, mark it, and sweep it. Multiply that by a million and the GC is doing serious work. Replace with `strings.Builder` or pre-formatted values on hot paths.

---

## 4. How It Works (Backend-Useful Level)

### 4.1 Mark and sweep, without the textbook

**Mark:** starting from places the runtime always knows about (goroutine stacks, globals, registers), Go walks pointers and marks everything still in use.

**Sweep:** unmarked heap memory is returned for reuse.

Most of this happens **while your code runs**, not in one giant stop. There are still **short stop-the-world** moments. For healthy services they are usually small. Under **allocation pressure** or huge heaps, pauses hurt tail latency.

**GC assist:** when allocation outpaces background GC, your allocating goroutine may **do collection work itself** before it gets more memory. That shows up as **surprise latency** inside business code — not in `runtime` frames you were looking for. Fewer allocations → less assist.

You do not need tri-color diagrams to ship a fast API. You need to know: **GC is real work**, tied to **heap size and allocation rate**.

### 4.2 Stack vs heap (why you hear "escape")

Values that **only** live inside one function and never leak out as pointers can live on the **stack**. The stack is cheap: when the function returns, the frame is dropped. **No GC** for those slots.

If you take the address of a local and return it, or store it somewhere that outlives the call, the value **escapes** to the **heap**. Now it participates in GC. **Escape analysis** decides this; `go build -gcflags="-m"` shows compiler notes.

---

### 4.3 Memory traces

### Trace 1 — Stack vs heap: `User` on stack vs pointer out

```go
func stackUser() User {
	user := User{Name: "ada"} // often stays on stack / registers; no heap object for this pattern
	return user               // returned by value — copy, still not necessarily a separate heap box
}

func heapUser() *User {
	user := User{Name: "ada"}
	return &user // pointer escapes: caller may hold *User after this returns → user lives on heap
}
```

```
MEMORY TRACE: stack vs heap (GC only traces heap objects)

Step 1: result := stackUser()
  stack frame [stackUser]:
    user = User{Name: "ada"}          ← lives at 0xC000040F00 (stack)
  Caller receives a COPY of user by value.
  stackUser returns → frame at 0xC000040F00 is gone. No heap object. GC never saw it.

Step 2: ptr := heapUser()
  Compiler sees `return &user` → user must outlive the frame → ESCAPES to heap.
  heap:  0xC0000A2000 → User{Name: "ada"}    ← GC tracks this object
  stack frame [heapUser]:
    (temporary — gone after return)
  Caller holds ptr = 0xC0000A2000.
  GC root chain: goroutine stack → ptr → 0xC0000A2000. Object is REACHABLE.

Step 3: ptr = nil (or function holding ptr returns)
  No root points to 0xC0000A2000 anymore.
  Next GC cycle: mark phase walks all roots → doesn't find 0xC0000A2000 → UNREACHABLE → swept.

(aha: returning &local forces heap allocation; by-value return of a small struct stays off heap entirely.)
```

### Trace 2 — What "reachable" means in an API handler

Picture: **HTTP handler** → calls **service** → loads **`[]Order`** → each **Order** has fields. While the handler is running and still holds references (directly or indirectly), that chain is **reachable**. After you send the response and drop your locals, if nothing else stores those pointers, the whole batch becomes **garbage** for the next cycle.

```
MEMORY TRACE: handler → service → orders

Step 1: request arrives, handler calls svc.LoadOrders(ctx)
  goroutine stack [handler frame]:
    svc    = 0xC0000B0000 (*OrderService)     ← points to long-lived service on heap
    orders = []Order{ptr: 0xC0000C4000, len: 50, cap: 64}
  heap:
    0xC0000B0000 → OrderService{db: *sql.DB}  ← reachable from stack
    0xC0000C4000 → [64]Order{...50 filled}    ← reachable from stack via orders.ptr

  GC root chain: goroutine stack → orders.ptr → 0xC0000C4000. All REACHABLE.

Step 2: json.Marshal(orders) — builds response
  heap (new allocations):
    0xC0000D0000 → []byte (JSON buffer, grows via append)
    0xC0000D2000 → temp strings from field formatting
  Still reachable from stack locals in the marshal call.

Step 3: w.Write(jsonBytes) done, handler returns
  goroutine stack: handler frame popped. orders, jsonBytes — all local vars gone.
  heap:
    0xC0000C4000 → [64]Order{...}       ← NO root points here anymore → GARBAGE
    0xC0000D0000 → []byte JSON buffer   ← NO root points here anymore → GARBAGE
    0xC0000B0000 → OrderService{...}    ← still reachable from server struct → KEPT

  Next GC cycle: marks 0xC0000B0000 (reachable). Sweeps 0xC0000C4000 and 0xC0000D0000.

(aha: "reachable" is about pointer chains from live roots — not about whether you still "need" it logically.)
```

---

## 5. Key Rules & Behaviors

### 5.1 Allocation rate = future GC work

```go
for i := 0; i < 10000; i++ {
    buf := make([]byte, 4096) // heap alloc each iteration
    process(buf)
}
```

```
  Each iteration:
    stack → make([]byte, 4096) → heap object
    → used briefly → unreachable → GC must reclaim

  10,000 iterations = 10,000 heap objects = 10,000 things GC tracks.
  Rate matters as much as size.
```

**Why (Section 4.1):** Every heap object adds to the mark phase workload. High allocation rate triggers more frequent GC cycles.

---

### 5.2 Stack values are invisible to GC

```go
func processOrder(id int64) int {
    total := 0            // stack — never escapes
    tax := total * 18     // stack
    return total + tax    // all die with the frame
}
```

```
  processOrder frame:
  ┌──────────────┐
  │ total = 0    │  ← stack slot
  │ tax   = 0    │  ← stack slot
  └──────────────┘
  Function returns → frame gone. GC never saw these.
```

**Why (Section 4.2):** Escape analysis keeps values on the stack when possible. Stack cleanup is free — just move the stack pointer.

---

### 5.3 Returning a pointer forces heap allocation

```go
func newSession(userID string) *Session {
    s := Session{UserID: userID, CreatedAt: time.Now()}
    return &s // s escapes to heap — GC will track it
}
```

```
  Compile decides: "s is returned by pointer → escapes."

  Without pointer:
    stack → Session{...} → copy out by value → frame gone, no heap.

  With pointer:
    heap → Session{...} → *Session returned → GC tracks until unreachable.
```

**Why (Section 4.2):** `return &local` means the value must outlive the function frame. The compiler escapes it to the heap, adding GC work.

---

### 5.4 Reuse buffers on hot paths

```go
var bufPool = sync.Pool{New: func() any { return new(bytes.Buffer) }}

func handle(w http.ResponseWriter, r *http.Request) {
    buf := bufPool.Get().(*bytes.Buffer)
    buf.Reset()
    defer bufPool.Put(buf)
    // ... encode into buf ...
}
```

```
  Without pool (per request):
    request 1 → alloc buf → use → unreachable → GC reclaims
    request 2 → alloc buf → use → unreachable → GC reclaims
    request 3 → alloc buf → ...  (thousands of short-lived objects)

  With pool:
    request 1 → Get buf → use → Put back
    request 2 → Get same buf → use → Put back
    (one long-lived object reused — GC sees almost nothing new)
```

**Why (Section 4.1):** Fewer allocations means the GC has less work. Pooling trades a small amount of memory for significantly lower allocation rate.

---

### 5.5 GOGC trades RAM for GC frequency

```go
// GOGC=100 (default): next GC when heap doubles vs live data
// GOGC=200: next GC when heap triples vs live data → fewer cycles, more RAM
// GOGC=50: next GC when heap grows 50% → more cycles, less RAM
```

```
  Live heap = 100 MB

  GOGC=100: GC triggers at ~200 MB  → moderate frequency
  GOGC=200: GC triggers at ~300 MB  → fewer cycles, uses more RAM
  GOGC=50:  GC triggers at ~150 MB  → more frequent cycles, tighter RAM

  GOMEMLIMIT adds a soft cap: "never grow beyond X" by collecting harder.
```

**Why (Section 4.1):** GC pacing is relative to live heap. Higher GOGC lets the heap grow more before the next cycle, trading memory for CPU.

---

### 5.6 Code smell quick reference

| Smell | Why it hurts | Direction |
|-------|----------------|-----------|
| `s += x` in a tight loop | Repeated string reallocations | `strings.Builder` |
| `fmt.Sprintf` in a hot loop | Allocations per call | format into `Builder`, reduce work |
| Fresh `[]byte` per JSON write | High alloc rate | `sync.Pool`, reuse buffers |
| Returning `&T` from helpers everywhere | More heap objects | return values, smaller pointer graphs |
| Huge pointer-heavy caches | More work for the marker | object pooling, sharding, bounded caches |

---

## 6. Code Examples (Show, Don't Tell)

### 6.1 The API handler that allocates `[]Order` every request

```go
func (h *Handler) ListOrders(w http.ResponseWriter, r *http.Request) {
	orders := make([]Order, 0, 64) // slice header often on stack; backing may be heap
	orders = h.svc.LoadOrders(r.Context()) // returns a new slice + rows — heap growth

	writeJSON(w, orders) // marshaling allocates hard — see below
}
```

If **every request** allocates fresh rows and fresh JSON buffers, you create a **steady stream** of short-lived heap objects. GC keeps up until it does not. **p99** wobbles: sometimes the collector runs hotter or your goroutine does **assist** work during a hot path.

**Not every allocation is evil.** **Sustained high rate** on a latency-sensitive path is the problem.

### 6.2 JSON: new buffer every call vs `sync.Pool`

**Bad pattern:** every response does `json.NewEncoder(w)` or `json.Marshal` into a newly grown `[]byte` you throw away immediately. That is thousands of allocations per second under load.

**Better pattern:** reuse a `[]byte` buffer from a **`sync.Pool`**. Reset length to 0 between uses; still watch for races — only one goroutine should use a pooled buffer at a time.

```go
var bufPool = sync.Pool{
	New: func() any {
		return new(bytes.Buffer)
	},
}

func marshalOrders(orders []Order) ([]byte, error) {
	buf := bufPool.Get().(*bytes.Buffer)
	buf.Reset()
	defer func() {
		buf.Reset()
		bufPool.Put(buf)
	}()
	if err := json.NewEncoder(buf).Encode(orders); err != nil {
		return nil, err
	}
	// Encoder writes a trailing newline; clone because the buffer returns to the pool
	out := bytes.Clone(buf.Bytes())
	return bytes.TrimSuffix(out, []byte("\n")), nil
}
```

You still pay for **one** output slice per request if you copy out — that is often fine. The win is **reusing** the `Buffer`'s **backing array** across requests instead of growing from zero every time. **Profile** to confirm; sometimes `json.Marshal` + pool is enough.

Real services tune **initial `Buffer` capacity** after seeing peak response sizes in production.

### 6.3 `strings.Builder` vs `+` in a loop

```go
// BAD: each += may allocate a new backing string; O(n²) copies for large inputs
func JoinIDs(ids []string) string {
	s := ""
	for _, id := range ids {
		s += id + ","
	}
	return s
}

// BETTER: one growing buffer
func JoinIDs(ids []string) string {
	var b strings.Builder
	for i, id := range ids {
		if i > 0 {
			b.WriteByte(',')
		}
		b.WriteString(id)
	}
	return b.String()
}
```

`String()` still copies once at the end. That is usually fine. The win is not allocating **every** iteration.

### 6.4 `pprof`: where the allocs come from

You see **80% of allocations in JSON** in a heap profile. You pool buffers and cut serialization copies. **p99** drops. Without the profile you would tune **GOGC** blindly.

```text
go test -bench=. -benchmem
# or for a live service, expose net/http/pprof and:
go tool pprof http://localhost:6060/debug/pprof/heap
```

Look for **flat** allocation counts in your handler path — `encoding/json`, `fmt`, string concat, `append` in tight loops.

**`allocs` profile** (CPU profile with sampling of allocations) helps tie **which lines** allocate to **request latency**. Start with **heap** for "what objects exist?", then **allocs** for "who keeps calling `new`?"

### 6.5 Reading `runtime.MemStats` (optional sanity check)

For dashboards or quick logs, `runtime.ReadMemStats` gives **heap size**, **total bytes allocated** (cumulative), **GC count**, and **pause time** totals. It is a **snapshot**, not a tracer — use **`pprof`** for line-level blame.

```go
var m runtime.MemStats
runtime.ReadMemStats(&m)
// m.HeapAlloc — bytes on heap now
// m.NumGC — completed GC cycles
// m.PauseTotalNs — sum of STW pauses (check docs: semantics evolved across Go versions)
```

Correlate **NumGC** rising fast with **traffic** spikes. If **HeapAlloc** is flat but **p99** is bad, your issue may not be GC — check **locks, IO, and downstreams**.

### 6.6 `GOGC` in one sentence

**`GOGC=200`** → target roughly **double** the live heap before the next GC cycle vs default → **fewer GC cycles**, **more RAM usage**, often **better CPU/latency** if you were GC-bound. **`GOGC=50`** → more aggressive collection → **smaller heap**, **more GC churn**. Always validate under load; **profile allocations first**.

**`GOMEMLIMIT`:** soft cap on **total memory** the runtime tries to respect by **collecting harder** before growing without bound. It can save you from OOM at the cost of **more GC CPU**. Full tradeoffs: [[T25 GC Tuning & Memory Limits]].

---

## 6.7. Practice Checkpoint

### Tier 1 — Handler pressure (2 min)

Your `GetReport` handler unmarshals JSON into a new struct every request, then calls `json.Marshal` on a fresh map for the response. Traffic doubles. Which metric is **most likely** to get worse **first** if you do nothing: **p50**, **p99**, or **average** CPU?

> [!success]- Answer
> **p99** (and tail latency generally) usually worsens before **p50** because GC and scheduling jitter hit worst-case paths. **Average CPU** rises too, but operators often notice **tail** regressions first on APIs. The fix starts with a **heap profile** to confirm JSON and per-request allocations.

### Tier 2 — Pooling sketch (5 min)

Sketch how you would reuse a `[]byte` for `json.Marshal` of a response in an HTTP handler. What is **one** correctness rule you must follow when using `sync.Pool`?

> [!success]- Answer
> **Sketch:** `pool.Get()` yields `*[]byte`, reset `b = (*b)[:0]`, marshal into `*b` (or `append` JSON bytes), write to `ResponseWriter`, then reset and `pool.Put`. **Rule:** a pooled value must **not** be used after `Put` — another goroutine may take it. Never retain a reference to the buffer after returning it to the pool.

### Tier 3 — `GOGC` tradeoff (2 min)

You set **`GOGC=200`**. Describe the **memory vs GC frequency** tradeoff in one sentence.

> [!success]- Answer
> **Higher `GOGC` lets the live heap grow more before the next cycle, so you run **fewer GC cycles** but typically use **more memory**; it can reduce GC overhead if you were spending a lot of time in the collector.

### Tier 4 — Builder vs concat (5 min)

This handler builds a CSV line of user IDs in a loop. Fix the allocation pattern.

```go
func UserIDsLine(ids []int64) string {
	line := ""
	for _, id := range ids {
		line += fmt.Sprintf("%d,", id)
	}
	return line
}
```

> [!success]- Answer
> Use **`strings.Builder`** (or pre-size with `Grow` if you know `len(ids)`). **`+=` with `fmt.Sprintf` each iteration** allocates new strings repeatedly. Example shape:
>
> ```go
> func UserIDsLine(ids []int64) string {
> 	var b strings.Builder
> 	for i, id := range ids {
> 		if i > 0 {
> 			b.WriteByte(',')
> 		}
> 		fmt.Fprintf(&b, "%d", id)
> 	}
> 	return b.String()
> }
> ```
>
> For huge inputs, also estimate capacity with `b.Grow(...)` from digit counts to avoid buffer reallocations.

---

## 7. Gotchas & Interview Traps

| Trap | Reality | Why (Section link) |
|------|---------|-------------------|
| "Go has no GC pauses" | Pauses are usually **short**, not **zero**. Tail latency still exists. | Section 4.1 — STW phases still happen even though most marking is concurrent. |
| "`new` always hits heap" | **Escape analysis** decides; keyword is not the rule. | Section 4.2 — the compiler, not `new`/`make`, decides stack vs heap. |
| "I'll set `GOGC` first" | **Profile allocations** on real traffic first; tuning without data often hides the bug. | Section 5.5 — GOGC is a frequency knob; the real fix is reducing allocation rate (Section 5.1). |
| "Stack is faster so I will return `&T` everywhere" | Returning pointers **increases** heap use and GC graph work. Use pointers when semantics need them. | Section 5.3 — `return &local` forces escape; return by value when the struct is small. |
| Finalizers fix cleanup | Prefer **`defer`** for files/sockets. Finalizers are **late** and **unreliable** under load. | Section 4.1 — finalizers run after GC sweep, which is non-deterministic and may be delayed under allocation pressure. |

---

## 8. Interview Gold Questions (Top 3)

### Interview stories you can tell

**Scenario A:** "Your API's **p99** went from **5ms** to **50ms**. **`pprof heap`** shows **~80%** of allocations in **JSON serialization**. You add **`sync.Pool`** for encode buffers and reduce extra copying. **p99** lands near **8ms** again."

**Scenario B:** "Every handler builds a **new `[]byte`** for the response body. After **10k RPS**, the allocator and GC are constantly cleaning short-lived objects. Every few hundred ms the runtime **pauses goroutines briefly** to finish a phase. Users see rare **latency spikes** — not CPU saturation, **tail** issues."

**Q1: Why does allocation rate matter for a Go API?**

Each heap allocation adds work for the allocator and later for the GC. Under high RPS, many short-lived objects increase GC frequency and **assist** work, which shows up as **CPU** and **tail latency**. Reducing allocations on hot paths is the first practical fix.

**Q2: What is the difference between stack and heap allocation in Go?**

Stack-allocated values live in the goroutine's frame and vanish when the function returns. Heap objects outlive the call because the compiler **escapes** them (e.g., returned pointers, captured by closures, stored in interfaces). **Only heap** objects are tracked by GC.

**Q3: What does `GOGC` do?**

`GOGC` sets the **relative growth** of the live heap that triggers the next GC cycle compared to the default (100). Higher values run GC **less often** but allow **more memory**; lower values do the opposite. Validate under production-like load.

---

## 9. 30-Second Verbal Answer

Go has a tracing garbage collector. It walks all live pointer chains from goroutine stacks and globals, marks every heap object it can reach, and frees the rest. You never call `free` yourself — the runtime handles it.

The cost you actually feel in production is tied to allocation rate. Every heap allocation is something the GC later has to track, mark, and sweep. On a backend doing thousands of requests per second, if each handler allocates fresh slices, fresh JSON buffers, and temp strings, the GC runs more often and your p99 latency spikes while p50 looks fine.

The compiler uses escape analysis to decide what goes on the heap. Values that stay inside one function can live on the stack — no GC cost. But the moment you return a pointer, store something in an interface, or capture a variable in a closure that outlives the frame, it escapes to the heap.

The practical fix is reducing allocation rate on hot paths: reuse buffers with `sync.Pool`, use `strings.Builder` instead of `+=`, avoid `fmt.Sprintf` in tight loops. Always profile with `pprof heap` first — it shows exactly which lines are allocating. `GOGC` lets you trade memory for fewer GC cycles, but that is a knob for after you have fixed the real allocation hot spots.

---

> See [[Glossary]] for term definitions.
