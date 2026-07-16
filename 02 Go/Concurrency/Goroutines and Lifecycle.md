---
type: canonical
domain: go
topic: goroutines-lifecycle
status: implementation-needed
aliases:
  - T13 Goroutine Internals
  - T23 Goroutine Leak Prevention
source_notes:
  - "[[99 Archive/Superseded Originals/root/T13 Goroutine Internals]]"
  - "[[99 Archive/Superseded Originals/prerequisites/P08 OS Threads vs Green Threads]]"
---

# Goroutines and Lifecycle

## Why this matters

A goroutine is a lightweight concurrently executing function managed by the Go runtime. Starting one is easy; defining its owner, completion, cancellation, error path, and resource bounds is the production skill.

## Explain like I am 12 and mental model

Starting a goroutine is assigning a task to a worker you cannot watch continuously. Before handing it off, decide who can cancel it, how it reports completion, and what prevents unlimited tasks from accumulating.

Concurrency means tasks can make progress during overlapping time. Parallelism means tasks actually execute simultaneously on multiple processors. `go f()` schedules work; it does not guarantee immediate execution or ordering.

## Minimum executable example and complete main usage

```go
package main

import (
	"context"
	"fmt"
	"sync"
)

func work(ctx context.Context, id int, out chan<- int) {
	select {
	case <-ctx.Done():
		return
	case out <- id * id:
	}
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	results := make(chan int)
	var wg sync.WaitGroup
	for _, id := range []int{2, 3} {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			work(ctx, id, results)
		}(id)
	}
	go func() { wg.Wait(); close(results) }()
	for result := range results {
		fmt.Println(result)
	}
}
```

## Detailed dry run

The parent establishes cancellation and counts two goroutines before starting them. Each goroutine owns one `Done` call and either observes cancellation or sends one result. A separate closer waits for all senders before closing the result channel. The receiver ranges until closure, so no fixed ordering is assumed.

## Core concepts and under the hood

- A goroutine begins with a runtime-managed stack that can grow.
- The runtime schedules many goroutines across OS threads; see [[Go Scheduler]].
- Channel, mutex, timer, syscall, and network events can block or park goroutines.
- `WaitGroup` handles completion, not cancellation or error propagation.
- Context carries cancellation and deadlines across request-scoped call chains; do not store it in a struct by default.
- Bound concurrency when work arrival can exceed capacity.

## Production usage, success, and failure

Success: every goroutine has an owner and exit condition, work is bounded, errors are observed, and shutdown waits for required completion. Failure: a send has no receiver, a ticker is never stopped, a background loop has no cancellation, a goroutine outlives request data, or the system launches one goroutine per unbounded item.

Use `go test -race`, goroutine profiles, block profiles, and execution traces to investigate. A stable goroutine count under steady load is a useful signal; a continuously rising count suggests leaks or increasing work.

## Common mistakes and trade-offs

- Calling `Add` inside the goroutine and racing with `Wait`.
- Assuming output order.
- Ignoring returned errors.
- Closing a channel from the receiver without ownership.
- Using goroutines to make CPU work faster without bounding parallelism.

Concurrency can improve throughput and responsiveness, but adds nondeterminism, coordination cost, and failure surfaces.

## Google / Senior Interview Lens

The minimum answer distinguishes concurrency, parallelism, and scheduling. Senior follow-ups ask for ownership, cancellation, error propagation, boundedness, leak diagnosis, race testing, and shutdown. In code, make completion and the failure path visible.

## Active recall and blank-editor challenge

Implement two cancellable workers and a closer, then change the requirement so the first error cancels all remaining work. Explain which component owns each channel.

## Related notes

- [[Go Channels]]
- [[Mutexes and Data Race Safety]]
- [[Worker Pool]]
- [[Go Scheduler]]
- [[Goroutines and Lifecycle - Quick Revision]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
