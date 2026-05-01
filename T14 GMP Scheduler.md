# T14 GMP Scheduler

> **Reading Guide**: Read Sections 1-3 first (15 min) to lock the mental model.
> Then Sections 4-6 for internals + traces (25 min).
> Sections 7-12 are interview prep.
> Full Q&A bank is linked in Section 13.
> Still fuzzy? Re-read [[prerequisites/P10 OS Threads, Processes, and Go Scheduling Basics]] first.

---

## 0. Prerequisites

Complete these before this topic:

- [[prerequisites/P08 OS Threads vs Green Threads]]
- [[prerequisites/P10 OS Threads, Processes, and Go Scheduling Basics]]
- [[T13 Goroutine Internals]]

---

## 1. Concept

The **GMP scheduler** is Go runtime's system for running many goroutines on fewer OS threads while still using CPU cores effectively.

---

## 2. Core Insight (TL;DR)

GMP means:

- **G** = goroutine (unit of work)
- **M** = machine (OS thread runner)
- **P** = processor slot (runtime context with local run queue)

The scheduler tries to keep each P busy with runnable Gs.  
If one M blocks in syscall, P is detached and given to another M so the system keeps moving.

---

## 3. Mental Model (Lock this in)

Use this picture:

- Gs are food orders.
- Ms are chefs (real workers).
- Ps are cooking stations.

A chef cannot cook without a station.  
Orders wait in a station queue.  
If one chef gets stuck in storage, station is reassigned to another chef.

```text
Orders (G):    G1 G2 G3 G4 G5 G6 ...
Stations (P):  P1            P2
Chefs (M):     M1->P1        M2->P2
```

### Mistake that teaches you

Wrong thought:
"Goroutine runs directly on CPU."

Correct flow:
"G runs on M, but M must own a P to run Go code."

```text
Wrong:
  G -> CPU

Correct:
  G -> P queue -> M with P -> CPU
```

> **In plain English:** G is the task ticket, M is the worker, P is the workbench. No workbench, no Go work.

---

## 4. How It Actually Works (Internals) [INTERMEDIATE -> ADVANCED]

### 4.1 Runtime topology at startup

At process startup, runtime initializes scheduler structures.

- Number of Ps defaults to `GOMAXPROCS`.
- Runtime creates at least one M and the main G.
- Each P has a local run queue.

```text
Process start:
  GOMAXPROCS = 4
  Ps: P0 P1 P2 P3
  Ms: M0 initially active (others created on demand)
  Gs: Gmain + runtime goroutines
```

### 4.2 Scheduling loop (the heartbeat)

Each active M with attached P repeats:

1. Pick G from local P run queue.
2. If local queue empty, check global run queue.
3. If still empty, try work stealing from another P.
4. Run picked G for some time / until block / completion.

```text
M1 + P1 loop:
  local? yes -> run G42
  local? no  -> global?
  global? no -> steal from P2
```

This design reduces lock contention versus one global queue for everything.

### 4.3 Local queue + global queue

Why both?

- local queues are fast and mostly lock-light.
- global queue helps fairness and overflow handling.

```text
P0 local: [G1 G2 G3]
P1 local: []
Global:   [G8 G9]

P1 first checks local (empty), then global, then steals.
```

### 4.4 Work stealing (load balancing)

If P1 is idle and P0 is busy, P1 steals runnable Gs from P0.

```text
Before:
  P0: [G10 G11 G12 G13]
  P1: []

After steal:
  P0: [G10 G11]
  P1: [G12 G13]
```

This is how scheduler avoids one-core-busy / others-idle behavior.

### 4.5 Syscall handoff path

If running G makes blocking syscall:

1. M enters blocking kernel call.
2. P is detached from blocked M.
3. P is attached to another available/new M.
4. Other runnable Gs continue.

```text
Before:
  M0+P0 running Gread

Gread blocks in syscall:
  M0 blocked in kernel
  P0 detached -> attaches to M1
  M1+P0 runs Gother
```

This is the key production behavior that prevents one blocked call from stalling whole service.

### 4.6 Preemption in scheduler fairness

If a G runs too long (for example hot loop), runtime can preempt to give others CPU time.

Modern Go supports async preemption, improving fairness and tail latency.

```text
Gspin hogs CPU on P0
Scheduler preempts Gspin
Gapi gets turn on same P0
```

### 4.7 Netpoll integration

Many goroutines wait on network I/O.
Runtime netpoller tracks readiness and moves waiting Gs back to runnable when events arrive.

```text
Greq_501 waiting on socket
socket readable event arrives
Greq_501 -> runnable queue
M with P picks Greq_501 and resumes
```

---

## 5. Key Rules & Behaviors

### Rule 1: G needs M+P to execute

```text
G alone cannot run.
M without P cannot run Go user code.
```

### Rule 2: `GOMAXPROCS` controls P count

```go
runtime.GOMAXPROCS(4)
```

```text
P count becomes 4.
Up to 4 goroutines can execute Go code truly in parallel.
```

### Rule 3: Blocked syscall should not freeze scheduler

```text
Blocked M can lose its P.
P reassigned so runnable Gs continue.
```

### Rule 4: Work stealing is normal under uneven load

```text
Idle P steals from busy P.
This keeps CPU usage balanced.
```

### Rule 5: Parked goroutine keeps state, not CPU

```text
G waits with preserved stack state.
CPU lane reused for another runnable G.
```

---

## 6. Code Examples (Show, Don't Tell)

### Example A: Uneven task load and scheduler balancing

