---
type: canonical
domain: go
topic: functions-closures
status: learning
source_notes:
  - "[[99 Archive/Superseded Originals/prerequisites/P07 Functions, Closures & Variable Capture]]"
---

# Functions and Closures

## Why this matters

Functions are values in Go. Closures power middleware, callbacks, dependency injection, retries, and goroutine tasks, but captured mutable state can create races and lifetime surprises.

## Mental model

A closure is a function plus access to variables from its surrounding scope. It does not merely freeze their printed value; it can observe and mutate captured variables for as long as the closure remains reachable.

## Minimum executable example

```go
package main

import "fmt"

func counter(start int) func() int {
	value := start
	return func() int {
		value++
		return value
	}
}

func main() {
	next := counter(10)
	fmt.Println(next()) // 11
	fmt.Println(next()) // 12
}
```

The returned function keeps `value` alive. Separate calls to `counter` create separate captured state.

## Production usage and failure paths

Middleware factories commonly close over immutable configuration or shared dependencies. That is clear when the captured values have an explicit lifetime. Capturing mutable state used concurrently requires synchronization. Capturing a large request object in a long-lived callback can retain it unexpectedly.

Loop-variable semantics changed in modern Go for variables declared by a range clause, but code must still reason about which variable is captured, especially for outer variables or assignments. Passing the iteration value as an explicit function argument remains a clear interview explanation.

## Common mistakes and trade-offs

- Starting goroutines that capture mutable state without ownership or a mutex.
- Assuming every capture is a value snapshot.
- Hiding too many dependencies in closures.
- Retaining request-scoped objects in long-lived callbacks.
- Using `defer` inside a large loop when cleanup must occur per iteration.

Closures can make composition concise; named types and structs are clearer when behavior has several dependencies, methods, or lifecycle rules.

## Google / Senior Interview Lens

Explain capture, lifetime, concurrency safety, and loop cases without relying on outdated absolutes. Be ready to convert a closure into a struct with methods when requirements grow.

## Active recall and challenge

Write a middleware-style function that closes over immutable configuration, then add a shared request count safely. Explain the race in the unsynchronized version.

## Related notes

- [[Goroutines and Lifecycle]]
- [[Mutexes and Data Race Safety]]
- [[Defer Panic and Recover]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
