# P09 GC Basics & Why It Matters

> **Prerequisite note** — complete this before starting [[T24 Garbage Collector Deep Dive]].
> Estimated time: ~20 min

---

## 1. Concept

**Garbage collection** is automatic memory management: the runtime finds heap objects that your program can never reach again and frees them so memory can be reused.

> **In plain English:** Think of the GC as an office janitor. The janitor walks the building, finds trash nobody is using anymore, and hauls it away. The office keeps running while the janitor works, but when the janitor blocks a hallway for a moment, everyone pauses briefly. Cleaning is necessary, but it is not free.

---

## 2. Core Insight (TL;DR)

**Go gives you pointers and heap objects without `malloc` and `free`.** That power comes with a trade: **the runtime must prove what is still reachable** and recycle the rest.

For interviews, the line that lands: **fewer heap allocations usually mean less GC work and more predictable latency.**

---

## 3. Mental Model (Lock this in)

Expand the janitor story. Your program builds a web of objects on the **heap**. Some objects are **anchored** by **roots**: places the runtime knows your execution might read from without chasing other pointers first. The GC’s job is to discover the **reachable** subgraph from those roots. Anything not proved reachable is **garbage**.

```
HEAP (objects are boxes, arrows are pointers)

  roots (conceptual anchors)
  ┌─────────┐     ┌─────────┐
  │ stack   │     │ globals │
  └───┬─────┘     └────┬────┘
      │                │
      ▼                ▼
   ┌──────┐         ┌──────┐
   │  A   │────────►│  B   │
   └──┬───┘         └──┬───┘
      │                │
      │                ▼
      │            ┌──────┐      ┌──────┐
      └───────────►│  C   │      │  X   │  ◄── no path from any root
                   └──────┘      └──────┘
                   REACHABLE      GARBAGE (candidate for sweep)
```

**Tri-color marking** is a bookkeeping trick while the janitor works. Each heap object is mentally painted:

```
WHITE  = not proved reachable yet        (default suspicion: might be garbage)
GREY   = proved reachable, work remains  (still need to scan its outgoing pointers)
BLACK  = reachable and fully scanned      (all outgoing pointers processed)
```

```
Progress picture (simplified):

  WHITE        GREY         BLACK
  ─────        ────         ─────
   ?            scan me      done

  The GC drains GREY until empty.
  Anything still WHITE at the end is garbage.
```

> **In plain English:** White means “I have not vouched for this yet.” Grey means “I know you exist; I still need to follow your arrows.” Black means “I know you exist and I already followed your arrows.” If the GC finishes and something is still white, your program cannot reach it anymore, so it can be recycled.

---

## 4. How It Works

### 4.1 Mark phase: start from roots

The mark phase discovers reachability by graph traversal from **roots**.

Typical root families:

- **Goroutine stacks**: local variables and arguments that hold pointers
- **Global variables** in the data segment
- **Registers** that temporarily hold pointers at safepoints

```
MARKING AS BFS/DFS (conceptual)

roots ──► enqueue GREY
GREY  ──► scan pointers
          ├─► first time seeing target? paint GREY, enqueue
          └─► when all outgoing pointers scanned, paint BLACK
```

### 4.2 Sweep phase: recycle the rest

After marking, **sweep** walks allocator structures and returns unmarked white memory to free lists or similar mechanisms so future allocations can reuse it.

```
BEFORE SWEEP                AFTER SWEEP
─────────────               ─────────────

[A]-[B]-[C]   [X]           [A]-[B]-[C]   ( )
reachable     garbage                     X reclaimed
```

### 4.3 Stop-the-world (STW)

**STW** means: for a short window, **all goroutines are paused** so the runtime can move the GC through a delicate step safely.

Go’s GC is famous for **short STW**, not zero STW. Treat STW as real, measurable, and something you design around.

```
TIMELINE (not to scale)

app:  ████ run ████ run ████ run ████
gc:       ^STW^   concurrent mark    ^STW^
          short                  short
```

### 4.4 Concurrent marking and the write barrier

Modern Go does **much of marking concurrently** while your goroutines run. That creates a race: your program mutates pointers while the GC walks the graph.

The **write barrier** is instrumentation on pointer writes. It records just enough information so the GC cannot “miss” a newly created edge from black objects to white objects. You can treat it as **a tiny tax on pointer updates** that buys correctness during concurrent marking.

```
WITHOUT BARRIER STORY (WRONG OUTCOME)

GC thinks it scanned BLACK node B fully.
Your code later does: B.next = W   (W was WHITE)
If GC does not notice, W might be swept while still reachable.

WRITE BARRIER IDEA (CORRECT OUTCOME)

On B.next = W, runtime notes the edge
or repaints bookkeeping so W is not lost.
```

