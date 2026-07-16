---
type: quick-revision
domain: go
topic: goroutines-lifecycle
canonical: "[[Goroutines and Lifecycle]]"
---

# Goroutines and Lifecycle - Quick Revision

## 30-second definition

A goroutine is a runtime-scheduled concurrent function. Starting one creates a lifecycle obligation: owner, exit condition, cancellation, error propagation, boundedness, and shutdown.

Five facts: `go` gives no ordering guarantee; `WaitGroup` tracks completion, not errors; context communicates cancellation; blocked goroutines still retain state; concurrency is not necessarily parallelism.

Common trap: launching one goroutine per unbounded item.

Interview answer: “I make goroutine ownership explicit, bound concurrency, propagate cancellation and errors, and verify shutdown with race tests and goroutine profiles.”

Production example: request-scoped workers select on context and results; a closer waits for senders before closing output.

Active recall: write two workers, one result closer, and first-error cancellation.

Canonical: [[Goroutines and Lifecycle]] · Drill: [[Worker Pool with Cancellation - Drill]]

Index: [[Quick Revision Index]]
