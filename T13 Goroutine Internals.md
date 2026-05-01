# T13 Goroutine Internals

> **Reading Guide**: Sections 1-3 and 6 are your first read (20 min).
> Sections 4-5 deepen runtime understanding (15 min).
> Sections 7-12 are interview prep blocks.
> Section 13 links your full Q&A bank.
> Something not clicking? -> [[simplified/T13 Goroutine Internals - Simplified]]

---

## 0. Prerequisites

Complete these before this topic:

- [[prerequisites/P06 Function Call Stack]]
- [[prerequisites/P07 Functions, Closures & Variable Capture]]

---

## 1. Concept

A **goroutine** is a very lightweight unit of work that the Go runtime schedules on a smaller pool of operating system threads.

---

## 2. Core Insight (TL;DR)

The key idea is: **you create many goroutines, but only a limited number run at once**.  
Go's runtime scheduler maps goroutines to operating system threads using the **GMP (Goroutine-Machine-Processor) model**.  
If you understand how goroutines move between runnable, running, blocked, and waiting states, most interview questions become straightforward.

---

## 3. Mental Model (Lock this in)

Think of your service like a restaurant kitchen:

- Orders are goroutines.
- Chefs are OS threads.
- Cooking stations are processors in the runtime.

You can take 2,000 orders, but you might only have 8 chefs and 8 stations at once. Orders wait in queues and get picked up fast.

### Mistake that teaches you

You spawn a background goroutine in an HTTP handler and forget cancellation:

```go
func (s *UserService) SyncUser(ctx context.Context, userID string) {
	go func() {
		// long DB + network work
		s.repo.RefreshUserCache(userID)
	}()
}
```

What you'd expect: request returns quickly and background work is "free."  
What actually happens: under load, thousands of these pile up and hold memory, sockets, or DB capacity.

```text
Step 1: 200 requests/sec call SyncUser
  runnable goroutines: [g1 g2 g3 ... g200]

Step 2: each request starts one background goroutine
  runnable+waiting goroutines: [g1 ... g400]

Step 3: external dependency slows down
  waiting goroutines keep growing: [g1 ... g6000]  <-- leak pattern starts
```

Why: goroutines are cheap, not free. If they have no lifetime control, they can outlive request intent and leak work.  
Fix: pass context, enforce timeout, and bound worker concurrency.

> **In plain English:** A goroutine is like opening a new sticky note task. Sticky notes are cheap, but if you keep adding them and never close them, your desk becomes unusable.

---

## 4. How It Actually Works (Internals) [INTERMEDIATE -> ADVANCED]

### 4.1 The three runtime actors: G, M, and P

Go runtime source (`runtime/proc.go`, `runtime/HACKING.md`) models scheduling with three pieces:

- **G (goroutine):** one unit of work plus metadata (stack, state, program counter snapshot).
- **M (machine):** one OS thread that can run Go code.
- **P (processor):** runtime execution context with a local run queue.

No P, no user Go code runs. M needs a P to execute goroutines.

```go
func fetchUserAndOrders(userID string) {
	go loadUser(userID)   // G1
	go loadOrders(userID) // G2
}
```

```text
Step 1:
  G queue (P0): [G1, G2]
  M0 attached to P0

Step 2:
  M0 picks G1 to run
  G2 stays runnable in P0 queue
```

The takeaway: your `go` keyword creates G; scheduler decides when M+P run it.

### 4.2 Local run queues first, global queue second

Each P keeps its own runnable queue. This avoids one giant lock for all scheduling decisions.

Scheduler preference:
1. Take from current P local queue.
2. If empty, check global queue.
3. If still empty, steal work from another P.

```go
for _, tenantID := range tenantIDs {
	go processTenant(tenantID)
}
```

```text
Step 1:
  P0 local queue: [G1 G2 G3 G4]
  P1 local queue: []

Step 2:
  P1 runs out of work
  P1 steals half of P0 queue -> [G3 G4]

Step 3:
  both Ps keep CPUs busy with less lock contention
```

