---
type: canonical
domain: go
topic: context-cancellation
status: implementation-needed
aliases:
  - T19 Context Package Internals
source_notes:
  - "[[Goroutines and Lifecycle]]"
  - "[[Go Channels]]"
  - "[[MongoDB with Go]]"
---

# Context Cancellation

## Why this matters and mental model

`context.Context` carries request-scoped cancellation, deadlines, and small cross-boundary metadata. It is a cancellation tree: when a parent is canceled, descendants become done. Cancellation is cooperative; work must observe `Done()` or call an API that does.

## Core concepts

- Accept context as the first parameter: `func Do(ctx context.Context, ...)`.
- Derive with `WithCancel`, `WithTimeout`, or `WithDeadline` and call the returned cancel function.
- Propagate the incoming context instead of replacing it with `Background` inside the call chain.
- Use values only for request-scoped metadata crossing API boundaries, not optional parameters or business state.
- A context should normally not be stored in a struct.

## Minimum executable example

```go
package main

import (
	"context"
	"fmt"
	"time"
)

func wait(ctx context.Context) error {
	select {
	case <-time.After(100 * time.Millisecond):
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Millisecond)
	defer cancel()
	fmt.Println(wait(ctx)) // context deadline exceeded
}
```

## Production success and failure

Success: an HTTP request deadline propagates through service and database calls; goroutines select on cancellation; cleanup calls `cancel`; errors preserve `context.Canceled` or `context.DeadlineExceeded` for boundary mapping.

Failure: a goroutine blocks on an unselectable send, code creates a new background context and loses the deadline, a timeout is applied independently at every layer without a budget model, or context values hide required arguments.

Cancellation does not guarantee rollback or remote termination. Downstream operations need their own cancellation support and idempotency or cleanup semantics.

## Trade-offs and interview lens

Deadlines prevent unbounded work but can amplify load when paired with careless retries. A senior answer connects end-to-end budget, cancellation propagation, cleanup, observability, and error classification.

## Active recall challenge

Build a request → service → repository chain that shares one deadline. Add a goroutine send and make it cancellation-safe.

## Related notes

- [[Goroutines and Lifecycle]]
- [[Select in Go]]
- [[Go Error Handling]]
- [[Context Cancellation - Quick Revision]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
