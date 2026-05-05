# Worker Pool (fixed workers)

## 1. Core Idea (max 5–6 lines)

- **What:** Bound work with **N** long-lived workers draining a shared queue — never **M** goroutines for **M** jobs.
- **When:** Job runners, parsers, crawlers, “bounded concurrency” system-design follow-ups.
- **Key concept:** **`jobs` channel + N identical loops**; **sender closes** to signal EOF; **`WaitGroup`/wait** until workers exit; **`ctx`** for shutdown pressure.

---

## 2. Interview Traps

**Trap A — `wg.Add` inside the worker loop / mismatched with job count**

<details>
<summary>Show Answer</summary>

- **Why it fails:** `WaitGroup` counts **goroutines or logical tasks**, not arbitrary increments — easy to panic (“negative WaitGroup”) or hang forever if `Add`/`Done` pairs don’t match under concurrency.
- **How to fix:** `Add(1)` **once per worker** at spawn, `Done` in `defer` at end of that worker; or use a different sync primitive (e.g. one `Add` per job in **one** place with a clear contract). Don’t scatter `Add` in racy paths without a lock.

</details>

**Trap B — Closing the `jobs` channel from a worker, or double-close**

<details>
<summary>Show Answer</summary>

- **Why it fails:** **Only the sender** should `close` a channel. Workers are receivers — closing from them races with the producer, can panic, or leave other workers reading garbage state.
- **How to fix:** Producer (or the type that **owns** the send side) calls `close(jobs)` **exactly once** when it will not send again. If multiple senders, use `sync.Once` or merge sends first.

</details>

**Trap C — No `ctx` in the receive loop — can’t stop mid-queue under shutdown**

<details>
<summary>Show Answer</summary>

- **Why it fails:** `for range jobs` exits only when the channel is **closed**. If the service must drain **or** exit on SIGTERM, blocking only on `jobs` can delay shutdown for a long queue.
- **How to fix:** `select` between `jobs` and `ctx.Done()`. On cancel, **stop receiving** and return; document whether in-flight work is best-effort cancelled (depends on `process`).

</details>

**Trap D — Unbuffered `jobs` + single producer pattern that waits on workers incorrectly → deadlock**

<details>
<summary>Show Answer</summary>

- **Why it fails:** Classic circular wait — e.g. main sends jobs **while** holding something workers need, or `Submit` blocks synchronously on unbuffered chan while workers wait on another lock/channel order.
- **How to fix:** Draw the goroutine graph; often fix with **buffered** `jobs` (small backlog), or producer in its **own goroutine**, or separate **collect** step so nobody holds locks across sends.

</details>

**Trap E — Logging/recording results from workers without synchronization**

<details>
<summary>Show Answer</summary>

- **Why it fails:** Concurrent writes to `slice`/`map` → **data race** (`go test -race`), flaky tests, corrupted summaries.
- **How to fix:** Mutex around shared aggregate, channel of results merged by **one** goroutine, `atomic`, or `sync.Map` only when justified.

</details>

---

## 3. Implementation Task (mandatory)

**Topic:** fixed-size worker pool in Go.

**Inputs**

- Positive integer **`workers`** — exact goroutine count (cap).
- **`jobs <-chan Job`** — `Job` holds at least `ID int64` and a **payload** string (e.g. file path or request id).
- **`process(ctx context.Context, j Job) error`** — your business function (may sleep or do I/O); must respect **`ctx`** cancellation if you call blocking APIs that support it.

**Outputs**

- All jobs read from **`jobs`** are passed to **`process`** at most **once** (each job received at most once across the pool).
- When **`jobs` is closed**, workers finish **current** job if any, then exit — **no goroutine leak** (verify with `-race` / shutdown test).
- Optional exported helper: **`Run(ctx context.Context, workers int, jobs <-chan Job, process func(context.Context, Job) error)`** returning **`error`** only from **`ctx`** early exit if you choose that contract.

**Constraints**

- **Exactly `workers`** long-lived goroutines for the lifetime of `Run` — no “spawn per job”.
- Producer **closes `jobs`** after last send; **do not close** from workers.
- **`process`** errors may be **logged or counted**; define behavior explicitly (don’t silently swallow without a comment).

**Expected behavior**

- **`go test`** passes a test that: sends **100** jobs on **`jobs`**, waits for completion after **`close(jobs)`**, asserts **`processed == 100`** (use atomic or mutex counter inside tests).

> Do NOT refer to notes while implementing. Only check after failure.

---

## 4. Debug Scenario (mandatory)

**Failure symptom:** Tests hang forever under **`go test -timeout 5s`** — no panic, CPU mostly idle.

**Repro:** In your pool, the main test goroutine **waits** on a **`WaitGroup` or channel** that signals “all work done” **before** the producer **finishes sending** and **before** it **closes** `jobs`. Alternatively: workers use **`for j := range jobs`** but **nobody** ever **closes** `jobs` in the test.