Details of barrier algorithms and tri-color invariants live in [[T24 Garbage Collector Deep Dive]].

### 4.5 What triggers GC

You do not call GC like `free`. Allocation **pays into** a pacing system. When live heap grows relative to expectations, the **GC cycle starts or intensifies**. More allocation pressure tends to mean **more frequent cycles** and more background work.

---

## 5. Key Rules & Behaviors

### Every heap allocation creates future GC work

```
LOOP ALLOCATES NEW SLICES

for i := 0; i < N; i++ {
    b := make([]byte, 1024) // heap object each time
    _ = b
}

Each iteration: new object → more bytes to track → more marking/sweep work eventually
```

> **In plain English:** Every new heap object is a new thing the janitor might need to inspect later. A tight loop of small allocations can overwhelm the pacing system.

### GC runs concurrently with your program (mostly)

```
YOUR CPU TIME BUDGET

your code:     ████████████████████
GC helpers:    ▓▓  ▓▓▓   ▓▓    ▓▓▓▓
               background assist + dedicated workers
```

> **In plain English:** The janitor mostly works alongside you, not only when you sleep. That reduces pause times but does not erase CPU cost.

### STW pauses are short but real

Interviewers sometimes mythologize “Go has no pauses.” More defensible: **pauses are usually sub-millisecond on healthy programs**, but **load, heap size, and allocation rate** move the needle.

> **In plain English:** The hallway block is short, not fictional.

### Reducing allocations is the #1 practical optimization lever

```
BAD PATTERN (many transient objects)

var sb strings.Builder
for _, s := range parts {
    sb.WriteString(strings.ToUpper(s)) // ToUpper allocates
}

BETTER PATTERN (reuse, fewer temps)

var sb strings.Builder
for _, s := range parts {
    for i := 0; i < len(s); i++ {
        sb.WriteByte(upperASCII(s[i])) // example: custom, no new string per part
    }
}
```

ASCII after the conceptual code:

```
ALLOCATION RATE

high:  * * * * * * * *   → GC cycles crowd the timeline
low:   *     *           → GC breathes
```

> **In plain English:** If you stop generating disposable objects, the janitor visits less often.

### Stack allocations are free from the GC’s perspective

```
STACK FRAME (conceptual)

high address
┌──────────────┐
│ return addr  │
├──────────────┤
│ local int    │  not a GC scan target
│ local *T     │  might point into heap; still rooted via stack while live
└──────────────┘
low address
```

> **In plain English:** Locals that do not escape live and die with the call frame. The GC is not maintaining a separate heap object for them.

### Pointers from heap to heap increase GC graph work and barrier traffic

```
HEAP GRAPH DENSITY

sparse:   A──►B                    fewer edges to scan
dense:    A──►B──►C──►D──►E──►...   more scanning + more mutation events
```

> **In plain English:** A bushy pointer graph is a bigger maze for the janitor, and every pointer write is a place the barrier must be careful.

### GOGC controls trigger frequency (default 100 means next cycle when heap roughly doubles)

**GOGC:** higher value → GC runs less often but each cycle may collect more; lower value → more frequent GC, smaller heaps, often more CPU spent in GC.

**GOMEMLIMIT:** a soft memory cap that pushes the GC to work harder before the process grows without bound; it trades CPU for staying under a budget.

Details and tuning tradeoffs: [[T25 GC Tuning & Memory Limits]].

---

## 6. Code Examples

### Heavy allocators vs reuse

```go
package main

import "fmt"

func heavy(n int) [][]int {
	out := make([][]int, n)
	for i := 0; i < n; i++ {
		row := make([]int, 100) // fresh backing array each row
		for j := range row {
			row[j] = j
		}
		out[i] = row
	}
	return out
}

func reuseBuffer(n int) int {
	buf := make([]int, 100) // one backing array reused
	sum := 0
	for i := 0; i < n; i++ {
		for j := range buf {
			buf[j] = i + j
		}
		for _, v := range buf {
			sum += v
		}
	}
	return sum
}

func main() {
	fmt.Println(len(heavy(10)))
	fmt.Println(reuseBuffer(10))
}
```

ASCII:

```
heavy:     row objects:  [####][####][####]...
reuseBuffer: one buffer [~~~~~~~~] reused
```

### Reading GC stats with `runtime.ReadMemStats`

