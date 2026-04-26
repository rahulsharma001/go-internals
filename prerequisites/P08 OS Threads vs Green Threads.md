# P08 OS Threads vs Green Threads

> **Prerequisite note** — complete this before starting [[T14 GMP Scheduler]].
> Estimated time: ~15 min

---

## 1. Concept

An **OS thread** is a unit of execution the **kernel** schedules on a CPU. The kernel allocates a large per-thread stack, tracks kernel state for the thread, and performs expensive context switches when it moves the CPU from one thread to another.

A **green thread** is a user-space thread the **language runtime** schedules. The kernel does not schedule individual green threads. The runtime multiplexes many green threads onto a smaller pool of OS threads.

> **In plain English:** Think of **OS threads** as **highway lanes**. Think of **goroutines** as **cars**. You do not need one lane per car. Most cars are **parked** most of the time, waiting on lights, loading zones, or passengers. A small number of lanes can serve a huge parking lot if the runtime keeps traffic moving and reuses lanes efficiently.

---

## 2. Core Insight (TL;DR)

**OS threads are kernel-managed, stack-heavy, and costly to create and switch.** **Green threads such as goroutines are runtime-managed, start with tiny stacks, and switch mostly in user space** so you can run **huge concurrency** with **few underlying OS threads**. **True parallelism across cores still requires multiple OS threads**; in Go, **GOMAXPROCS** sets how many OS threads can execute Go code at once.

---

## 3. Mental Model (Lock this in)

### Highway analogy expanded

```
HIGHWAY ... CPU-bound work that actually moves
  LANE  = OS thread ... kernel schedules this on a core
  CAR   = goroutine ... runtime schedules this onto a lane

Most cars are NOT cruising at top speed.
They are waiting: network, disk, locks, channels, timers.

So: many parked cars, few moving lanes, still feels "busy"
    because the parking lot is huge.
```

### ASCII comparison table

```
+------------------+---------------------------+---------------------------+
|                  | OS thread                 | Goroutine in Go           |
+------------------+---------------------------+---------------------------+
| Stack (typical)  | ~1-8 MB, commonly MB-scale| ~2-8 KB initial segment   |
|                  |                           | grows when required       |
+------------------+---------------------------+---------------------------+
| Create/destroy   | Heavy: kernel structures  | Light: runtime allocates  |
|                  | + accounting              | small stack + descriptor  |
+------------------+---------------------------+---------------------------+
| Switch cost      | ~1-10 µs typical ballpark | ~200 ns order of magnitude|
|                  | kernel path + cache/TLB   | in-process cooperative +  |
|                  | effects vary by workload  | small scheduler work      |
+------------------+---------------------------+---------------------------+
| Who schedules?   | Kernel                    | Go runtime schedules Gs;  |
|                  |                           | kernel still schedules Ms |
+------------------+---------------------------+---------------------------+
| Visible to       | Yes in perf, gdb, top     | Ms show up; individual Gs |
| `top`/`ps`?      |                           | do not map 1:1 in `ps`    |
+------------------+---------------------------+---------------------------+
```

### M:N mapping

In Go scheduler vocabulary, **M** names an **OS thread** that executes goroutines. **P** and **G** show up later in [[T14 GMP Scheduler]]. For this prerequisite, lock in the idea: **many Gs**, **few Ms**.

```
Many goroutines  ---- multiplexed onto ---->  fewer OS-thread Ms

     g g g g g g g g g g g g g g g
       \ \ \ \ \ | | | | | | | | /
        \ \ \ \ \| | | | | | | /
         v v v v v v v v v v v
         M M M M M M M M M M M
              ^   ^   ^
              |   |   |__ count follows GOMAXPROCS and runtime policy,
              |   |       not "one M per g"
              |   |
              v   v
           [ CPU cores / kernel run queue ]
```

> **In plain English:** **Many goroutines** time-share a **small pool of OS threads**. When one goroutine waits, the OS thread can run a **different** goroutine. You pay the **big** OS-thread costs only **N** times, not once per goroutine.

---

## 4. How It Works

### 4.1 OS thread lifecycle