```go
package main

import (
	"fmt"
	"runtime"
	"sync"
	"time"
)

func main() {
	runtime.GOMAXPROCS(4)
	var wg sync.WaitGroup

	for i := 0; i < 20; i++ {
		wg.Add(1)
		id := i
		go func() {
			defer wg.Done()
			// Simulate uneven durations to trigger queue imbalance.
			time.Sleep(time.Duration((id%5)*40) * time.Millisecond)
			fmt.Println("done", id)
		}()
	}
	wg.Wait()
}
```

```text
Step trace:
  1) 20 goroutines become runnable.
  2) Ps pick from local/global queues.
  3) some tasks finish early, some remain.
  4) idle P can steal remaining work.
  5) all complete; waitgroup unblocks.
```

### Example B: Blocking path intuition

```go
func handler(repo *PostgresRepo, userID string) (User, error) {
	// goroutine runs on M+P
	user, err := repo.GetUser(userID) // may block in I/O syscall path
	if err != nil {
		return User{}, err
	}
	return user, nil
}
```

```text
Step trace:
  1) Ghandler running on M0+P0
  2) GetUser enters blocking I/O
  3) Ghandler waits; M0 may block
  4) P0 gets reassigned to M1
  5) M1+P0 runs other runnable goroutines
  6) I/O ready event -> Ghandler runnable
  7) any M with a P resumes Ghandler
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict behavior (2 min)

If `GOMAXPROCS=2` and you spawn 200 CPU-bound goroutines, how many execute in parallel at once?

> [!success]- Answer
> Roughly 2 at a time for Go code execution lanes. Others remain runnable/waiting in queues.

### Tier 2: Fix scheduler misunderstanding (5 min)

Statement:
"If one goroutine blocks in syscall, all goroutines on that process freeze."

> [!success]- Answer
> Incorrect. Runtime detaches P from blocked M and schedules other runnable goroutines using another M.

### Tier 3: Build It (15 min)

Build a small program with:

- `GOMAXPROCS(2)`
- 1 goroutine doing periodic I/O wait (`Sleep`)
- 1 goroutine doing CPU loop
- 1 goroutine ticker logging progress

Observe how scheduler keeps system responsive.

> Full solutions with explanations -> [[exercises/T14 GMP Scheduler - Exercises]]

---

## 7. Edge Cases & Gotchas

| Trap | Why it happens | Fix |
|---|---|---|
| "goroutine = thread" | skips M and P roles | always explain G -> P -> M |
| wrong `GOMAXPROCS` expectation | treated as goroutine cap | treat as parallel lane count |
| CPU-bound overload | too many runnable Gs thrash | bound workers; profile p99 |
| ignoring syscall behavior | assume blocked thread stalls all | mention P handoff in answers |
| fairness confusion | assumes strict round-robin | explain local queues + stealing + preemption |

> **In plain English:** GMP bugs in understanding are usually mapping bugs (who does what), not syntax bugs.

---

## 8. Performance & Tradeoffs

Scheduler design tradeoffs:

| Decision | Benefit | Cost |
|---|---|---|
| per-P local queues | low contention, better cache locality | balancing logic needed |
| work stealing | better core utilization | stealing overhead |
| syscall handoff | avoids global stalls | more runtime complexity |
| preemption | fairness and latency control | interrupt bookkeeping |

Production lens:

- Too many runnable CPU-heavy Gs can increase scheduling overhead.
- I/O-heavy workloads benefit strongly because parked Gs are cheap.
- Use profiling, not guesses, before tuning.

Useful commands:

```bash
GODEBUG=schedtrace=1000,scheddetail=1 go test ./...
go tool pprof -http=:0 http://localhost:6060/debug/pprof/goroutine
go tool trace trace.out
```

---

## 9. Common Misconceptions

| Misconception | Reality |
|---|---|
| "M is optional in GMP" | M is the actual OS thread runner |
| "P is a CPU core" | P is runtime scheduling context, not literal hardware core |
| "Go scheduler ignores OS scheduler" | Go schedules Gs on Ms; OS still schedules Ms on cores |
| "more goroutines always faster" | only if work is I/O-overlapped or parallelizable |
| "syscall blocks entire runtime" | runtime hands P to another M when possible |

---

## 10. Related Tooling & Debugging

- `GODEBUG=schedtrace=1000,scheddetail=1` for scheduler snapshots.
- `runtime.NumGoroutine()` for rough goroutine growth signal.
- goroutine/block profiles for waiting hotspots.
- `runtime/trace` to inspect scheduling timeline.

Use these when interview asks "how would you verify scheduler issues in production?"

---

## 11. Interview Gold Questions

### Q1: Why does Go need P in addition to G and M?

Because P carries local runnable queues and runtime execution context; decoupling P from M enables syscall handoff and efficient scheduling.

### Q2: What happens in GMP when a goroutine blocks in syscall?

Running M may block in kernel; runtime detaches P and reassigns it to another M so other runnable Gs continue.

### Q3: If `GOMAXPROCS=4`, can 10,000 goroutines still exist?

Yes. Goroutine count is independent. `GOMAXPROCS` controls parallel execution lanes, not task count.

---

## 12. Final Verbal Answer

> GMP is Go runtime's scheduler model: G is work, M is OS thread, P is runtime execution slot.  
> Goroutines wait in P queues, Ms execute them, and OS runs Ms on cores.  
> Local queues plus work stealing keep cores busy with low contention.  
> If one goroutine blocks in syscall, runtime detaches P and reuses it on another M, so the service keeps moving.  
> `GOMAXPROCS` sets parallel Go execution lanes, not goroutine count.

---

## 13. Comprehensive Interview Questions

> Full interview question bank (12 questions) -> [[questions/T14 GMP Scheduler - Interview Questions]]

Preview:

- Why does P exist separately from M?
- How does work stealing improve throughput?
- What exactly does schedtrace tell you?

---

> See [[Glossary]] for term definitions.
