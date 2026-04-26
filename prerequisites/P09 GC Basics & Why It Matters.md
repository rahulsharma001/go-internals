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
MEMORY TRACE:
Step 1: roots are known starting points (stack slots, globals, registers at safepoints).
  stack @0x7fff_1000:  local p ──→ heap @0x1c000_0000 (object A)
  globals @0x55aa_2000: g ──→ heap @0x1c000_0040 (object B)

Step 2: heap objects form a pointer graph from those roots.
  heap @0x1c000_0000 (A) ──field──→ heap @0x1c000_0040 (B)
  heap @0x1c000_0040 (B) ──field──→ heap @0x1c000_0080 (C)
  heap @0x1c000_00c0 (X) ◄── no incoming path from any root in Step 1–2

Step 3: transitive closure from roots visits {A, B, C}; X is never enqueued.
  reachable:  A ──→ B ──→ C
  garbage:    X   (candidate for sweep)

(aha: reachability is graph reachability from roots; “orphan” heap objects are not roots by themselves.)
```

**Tri-color marking** is a bookkeeping trick while the janitor works. Each heap object is mentally painted:

```
WHITE  = not proved reachable yet        (default suspicion: might be garbage)
GREY   = proved reachable, work remains  (still need to scan its outgoing pointers)
BLACK  = reachable and fully scanned      (all outgoing pointers processed)
```

```
MEMORY TRACE: tri-color during marking (same objects as above; colors are GC bookkeeping)
Step 1: all heap objects start WHITE (unproven).
  heap:  A=white  B=white  C=white  X=white

Step 2: roots seed the frontier — roots’ targets become GREY.
  stack/globals ──→ enqueue GREY: {A, B}   (order conceptual)
  heap:  A=grey  B=grey  C=white  X=white

Step 3: scan GREY — follow outgoing pointers; first-seen targets turn GREY; finished nodes turn BLACK.
  scan A: no new edges ──→ A=black
  scan B: discovers C ──→ C=grey, then scan C ──→ C=black; B=black
  heap:  A=black  B=black  C=black  X=white

Step 4: GREY empty; remaining WHITE is unreachable.
  heap:  X=white ◄── never reached from roots

(aha: “still white at end” means no path from roots existed during this cycle — safe to recycle X.)

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
MEMORY TRACE: mark phase (BFS/DFS — conceptual queue/stack)
Step 1: collect roots — every pointer live in goroutine stacks, globals, registers @ safepoint.
  stack @0x7fff_1000:  &A ──→ heap @0x1c000_0000
  globals @0x55aa_2000: &G ──→ heap @0x1c000_0100

Step 2: GREY frontier — each root’s object is reachable but not fully scanned.
  frontier (grey):  [ A, G ]   (order depends on traversal)

Step 3: pop GREY node, scan its outgoing pointers — each unseen target becomes GREY.
  scan A:  A ──ptr──→ B   (B first seen) ──► enqueue B as GREY
  heap marks:  A=grey→black (when A’s fields done), B=grey, …

Step 4: repeat until frontier empty — all reachable nodes end BLACK.
  (aha: marking is just graph traversal from roots; anything never visited is not reachable.)
```

### 4.2 Sweep phase: recycle the rest

After marking, **sweep** walks allocator structures and returns unmarked white memory to free lists or similar mechanisms so future allocations can reuse it.

```
MEMORY TRACE: sweep phase (after marking, X stayed WHITE)
Step 1: BEFORE SWEEP — allocator still holds dead object X’s span metadata.
  heap reachable (BLACK):  A ──→ B ──→ C
  heap garbage (WHITE):    X @0x1c000_00c0   ◄── no root path

Step 2: sweep walks allocator structures; unmarked objects return to free lists.
  sweep visits X @0x1c000_00c0 ──→ memory returned to allocator pool

Step 3: AFTER SWEEP — logical program graph unchanged for live data; X’s slot reusable.
  heap:  A ──→ B ──→ C     (X’s storage eligible for next allocation)

