# T15 Channel Internals

> **Reading Guide**: Read Sections 1-3 first (15 min) to lock semantics.
> Read Sections 4-6 next (25 min) for runtime internals and traces.
> Sections 7-12 are interview prep.
> Full Q&A bank is linked in Section 13.
> If the basics feel fuzzy, re-read [[prerequisites/P03 Mutex & Concurrency Safety Basics]] and [[T14 GMP Scheduler]].

---

## 0. Prerequisites

Complete these before this topic:

- [[T13 Goroutine Internals]]
- [[T14 GMP Scheduler]]
- [[prerequisites/P03 Mutex & Concurrency Safety Basics]]

---

## 1. Concept

A channel is Go's synchronization + communication primitive that safely transfers data between goroutines.

---

## 2. Core Insight (TL;DR)

Internally, a channel is an `hchan` runtime structure with:

- optional circular buffer (for buffered channels),
- waiting sender queue,
- waiting receiver queue,
- lock to protect channel state.

Unbuffered channel means direct handoff (sender and receiver meet).  
Buffered channel means sender may proceed without immediate receiver until buffer fills.

---

## 3. Mental Model (Lock this in)

Think of a reception desk:

- Channel = desk.
- Senders = people dropping packets.
- Receivers = people picking packets.
- Buffer = desk tray with limited slots.

No tray (`cap=0`) means hand-to-hand transfer only.  
Tray with slots (`cap>0`) means packets can wait there.

```text
Unbuffered:
  Sender <-> Receiver (must meet now)

Buffered(cap=3):
  Sender -> [slot1][slot2][slot3] -> Receiver
```

### Mistake that teaches you

Wrong thought:
"Buffered channel always prevents blocking."

Correct:
"Buffered channel avoids blocking only until capacity is full."

```text
cap=2
send A -> ok
send B -> ok
send C -> blocks (buffer full, no receiver yet)
```

> **In plain English:** Buffer is a small waiting bench, not infinite storage.

---

## 4. How It Actually Works (Internals) [INTERMEDIATE -> ADVANCED]

### 4.1 `hchan` structure (runtime view)

Channel runtime state includes:

- queue count (`qcount`) for buffered items,
- buffer size (`dataqsiz`),
- circular buffer pointer,
- send index / receive index,
- waiting sender list (`sendq`),
- waiting receiver list (`recvq`),
- lock.

```text
hchan
  qcount=1
  dataqsiz=3
  buf=[A _ _]
  sendx=1
  recvx=0
  sendq=[G17,G22]
  recvq=[]
```

### 4.2 Send path (high level)

When goroutine does `ch <- x`, runtime checks in this rough order:

1. Is there a waiting receiver? -> direct handoff.
2. Else if buffer has room? -> enqueue into buffer.
3. Else -> sender goroutine parks in `sendq`.

```text
Case 1:
  recvq has G9 waiting
  sender copies value directly to receiver path
  both continue

Case 2:
  recvq empty, buffer has slot
  enqueue value, sender continues

Case 3:
  recvq empty, buffer full
  sender parks in sendq
```

### 4.3 Receive path (high level)

When goroutine does `<-ch`, runtime checks:

1. Is buffer non-empty? -> dequeue from buffer.
2. Else is there waiting sender? -> direct receive from sender.
3. Else if channel closed? -> zero value + closed indication.
4. Else -> receiver parks in `recvq`.

```text
Case:
  buffer empty + no sender + not closed
  receiver parks in recvq
```

### 4.4 Circular buffer behavior

Buffered channels use ring semantics.

```text
cap=3
Initial:  [_ _ _] sendx=0 recvx=0
send A:   [A _ _] sendx=1 recvx=0
send B:   [A B _] sendx=2 recvx=0
recv ->A: [_ B _] sendx=2 recvx=1
send C:   [_ B C] sendx=0 recvx=1  (wrap)
```

This avoids shifting elements like a slice queue.

### 4.5 Parking, wakeup, and scheduler integration

Blocked sender/receiver goroutines park and yield CPU lane.  
When complementary operation arrives, runtime wakes parked goroutine and marks it runnable.