```go
package main

import (
	"fmt"
	"runtime"
)

func main() {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	fmt.Println("HeapAlloc bytes:", m.HeapAlloc)
	fmt.Println("TotalAlloc bytes (cumulative):", m.TotalAlloc)
	fmt.Println("NumGC:", m.NumGC)
	fmt.Println("PauseTotalNs:", m.PauseTotalNs)
}
```

ASCII:

```
MemStats snapshot is a photograph, not a movie

camera click → one struct filled with counters
```

### Escape analysis: stack vs heap

```go
package main

//go:noinline
func identity(x int) int { return x }

func stackInt() int {
	n := 42
	return identity(n) // n can live in registers/stack; no heap box needed for n
}

type big struct{ a, b, c int }

func heapBig() *big {
	x := big{1, 2, 3}
	return &x // escapes: caller needs pointer after return → likely heap
}

func main() {
	_ = stackInt()
	_ = heapBig()
}
```

Build with escape diagnostics:

```
go build -gcflags="-m -m" .
```

Typical directionally-correct story in output:

```
stackInt: values do not escape
heapBig: moved to heap: escapes to heap
```

ASCII after the commands concept:

```
compiler sees: "does pointer outlive stack frame?"
yes → heap
no  → stack / registers
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

What is a defensible statement about `heapBig` in the escape example?

1. `new` forced the heap
2. Returning `&x` can force `x` to the heap because the pointer outlives the callee
3. `big` is always on the stack because it is a struct

> [!success]- Answer
> **2 is correct.** Returning the address of a local variable means the storage must survive after `heapBig` returns, so the compiler typically allocates `x` on the heap. **1 is the classic trap:** `new` is just syntax; placement follows escape analysis and compiler rules, not the keyword name. **3 is wrong** for this pattern because struct value does not imply stack placement.

### Tier 2: Fix the Bug (5 min)

This function builds a large string in a loop. It allocates badly.

```go
func JoinInts(nums []int) string {
	s := ""
	for _, n := range nums {
		s += fmt.Sprintf("%d,", n)
	}
	return s
}
```

Rewrite it to reduce per-iteration allocations without changing the comma-separated format intent.

> [!success]- Answer
> Use `strings.Builder` and format into it once per iteration, or precompute capacity if you can estimate size. Example shape:

```go
func JoinInts(nums []int) string {
	var b strings.Builder
	for i, n := range nums {
		if i > 0 {
			b.WriteByte(',')
		}
		fmt.Fprintf(&b, "%d", n)
	}
	return b.String()
}
```

> The bug was repeated string concatenation creating new backing strings each loop iteration. Builder keeps one growing buffer.

---

## 7. Gotchas & Interview Traps

- **`new` always allocates on the heap** is wrong. Escape analysis and compiler choices decide placement. `new(T)` can be optimized similarly to `&T{}` in many cases.
- **GC pauses are seconds long in normal servers** is wrong as a blanket claim. Pauses are usually tiny compared to second-scale stalls; second-scale issues are more often **locks, IO, oversubscription, or bugs**, not baseline STW.
- **Finalizers are a reliability tool** is wrong. Finalizers run late, may not run under pressure, and do not solve resource lifetimes. Close files with `defer`, not `runtime.SetFinalizer`.
- **“I will tune GOGC first”** without profiling allocations often signals backwards reasoning. Start with **allocation profiles**, then tune.

---

## 8. Interview Gold Questions (Top 3)

1. **What is reachable memory, and what are roots?**  
   Give a crisp graph definition: roots are stack slots, globals, registers at safepoints; reachability is transitive closure following pointers from roots.

2. **Why can’t naive reference counting replace Go’s GC?**  
   Cycles, atomic refcount updates on hot paths, and the cost of writes on every pointer assignment. Go’s mutation-heavy pointer graphs fit tracing GC better in practice.

3. **What is the write barrier for in a concurrent GC?**  
   It prevents the mutator from hiding new edges from the marker while the graph is being scanned; it keeps the tri-color invariant from breaking.

---

## 9. 30-Second Verbal Answer

Go uses a **tracing garbage collector** that **marks** everything reachable from **roots** like stacks and globals, then **sweeps** unreachable heap objects. Most marking runs **concurrently**, but there are still **short STW** windows. **Tri-color marking** is the standard bookkeeping, and **write barriers** keep concurrent mutation safe. In real systems, **allocation rate drives GC cost**, so **reducing heap allocations** is the first latency win. **GOGC** adjusts how aggressively cycles trigger, and **GOMEMLIMIT** adds a soft cap that trades CPU for memory.

---

> See [[Glossary]] for term definitions.
