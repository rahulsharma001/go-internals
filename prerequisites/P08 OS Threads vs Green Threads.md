# P08 OS Threads vs Green Threads

> **Prerequisite note** — complete this before starting [[T14 GMP Scheduler]].
> Estimated time: ~15 min

---

## 1. Concept

You have probably used **OS threads** before. Your language runtime asks the kernel for a thread. The kernel gives you a real scheduling unit: a big stack, kernel bookkeeping, and a slot on the CPU run queue. Switching the CPU from one OS thread to another is the kernel's job. It is not free.

A **goroutine** is like a super lightweight thread that **Go manages itself**. The kernel does not schedule individual goroutines. Go's runtime parks them, wakes them, and runs many of them on a small pool of OS threads. You still get blocking `db.Query()` and `http` handlers that *read* like normal synchronous code. Under the hood, waiting work gets out of the way so the same OS thread can run something else.

---

## 2. Core Insight (TL;DR)

**OS threads are heavy.** Big stacks, kernel involvement, expensive creation and context switches.

**Goroutines are cheap.** Tiny starting stacks, runtime bookkeeping, switches mostly in user space.

**Go maps many goroutines onto fewer OS threads (M:N).** That is why your HTTP server can have one goroutine per request, or your WebSocket layer can hold tens of thousands of idle connections, without spawning tens of thousands of kernel threads.

**Real parallelism across CPU cores still needs multiple OS threads running Go code.** In Go, **`GOMAXPROCS`** sets how many of those runners you use by default. It is **not** a cap on goroutine count.

---

## 3. Mental Model (Lock this in)

Picture your production service.

- **Each incoming HTTP request** often becomes its own goroutine (or sits on a goroutine that reads the request). Ten thousand slow clients do not mean ten thousand OS threads. They mean ten thousand goroutines that are mostly **waiting** on the network.
- **Each `db.Query` or `rows.Scan`** blocks *your* goroutine, not necessarily the whole process. While Postgres is thinking, that goroutine is **parked**. An OS thread that was running it can pick up **another** goroutine—another request, another query, a worker draining a channel.
- **Fifty thousand idle WebSockets** can be fifty thousand goroutines. You still only have a handful of OS threads actually executing Go code at once. The rest of the story is waiting and I/O.

The scheduler vocabulary you will see in [[T14 GMP Scheduler]]: **G** is a goroutine, **M** is an OS thread that runs Go code. Many **G**s, few **M**s. For now, that picture is enough.

```
                 Go runtime (user space)                    Kernel
  ┌─────────────────────────────────────────┐      ┌─────────────────────┐
  │  G1 (running)  G2 (parked on I/O)      │      │                     │
  │  G3 (runnable) G4 (parked on channel)  │      │   CPU core 0        │
  │  G5 (runnable) G6 (parked on I/O)      │──M1──│   CPU core 1        │
  │  G7 (parked)   G8 (parked)             │──M2──│                     │
  │  ...           ...                      │      │                     │
  │  G10000 (parked on I/O)                │      └─────────────────────┘
  └─────────────────────────────────────────┘
   10,000 goroutines → ~20 MB stack memory       2 OS threads (Ms) → ~2 MB stack memory
   Most are parked (waiting). Only a few          GOMAXPROCS controls how many Ms
   run Go code at any given moment.               execute Go code in parallel.
```

### The mistake that teaches you

```go
package main

import (
	"fmt"
	"runtime"
	"sync"
	"time"
)

func main() {
	fmt.Println("GOMAXPROCS:", runtime.GOMAXPROCS(0))
	fmt.Println("NumGoroutine before:", runtime.NumGoroutine())

	var wg sync.WaitGroup
	for i := 0; i < 10_000; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			time.Sleep(100 * time.Millisecond) // simulate I/O wait
		}()
	}

	fmt.Println("NumGoroutine during:", runtime.NumGoroutine())
	fmt.Println("NumCPU:", runtime.NumCPU())
	wg.Wait()
	fmt.Println("NumGoroutine after:", runtime.NumGoroutine())
}
```

**What you'd expect (if goroutines were OS threads):** 10,000 OS threads created, ~10 GB of stack memory reserved, likely hitting ulimit before finishing.

**What actually happens:** All 10,000 goroutines run fine. Memory stays in the tens-of-MB range. `NumGoroutine` shows 10,000+ but the process uses only a handful of OS threads (check with `runtime.NumCPU()` for GOMAXPROCS default). The program finishes in ~100ms.