```text
Gsend parks in sendq
Grecv arrives and matches
Gsend -> runnable
both continue via scheduler
```

### 4.6 Close semantics internally

`close(ch)` marks channel closed and wakes blocked receivers/senders.

Rules:

- receiving from closed channel: returns zero value after buffered items drain.
- sending to closed channel: panic.
- closing already closed channel: panic.

```text
close(ch)
  wake recvq -> they can proceed
  wake sendq -> senders fail (panic on send attempt path)
```

> **In plain English:** Closing channel is like saying "desk is permanently shut." People can pick remaining packets, but no one can drop new packets.

---

## 5. Key Rules & Behaviors

### Rule 1: Unbuffered channel is synchronization point

```go
ch := make(chan int)
go func() { ch <- 42 }()
v := <-ch
```

```text
Send and receive handshake directly.
```

### Rule 2: Buffered channel is bounded queue

```go
ch := make(chan int, 2)
ch <- 1
ch <- 2
// next send blocks until receive happens
```

```text
Buffer helps burst smoothing, not unlimited throughput.
```

### Rule 3: Channel close is broadcast-style signal for receivers

```go
close(ch)
v, ok := <-ch // ok=false when drained and closed
```

```text
Receivers can detect completion without extra mutex.
```

### Rule 4: Nil channel blocks forever on send/receive

```go
var ch chan int
// <-ch and ch<-1 both block forever
```

```text
Useful in select tricks, dangerous if accidental.
```

### Rule 5: Channel safety is for communication, not all shared-state design

```text
Channels help coordination.
For shared mutable maps/counters, mutex/atomics may still be better.
```

---

## 6. Code Examples (Show, Don't Tell)

### Example A: Unbuffered handoff trace

```go
package main

import "fmt"

func main() {
	ch := make(chan string)
	go func() {
		ch <- "ready"
	}()
	msg := <-ch
	fmt.Println(msg)
}
```

```text
Step 1: receiver main waits on <-ch (if sender not ready yet)
Step 2: sender goroutine executes ch<-"ready"
Step 3: runtime matches sender and receiver directly
Step 4: both proceed; main prints "ready"
```

### Example B: Buffered queue and blocking boundary

```go
package main

import "fmt"

func main() {
	ch := make(chan int, 2)
	ch <- 10
	ch <- 20

	fmt.Println(<-ch)
	fmt.Println(<-ch)
}
```

```text
Step 1: send 10 -> buffer slot0
Step 2: send 20 -> buffer slot1
Step 3: receive -> gets 10
Step 4: receive -> gets 20
```

### Example C: Close and range consumption

```go
package main

import "fmt"

func main() {
	ch := make(chan int, 2)
	ch <- 1
	ch <- 2
	close(ch)

	for v := range ch {
		fmt.Println(v)
	}
}
```

