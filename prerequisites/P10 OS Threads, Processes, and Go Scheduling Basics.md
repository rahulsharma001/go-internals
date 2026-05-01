# P10 OS Threads, Processes, and Go Scheduling Basics

> **Prerequisite note** — complete this before starting [[T13 Goroutine Internals]] and [[T14 GMP Scheduler]].
> Estimated time: ~25 min

---

## 1. Concept

Before GMP makes sense, you need one simple chain:

**Machine -> OS -> Process -> Thread -> Your code**

Go does not remove OS threads. Go uses them smarter by scheduling many goroutines on top of fewer threads.

---

## 2. Core Insight (TL;DR)

- A **process** is one running app instance (like your API service).
- A **thread** is one worker lane inside that process.
- Traditional multithreading asks the OS to manage lots of threads directly.
- Go creates many goroutines and maps them onto fewer OS threads.
- This gives you high concurrency without "one thread per task" overhead.

---

## 3. Mental Model (Lock this in)

Think of a mall food court:

- The whole food court building is the process.
- Each counter worker is a thread.
- Customer tickets are goroutines.

You can have 10,000 tickets waiting, but only a small number of workers actively serving at once.

### Mistake that teaches you

Wrong thought:
"If I create 20,000 goroutines, I created 20,000 OS threads."

Correct thought:
"I created 20,000 tasks. Go runtime schedules those tasks over a much smaller thread pool."

```text
Wrong picture:
  20,000 tasks -> 20,000 OS threads  (too heavy)

Go picture:
  20,000 tasks -> runtime queues -> small thread pool
```

---

## 4. How It Works

### 4.1 What is an OS process?

A process is your running program with:

- its own memory space,
- open files/sockets,
- one or more threads.

Example: your running Go HTTP service is one process.

```text
+-------------------------------------------------------+
| PROCESS: user-api-service                             |
|-------------------------------------------------------|
| Memory (heap, stacks)                                 |
| Open sockets (:8080, DB connection)                   |
| Threads                                                |
+-------------------------------------------------------+
```

### 4.2 What is an OS thread?

A thread is the thing the OS scheduler puts on CPU cores.

If you have 4 CPU cores, at most 4 threads can run truly in parallel at the exact same moment.

```text
CPU Cores: [Core0] [Core1] [Core2] [Core3]
Running now:  T1      T2      T3      T4
Waiting:      T5 T6 T7 ...
```

Key point: OS threads are not free. Creating and switching many threads has cost.

### 4.3 Multithreading in general (traditional model)

Traditional model in many systems:

1. Create thread(s) directly.
2. OS schedules those threads.
3. If threads block, you often create more threads to keep throughput.

```text
App work -> OS Thread 1
        -> OS Thread 2
        -> OS Thread 3
        -> OS Thread 4
        ...
        -> OS Thread N
```

This works, but becomes heavy if N gets very large.

### 4.4 How Go changes the model

Go adds a runtime scheduler layer between your tasks and OS threads.

```text
+------------------------------------------------------+
| OS                                                   |
|  +-----------------------------------------------+   |
|  | Go Process                                    |   |
|  |                                               |   |
|  |  +-----------------------------------------+  |   |
|  |  | Go Runtime Scheduler                    |  |   |
|  |  |  Goroutine Queue: G1 G2 G3 ... G20000  |  |   |
|  |  +-------------------+---------------------+  |   |
|  |                      |                        |   |
|  |                 OS Thread Pool (M)            |   |
|  |                 M1 M2 M3 M4                   |   |
|  +-----------------------------------------------+   |
+------------------------------------------------------+
```

You create many goroutines. Runtime decides which goroutine runs on which thread and when.

### 4.5 Where P fits in GMP

Now add P in one line:

- **G** = goroutine (task)
- **M** = machine (OS thread runner)
- **P** = processor context (scheduler slot with runnable queue)

Simple visual:

```text
G (tasks):      [G1 G2 G3 G4 G5 ...]
P (slots):      [P1] [P2] [P3] [P4]
M (threads):     M1   M2   M3   M4
CPU cores:      C1   C2   C3   C4
```

M needs P to run Go code. G waits in P queues until scheduled.

