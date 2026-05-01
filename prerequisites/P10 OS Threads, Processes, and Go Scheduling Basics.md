# P10 OS Threads, Processes, and Go Scheduling Basics

> **Prerequisite note** — complete this before starting [[T13 Goroutine Internals]] and [[T14 GMP Scheduler]].
> Estimated time: ~35 min

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

## 2.5 Quick Visual Recap (2 min before interviews)

If you remember only one picture, remember this:

```text
Physical machine
  └─ OS (kernel scheduler)
      └─ Process: your-go-api
          ├─ Heap (shared objects)
          ├─ Thread stacks (one stack per OS thread)
          └─ Go runtime scheduler
              ├─ Goroutines: G1 G2 G3 ... G100000
              ├─ P slots:    P1 P2 P3 P4
              └─ M threads:  M1 M2 M3 M4 -> CPU cores
```

5 fast lines:

1. Process is the app container.
2. OS thread is what kernel runs on a CPU core.
3. Goroutine is lightweight work managed by Go runtime.
4. Go schedules many goroutines over fewer OS threads.
5. `GOMAXPROCS` controls parallel running lanes, not goroutine count.

One-line request trace:

```text
HTTP request -> handler goroutine runs -> DB call waits -> goroutine parks -> M runs other goroutine -> DB reply -> original goroutine resumes
```

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

### 4.2.1 How OS decides "this is a thread"

A thread becomes real when the program/runtime asks OS to create one.
At that point kernel creates a thread control record (conceptually):

- thread ID
- state (`running`, `runnable`, `blocked`)
- register snapshot
- stack pointer
- next instruction pointer
- scheduling info (priority, policy)

If this kernel record exists, it is a native OS thread.

```text
User code/runtime -> "create thread"
                 -> Kernel creates thread record
                 -> Thread is now schedulable on CPU
```

### 4.2.2 How OS decides where that thread runs

Very simple scheduler loop:

1. Core asks for next runnable thread.
2. Scheduler picks one from run queue.
3. Core runs it for a time slice.
4. On slice end/block/high-priority arrival, switch thread.

```text
Runnable Queue: [T1 T2 T3 T4 T5 ...]
Core0 picks T1
Core1 picks T2
Core2 picks T3
Core3 picks T4
```

### 4.2.3 How thread code is actually executed

Thread execution is "load its CPU state and continue."

Context switch in plain words:

- save old thread registers
- load new thread registers
- switch stack pointer
- jump to new instruction pointer

That is why too many thread switches hurt performance.

### 4.2.4 Stack vs heap for thread work

- **Thread stack:** function frames, local variables, return addresses.
- **Process heap:** dynamic/shared objects used across threads.

```text
Process Memory
+------------------------------------------+
| Heap (shared by all threads in process)  |
|  - request objects, caches, buffers      |
+------------------------------------------+
| Stack T1 (private)                       |
|  - handler locals, function frames       |
+------------------------------------------+
| Stack T2 (private)                       |
|  - other call chain locals               |
+------------------------------------------+
```

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

### 4.3.1 What is a thread pool

Thread pool means:

- create a bounded number of OS threads once,
- keep feeding tasks to those threads via queue.

```text
Task Queue -> [task1 task2 task3 ...]
               |    |    |
Thread Pool -> T1   T2   T3   T4
```

Why used:

- avoids creating/destroying threads repeatedly,
- avoids one-thread-per-task explosion,
- gives predictable resource usage.

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

### 4.9 Life of one request (the click section)

Trace: `HTTP request -> goroutine -> DB wait -> park -> resume`.

#### Step 1: Request arrives

- TCP connection accepted by server process.
- Go runtime has an OS thread (`M1`) running on a CPU core.
- Handler goroutine `G_req_501` starts running.

```text
OS
  Process: user-api
    Scheduler queues: [G_req_501, G_req_502, ...]
    M1 -> running G_req_501

Memory:
  Stack(G_req_501):
    - userID (local)
    - err (local)
  Heap:
    - request object
    - shared DB pool
```

#### Step 2: Handler reaches DB call

`G_req_501` executes `db.QueryContext(...)`.

- Request is now waiting for DB network response.
- `G_req_501` cannot continue immediately.

```text
Code path:
  handler() -> repo.GetUser() -> db.QueryContext()
```

#### Step 3: Goroutine parks

- Runtime marks `G_req_501` as waiting (parked).
- `M1` is freed to run another runnable goroutine (say `G_req_777`).

```text
Before park:
  M1 -> G_req_501 (running)

After park:
  G_req_501 -> waiting on DB socket
  M1 -> G_req_777 (running)
```

Important memory point:

- `G_req_501` stack is preserved (its function frames and locals remain).
- shared data (`db pool`, caches, request metadata objects) stay on heap as usual.

#### Step 4: DB response arrives

- OS/network event notifies runtime poller.
- Runtime marks `G_req_501` runnable again.
- It goes back to a run queue.

```text
Event: DB socket readable
G_req_501: waiting -> runnable
RunQueue: [..., G_req_501]
```

#### Step 5: Resume and respond

- Some available M (M1 or M2) picks `G_req_501`.
- Execution resumes after DB call.
- Handler builds response and returns.

```text
Resume point:
  row.Scan(...) succeeded
  write JSON response
  goroutine completes
```

#### One-line memory recap

- During wait, goroutine is not burning CPU.
- Its stack state is parked safely.
- Heap remains shared process memory.
- CPU thread is reused for other runnable work.

This is the core reason Go handles high I/O concurrency efficiently.

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

### Rule 5: Parked goroutine keeps state, not CPU

When parked, goroutine keeps its call state (stack + references), but does not consume a running CPU lane.

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

### Example C: one-request flow in code

```go
func GetUserHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	userID := r.URL.Query().Get("id") // stack local

	user, err := repo.GetUser(ctx, userID) // goroutine may park during DB wait
	if err != nil {
		http.Error(w, "not found", http.StatusNotFound)
		return
	}
	writeJSON(w, user)
}
```

```text
Walkthrough:
  1) handler goroutine starts on some M
  2) repo.GetUser -> db query
  3) goroutine parks while waiting for DB
  4) M runs some other goroutine
  5) DB reply arrives -> original goroutine resumes -> response sent
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
4. Where are thread execution values stored: stack or heap?
5. What exactly happens when a waiting goroutine resumes?

---

## 9. 30-Second Verbal Answer

> A process is a running app, and threads are the execution workers inside it.  
> In traditional multithreading, the OS directly manages lots of threads, which gets heavy at large counts.  
> Go keeps OS threads, but introduces goroutines as lightweight tasks and schedules many goroutines over fewer OS threads.  
> That gives very high concurrency for backend workloads where many tasks are waiting on I/O.  
> Parallel CPU execution is still bounded by core count and `GOMAXPROCS`.

---

> See [[Glossary]] for term definitions.
