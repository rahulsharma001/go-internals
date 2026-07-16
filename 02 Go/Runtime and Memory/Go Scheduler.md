---
type: canonical
domain: go
topic: go-scheduler
status: learning
aliases:
  - T14 GMP Scheduler
source_notes:
  - "[[99 Archive/Superseded Originals/root/T14 GMP Scheduler]]"
  - "[[99 Archive/Superseded Originals/prerequisites/P10 OS Threads, Processes, and Go Scheduling Basics]]"
---

# Go Scheduler

## Why this matters

The scheduler explains why many goroutines can share fewer OS threads, why blocking does not always stop progress, and why goroutine count is different from CPU parallelism. It is an advanced diagnostic model, not a prerequisite for writing a correct goroutine.

## Explain like I am 12 and mental model

G is a task, M is an OS thread that can execute instructions, and P is the runtime resource needed for an M to execute Go code. Each P has runnable work; idle Ps can steal work. `GOMAXPROCS` controls the number of Ps and therefore the maximum simultaneous Go execution, not the number of goroutines.

## Core concepts

- Runnable goroutines usually enter per-P or global queues.
- An M with a P selects runnable Gs; work stealing balances uneven queues.
- Blocking channel or mutex operations can park a G so its M can run another.
- For many blocking syscalls, the runtime can detach the P so other work proceeds; network polling integrates readiness without one permanently blocked thread per connection.
- Preemption helps prevent long-running Go code from monopolizing execution, but programs must never depend on exact fairness.
- Goroutine stacks are runtime-managed and grow as needed.

## Minimum executable diagnostic

```go
package main

import (
	"fmt"
	"runtime"
	"sync"
)

func main() {
	fmt.Println("P count:", runtime.GOMAXPROCS(0))
	var wg sync.WaitGroup
	for i := 0; i < 4; i++ {
		wg.Add(1)
		go func(id int) { defer wg.Done(); fmt.Println("G", id) }(i)
	}
	wg.Wait()
}
```

The program demonstrates that goroutine count and P count are separate. Print order is unspecified; it does not reveal a stable scheduling algorithm.

## Production usage, success, and failure

Use this model to interpret execution traces, scheduler latency, runnable queues, blocking profiles, and CPU saturation. For CPU-bound work, increasing goroutines beyond available parallelism can add scheduling overhead. For I/O-bound work, concurrency may remain useful while many goroutines wait, but downstream capacity still requires bounds.

Success: diagnose from measurements such as profiles, traces, latency, CPU, and goroutine state. Failure: treating “goroutines are cheap” as unlimited, changing `GOMAXPROCS` without a workload hypothesis, or promising exact scheduler fairness and queue behavior across Go releases.

## Common mistakes and trade-offs

- Saying one goroutine equals one thread.
- Saying a blocked goroutine always blocks its OS thread.
- Confusing concurrency with parallelism.
- Explaining every latency issue through the scheduler before checking application locks, I/O, queues, and GC.
- Memorizing runtime field names as a durable API.

## Google / Senior Interview Lens

Give the G/M/P model in under a minute, then explain work stealing, parking, syscall handoff, netpoll, and `GOMAXPROCS`. Connect internals to worker bounds, CPU versus I/O workloads, and trace-based diagnosis. Do not imply Google requires Go.

## Active recall and design challenge

Explain what happens when 10,000 goroutines exist with `GOMAXPROCS=4`, including runnable, running, and waiting states. Identify measurements before changing any runtime setting.

## Related notes

- [[Goroutines and Lifecycle]]
- [[Go Memory Allocation and Escape Analysis]]
- [[Go Scheduler - Quick Revision]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
