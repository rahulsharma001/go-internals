---
type: coding-drill
domain: go
topic: worker-pool
status: not-attempted
canonical: "[[Worker Pool]]"
---

# Worker Pool with Cancellation - Drill

## Problem

Implement `run(ctx context.Context, jobs []int, workers int) ([]int, error)`. Process jobs with at most `workers` goroutines. Squaring a negative job returns an error and cancels remaining work.

Input: `[2, 3, 4]`, workers `2`. Expected values: `4, 9, 16` in any order. Input `[2, -1, 4]` must return an error without leaking goroutines.

## Constraints and starter signature

```go
func run(ctx context.Context, jobs []int, workers int) ([]int, error)
```

- Reject `workers <= 0`.
- Bound worker count and queue capacity.
- Make every send cancellation-aware.
- Close channels only from their owning side.
- Provide a complete `main()` for success and failure cases.

## Edge cases and checklist

- Empty jobs; one worker; more workers than jobs; cancellation before start; first job fails.
- `WaitGroup.Add` happens before goroutine start.
- Result closure happens after workers exit.
- Error and cancellation cannot deadlock each other.

## Modification challenge

Preserve input order without removing concurrency. Then change overload policy from waiting to rejecting when the queue is full.

## Attempt and re-test history

| Date | Time | Result | Hints | Failure category |
|---|---:|---|---|---|
| | | not attempted | | |

| Re-test date | Variant | Result | Remaining mistake |
|---|---|---|---|
| | ordered / reject-on-full | | |

Keep the solution in a separate scratch file or collapsed section only after the first attempt.

Related: [[Worker Pool]] · [[Go Channels]] · [[Goroutines and Lifecycle]]

Index: [[Coding Drill Index]]
