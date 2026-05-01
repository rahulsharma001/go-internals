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

### Example D: Go concurrency program #1 (I/O-style waiting) with comments on each line

```go
package main // declares the executable package

import ( // imports packages used by this file
	"fmt"     // prints logs to stdout
	"runtime" // reads and sets Go scheduler settings
	"sync"    // provides WaitGroup for goroutine coordination
	"time"    // provides sleep/timing utilities
)

func fakeDBCall(id int) string { // simulates a blocking I/O call
	time.Sleep(150 * time.Millisecond) // parks this goroutine while timer/network-like wait happens
	return fmt.Sprintf("user-%d", id)  // returns fake data after wait
}

func main() { // process entrypoint after runtime startup
	fmt.Println("start: goroutines =", runtime.NumGoroutine()) // prints initial goroutine count
	fmt.Println("GOMAXPROCS =", runtime.GOMAXPROCS(0))         // reads current parallel CPU lane count

	var wg sync.WaitGroup // tracks child goroutines so main waits correctly

	for i := 1; i <= 5; i++ { // creates 5 concurrent request-like tasks
		wg.Add(1) // increments wait counter before starting goroutine

		id := i // creates per-iteration copy to avoid closure capture confusion

		go func() { // starts a new goroutine (G) managed by Go scheduler
			defer wg.Done() // decrements wait counter when this goroutine exits

			fmt.Println("start task", id) // logs start of this goroutine's work

			user := fakeDBCall(id) // goroutine parks during sleep (simulated DB wait)

			fmt.Println("done task", id, "->", user) // logs completion after resume
		}() // immediately invokes anonymous function as goroutine body
	}

	wg.Wait() // blocks main goroutine until all child goroutines finish

	fmt.Println("end: goroutines =", runtime.NumGoroutine()) // should return near initial count
}
```

#### When you run it with `go run` (full cycle, step by step)

```text
Step 1: Shell executes `go run main.go`.
  - `go` tool compiles source to a temporary binary.
  - linker creates executable with Go runtime included.

Step 2: OS starts a new process for that binary.
  - process gets virtual memory space (code, heap, stacks).
  - initial OS thread is created by OS for process startup.

Step 3: Go runtime bootstrap runs before your main().
  - runtime initializes scheduler internals.
  - runtime reads CPU count and sets GOMAXPROCS default.
  - runtime creates initial scheduler state (G/M/P structures).

Step 4: runtime starts main goroutine (G_main) on an M with an attached P.
  - your main() begins executing.
  - `runtime.GOMAXPROCS(0)` reads already-initialized value.

Step 5: loop launches 5 goroutines.
  - each `go func` creates a new G and puts it in runnable queue.
  - available Ms with Ps pick runnable Gs.

Step 6: goroutines call `fakeDBCall` -> `time.Sleep`.
  - each sleeping goroutine transitions to waiting (parked).
  - OS thread M is not blocked permanently by that goroutine.
  - M runs other runnable goroutines.

Step 7: timer events fire after ~150ms.
  - parked goroutines become runnable again.
  - scheduler queues them; Ms pick and resume execution.

Step 8: goroutines print results and exit.
  - deferred `wg.Done()` executes on each goroutine exit.
  - wait counter reaches zero.

Step 9: main goroutine unblocks from `wg.Wait()`, prints final line, returns.
  - process exits when no non-daemon Go work remains.
  - OS reclaims process resources.
```

### Example E: Go concurrency program #2 (CPU-bound work + GOMAXPROCS) with comments on each line

```go
package main // executable package

import ( // imports needed packages
	"fmt"     // print logs
	"runtime" // scheduler/CPU controls
	"sync"    // WaitGroup sync
	"time"    // timing helper for rough benchmark
)

func cpuWork(n int) int { // CPU-heavy function to show parallel lane limits
	sum := 0 // local accumulator on goroutine stack
	for i := 0; i < n; i++ { // tight CPU loop
		sum += (i % 7) * (i % 11) // arithmetic keeps CPU busy
	}
	return sum // returns computed result
}

func main() { // entrypoint
	runtime.GOMAXPROCS(2) // explicitly sets two parallel execution lanes for Go code
	fmt.Println("GOMAXPROCS set to", runtime.GOMAXPROCS(0)) // verifies current setting

	start := time.Now() // captures start time for elapsed measurement

	var wg sync.WaitGroup // tracks worker completion
	results := make([]int, 4) // shared result slice allocated on heap

	for w := 0; w < 4; w++ { // starts 4 CPU-bound goroutines
		wg.Add(1) // increments wait counter
		idx := w // capture safe index copy

		go func() { // worker goroutine body
			defer wg.Done() // decrements counter on exit
			results[idx] = cpuWork(20_000_000) // runs CPU-heavy function
		}() // launches goroutine
	}

	wg.Wait() // waits until all CPU workers finish

	fmt.Println("elapsed:", time.Since(start)) // reports runtime
	fmt.Println("sample result:", results[0])  // prevents optimization-elision confusion
}
```

#### When you run this Go CPU example (how threads pick work)

```text
Step 1: `go run` compiles + links + launches process (same startup flow as Example D).

Step 2: runtime sets up scheduler.
  - you override default with `runtime.GOMAXPROCS(2)`.
  - this means at most two Ms run Go code in parallel at once.

Step 3: main goroutine launches 4 worker goroutines.
  - 4 goroutines become runnable.
  - only two can execute simultaneously (because GOMAXPROCS=2).
  - remaining runnable goroutines wait in run queues.

Step 4: as one running goroutine yields/completes time slice, scheduler picks next runnable one.
  - execution interleaves among all 4 workers.
  - true parallel execution lanes remain capped at 2.

Step 5: all workers eventually finish; `wg.Wait` unblocks; process exits.

Key learning:
  - Goroutine count (4 here, or 100k elsewhere) is not the same as parallel CPU lanes.
  - GOMAXPROCS controls parallel Go execution capacity.
```