**Why:** Goroutines start with ~2 KB stacks. 10,000 × 2 KB = ~20 MB. Most of those goroutines are parked in `time.Sleep` — they're not consuming OS threads. The Go runtime multiplexes them onto a small number of Ms. This is the M:N model in action.

---

## 4. How It Works

### 4.1 OS threads: what you are used to

When you create an OS thread (or your JVM or thread pool does), the kernel allocates a **large per-thread stack**—often on the order of **~1 MB** per thread on many 64-bit Linux setups unless you tune it. The thread is a first-class citizen in the scheduler. Context switches save and restore full register sets, update kernel structures, and often hurt cache warmth.

If you wrote a server that mapped **one OS thread per TCP connection**, you would feel it quickly: memory from stacks, OS thread limits, and scheduler overhead bite long before you run out of *ideas* for work.

### 4.2 Goroutines: cheap units the runtime schedules

A goroutine is a **runtime object**: small initial stack (on the order of **~2 KB** to start; it grows if your function calls go deep), saved registers when it is not running, and a status like runnable or waiting. Creating one is **`go func() { ... }()`**—low ceremony.

**Switching** between goroutines on the same OS thread is mostly **user-space** work: save a little state, pick the next **G**, restore, keep going. You are not paying for a full kernel thread switch every time.

### 4.3 Blocking and parking (the feature, not the bug)

When your handler calls **`http.ResponseWriter`** flushes, **`db.Query`**, **`conn.Read`**, or waits on a **channel**, your goroutine may **block**. The runtime marks it as waiting and **does not** waste an OS thread spinning. When the network packet, database reply, or channel send arrives, the goroutine becomes runnable again.

That is how you get **high concurrency with few threads**: most goroutines are parked most of the time. The ones that actually burn CPU share the cores; the ones waiting on I/O stay cheap.

### 4.4 GOMAXPROCS and real parallelism

**`GOMAXPROCS`** (default: number of logical CPUs on your machine) controls how many OS threads are in play to execute Go code **in parallel** on the CPU. On your **4-core** machine, the default is often **4**—so up to **four goroutines** can be executing Go bytecode **at the same instant** on different cores, in the rough mental model.

It does **not** limit how many goroutines exist. You can have **500k** goroutines and **`GOMAXPROCS=4`**. You simply have **four** hot runners for CPU-bound Go work; the rest are waiting or runnable in queues.

**Concurrency vs parallelism:** Many tasks **in flight** is concurrency. **Parallel** means **multiple cores** actually executing at once. Goroutines give you cheap concurrency; **`GOMAXPROCS`** and the **M** pool give you parallelism.

### 4.5 How this differs from classic Java (one paragraph)

**Java** (classic **platform threads**) is closer to the OS thread model: a thread pool with **200 threads** might mean **200 × ~1 MB** stacks before you count anything else, and the kernel is scheduling each of those threads. **Project Loom / virtual threads** move Java closer to the "many lightweight tasks, few carrier threads" story Go had from the start—but the contrast you should feel in your bones is: **in Go you routinely model each request or each connection as its own goroutine** without treating `new Thread` as a scarce resource.

### 4.6 Three backend shapes you actually ship

**HTTP / RPC front door.** You accept connections, hand work to goroutines, most of them spend their lives **waiting** on clients or backends. The win is **cheap parking**, not infinite CPU.

**Database-heavy middle tier.** Your handler goroutine calls **`Query`**, **`Exec`**, **`Begin`**. Each call may **park** the goroutine while Postgres or MySQL works. Same OS threads keep other requests moving. You write **straight-line** code; you do not manually thread-pool every query.

**Worker pool + channel.** You have **100 goroutines** pulling **`Job`** values from a **`chan Job`**. Maybe they call an external API, resize images, or enqueue to Kafka. If work is **mostly I/O**, **100 goroutines** on **few Ms** is normal. If work is **pure CPU**, **100** fighting for **`GOMAXPROCS`** cores buys you little—**cap** workers or shard across processes.

**Error-driven intuition:** Match **goroutine count** to **waiting**, not to "I want more speed." **CPU** needs **cores** and **bounded** parallelism.

---

### 4.7 Memory trace — Stacks: 10k threads vs 10k goroutines

You want **10,000** concurrent pieces of work—say 10k idle HTTP connections or 10k channel-backed jobs.

**If each unit were an OS thread** with **~1 MB** stack reservation (typical ballpark on Linux):

```
10,000 threads × ~1 MB stack ≈ ~10 GB address space (often reserved) just for stacks
Plus kernel thread structs, TLS, accounting — you hit limits and RSS pressure fast
```

