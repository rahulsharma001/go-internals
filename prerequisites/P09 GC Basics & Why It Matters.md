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

## 5. Memory Traces (Only Two)

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

Step 1: stackUser()
  stack:  user = User{Name: "ada"}
  heap:   (often nothing for `user` itself — dies with the frame when you're done copying out)

Step 2: heapUser()
  stack:  temporary frame while building user
  heap:   one User object — the returned *User points here
          GC keeps this object while anything reachable still points at it

(aha: returning &local forces heap allocation; by-value return of a small struct often stays off heap.)
```

### Trace 2 — What "reachable" means in an API handler

Picture: **HTTP handler** → calls **service** → loads **`[]Order`** → each **Order** has fields. While the handler is running and still holds references (directly or indirectly), that chain is **reachable**. After you send the response and drop your locals, if nothing else stores those pointers, the whole batch becomes **garbage** for the next cycle.

```
MEMORY TRACE: handler → service → orders

Step 1: request arrives
  goroutine stack:  handler has *Service, ctx, writer…
  heap:             service object, slice header for orders, backing array of Order structs

Step 2: you build JSON from orders
  heap:             temporary buffers / strings from marshaling (often many short-lived objects)

Step 3: response sent, handler returns, no global cache kept
  stack:            handler frame gone
  heap:             orders + temporaries no longer reachable from any root → garbage

(aha: "reachable" is about pointer chains from live code — not about whether you still "need" it logically.)
```

---

## 6. Why This Shows Up in Production

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

## 7. Story You Can Tell in an Interview

**Scenario A:** "Your API's **p99** went from **5ms** to **50ms**. **`pprof heap`** shows **~80%** of allocations in **JSON serialization**. You add **`sync.Pool`** for encode buffers and reduce extra copying. **p99** lands near **8ms** again."

**Scenario B:** "Every handler builds a **new `[]byte`** for the response body. After **10k RPS**, the allocator and GC are constantly cleaning short-lived objects. Every few hundred ms the runtime **pauses goroutines briefly** to finish a phase. Users see rare **latency spikes** — not CPU saturation, **tail** issues."

---

## 8. Key Rules & Behaviors

- **Heap allocations** → future GC work. **Rate** matters as much as size.
- **Stack** values that do not escape are **invisible** to GC sweep — they disappear when the function returns.
- **Escaping** pointers (`return &local`, storing into globals, interface boxing sometimes) → **heap**.
- **Fewer, larger, reused** buffers usually beat **many tiny** throwaway allocations on hot paths.
- **`GOGC`** trades **RAM for GC frequency**. **`GOMEMLIMIT`** (see [[T25 GC Tuning & Memory Limits]]) adds a **soft cap** so the process does not grow without bound — different knob, same family of tradeoffs.

---

## 9. Code Smell Quick Reference

| Smell | Why it hurts | Direction |
|-------|----------------|-----------|
| `s += x` in a tight loop | Repeated string reallocations | `strings.Builder` |
| `fmt.Sprintf` in a hot loop | Allocations per call | format into `Builder`, reduce work |
| Fresh `[]byte` per JSON write | High alloc rate | `sync.Pool`, reuse buffers |
| Returning `&T` from helpers everywhere | More heap objects | return values, smaller pointer graphs |
| Huge pointer-heavy caches | More work for the marker | object pooling, sharding, bounded caches |

---

## 10. Practice Checkpoint

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

## 11. Gotchas & Interview Traps

| Trap | Reality |
|------|---------|
| "Go has no GC pauses" | Pauses are usually **short**, not **zero**. Tail latency still exists. |
| "`new` always hits heap" | **Escape analysis** decides; keyword is not the rule. |
| "I'll set `GOGC` first" | **Profile allocations** on real traffic first; tuning without data often hides the bug. |
| "Stack is faster so I will return `&T` everywhere" | Returning pointers **increases** heap use and GC graph work. Use pointers when semantics need them. |
| Finalizers fix cleanup | Prefer **`defer`** for files/sockets. Finalizers are **late** and **unreliable** under load. |

---

## 12. Interview Gold Questions (Top 3)

**Q1: Why does allocation rate matter for a Go API?**

Each heap allocation adds work for the allocator and later for the GC. Under high RPS, many short-lived objects increase GC frequency and **assist** work, which shows up as **CPU** and **tail latency**. Reducing allocations on hot paths is the first practical fix.

**Q2: What is the difference between stack and heap allocation in Go?**

Stack-allocated values live in the goroutine's frame and vanish when the function returns. Heap objects outlive the call because the compiler **escapes** them (e.g., returned pointers, captured by closures, stored in interfaces). **Only heap** objects are tracked by GC.

**Q3: What does `GOGC` do?**

`GOGC` sets the **relative growth** of the live heap that triggers the next GC cycle compared to the default (100). Higher values run GC **less often** but allow **more memory**; lower values do the opposite. Validate under production-like load.

---

## 13. 30-Second Verbal Answer

Go uses a **tracing garbage collector**: it finds **reachable** heap objects from stacks and globals, then **frees** the rest. You pay for **heap allocations** with **future GC work** — under API load that often hurts **p99** before **p50**. **Escape analysis** decides stack vs heap; **returning pointers** usually forces **heap**. Reduce pressure with **`strings.Builder`**, **fewer `fmt` temps**, and **`sync.Pool`** for **JSON buffers** where profiling proves it helps. Use **`pprof` heap** to find the real hotspots. **`GOGC`** trades **memory for GC frequency** — e.g. **`GOGC=200`** runs fewer cycles but uses more RAM.

---

> See [[Glossary]] for term definitions.