(aha: sweep does not “delete pointers”; it recycles memory backing objects proven unreachable.)
```

### 4.3 Stop-the-world (STW)

**STW** means: for a short window, **all goroutines are paused** so the runtime can move the GC through a delicate step safely.

Go’s GC is famous for **short STW**, not zero STW. Treat STW as real, measurable, and something you design around.

```
MEMORY TRACE: STW vs concurrent marking (logical mutator view)
Step 1: mutator running — stacks and heap mutate freely between GC cycles.
  stack: goroutine frames active   heap: objects allocated/mutated

Step 2: short STW — all Ps pause; roots scanned precisely; GC phase transition.
  (aha: even “concurrent” GC needs brief STW windows for correctness/barrier handoffs.)

Step 3: concurrent mark — mutator resumes with write barrier on; marker scans heap in parallel.
  stack/heap: mutator updates pointers ◄──► barrier records shade/references

Step 4: short STW — finalize marking/sweep handoff (details in T24); mutator pauses again briefly.

TIMELINE (not to scale)

app:  ████ run ████ run ████ run ████
gc:       ^STW^   concurrent mark    ^STW^
          short                  short
```

### 4.4 Concurrent marking and the write barrier

Modern Go does **much of marking concurrently** while your goroutines run. That creates a race: your program mutates pointers while the GC walks the graph.

The **write barrier** is instrumentation on pointer writes. It records just enough information so the GC cannot “miss” a newly created edge from black objects to white objects. You can treat it as **a tiny tax on pointer updates** that buys correctness during concurrent marking.

```
MEMORY TRACE: write barrier during concurrent marking
Step 1: marker has finished scanning B — B is BLACK (all outgoing edges were GREY/BLACK when scanned).
  heap:  B=black @0x1c000_0040   field next was nil (or old target already non-white)

Step 2: mutator runs concurrently — stores new pointer into BLACK object.
  stack:  tmp = &W @0x1c000_0200 (W still WHITE — not yet reached by marker)
  heap:   B.next ──store──→ W   (new edge BLACK ──→ WHITE)

Step 3 WITHOUT barrier (broken invariant): marker believes “all live refs from B” already processed.
  (aha: W could stay WHITE and be swept while still reachable from B — use-after-free class bug.)

Step 4 WITH write barrier: on B.next = W, runtime shades W (GREY) or logs edge so marker revisits.
  heap after barrier:  W=grey (or enqueued for scan) ◄── W cannot be swept while reachable

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

```
MEMORY TRACE: per-iteration heap allocation (GC pressure)
Step 1: enter iteration i — stack frame holds loop variable i, local b (slot empty).
  stack @frame+0x10:  i = 0..N-1
  stack @frame+0x20:  b (slice header, not yet filled)

Step 2: make([]byte, 1024) — new backing array on heap; slice header on stack points to it.
  heap @0x1c000_1000+i*0x400:  [1024]byte backing array (new object every i)
  stack @frame+0x20:  b.ptr ──→ heap backing @0x1c000_1000+…   b.len=1024 b.cap=1024

Step 3: previous iteration’s b is dead if not saved — old backing becomes garbage unless rooted elsewhere.
  heap: older backings WHITE after last reference drops ◄── more objects to mark/sweep later

Step 4: N iterations ⇒ N distinct heap objects (high allocation rate).
  (aha: each new backing raises live/total heap bytes and the GC’s future work — pacing fires more often under pressure.)

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

```
MEMORY TRACE: BAD pattern — per-iteration transient string on heap
Step 1: for each s, strings.ToUpper allocates a new string; data lives on heap.
  stack:  s (string header) points to parts[i] backing
  heap:   NEW string @0x1c000_2000 — ToUpper copies bytes here

Step 2: sb.WriteString copies again into Builder’s growing buffer — double traffic.
  heap:  Builder.buf may reallocate several times ◄── each growth can abandon old backing arrays

Step 3: after iteration, temporary ToUpper string becomes garbage unless retained.
  heap:  many short-lived WHITE objects between cycles ◄── high GC pressure

MEMORY TRACE: BETTER pattern — bytes flow into Builder without per-part string object
Step 1: upperASCII + WriteByte — no new heap string per iteration (conceptually stack/registers only).
  stack:  byte scratch from s[i]   heap:  only Builder’s internal buf grows

Step 2: fewer distinct heap objects survive each iteration.
  (aha: lowering allocation rate throttles how often the pacer starts / assists GC.)

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
