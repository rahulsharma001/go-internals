---
type: canonical
domain: go
topic: go-memory-model
status: learning
aliases:
  - Go Memory Model (Happens-Before)
source_notes:
  - "[[99 Archive/Superseded Originals/root/Go Memory Model (Happens-Before)]]"
  - "[[Mutexes and Data Race Safety]]"
  - "[[Go Channels]]"
---

# Go Memory Model

## Why this matters

The memory model answers when a write performed by one goroutine is guaranteed to be observed by another. Without a defined synchronization relationship, apparent results are not a correctness argument.

## Explain like I am 12 and mental model

Two people edit separate copies of a whiteboard. Synchronization is the agreed handoff that makes earlier edits visible before later reading. Wall-clock intuition, sleeping, or “it ran first in my test” is not that handoff.

## Core concepts

Within one goroutine, operations follow the language's sequencing rules. Across goroutines, synchronization establishes ordering often described as “synchronized before” and, when combined with program order, “happens before.” A program with a data race is incorrect; design it to be race-free rather than reasoning from accidental hardware behavior.

Important synchronizers include:

- unlocking a mutex and a later successful lock of that mutex;
- channel send/receive relationships and close observations defined by the language;
- atomic operations with their specified ordering;
- initialization completion before package use;
- lifecycle primitives whose documentation states the relevant synchronization.

## Minimum executable example

```go
package main

import "fmt"

func main() {
	done := make(chan struct{})
	value := 0
	go func() {
		value = 42
		close(done)
	}()
	<-done
	fmt.Println(value) // 42
}
```

The close and corresponding receive order the write before the read. Replacing `<-done` with `time.Sleep` would not be a valid synchronization design.

## Production usage, success, and failure

Success: shared-state invariants are protected by mutexes, ownership transfer uses channels, small independent state uses appropriate atomics, and tests run with the race detector. Failure: a boolean flag is read/written concurrently without synchronization, a sleep is used as coordination, or a concurrent map appears to work during a light test.

The race detector observes executed paths, so a clean run increases confidence but does not prove every path. Code review should identify the synchronizer for each shared mutable invariant.

## Trade-offs and common mistakes

- Adding atomics field-by-field while a multi-field invariant remains broken.
- Assuming goroutine creation alone orders later arbitrary operations.
- Mixing channel ownership and shared mutation without documenting both.
- Using “volatile” reasoning from another language; Go has its own model.
- Treating the runtime implementation as the contract.

Synchronization costs are usually worth correctness. Optimize contention only after the invariant is clear and measured.

## Google / Senior Interview Lens

Define a data race, identify the exact happens-before path, and repair a broken publication example. Follow-ups include atomics versus locks, channel close semantics, race-detector limits, and distributed-systems analogy: process-local memory ordering is not network or storage consistency.

## Active recall and blank-editor challenge

Write three safe publication variants using a channel, mutex, and atomic. State what each protects and where it stops being sufficient.

## Related notes

- [[Mutexes and Data Race Safety]]
- [[Go Channels]]
- [[Goroutines and Lifecycle]]
- [[Go Memory Model - Quick Revision]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