```
CREATE THREAD
   |
   v
Kernel allocates:
  - kernel thread struct
  - kernel + user stacks; footprint varies by OS and config
  - scheduling entity on run queue
   |
   v
RUNNING on a core; kernel picks what runs
   |
   +--> BLOCKED on I/O wait, futex, and similar --+
   |                                            |
   +--> READY when runnable again --------------+--> back to RUNNING
   |
   v
EXIT: teardown + bookkeeping
```

**Error-driven intuition:** If your design creates a thread per incoming request, you can hit **thread count limits**, **memory pressure from stacks**, and **scheduler overhead** long before you run out of "logical work."

### 4.2 Context switch cost

When the kernel switches between OS threads on a core, it must **save and restore** register state, update kernel bookkeeping, and often pay **cache and TLB** effects. **Rule of thumb:** roughly **1-10 microseconds** for the switch itself; **downstream** cost can dominate if **working sets** no longer fit cache.

```
Thread A running on Core 0
        |
        |  timer interrupt / syscall / preemption
        v
Save A's registers -> pick Thread B -> restore B's registers
        |
        v
Thread B running on Core 0

Caches may now be "cold" for B's memory.
TLB entries may be less helpful after the switch.
```

### 4.3 Green thread mechanics

A green thread is a **runtime object** with:

```
+----------------------------------+
| goroutine descriptor             |
|  - stack bounds                  |
|  - saved registers while parked  |
|  - status: runnable / waiting    |
|  - scheduler links               |
+----------------------------------+
```

**Switching** often means: save a **small** register set to the goroutine struct, pick another runnable goroutine, restore its registers, continue in user space **without** asking the kernel to create a new OS thread.

**Error-driven intuition:** If you wrongly assume every goroutine is a **new** OS thread, you will **overestimate** memory use and **underestimate** how many concurrent tasks Go can track.

### 4.4 M:N multiplexing

```
Time ---->

OS thread M1:  [g3][g7][g1][g3 resumes][g9]...
OS thread M2:  [g2][g2][g8][g8][g4]...

Many goroutines interleave on each M.
Only some goroutines are actively executing at a given instant.
```

Blocking operations are the key: **waiting** goroutines **release** their M to run **other** goroutines.

### 4.5 GOMAXPROCS and CPU parallelism

**GOMAXPROCS** sets the **default** number of OS threads that can execute user-level Go code **simultaneously** across available logical CPUs. It does **not** cap how many goroutines exist.

```
GOMAXPROCS = 4   ... illustrative only

At most ~4 pieces of Go code "in flight" on CPU at once
for the scheduler's P/M arrangement,

while thousands of goroutines may exist total.
```

**Interview nuance:** **Parallelism** needs **multiple** executing OS threads. **Concurrency** is a broader pattern: many tasks **in progress**, not necessarily all on-CPU at once.

### 4.6 Peer runtimes at a glance

The point is not to memorize release dates. The point is to **place Go** on a map: **who schedules what**, and **where** parallelism actually comes from.

```
                    KERNEL KNOWS ABOUT          USER-SPACE SCHEDULER
                    EACH UNIT?                  MULTIPLEXES HEAVILY?
                    -----------                 ---------------------
Java platform       yes: 1:1 OS threads        JVM still maps to OS threads
Java virtual        yes at bottom             yes: huge stacks of cheap tasks
Python CPython      OS threads exist          GIL caps bytecode parallelism
Node.js             one main OS thread        event loop + callbacks/promises
Erlang              OS threads for VM         millions of lightweight processes
Go                  OS threads = Ms           goroutines on Ms + netpoller story
```

**Java before virtual threads:** A straightforward mental model is **platform threads** as **thick** OS-level units. You can create many, but you will feel **memory** and **scheduler** pressure if you pretend they are free like goroutines.

**Java virtual threads:** The runtime **stacks** enormous **logical** concurrency onto **fewer** carrier threads. Interview phrase: **mount** many virtual threads on a **small** OS-thread pool. The **shape** rhymes with Go even if the implementation details differ.