**If each unit is a goroutine** with **~2 KB** initial stack (order of magnitude; grows only if needed):

```
10,000 goroutines × ~2 KB ≈ ~20 MB class for stack *starts* (plus per-G metadata on the heap)
Kernel still sees only a small number of OS threads (Ms), each with its own large pthread-style stack
```

Same *count* of logical workers. Totally different *memory* story. That is why Go servers talk about **10k concurrent connections** without bragging about **10k `pthread_create`** calls.

---

### 4.8 Memory trace — Parking: `db.Query` on a request goroutine

Your **`http.Handler`** runs on a goroutine—call it the **request goroutine**.

```
1. Request goroutine runs your handler code on OS thread M.

2. You call db.Query(...). Your goroutine needs rows from Postgres.
   While it waits for the network + server, the runtime parks THIS goroutine.
   It is not burning a CPU core in a busy-loop.

3. OS thread M is now free to run ANOTHER goroutine:
   another HTTP request, a worker reading from a channel, whatever is runnable.

4. Postgres responds; the runtime marks your request goroutine runnable again.
   Eventually M (or another M) resumes your handler past db.Query.

5. You write the response. Maybe tens of thousands of other goroutines did the same dance
   on the same handful of Ms while yours was parked.
```

The lesson: **waiting is cheap** in Go because **parking** is cheap. You are not dedicating a whole OS thread and **~1 MB** stack to every blocked database call.

---

## 5. Key Rules & Behaviors

### OS threads stay expensive

Treat every new long-lived OS thread as a big commitment. Thread pools exist because nobody wants a million kernel threads.

```go
// In C or Java, spawning 10k threads:
// for (int i = 0; i < 10000; i++) pthread_create(...)
// → ~10 GB virtual memory for stacks, scheduler thrashing, ulimit failures

// In Go, the runtime manages a small thread pool internally.
// You don't call pthread_create. You call: go func() { ... }()
```

```
OS thread cost per unit:
  Stack:    ~1 MB (reserved virtual memory, committed on use)
  Switch:   ~1-5 μs (kernel mode, full register save/restore, TLB flush risk)
  Create:   ~50-100 μs (kernel allocation, scheduler registration)
  
Goroutine cost per unit:
  Stack:    ~2 KB (grows as needed, shrinks on GC)
  Switch:   ~100-200 ns (user space, save 3 registers, pick next G)
  Create:   ~1-3 μs (runtime allocation, add to run queue)
```

**Why (Section 4.1, 4.2):** OS threads are kernel objects with full scheduling support. Goroutines are runtime objects scheduled in user space — orders of magnitude cheaper per unit.

### Goroutines stay cheap (but not magic)

Spawning `go func()` is cheap. But CPU work is still CPU work. A million goroutines all doing tight loops will still fight for `GOMAXPROCS` cores.

```go
// This creates 1M goroutines — fine for memory (~2 GB stack space).
// But if they all do CPU work, only GOMAXPROCS can run at once.
for i := 0; i < 1_000_000; i++ {
    go func() {
        heavyComputation() // CPU-bound
    }()
}
```

```
1M goroutines, GOMAXPROCS=4:
  ┌─────────────────────────────────┐
  │ 4 running on CPUs               │ ← actually executing
  │ 999,996 in run queue (waiting)  │ ← waiting for a turn
  └─────────────────────────────────┘
  Throughput ≈ same as 4 goroutines doing the work (for pure CPU).
  The extra 999,996 add scheduling overhead without adding speed.
```

**Why (Section 4.4):** Goroutines give you cheap *concurrency* (many things in flight). *Parallelism* (things actually running at the same time) is still limited by CPU cores and GOMAXPROCS.

### `GOMAXPROCS` dials CPU parallelism, not goroutine count

```go
runtime.GOMAXPROCS(2) // only 2 OS threads run Go code in parallel
// You can still have 100k goroutines. Most will be parked or queued.
```

```
GOMAXPROCS=2 on a 4-core machine:
  Core 0: M1 running goroutines  ✅
  Core 1: M2 running goroutines  ✅
  Core 2: idle (Go won't use it) 
  Core 3: idle (Go won't use it)
  
  100k goroutines still exist — they just share 2 runners.
```

**Why (Section 4.4):** GOMAXPROCS sets how many Ms (OS threads) actively execute Go code. It's a parallelism dial, not a concurrency cap.

### Blocking I/O parks the goroutine, not the thread

Your code blocks on reads and DB calls. The runtime makes that okay for throughput by parking goroutines and reusing threads. You don't need to rewrite everything as callbacks.

