---
type: canonical
domain: go
topic: channels
status: implementation-needed
aliases:
  - T15 Channel Internals
  - T16 Buffered vs Unbuffered Channels
source_notes:
  - "[[99 Archive/Superseded Originals/root/T15 Channel Internals]]"
  - "[[99 Archive/Superseded Originals/root/T16 Buffered vs Unbuffered Channels]]"
---

# Go Channels

## Why this matters

Channels communicate values and coordinate goroutines. Correct code depends on ownership, close semantics, cancellation, and capacity—not just send/receive syntax.

## Explain like I am 12 and mental model

An unbuffered channel is a handoff: sender and receiver meet. A buffered channel is a bounded shelf: sends can proceed while space remains, but a slow consumer eventually applies backpressure.

## Core concepts

```go
jobs := make(chan int)     // unbuffered
queue := make(chan int, 8) // buffered
queue <- 3
value, ok := <-queue
close(queue)
```

- Send blocks until a receiver participates or buffer space exists.
- Receive blocks until a value arrives; after close and drain it returns the zero value with `ok == false`.
- Sending to or closing an already closed channel panics.
- A nil channel blocks forever; in `select`, a nil case is disabled.
- The sender side that knows no more values will arrive normally owns closure.
- Closing is a broadcast about future sends, not a way to free memory.

## Minimum executable example and complete main usage

```go
package main

import "fmt"

func produce(out chan<- int) {
	defer close(out)
	for _, value := range []int{2, 4, 6} {
		out <- value
	}
}

func main() {
	values := make(chan int, 1)
	go produce(values)
	for value := range values {
		fmt.Println(value)
	}
}
```

## Detailed dry run

The producer owns the send-only view and closure. Capacity one absorbs at most one value ahead of the consumer. When production ends, close lets the range terminate after buffered values drain. Neither side assumes timing or closes a channel it does not own.

## Under the hood

The runtime coordinates waiting senders and receivers and, for buffered channels, a bounded queue. Runtime layout is version-sensitive; use the behavior contract as the design foundation. Channel operations create synchronization relationships described in [[Go Memory Model]].

## Production usage, success, and failure

Use channels for ownership transfer, bounded queues, results, and lifecycle signals. Use a mutex when several goroutines share state and event transfer would obscure the invariant.

Success: producer/consumer rates and capacity are understood, cancellation is selectable, and closure ownership is singular. Failure: a sender blocks after consumers exit, a buffer hides overload until memory or latency spikes, a receiver closes the channel, or a nil channel accidentally disables progress.

Buffer capacity is a system parameter. Size it from bounded burst and service-time reasoning, then measure queue depth and wait time. A larger buffer does not fix a sustained throughput mismatch.

## Common mistakes and trade-offs

- Believing buffered means non-blocking.
- Closing to signal one receiver when context or a value is clearer.
- Using a channel as an unbounded queue by adding another goroutine and slice.
- Losing errors from worker goroutines.
- Assuming channel use eliminates all races on separately shared memory.

## Google / Senior Interview Lens

State send/receive/close/nil behavior precisely. Senior follow-ups cover ownership, cancellation, backpressure, leaks, buffer sizing, fan-in, and when a mutex is simpler. In code, show the complete shutdown path.

## Active recall and blank-editor challenge

Build a producer, two workers, and one results closer. Then make the consumer stop early and repair the leak with cancellation.

## Related notes

- [[Select in Go]]
- [[Goroutines and Lifecycle]]
- [[Worker Pool]]
- [[Go Memory Model]]
- [[Go Channels - Quick Revision]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