**Python and the GIL:** CPython **bytecode** execution is **serialized** by the **Global Interpreter Lock** for many core paths. OS threads exist, yet **CPU-bound Python threads** often fail to speed up **pure Python** numeric loops the way **independent** native threads would. **IO** can still overlap with threads and libraries that **release** the GIL.

```
Thread-1  [|||||python bytecode|||||][  wait  ]
Thread-2           [|||||python bytecode|||||]

Those "|||||" regions cannot execute on two cores at once
for typical pure-Python CPU work under the GIL story.
```

**Error-driven intuition:** If you spawn **10** Python threads for a **CPU-heavy** loop and expect **10x**, you may measure **~1x** and blame the wrong layer. The fix is **multiprocessing**, **native extensions**, or a **different** runtime — not "more threads" alone.

**Node.js:** The classic model is **one** main **JavaScript** execution thread plus an **event loop**. **Concurrency** comes from **non-blocking IO** and **callbacks** or **async**/`await` state machines, not from **spawning** one OS thread per request.

```
[ JS thread ]  <-- single lane for your JS bytecode execution
      |
      +---- epoll/kqueue/etc. wakes you when sockets ready

Thousands of "in flight" requests can exist
without thousands of OS threads for JS stacks.
```

**Error-driven intuition:** If you **block** the event loop with a **CPU** burn or a **synchronous** file read on the wrong API, you **freeze** everyone behind you. The ecosystem answer is **worker threads** or **splitting** processes — different tradeoffs than goroutines, same **lesson**: **cheap concurrency** requires **disciplined** blocking rules.

**Erlang processes:** **BEAM** schedules **massive** counts of **lightweight processes** with **small** per-process heaps in the **actor** style. **Parallelism** still lands on **real** CPU cores via **OS threads** inside the VM, but **your** unit of concurrency is **not** a **1 MB** POSIX thread stack per actor.

```
Erlang world:

  process process process process ...
       \         |        /
        \        |       /
         BEAM schedulers on OS threads
```

> **In plain English:** **Go** is not unique in wanting **millions** of cheap tasks. **Erlang** and **virtual threads** push the same **economic** idea. **Node** gets there with **one** JS lane plus **async IO**. **Classic Java threads** and **Python's GIL story** teach the **pain** of treating **OS threads** as **unlimited** scratch paper.

### 4.7 Why Go bet on this shape

```
Goals in one screenful:

  * millions of goroutines for connection-style servers
  * `go func()` as a low-ceremony fork
  * blocking reads look synchronous in user code
    while runtime parks goroutines cheaply
```

**Error-driven lesson:** If you **disable** parallelism accidentally, you still keep **concurrency**. If you spawn **infinite** CPU-bound goroutines, you still **saturate** cores. **Green threads** fix **waiting**, not **physics**.

---

## 5. Key Rules & Behaviors

### OS threads are expensive

```
One OS thread ~= big stack + kernel entity + heavier switches

     $$$$  per thread ... memory plus scheduler tax add up fast
```

> **In plain English:** Treat an OS thread like **leasing a full-size truck** for every errand. It works, but the fleet gets **expensive** fast.

### Goroutines are cheap

```
Many goroutines ~= small initial stacks + runtime bookkeeping

     $  per goroutine at creation ... not free, yet tiny next to an OS thread
```

> **In plain English:** Goroutines are closer to **handing out numbered tickets** at a deli counter than **building a new lane** for each customer.

### M:N model: many goroutines, few OS threads

```
        g's ... many
          |
          v
        M pool ... fewer
          |
          v
      CPU cores
```

> **In plain English:** The **runtime** is the **traffic cop** in the parking lot. The **kernel** only polices the **lanes**.

### GOMAXPROCS controls simultaneous OS-thread execution of Go code

```
Raise GOMAXPROCS  -> more OS parallelism opportunity for CPU work
Lower GOMAXPROCS  -> less parallel CPU execution; not a goroutine limit
```

> **In plain English:** **GOMAXPROCS** dials **how many lanes** the runtime tries to use for **actually driving**, not **how many cars** exist.

### Goroutine blocking does not necessarily block progress of the whole program