```go
// This looks blocking, but only parks the goroutine:
rows, err := db.QueryContext(ctx, "SELECT ...")
// While Postgres thinks, the OS thread runs another goroutine.
```

```
Before db.Query:        After db.Query starts:
  M1 → G_request         M1 → G_other (picked from run queue)
                          G_request: parked, waiting on network
                          
When Postgres responds:
  G_request → runnable → M1 (or another M) picks it up and resumes
```

**Why (Section 4.3):** The Go runtime's netpoller uses epoll/kqueue to know when I/O completes. It doesn't dedicate an OS thread to each blocked goroutine — it parks them and reuses threads for runnable work.

### When to worry

- **CPU-bound work**: you need cores, batching, or worker limits — not infinite goroutines.
- **Too many runnable goroutines**: scheduling overhead and latency spikes.
- **C extensions or blocking syscalls** that pin OS threads: these create thread pressure outside the M:N model. Profile and read [[T14 GMP Scheduler]] when you get there.

---

## 6. Code Examples (Show, Don't Tell)

### HTTP server: one goroutine per request (mental model)

The standard library accepts connections and handles each request with goroutines (details vary by API, but the **per-request goroutine** mental model is what you carry into production).

```go
package main

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"
)

var db *sql.DB // wired up in main

func main() {
	http.HandleFunc("/api/user", func(w http.ResponseWriter, r *http.Request) {
		// This handler runs on a goroutine.
		// Under load, thousands of these exist; only a few OS threads run Go code at once.
		var id int
		err := db.QueryRowContext(
			r.Context(),
			`SELECT id FROM users WHERE email = $1`,
			r.URL.Query().Get("email"),
		).Scan(&id)
		if err != nil {
			http.Error(w, "lookup failed", http.StatusInternalServerError)
			return
		}
		fmt.Fprintf(w, "%d", id)
	})
	log.Fatal(http.ListenAndServe(":8080", nil))
}
```

While **`QueryRowContext`** waits on Postgres, **your** request goroutine is **parked**. The OS thread that was running it can serve **another** request's goroutine. That is how one process keeps **10k slow clients** from turning into **10k kernel threads**.

### Worker pool: 100 goroutines, one job channel

You often cap **how much CPU-heavy work** runs at once, but the **goroutine count** can still be large if workers spend time waiting on **HTTP**, **S3**, or **message brokers**.

```go
package main

import "sync"

type Job struct {
	UserID int
	// ...
}

func process(j Job) {
	// Maybe call payment API, write audit row, push to queue — lots of waiting is typical.
}

// StartWorkers launches n goroutines; each pulls from jobs until the channel closes.
func StartWorkers(jobs <-chan Job, n int, wg *sync.WaitGroup) {
	for i := 0; i < n; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := range jobs {
				process(j)
			}
		}()
	}
}
```

**100 goroutines** here are **100 logical workers**, not **100 MB stacks × 100**. If **`process`** is **I/O-bound**, most of those goroutines are **parked** most of the time. If **`process`** is a **CPU furnace**, **`GOMAXPROCS`** still caps how much Go code runs **in parallel**—you tune **`n`** for queue depth and latency, not "more goroutines = more cores."

**Hundred goroutines** draining a channel is normal in Go. **Hundred dedicated OS threads** for the same pattern would be a harder conversation with **ops** and **ulimits**.

### WebSocket-style concurrency (sketch)

Thousands of connections each have a **read loop** goroutine. Most of the time those goroutines block in **`ReadMessage`**. You are not paying **50,000 × 1 MB** thread stacks for **50,000** quiet sockets.

### Checking `GOMAXPROCS`

```go
package main

import (
	"fmt"
	"runtime"
)

func main() {
	fmt.Println(runtime.GOMAXPROCS(0)) // 0 = read current setting; often == logical CPU count
}
```

On your **4-core** laptop, you will often see **4**. That means **four goroutines** can execute Go code **truly in parallel** at peak—not "only four goroutines allowed."

---

## 6.5. Practice Checkpoint

### Tier 1: Reason about the server (2 min)

You deploy an API behind `net/http`. At peak you have **8,000** open connections. Each connection is served by **one long-lived goroutine** waiting on reads most of the time.

**A.** Roughly how many **~1 MB** OS-thread stacks should you expect **just** because you have 8,000 goroutines?

**B.** You set **`GOMAXPROCS=4`** on a **4-core** box. Does that mean only **four** of your 8,000 connection goroutines can exist?