This is why goroutine scheduling scales well on multicore machines.

### 4.3 Blocking syscall path: P gets handed off

If a goroutine blocks in a syscall, the runtime tries hard to keep a P active with another M.

```go
func readProfile(path string) ([]byte, error) {
	return os.ReadFile(path) // may block in syscall
}
```

```text
Step 1:
  M0 + P0 running Gread

Step 2:
  Gread enters blocking syscall
  M0 is tied up in kernel wait

Step 3:
  runtime detaches P0 from blocked M0
  P0 attaches to M1
  M1 continues running other goroutines
```

This handoff is a core reason one blocked goroutine does not freeze your whole service.

> **In plain English:** If one chef goes to the storage room and gets stuck waiting, the cooking station is reassigned to another chef so orders keep moving.

### 4.4 Preemption: long-running goroutines can be interrupted

If one goroutine runs too long, scheduler can preempt it so others get CPU time.
Modern Go supports asynchronous preemption (introduced in Go 1.14 era and improved later), which helps avoid starvation from tight loops.

```go
func spin() {
	for {
		_ = 1 + 1
	}
}
```

```text
Step 1:
  Gspin runs continuously on P0

Step 2:
  scheduler requests preemption
  Gspin yields at a safe point

Step 3:
  another runnable goroutine gets CPU
```

Without this behavior, one bad loop could starve request handlers.

### 4.5 Goroutine stacks start small and grow

Each goroutine starts with a small stack (commonly described as around 2KB in many runtime talks; exact details can evolve across versions).  
When needed, runtime grows stack instead of reserving megabytes per goroutine.

```go
func recursiveDepth(n int) int {
	if n == 0 {
		return 0
	}
	return 1 + recursiveDepth(n-1)
}
```

```text
Step 1:
  G1 stack: [small initial stack]

Step 2:
  deeper calls need more frames
  runtime grows stack and copies frames safely

Step 3:
  function returns; goroutine continues with larger usable stack
```

This is the memory trick that makes huge goroutine counts practical.

---

## 5. Key Rules & Behaviors

### Rule 1: `go` only schedules work, it does not guarantee immediate execution

```go
go sendAuditLog("login")
fmt.Println("request done")
```

```text
Possible order:
  main prints first
  goroutine may run later
```

> **In plain English:** Writing `go` is like placing a task in a queue, not forcing it to run right now.

### Rule 2: Goroutine lifetime must be tied to cancellation or ownership

```go
func (h *UserHandler) GetProfile(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
	defer cancel()
	go h.metrics.PushAsync(ctx, "profile_request")
}
```

```text
Request ends -> context canceled
background goroutine sees Done() and exits
```

> **In plain English:** If you start a side task, also decide who is responsible for stopping it.

### Rule 3: Channel operations can park goroutines

```go
ch := make(chan string)
go func() { ch <- "ok" }()
msg := <-ch
```

```text
Unbuffered channel:
  sender waits until receiver is ready
  receiver waits until sender is ready
```

> **In plain English:** Unbuffered channels are a hand-to-hand pass. Both sides must arrive at the same time.

### Rule 4: Scheduler fairness improved, but correctness is still your job

```go
var hits int
for i := 0; i < 1000; i++ {
	go func() { hits++ }()
}
```

```text
Many goroutines may run "fairly",
but shared write without sync still races.
```

> **In plain English:** A fair turn system does not make unsafe shared data magically safe.

---

## 6. Code Examples (Show, Don't Tell)

### Example A: Work stealing in a worker pool

```go
type Job struct {
	ID string
}

func runWorkers(jobs []Job) {
	jobCh := make(chan Job, len(jobs))
	var wg sync.WaitGroup

	for i := 0; i < runtime.GOMAXPROCS(0); i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for job := range jobCh {
				_ = handleJob(workerID, job)
			}
		}(i)
	}

	for _, job := range jobs {
		jobCh <- job
	}
	close(jobCh)
	wg.Wait()
}
```