```
Goroutine waits on network
        |
        v
Runtime parks that goroutine
        |
        v
Underlying M runs a different goroutine.
Netpoller integration and thread handoff also matter for I/O; [[T14 GMP Scheduler]] fills that in.
```

> **In plain English:** **Waiting** is not a **sin** in Go. **Parking** a waiter is the **feature**.

---

## 6. Code Examples

### Spawning many goroutines

```go
package main

import (
	"fmt"
	"sync"
)

func main() {
	const n = 100_000
	var wg sync.WaitGroup
	wg.Add(n)
	for i := 0; i < n; i++ {
		go func() {
			defer wg.Done()
		}()
	}
	wg.Wait()
	fmt.Println("done")
}
```

MEMORY TRACE:

Step 1: `main` runs as goroutine `G-main` on OS thread `M0`. Kernel has already given `M0` a **full-size pthread-style user stack** (order **~1–8 MB** depending on OS/ulimit). The heap holds `sync.WaitGroup` state and scheduler metadata; no extra goroutines yet.

```
Process (illustrative):
  text/data           ◄── program + runtime
  heap                ◄── `wg`, global state
  M0 stack [~1–8 MB]  ◄── kernel-mapped for this OS thread
  G-main stack        ◄── ~2–8 KB initial segment, runtime-grown if needed
```

Step 2: Each `go func()` creates `G₀…G₉₉₉₉₉`. Per goroutine: descriptor + **~2–8 KB** initial stack (runtime allocates; grows on demand). **100_000** such stacks are **~400 MB** order-of-magnitude *if* each stays tiny—vs **100_000 OS threads** at **~2 MB** average stack ⇒ **~200 GB** virtual stack footprint before you count TLS and kernel structs.

```
100_000 goroutines:
  Σ(initial G stacks)  ──→ ~100_000 × (~2–8 KB)  ◄── hundreds of MB, manageable on many machines
100_000 OS threads (hypothetical same pattern):
  Σ(per-thread stacks) ──→ ~100_000 × (~1–8 MB)   ◄── TB-scale address space / RLIMIT cliff
```

Step 3: Each child immediately `Done()`s and exits. Runtime frees or pools `G` stacks; `wg.Wait()` observes zero waiters. **M:N:** thousands of `G` completions interleave on **few** `M`s—no **1:1** `G`↔kernel thread mapping.

```
Scheduler view:
  G's completed in bursts  ──→  bound to ≤ GOMAXPROCS active runners on CPU at once
  context switches among G's on same M  ◄── mostly user-space (~100s ns class) vs kernel thread switch (~µs class + cache/TLB)
```

```
Aha: Fan-out to 100_000 tasks stayed in **runtime-sized** memory because each unit is a **kilobyte-scale** green thread, not a **megabyte-scale** OS thread stack.
```

**Error-driven contrast:** The same **pattern** with **100_000 OS threads** is not a fair fight. You will typically blow **memory** on stacks, hit **OS limits**, and spend time in **kernel scheduling** long before you finish.

### Why 100_000 OS threads is a trap

```go
// DO NOT RUN naively at full 100_000 on a typical laptop.
package main

import (
	"fmt"
	"sync"
)

func main() {
	const n = 100_000
	var wg sync.WaitGroup
	wg.Add(n)
	for i := 0; i < n; i++ {
		go func() {
			defer wg.Done()
			// Pretend this were a real OS thread per iteration:
			// you would need a different API and pay OS-thread costs each time.
		}()
	}
	wg.Wait()
	fmt.Println("done")
}
```

MEMORY TRACE:

Step 1: Identical **Go** layout as the previous example: **100_000** `G` records with **~2–8 KB** stacks and runtime descriptors. Kernel still sees only **few** `M` stacks (**~1–8 MB** each).

```
Actual memory story (this program):
  goroutine side  ──→ ~100_000 × (small stack + descriptor)
  OS thread side  ◄── O(GOMAXPROCS)-sized M stacks, not O(n)
```

Step 2: **Hypothetical** `pthread_create` per iteration: each new thread gets kernel bookkeeping + **default stack** often **megabytes**. Creation walks syscall paths; the global run queue holds **100_000** kernel schedulable entities.