**Task:** **Fix** the shutdown/close ordering so the pool always terminates after the last job is processed (or `ctx` is cancelled).

<details>
<summary>Show Answer</summary>

- **Root cause:** **No close on `jobs`** → `range`/`receive` never completes → workers block → `Wait` never unblocks. Or **wait on “done”** in the test **before** the send side has **closed** the work stream, so workers are still expected to read but the test is already waiting on the wrong end of the pipeline.
- **Correct fix:** **Single owner** rule: the **sender** closes `jobs` when no more jobs. In tests: send in a **goroutine** and `close(jobs)` after the send loop, **or** use a **deferred** `close` in the same flow that produced all jobs. Ensure `Wait` waits for **workers**, not for the producer to finish before `close` in a way that deadlocks. If using `ctx`, ensure workers **exit** on `ctx.Done()` and the test cancels or times out.

</details>

---

## 5. Optimized Approach / Solution Outline

Derive approach and complexity before opening.

<details>
<summary>Show Answer</summary>

- **Optimal pattern:** **N** workers, each running a loop: **receive** job (with optional **`select` + `ctx.Done()`**), **process**, repeat until `jobs` **closed** and channel drained.
- **Key idea:** **Multiplex M jobs onto N goroutines** — throughput bounded by N and work cost, not by M.
- **Data structures:** One **`chan Job`** (buffered or not per backpressure design); **`sync.WaitGroup`** to wait for N workers; optional **`errgroup`** for structured error return.
- **Time:** **O(M × T_process)** wall-clock with **N**-way parallelism (ideal **~M/N** if work is uniform). **Space:** **O(B + N)** if `jobs` buffer size B, else **O(N)** for goroutine stacks and small state.

</details>

---

## 6. Code (optional but preferred)

Idiomatic Go below — try implementing from §3 first.

<details>
<summary>Show Answer</summary>

```go
package pool

import (
	"context"
	"sync"
)

type Job struct {
	ID      int64
	Payload string
}

// Run starts exactly 'workers' goroutines that read from 'jobs' until it is closed.
// process is invoked with ctx; workers exit when jobs is closed and drained, or when ctx is cancelled.
func Run(ctx context.Context, workers int, jobs <-chan Job, process func(context.Context, Job) error) {
	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for {
				select {
				case <-ctx.Done():
					return
				case j, ok := <-jobs:
					if !ok {
						return
					}
					_ = process(ctx, j) // handle/log per your contract
				}
			}
		}()
	}
	wg.Wait()
}
```

**Note:** If `process` is long and you need **cooperative** cancel, pass a **child context** with timeout per job, or check `ctx` inside `process`. The `select` only helps between **jobs**; in-flight work still runs until `process` returns.

</details>

---

## 7. Verbal Answer (60–90 sec)

Deliver aloud without reading — open after.

<details>
<summary>Show Answer</summary>

- **Approach:** I’d run **N worker goroutines** pulling from a **single `jobs` channel**. The producer **owns sends** and **`close(jobs)`** when finished — that signals workers there’s nothing left so they can exit after draining.
- **Tradeoffs:** **Unbuffered** channels sync producer and workers (backpressure tight); **buffered** smooth spikes but can hide overload until the buffer fills. **Fixed N** caps tail latency vs resource usage — versus unlimited goroutines that look fast until the **DB** or **kernel** says no.
- **Why it’s “optimal” for the constraint:** We get **O(1)** worker count and predictable memory; work is **O(M)** to complete, wall time scales with **parallelism** and I/O, not with spawning **M** goroutines.

</details>

---

## 8. Follow-up Variations

**Variation 1 — Scaling:** “Throughput doubles at peak — how would you change the pool **without** spawning unbounded goroutines?”

**Variation 2 — Constraint:** “Job **results must be emitted in strict Job.ID order** — how does the pool change?”

<details>
<summary>Show Answer</summary>

1. **Scaling:** Raise **N** within machine limits, tune **`jobs` buffer**, shard across **multiple machines** or **partitions** with **consistent hashing**, or add **priority queues** — still **bounded** workers **per** shard.
2. **Ordered output:** Raw worker completion is **unordered** — buffer results in a **heap/map by ID** and emit from a **single merger goroutine**, or assign **partition by ID mod N** only if order constraints allow; strict global order usually needs **merge** or **sequence** discipline.

</details>

---

## 9. Definition of Done

- Solution works correctly on sample + edge tests (**empty jobs**, **workers > job count**, **large M**).
- **No hang** after **`close(jobs)`**; **`ctx` cancel** stops new work from being accepted in your design.
- **Optimal** for the problem class: **fixed N**, **O(M)** job handling, no **O(M)** goroutines.
- Can **explain** channel close ownership, **WaitGroup** vs per-job sync, and **backpressure** in **≤90 seconds**.