### 4.6 Concurrency vs parallelism (super simple)

- **Concurrency** = many tasks in progress (some waiting, some running).
- **Parallelism** = multiple tasks executing at the same exact time on different cores.

```text
Concurrency:
  10,000 tasks exist, mostly waiting on I/O

Parallelism:
  4 cores -> roughly 4 tasks running at one instant
```

Go is great at high concurrency. Parallelism is still limited by CPU cores and `GOMAXPROCS`.

### 4.7 Blocking I/O: why Go feels fast under load

If one goroutine waits on DB/network:

- that goroutine parks (wait state),
- thread can run another goroutine,
- service keeps moving.

```text
Before DB call:
  M1 running G_request_42

During DB wait:
  G_request_42 -> waiting
  M1 runs G_request_77
```

This is the core reason Go handles many slow connections well.

### 4.8 Why this helps compared to "thread per request"

If you forced one OS thread per request, memory and scheduling overhead grows too fast.
With Go, one goroutine per request is practical because goroutines are lightweight and park cheaply.

---

## 5. Key Rules & Behaviors

### Rule 1: Process is the container, thread is the runner

```text
Process = house
Threads = rooms where work happens
```

### Rule 2: OS schedules threads, Go schedules goroutines

```text
OS picks which thread runs on CPU.
Go runtime picks which goroutine runs on that thread.
```

### Rule 3: More goroutines != more CPU cores

```text
100,000 goroutines + 4 cores
=> huge concurrency, but limited true parallel execution
```

### Rule 4: Waiting tasks are normal

Most backend work waits on network, DB, cache, disk.
Go's scheduler is designed for this waiting-heavy reality.

---

## 6. Code Examples (Show, Don't Tell)

### Example A: goroutines are many, threads are fewer

```go
package main

import (
	"fmt"
	"runtime"
	"time"
)

func main() {
	for i := 0; i < 10000; i++ {
		go func() { time.Sleep(1 * time.Second) }()
	}
	time.Sleep(50 * time.Millisecond)
	fmt.Println("goroutines:", runtime.NumGoroutine())
}
```

```text
What to observe:
  goroutine count becomes very high quickly.
  Program still runs fine because these goroutines are mostly sleeping (waiting).
```

### Example B: control parallelism

```go
runtime.GOMAXPROCS(4)
```

```text
Meaning:
  Use up to 4 OS-thread execution lanes for Go code in parallel.
  This is not a goroutine limit.
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

If `NumGoroutine()` prints `15001`, does that mean 15001 CPU cores are busy?

> [!success]- Answer
> No. It means 15001 goroutines exist. Most may be waiting. Running in parallel depends on cores and `GOMAXPROCS`.

### Tier 2: Fix the Understanding Bug (5 min)

Buggy statement:
"Go replaces OS threads, so the kernel scheduler is not used anymore."

> [!success]- Answer
> Go still uses OS threads and kernel scheduling. Go adds runtime scheduling for goroutines on top of those threads.

---

## 7. Gotchas & Interview Traps

| Trap | Reality |
|---|---|
| "goroutine = thread" | goroutine is a runtime task; thread is an OS execution unit |
| "GOMAXPROCS limits goroutines" | it limits parallel Go execution lanes (threads running Go code) |
| "if I have many goroutines, I always get speed" | only if workload has useful parallel or overlapped waiting |
| "Go ignores OS scheduler" | Go cooperates with OS threads; it does not bypass the OS |

---

## 8. Interview Gold Questions (Top 3)

1. What is the difference between a process and a thread?
2. Why can Go handle many concurrent requests with goroutines?
3. What does `GOMAXPROCS` control and what does it not control?

---

## 9. 30-Second Verbal Answer

> A process is a running app, and threads are the execution workers inside it.  
> In traditional multithreading, the OS directly manages lots of threads, which gets heavy at large counts.  
> Go keeps OS threads, but introduces goroutines as lightweight tasks and schedules many goroutines over fewer OS threads.  
> That gives very high concurrency for backend workloads where many tasks are waiting on I/O.  
> Parallel CPU execution is still bounded by core count and `GOMAXPROCS`.

---

> See [[Glossary]] for term definitions.