```
If `go` → `pthread_create` mentally:
  thread 0 stack [~1–8 MB] ──→ 0x7f.... 
  thread 1 stack [~1–8 MB] ──→ 0x7f.... 
  ...
  thread 99999               ──→ address space + `/proc/self/status` VmRSS grows like a cliff
  context switches           ──→ kernel saves/restores full thread_t + MM state more often
```

Step 3: Comment in source is the lesson: **same syntax shape in Go** still maps to **green threads**; swapping APIs swaps **memory class** from **KB/G** to **MB/M**.

```
Aha: The trap is not the loop—it's **what each iteration allocates**. OS thread = **kernel stack + sched entity**; goroutine = **runtime slice + tiny stack**.
```

### Checking GOMAXPROCS

```go
package main

import (
	"fmt"
	"runtime"
)

func main() {
	fmt.Println(runtime.GOMAXPROCS(0))
}
```

MEMORY TRACE:

Step 1: `runtime.GOMAXPROCS(0)` only **reads** the parallelism limit; it does not allocate goroutines or grow the `M` pool beyond what the runtime already uses. **Heap / stacks unchanged** by this call except for any temporary args on the caller's stack.

```
Illustrative:
  GOMAXPROCS = N   ──→ at most **N** logical Ps driving **N** pieces of Go code on-CPU simultaneously (model detail in [[T14 GMP Scheduler]])
  goroutine count  ◄── **uncapped** by this setting; millions of Gs may exist while N Ms run bytecode
```

Step 2: On a laptop with 8 logical CPUs and default settings, print is often **8**. That means **up to ~8 parallel OS-thread runners** for **CPU-bound** Go work—not "8 goroutines max."

```
CPU parallelism budget:
  raise GOMAXPROCS  ──→ more M's may execute Go in parallel on different cores (if hardware/OS allow)
  lower GOMAXPROCS  ──→ fewer parallel runners; **does not** shrink existing G stacks or free parked Gs
```

```
Aha: **GOMAXPROCS** dials **how many OS-backed runners** can burn CPU at once; it is not a goroutine **count** knob or a memory **release** knob.
```

### Many waiters, few runners

```go
package main

import "time"

func main() {
	ch := make(chan struct{})
	for i := 0; i < 50_000; i++ {
		go func() {
			<-ch
		}()
	}
	time.Sleep(time.Second)
	close(ch)
	time.Sleep(100 * time.Millisecond)
}
```

MEMORY TRACE:

Step 1: **50_000** `go func()` launches. Each `G` allocates **~2–8 KB** initial stack + wait state pointing at channel `ch`. All block on `<-ch`; runtime marks them **waiting**, not **runnable**.

```
Channel waiters (conceptual per G):
  Gᵢ stack        ◄── ~2–8 KB (idle frame for `<-ch`)
  Gᵢ status       ──→ parked on `ch`'s receive queue
  backing M       ◄── few Ms still exist; **no** 50_000 kernel stacks for these waiters
```

Step 2: During `Sleep`, **no** 50_000 OS threads each hold **~1–8 MB** stacks blocked in the kernel. **M:N:** a small set of `M`s idles or runs other work; **context-switch savings** vs 50_000 futex-blocked pthreads are enormous (kernel thread switch + TLB/cache vs runtime dequeue of another `G` on same `M`).

```
If each waiter were OS thread k:
  Σ stacks  ──→ 50_000 × (~1–8 MB)  ◄── same cliff as 100_000-thread thought experiment, scaled
As goroutines:
  Σ stacks  ──→ 50_000 × (~2–8 KB)  ◄── parked cheaply in user heap / runtime structures
```

Step 3: `close(ch)` broadcasts; waiters become runnable, drain, exit. Memory for stacks returns to runtime pools.

```
M:N snapshot while parked:
  g g g … (50k waiting)  ──→ multiplexed onto ──→  M M … (few, ≤ GOMAXPROCS busy at once for runnable work)
```

```
Aha: **Blocking** in Go **parks** the **kilobyte-scale** goroutine; it does not force a **megabyte-scale** **dedicated** kernel thread per waiter.
```

