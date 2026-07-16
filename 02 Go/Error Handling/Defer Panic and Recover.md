---
type: canonical
domain: go
topic: defer-panic-recover
status: implementation-needed
aliases:
  - T10 Defer, Panic & Recover Internals
source_notes:
  - "[[99 Archive/Superseded Originals/root/T10 Defer, Panic & Recover Internals]]"
  - "[[99 Archive/Superseded Originals/prerequisites/P06 Function Call Stack]]"
---

# Defer, Panic and Recover

## Why this matters

`defer` makes cleanup follow acquisition. Panic unwinds a goroutine's stack and runs its defers. `recover` can translate a panic only at a deliberate boundary; it is not ordinary error handling.

## Explain like I am 12 and mental model

Each successful cleanup registration is a sticky note placed on the current function. When the function exits, the notes run last-in, first-out. A panic walks back through calls, running those notes. A deferred function in the same goroutine can catch the panic value.

## Core concepts

- Defer arguments are evaluated when the `defer` statement executes.
- A deferred closure reads captured variables when the closure runs.
- Defers run on normal return and panic, but not after `os.Exit` or process termination.
- `recover` is effective only when called by a deferred function during panic unwinding.
- One goroutine cannot recover a panic occurring in another; the boundary belongs inside that goroutine.
- Expected failures return errors. Panics are for violated invariants, programmer errors, or narrowly defined framework boundaries.

## Minimum executable example and complete main usage

```go
package main

import "fmt"

func safeDivide(a, b int) (result int, err error) {
	defer func() {
		if value := recover(); value != nil {
			err = fmt.Errorf("divide failed: %v", value)
		}
	}()
	if b == 0 {
		panic("zero denominator")
	}
	return a / b, nil
}

func main() {
	value, err := safeDivide(8, 0)
	if err != nil {
		fmt.Println(err)
		return
	}
	fmt.Println(value)
}
```

## Detailed dry run

The recovery closure is registered first. The zero denominator triggers panic. Stack unwinding calls the closure, which observes the panic and assigns the named error result. The function returns a normal error to `main`. This translation is appropriate only because the example defines a boundary; division validation would normally return an error directly.

## Production usage, success, and failure

Use `defer rows.Close()`, `defer file.Close()`, or a deferred rollback immediately after successful acquisition. For loop-scoped resources, put one iteration in a helper so the defer runs each iteration.

At an HTTP or job-runner boundary, recovery may log stack/context, emit a metric, return a generic failure, and keep the process serving when safe. Do not silently continue after corrupted shared state. A goroutine entry point needs its own recovery policy if one is justified.

Success: cleanup is registered only after acquisition succeeds and errors are not hidden. Failure: defers accumulate across a huge loop, recovery swallows the cause, a child goroutine panics without a boundary, or panic is used for invalid user input.

## Common mistakes and trade-offs

- Forgetting LIFO order.
- Expecting a deferred argument to see a later variable value.
- Calling `recover` outside a deferred function.
- Recovering without logging or returning a failure.
- Using named returns plus defer so cleverly that the flow becomes hard to review.

Defer improves correctness and locality. In extremely hot paths, benchmark instead of removing it based on old runtime folklore.

## Google / Senior Interview Lens

State the execution rules precisely, then discuss boundary placement, goroutine isolation, observability, and when not to recover. In a code exercise, prefer explicit errors for expected input failures.

## Active recall and blank-editor challenge

Write a resource helper with acquisition, deferred cleanup, a returned error, and a panic boundary around one job. Add a second goroutine and place recovery correctly.

## Related notes

- [[Go Error Handling]]
- [[Goroutines and Lifecycle]]
- [[Defer Panic and Recover - Quick Revision]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
