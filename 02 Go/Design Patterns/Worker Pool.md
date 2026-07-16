---
type: canonical
domain: go
topic: worker-pool
status: implementation-needed
aliases:
  - T20 Worker Pool Pattern
source_notes:
  - "[[99 Archive/Superseded Originals/Coding Problems/Worker Pool (fixed workers)]]"
---

# Worker Pool

## Problem and mental model

A worker pool bounds the number of jobs executing concurrently. A fixed group of workers pulls from a queue; the queue absorbs only a defined burst, and cancellation/shutdown defines what happens to remaining work.

## When to use and when not to use

Use a pool when per-item work is independent and an external or local resource needs a concurrency limit. Do not add a pool when the called library already enforces the right bound, work must be strictly ordered, or queueing would merely hide overload.

## Architecture and executable example

```go
package main

import (
	"fmt"
	"sync"
)

func worker(jobs <-chan int, results chan<- int, wg *sync.WaitGroup) {
	defer wg.Done()
	for job := range jobs { results <- job * job }
}

func main() {
	jobs := make(chan int, 2)
	results := make(chan int)
	var wg sync.WaitGroup
	for i := 0; i < 2; i++ {
		wg.Add(1)
		go worker(jobs, results, &wg)
	}
	go func() {
		defer close(jobs)
		for _, job := range []int{2, 3, 4} { jobs <- job }
	}()
	go func() { wg.Wait(); close(results) }()
	for result := range results { fmt.Println(result) }
}
```

## Complete success and failure flows

Success: producer enqueues a bounded set, closes jobs, workers drain and exit, a closer waits for all workers, and the consumer drains results. Output order is unspecified.

Failure: if the consumer stops, workers can block sending results; if producers outpace the pool indefinitely, queueing increases latency; if a job fails and errors are ignored, completion appears successful. A production pool therefore needs an explicit error policy, cancellation, admission/backpressure behavior, and observability for active workers, queue depth, wait time, duration, errors, and rejected work.

## Trade-offs and production tools

More workers improve throughput only until CPU, database, network, or downstream limits dominate. Buffers smooth bursts but lengthen worst-case queueing. Cancellation may drain, discard, or finish queued work; choose deliberately. Libraries such as `errgroup` can simplify first-error cancellation, but the ownership model still matters.

## Common mistakes

- Closing results before workers finish.
- Calling `WaitGroup.Add` after starting work.
- Leaking workers when result consumption stops.
- Retrying inside workers without a budget, idempotency, or backoff.
- Treating the queue as infinite.

## Google / Senior Interview Lens

Implement the basic pool from a blank editor, then handle first-error cancellation, preserved order, per-job timeout, dynamic sizing, and overload. State complexity as O(n) work plus the job cost; memory includes bounded queues and active job state.

## Active recall and design challenge

Complete [[Worker Pool with Cancellation - Drill]], then modify it to preserve input order without serializing execution.

## Related notes

- [[Go Channels]]
- [[Goroutines and Lifecycle]]
- [[Select in Go]]
- [[Worker Pool - Quick Revision]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
