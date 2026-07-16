---
type: canonical
domain: go
topic: select
status: implementation-needed
aliases:
  - T17 Select Statement Internals
source_notes:
  - "[[99 Archive/Superseded Originals/root/T17 Select Statement Internals]]"
---

# Select in Go

## Why this matters

`select` waits on several channel operations and is the core tool for cancellation, timeouts, multiplexing, and state-dependent channel behavior.

## Mental model and core concepts

Think of one goroutine waiting at several doors. It proceeds through one ready door. If several are ready, one is chosen; code must not depend on deterministic fairness. `default` means “do not wait.” A nil channel disables its case.

## Minimum executable example

```go
package main

import (
	"context"
	"fmt"
	"time"
)

func receive(ctx context.Context, in <-chan string) error {
	select {
	case value, ok := <-in:
		if !ok { return fmt.Errorf("input closed") }
		fmt.Println(value)
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second)
	defer cancel()
	in := make(chan string, 1)
	in <- "ready"
	if err := receive(ctx, in); err != nil { fmt.Println(err) }
}
```

## Detailed dry run

The buffered value makes the receive ready before the timeout. `select` chooses it and returns. If no value arrives before the deadline, `ctx.Done()` becomes ready and the function returns the context error. If the input closes, the two-value receive distinguishes closure from a real zero value.

## Production usage and failure scenarios

Use select in owned loops that respond to input, cancellation, and periodic signals. Reuse timers carefully in hot loops; repeatedly allocating `time.After` can create avoidable timer work. A `default` case can turn waiting into a CPU spin—use it only for deliberate best-effort or polling behavior.

Closed channels remain ready forever. In a multiplexing loop, set a drained channel variable to nil to disable that case. Success means every blocking operation has an exit path; failure means cancellation cannot be observed because code is blocked on a plain send or receive outside select.

## Common mistakes and trade-offs

- Expecting round-robin ordering.
- Adding `default` and accidentally busy-spinning.
- Reading endless zero values from a closed channel without checking `ok`.
- Using `time.After` repeatedly in a long-running loop without considering timer cost.
- Assuming select itself cancels the work that loses.

## Google / Senior Interview Lens

Explain ready-case selection, default, nil and closed channels, then apply them to cancellation and leak prevention. Be ready to design a loop that drains, shuts down, or disables inputs without starvation assumptions.

## Active recall and challenge

Merge two channels until both close, using nil to disable each completed input. Add cancellation and explain every termination condition.

## Related notes

- [[Go Channels]]
- [[Goroutines and Lifecycle]]
- [[Select in Go - Quick Revision]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