> [!success]- Answer
> **A.** You should **not** expect **8,000 × ~1 MB** from goroutines alone. Goroutines start around **kilobyte-scale** stacks; the process still has **a small number** of OS threads with large stacks, not one per connection.
>
> **B.** **No.** **`GOMAXPROCS`** limits how much **parallel CPU execution** Go uses, not goroutine count. You can have **8,000** parked goroutines and **`GOMAXPROCS=4`**. Thousands wait on I/O; up to **four** run CPU-heavy Go code at once on that setting.

### Tier 2: Worker pool intuition (5 min)

You process jobs from **`chan Job`**. You start **100** worker goroutines. Each worker spends **90%** of its time waiting on a **downstream HTTP call** and **10%** doing CPU work in **`process(j)`**.

**A.** Is the main win here "100 goroutines are cheaper than 100 OS threads," or "most workers are parked on I/O most of the time"?

**B.** You change **`process(j)`** to a **pure tight CPU loop** with no I/O, but keep **100** workers and feed jobs as fast as possible. What happens to CPU saturation and latency?

> [!success]- Answer
> **A.** Both matter, but the **I/O** picture is the **big** one: most workers are **blocked** waiting on the network, so **parking** goroutines and reusing a few **M**s is exactly what Go is good at. The **100 vs 100 OS threads** stack argument still holds, but the **scheduler story** is driven by **waiting**.
>
> **B.** You become **CPU-bound**. **`GOMAXPROCS`** cores saturate. Extra goroutines mostly **queue** and **fight** for time on those cores—throughput may plateau and **p99 latency** can spike. You would cap workers, batch, or scale out.

---

## 7. Gotchas & Interview Traps

| Trap | Reality | Why (Section link) |
|------|---------|-------------------|
| "Each goroutine is an OS thread" | **No.** Many Gs map onto few Ms. | M:N model — runtime schedules Gs onto a small pool of Ms (Section 4.2) |
| "More goroutines = always faster" | CPU work still needs cores. Too many runnable goroutines adds scheduling cost. | Goroutines give concurrency, not parallelism — GOMAXPROCS caps parallel execution (Section 4.4) |
| "`GOMAXPROCS` caps goroutines" | It shapes parallel OS-thread execution of Go code, not goroutine count. | GOMAXPROCS = how many Ms run Go code at once (Section 4.4, Section 5 Rule 3) |
| "Goroutines give free multi-core speedup" | Parallelism needs multiple Ms running; GOMAXPROCS and your workload determine that. | Concurrency ≠ parallelism — you need actual cores executing (Section 4.4) |
| "`db.Query` holds a thread so nobody else runs" | Your goroutine waits; the runtime runs other goroutines on the M. | Parking: blocked goroutine releases the M to serve other work (Section 4.3) |

---

## 8. Interview Gold Questions (Top 3)

**Q1: Why can Go run tens of thousands of goroutines but not tens of thousands of OS threads?**

Point to **small initial stacks** vs **~MB-scale thread stacks**, **runtime vs kernel scheduling**, **creation and switch cost**, and **parked I/O-heavy** workloads.

**Q2: What does M:N mean here?**

**Many** goroutines (**N**) multiplexed onto **fewer** OS threads (**M**). Waiting goroutines **release** their **M** to do other work.

**Q3: What does `GOMAXPROCS` do?**

Sets how many OS threads execute Go code **in parallel** across CPUs (default ≈ logical cores). Does **not** limit goroutines. Explains why your **4-core** box runs **four** goroutines **truly parallel** at peak, while **10k** others may wait.

---

## 9. 30-Second Verbal Answer

> "An OS thread is a kernel-scheduled entity with a large stack — about 1 MB — and creating or switching between them involves the kernel. It's expensive. A goroutine is Go's green thread: tiny starting stack of about 2 KB, scheduled entirely by Go's runtime in user space, and dirt cheap to create and switch.
> 
> Go uses an M:N model — many goroutines multiplexed onto a few OS threads. That's why your HTTP server can have 10,000 concurrent connections without 10,000 kernel threads. Most of those goroutines are just waiting on I/O, and waiting is cheap because the runtime parks them and reuses the OS thread for other work.
> 
> GOMAXPROCS controls how many OS threads actually execute Go code in parallel — it defaults to your core count. So on a 4-core machine, up to 4 goroutines run truly in parallel at any instant. The other thousands just wait their turn or stay parked on I/O. Goroutines make concurrency cheap, but they don't give you more CPU cores."

---

> See [[Glossary]] for term definitions.