### Example F: C++ concurrency example (thread pool style) with comments on each line

```cpp
#include <condition_variable> // thread wait/notify primitive
#include <functional>         // std::function for generic tasks
#include <iostream>           // console output
#include <mutex>              // std::mutex and std::unique_lock
#include <queue>              // task queue container
#include <thread>             // std::thread
#include <vector>             // worker thread storage

int main() { // process entrypoint
    std::queue<std::function<void()>> tasks; // shared task queue
    std::mutex mtx;                          // protects queue and stop flag
    std::condition_variable cv;              // wakes sleeping workers when tasks arrive
    bool stop = false;                       // signals worker shutdown

    const int workerCount = 3;               // fixed OS thread pool size
    std::vector<std::thread> workers;        // owns worker threads
    workers.reserve(workerCount);            // avoids vector realloc moves

    for (int i = 0; i < workerCount; ++i) {  // creates worker OS threads
        workers.emplace_back([&]() {         // thread entry lambda
            while (true) {                   // worker loop
                std::function<void()> task;  // local holder for one task

                { // start critical section
                    std::unique_lock<std::mutex> lock(mtx); // lock shared state

                    cv.wait(lock, [&]() { // sleep thread until task exists or stop is true
                        return stop || !tasks.empty();
                    });

                    if (stop && tasks.empty()) { // graceful shutdown condition
                        return;                  // exits this worker thread
                    }

                    task = std::move(tasks.front()); // take next task from queue
                    tasks.pop();                     // remove consumed task
                } // end critical section (unlock mutex)

                task(); // execute task outside lock for better concurrency
            }
        });
    }

    for (int j = 1; j <= 6; ++j) { // produce 6 tasks
        { // lock scope for queue push
            std::lock_guard<std::mutex> lock(mtx); // lock queue
            tasks.push([j]() {                     // enqueue one work item
                std::cout << "task " << j          // print task id
                          << " on thread "         // print execution context text
                          << std::this_thread::get_id()
                          << "\n";
            });
        } // unlock queue
        cv.notify_one(); // wake one sleeping worker thread
    }

    { // begin shutdown signal section
        std::lock_guard<std::mutex> lock(mtx); // lock shared stop flag
        stop = true;                           // tell workers to exit when queue drains
    } // unlock
    cv.notify_all(); // wake all workers so they can observe stop signal

    for (auto& t : workers) { // join all worker threads
        t.join();              // blocks until thread completes
    }

    std::cout << "all tasks complete\n"; // final status line
    return 0; // process exits
}
```

#### When C++ concurrency program runs (full cycle)

```text
Step 1: You compile binary (e.g. g++) and run executable.
  - OS starts process and initial main thread.

Step 2: `std::thread` creation asks OS for native threads.
  - each worker is a real kernel-scheduled OS thread.
  - each thread gets its own thread stack.

Step 3: workers block on `condition_variable::wait`.
  - blocked workers sleep at OS level until notified.

Step 4: main thread pushes tasks, calls `notify_one`.
  - one worker wakes, locks queue, pops task, executes.
  - OS scheduler decides which worker thread runs on which core.

Step 5: when all tasks dispatched, main sets stop=true and `notify_all`.
  - workers wake, see stop condition after queue drains, exit.

Step 6: main calls `join` on all worker threads and exits process.

Key contrast with Go:
  - C++ worker threads here are direct OS threads.
  - Go goroutines are runtime tasks multiplexed over fewer OS threads.
```

### Go vs C++ quick comparison (for interview answers)

| Dimension | Go goroutines | C++ `std::thread` model |
|---|---|---|
| Unit you create directly | goroutine (`go`) | OS thread (`std::thread`) |
| Who schedules units | Go runtime + OS threads | OS scheduler directly on threads |
| Typical scale | very high task count | lower thread count, often pooled |
| Waiting I/O behavior | goroutine parks, thread reused | thread usually blocked unless async framework used |
| Complexity | easier default concurrency ergonomics | powerful but more manual control burden |

### 60-second side-by-side execution timeline (memorize this)

```text
Go (`go run main.go`)                            C++ (`./app`)
----------------------------------------         ----------------------------------------
1) Tool compiles + links binary                  1) Binary already compiled (or compile first)
2) OS starts process + initial OS thread         2) OS starts process + main OS thread
3) Go runtime bootstraps G/M/P scheduler         3) No language runtime scheduler layer by default
4) main goroutine starts on M+P                  4) main thread runs main()
5) `go` creates many goroutines (G)              5) `std::thread` creates real OS threads
6) Gs enter runtime run queues                   6) Threads enter OS runnable/blocked states
7) Ms pick runnable Gs via Ps                    7) OS scheduler picks threads directly
8) I/O wait -> goroutine parks                   8) I/O wait -> thread often blocks
9) M immediately runs another G                  9) Blocked thread cannot run other task
10) event arrives -> G runnable -> resume        10) event arrives -> same thread wakes/resumes
11) all Gs done -> process exits                 11) join threads -> process exits
```

Fast memory hook:

- **Go:** "tasks are cheap; threads are reused."
- **C++ threads:** "threads are the tasks unless you build your own task runtime."

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