```text
Step 1: two buffered values exist
Step 2: close marks channel closed
Step 3: range drains buffered values
Step 4: loop ends when channel empty + closed
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict output (2 min)

What happens?

```go
ch := make(chan int, 1)
ch <- 1
select {
case ch <- 2:
	println("sent")
default:
	println("blocked")
}
```

> [!success]- Answer
> Prints `blocked` because channel capacity is full and no receiver is draining.

### Tier 2: Fix the bug (5 min)

Buggy code:

```go
func producer(ch chan<- int) {
	for i := 0; i < 10; i++ {
		ch <- i
	}
	// forgot close
}
```

> [!success]- Answer
> If consumer uses `for range ch`, producer must close channel when production finishes, or consumer may block forever.

### Tier 3: Build It (15 min)

Build bounded worker pipeline:

- jobs channel (buffered)
- N workers consume jobs
- results channel collected by aggregator
- close results after workers finish

> Full solutions with explanations -> [[exercises/T15 Channel Internals - Exercises]]

---

## 7. Edge Cases & Gotchas

| Trap | Why it happens | Fix |
|---|---|---|
| send on closed channel panic | channel no longer accepts sends | coordinate close ownership clearly |
| forgetting to close producer channel | consumers using range block forever | close after producer done |
| nil channel accidental use | send/recv blocks forever | initialize channel before use |
| assuming buffered means non-blocking forever | capacity finite | size buffer intentionally + drain path |
| deadlock with no receiver | all goroutines blocked on channel ops | validate communication topology |

> **In plain English:** Most channel bugs are lifecycle bugs: who sends, who receives, who closes, and when.

---

## 8. Performance & Tradeoffs

Your service has fan-out workers consuming jobs from a queue channel.  
Your real question is "Does channel coordination help this flow, or is lock-free/atomic path better for this hotspot?"

| Pattern | What it costs | You'd see this in... | Verdict |
|---|---|---|---|
| unbuffered channel handshake | strict sync point; potential wait | request/response handoff | ✅ for correctness |
| small buffered channel | bounded queue overhead | worker pools, bursts | ✅ common default |
| huge channel buffer | memory + delayed backpressure | queue absorbing spikes too long | ⚠ use carefully |
| channel in ultra-hot counter path | coordination overhead | high-frequency shared counters | ❌ mutex/atomic often better |

What actually hurts in production:

Oversized buffers can hide overload until latency explodes.  
Missing close/drain contracts create goroutine leaks and deadlocks.

What to measure:

```bash
go test -bench=. -benchmem ./...
go test -race ./...
go tool pprof -http=:0 http://localhost:6060/debug/pprof/block
go tool pprof -http=:0 http://localhost:6060/debug/pprof/goroutine
```

---

## 9. Common Misconceptions

| Misconception | Reality |
|---|---|
| "channel replaces mutex everywhere" | channels solve communication; mutex may be simpler for shared state |
| "buffered channel never blocks" | blocks when full |
| "close is required for every channel" | close is required only to signal no more sends |
| "receiver should close channel" | sender side usually owns close |
| "nil channel is same as closed channel" | nil blocks forever; closed returns zero-value receives |

---

## 10. Related Tooling & Debugging

- `go test -race` for unsafe shared state around channel workflows.
- block profile to find channel contention stalls.
- goroutine profile to detect parked/leaked goroutines.
- `runtime/trace` for send/recv timeline.

Interview-ready debug line:
"I would inspect block profile + goroutine dump first to find where send/receive are parked."

---

## 11. Interview Gold Questions

### Q1: Explain unbuffered vs buffered channel internals.

Nuanced answer: unbuffered channel is direct sender-receiver synchronization. Buffered channel uses ring buffer and only synchronizes directly when buffer boundary conditions require.

Interview-ready verbal summary: "Unbuffered is handshake now; buffered is bounded mailbox."

### Q2: What happens when you close a channel?

Nuanced answer: channel is marked closed, blocked receivers are woken and can drain remaining buffered values, future receives get zero value with `ok=false`, and any send causes panic.

Interview-ready verbal summary: "Close means no more sends, but remaining buffered data can still be read."

### Q3: Why can channel misuse leak goroutines?

Nuanced answer: if send/receive/close contracts are broken, goroutines can park forever waiting for events that never happen.

Interview-ready verbal summary: "Leaked goroutine usually means parked forever on a channel contract bug."

---

## 12. Final Verbal Answer

> Channel internals are built around `hchan`: lock, buffer metadata, and wait queues for blocked senders and receivers.  
> Unbuffered channels synchronize sender and receiver directly. Buffered channels use a ring queue with bounded capacity.  
> When operations cannot proceed, goroutines park; when matching operations arrive, they wake and resume.  
> Correct channel design is mostly about lifecycle contracts: who sends, who receives, who closes, and when.  
> In performance terms, channels are excellent for coordination but should be measured before using in ultra-hot shared-state paths.

---

## 13. Comprehensive Interview Questions

> Full interview question bank (12 questions) -> [[questions/T15 Channel Internals - Interview Questions]]

Preview:

- Why is sender-owned close the common pattern?
- How does buffered channel ring indexing work?
- Why does nil channel block forever?

---

> See [[Glossary]] for term definitions.
