---
type: canonical
domain: go
topic: mutex-data-race
status: implementation-needed
aliases:
  - T18 Mutex & RWMutex Internals
source_notes:
  - "[[99 Archive/Superseded Originals/prerequisites/P03 Mutex & Concurrency Safety Basics]]"
---

# Mutexes and Data Race Safety

## Why this matters

A data race occurs when concurrent accesses touch the same memory, at least one is a write, and synchronization does not order them. Races are correctness bugs even when output appears right.

## Mental model and core concepts

A mutex is the key to an invariant, not merely to a field. Lock before reading or changing the protected state and unlock on every path. Keep the protected region small enough to avoid unnecessary contention, but large enough that the invariant is atomic.

- `sync.Mutex` permits one holder.
- `sync.RWMutex` permits multiple readers or one writer; it is not automatically faster.
- Atomics are useful for small independent state, not multi-field invariants.
- Channels coordinate ownership and events; mutexes protect shared memory. Choose the model that makes the invariant clearest.
- A type containing a mutex must not be copied after first use; pointer receivers are the normal choice.

## Minimum executable example

```go
package main

import (
	"fmt"
	"sync"
)

type Counter struct {
	mu    sync.Mutex
	value int
}

func (c *Counter) Increment() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.value++
}

func (c *Counter) Value() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.value
}

func main() {
	var c Counter
	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() { defer wg.Done(); c.Increment() }()
	}
	wg.Wait()
	fmt.Println(c.Value()) // 100
}
```

## Dry run, success, and failure

All increments may start concurrently, but the mutex serializes the read-modify-write operation. Waiting establishes completion before reading. Without the lock, increments can overwrite one another and the program has a race. Locking only the write but reading concurrently would still race.

Success: one documented lock protects a clear invariant, callers cannot bypass it, and race tests cover concurrent paths. Failure: a mutex is copied, a function returns while still locked, lock order creates deadlock, or a pointer escapes while the caller assumes exclusive ownership.

## Production trade-offs and tooling

Contention increases latency. Sharding state, reducing shared mutation, batching, or using immutable snapshots can help. `RWMutex` benefits read-heavy workloads only when critical sections and contention justify its overhead; benchmark. Use `go test -race`; add mutex/block profiles when contention is suspected.

## Common mistakes

- Locking individual fields while violating a cross-field invariant.
- Double-locking a non-reentrant mutex.
- Holding a lock across slow I/O or an unknown callback.
- Copying a struct that contains a mutex.
- Using a map concurrently because reads “usually work.”

## Google / Senior Interview Lens

Explain the exact invariant and happens-before edge, not “mutex makes it thread-safe.” Expect lock granularity, deadlock, starvation, atomics, race detector, and channel-versus-mutex follow-ups.

## Active recall and challenge

Implement a concurrency-safe balance transfer across two accounts. Define a stable lock order, then explain how you would test deadlock and invariant preservation.

## Related notes

- [[Go Memory Model]]
- [[Goroutines and Lifecycle]]
- [[Go Maps]]
- [[Synchronization - Quick Revision]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