**Error-driven reading:** This program is a **stress toy**, not a **template** for production logic. It exists to **contrast** **parked goroutines** with **parked OS threads**.

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

**Question A.** What is a reasonable expectation for `runtime.GOMAXPROCS(0)` on a machine with 8 logical CPUs if you never called `GOMAXPROCS` with a positive value earlier in `main`?

**Question B.** You launch **500_000** goroutines that **all** spin in a tight **empty `for {}`**. Does **green-thread cheapness** imply your laptop will stay **responsive**?

> [!success]- Answer
> **A.** It commonly reports **8**, matching the number of **logical CPUs** the Go runtime sees. This is **not** a promise about every environment; always measure in your deployment. The interview punchline: **default** `GOMAXPROCS` tracks **available logical CPUs** unless configured otherwise.
>
> **B.** No. **Cheap scheduling** does not erase **CPU contention**. Half a million **runnable** tight loops **fight** for **few** cores. Expect **latency collapse**, **thermal** throttling, and **preemption** traffic. **Cheap** means **cheap to park and switch**, not **free infinite compute**.

### Tier 2: Fix the Bug (5 min)

You wrote a benchmark-style loop. You spawn one goroutine per iteration to compute `i*i`, but your process becomes sluggish and memory grows far more than expected. You **intended** cheap concurrency, but you accidentally created **one OS thread per task** via a C library binding.

Which symptom triad best signals "I am actually making OS threads, not just goroutines" in production triage?

> [!success]- Answer
> Look for **thread count** in the OS exploding toward your task count, **resident memory** climbing roughly with **thread stack footprint**, and **context switch** metrics going nonlinear. Fix by **reusing** a worker pool, **batching** calls, or using an **async** interface that does not map 1:1 to OS threads. In Go specifically, **pure goroutines** should not create **one** OS thread **per** goroutine; if they do, something **outside** the Go scheduler model is pinning threads.

---

## 7. Gotchas & Interview Traps

```
TRAP: "Each goroutine is a thread"
REALITY: Goroutines are multiplexed; OS threads are the underlying carriers.

TRAP: "More goroutines always means more speed"
REALITY: CPU-bound work still needs cores; excess goroutines add scheduling work.

TRAP: "GOMAXPROCS limits goroutines"
REALITY: It shapes OS-thread parallelism for the Go scheduler model, not goroutine count.

TRAP: "Green threads mean free parallelism"
REALITY: Multiple cores still require multiple executing OS threads underneath.

TRAP: "Context switch is always ~X nanoseconds"
REALITY: OS switch costs vary; cache/TLB effects dominate many real workloads.
```

**CPU-bound goroutines can starve others** if work is not yielded and preemption is not helping your mental model. **IO-bound** workloads are where goroutines shine brightest in **throughput-per-thread** stories.

---

## 8. Interview Gold Questions (Top 3)

1. **Why can Go spawn hundreds of thousands of goroutines but spawning the same count of OS threads is unrealistic?**  
   Tie answer to **stack size**, **kernel scheduling entities**, **creation cost**, and **switch cost**.

2. **What does M:N mean, and what are M and N in plain language?**  
   **Many** user-space goroutines mapped onto **fewer** OS threads; goroutines **wait** cheaply while Ms keep cores useful.

3. **Why does Go still need GOMAXPROCS if goroutines are cheap?**  
   Because **parallel CPU execution** requires **multiple** OS threads executing at once; **GOMAXPROCS** configures that **parallelism** budget for the scheduler.

---

## 9. 30-Second Verbal Answer

**OS threads** are **kernel-scheduled** with **large stacks** and **microsecond-scale** context switches. **Goroutines** are **runtime-scheduled** **green threads** with **tiny initial stacks** and **hundreds-of-nanoseconds-scale** switching in typical discussions. Go uses **M:N multiplexing** so **many** goroutines share **few** OS threads, which fits **I/O-heavy** servers and simple **`go` syntax**. **GOMAXPROCS** sets how many OS threads run Go code **in parallel**, because **green threads alone** do not magically occupy **all cores** without that **underlying** thread pool.

---

> See [[Glossary]] for term definitions.