```text
Step 1: enqueue jobs quickly
  channel buffer has pending work

Step 2: workers pull jobs independently
  busy worker goroutines stay running

Step 3: when one worker empties local work,
  scheduler can run another ready worker on available P
```

Why this matters: interviewers often ask how Go keeps cores utilized with uneven work.

### Example B (trap): loop variable capture in goroutines

```go
for _, userID := range []string{"u1", "u2", "u3"} {
	go func() {
		fmt.Println("syncing", userID)
	}()
}
```

```text
Step 1:
  goroutines capture loop variable slot

Step 2:
  loop advances quickly

Step 3:
  many goroutines print same/final value (older Go behavior)
```

Correct pattern that is safe across versions and explicit in interviews:

```go
for _, userID := range []string{"u1", "u2", "u3"} {
	userID := userID
	go func(id string) {
		fmt.Println("syncing", id)
	}(userID)
}
```

### Example C: Leak-safe background worker

```go
func startCacheRefresher(ctx context.Context, repo *PostgresRepo) {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			_ = repo.RefreshActiveUsers(ctx)
		}
	}
}
```

```text
Step 1:
  goroutine blocks in select

Step 2:
  ticker wakes periodically for work

Step 3:
  cancel context -> Done fires -> goroutine exits cleanly
  <-- THIS is the leak prevention moment
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

```go
func main() {
	for i := 0; i < 3; i++ {
		i := i
		go func() { fmt.Println(i) }()
	}
	time.Sleep(50 * time.Millisecond)
}
```

> [!success]- Answer
> The program prints `0`, `1`, and `2` in non-deterministic order.  
> The order is not guaranteed because scheduler timing is not deterministic.

### Tier 2: Fix the Bug (5 min)

Buggy code:

```go
func fanout(reqs []Request, svc *UserService) {
	for _, r := range reqs {
		go svc.Process(r)
	}
}
```

Bug: no waiting, no cancellation, no concurrency limit.

> [!success]- Answer
> Use `context.Context`, `sync.WaitGroup`, and a bounded semaphore/channel to cap active goroutines; wait for completion or timeout before returning.

### Tier 3: Build It (15 min)

Build a tenant-aware worker pool:

- input: `[]Job`
- max workers: `runtime.GOMAXPROCS(0)`
- each worker honors context cancel
- collect first error and stop remaining work

> Full solutions with explanations -> [[exercises/T13 Goroutine Internals - Exercises]]

---

## 7. Edge Cases & Gotchas

| Trap | Why it happens | Fix |
|---|---|---|
| Fire-and-forget in handlers | Request finishes, background goroutine keeps running forever | tie work to `r.Context()` or dedicated worker service |
| Unbounded goroutine fan-out | every request starts more goroutines under load | add worker pool or semaphore |
| Main exits before workers finish | program exits and tears down process with active goroutines | use `WaitGroup` or explicit shutdown barrier |
| Assuming `go` means parallel | goroutine creation is async scheduling, not instant CPU execution | design with queueing and backpressure |
| Loop capture confusion in old code | closure reads changing loop variable | pass value explicitly into closure |
| Blocked sends on channel | receiver not draining channel | buffer, select with context, or close coordination |

> **In plain English:** Most goroutine bugs are not "Go is broken." They are lifetime bugs, ownership bugs, or backpressure bugs.

---

## 8. Performance & Tradeoffs

Your API service does 3k requests per second. Each request fans out to profile + payment + recommendation services.  
The real question is not "Are goroutines fast?" The real question is "Where does latency and memory blow up when load spikes?"

| Pattern | What it costs | You'd see this in... | Verdict |
|---|---|---|---|
| goroutine per small I/O task | tiny scheduling + stack overhead | parallel API calls in handler | ✅ usually worth it |
| unbounded goroutine fan-out | memory growth + downstream saturation | one request spawning hundreds of goroutines | ❌ dangerous |
| fixed worker pool | queueing delay under peak, but stable memory | batch jobs, webhooks, email delivery | ✅ safer for sustained load |
| channel-heavy pipelines | channel coordination overhead | multi-stage event processing | ✅ good for clarity, profile if hot path |

What actually hurts: creating goroutines is rarely the main bottleneck. The common production issue is downstream saturation (DB pool, Redis, HTTP dependency) caused by too much concurrent demand.

What to measure:

```bash
go test -bench=. -benchmem ./...
go test -run TestHotPath -race ./...
go tool pprof -http=:0 http://localhost:6060/debug/pprof/goroutine
go tool pprof -http=:0 http://localhost:6060/debug/pprof/block
```

Also track:

- goroutine count (`runtime.NumGoroutine`)
- p99 (99th percentile latency)
- queue depth for worker channels

---

## 9. Common Misconceptions

| Misconception | Reality |
|---|---|
| "Goroutine = OS thread" | many goroutines are multiplexed onto fewer OS threads |
| "Goroutines are free" | they are cheap, but still consume memory and scheduler time |
| "If it compiles, goroutines are safe" | race conditions and leaks are runtime behavior bugs |
| "More goroutines always means more throughput" | too many can reduce throughput by contention and overload |
| "Scheduler fairness solves starvation completely" | it helps, but bad locking or blocking design still starves work |

---

## 10. Related Tooling & Debugging

- `go test -race ./...` catches shared-memory race bugs.
- `pprof` goroutine profile shows stacks of active and parked goroutines.
- block profile helps locate channel/mutex stalls.
- `GODEBUG=schedtrace=1000,scheddetail=1` gives scheduler snapshots every second.
- `runtime/trace` helps inspect scheduling timelines and blocking events.

Minimal scheduler trace run:

```bash
GODEBUG=schedtrace=1000,scheddetail=1 go test ./...
```

---

## 11. Interview Gold Questions

Research signals folded into this section:

- Community interview prep discussions repeatedly emphasize "explain concurrency decisions from production code," not just definitions.
- Long-running deep dives and runtime source walkthroughs consistently center on GMP, syscall handoff, and scheduler behavior under load.
- Common mistake threads repeatedly call out leak patterns, loop capture confusion, and missing shutdown synchronization.

### Q1: "Explain the GMP model and why Go needs all three."

Nuanced answer: G is the unit of work, M is the real thread, P is the scheduler context with local queue and runtime resources. Separating P from M lets Go detach execution context from blocked threads and keep running other goroutines.

Interview-ready verbal summary: "G is task, M is worker thread, P is the work station. If one worker blocks in syscall, the station can be reassigned."

### Q2: "What happens when a goroutine makes a blocking syscall?"

Nuanced answer: the running M can block in kernel; runtime detaches P and hands it to another M so ready goroutines continue. When syscall returns, old M must acquire a P again before running Go code.

Interview-ready verbal summary: "The runtime prevents one syscall from freezing everybody by moving P to a different M."

### Q3: "What goroutine mistakes have you seen in production?"

Nuanced answer (backed by current community threads): unbounded fan-out, request-scoped goroutines that outlive request cancellation, and missing drain/cancel paths on channels. Recent interview discussions also emphasize being able to explain tradeoffs, not just terminology.

Interview-ready verbal summary: "The killer bugs are lifetime and backpressure bugs, not syntax bugs."

---

## 12. Final Verbal Answer

If someone asks me "Explain goroutine internals," I'd say:

> A goroutine is a lightweight unit of work managed by the Go runtime.  
> The scheduler uses GMP: goroutines are queued on processors, and OS threads execute them.  
> This design lets Go run huge numbers of tasks while keeping a smaller number of real threads.  
> The important internals are local run queues, work stealing, syscall handoff, and preemption.  
> In production, the main risks are leaks and unbounded concurrency, so you always tie goroutine lifetime to context and use bounded worker patterns.

---

## 13. Comprehensive Interview Questions

> Full interview question bank (12 questions) -> [[questions/T13 Goroutine Internals - Interview Questions]]

Preview questions:

- How does work stealing reduce scheduler contention?
- Why does Go need both local run queues and a global run queue?
- What does goroutine profile growth usually indicate in production?

---

> See [[Glossary]] for term definitions.
