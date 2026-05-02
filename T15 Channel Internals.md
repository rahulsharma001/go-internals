# T15 Channel Internals

> **Reading Guide**: Sections 1-3 and 6 are essential first read (20 min).
> Sections 4-5 deepen understanding (15 min).
> Sections 7-12 are interview-specific — read closer to interview day.
> Section 13 is your comprehensive interview Q&A bank → [[questions/T15 Channel Internals - Interview Questions]]
> Something not clicking? → [[simplified/T15 Channel Internals - Simplified]]

---

## 0. Prerequisites

This topic assumes you understand:
- Basic goroutine concepts (launch with `go`, concurrency vs parallelism)
- Mutex basics (what locking means)

If you need a refresher:
- [[prerequisites/P03 Mutex & Concurrency Safety Basics]]
- [[prerequisites/P08 OS Threads vs Green Threads]]

---

## 1. Concept

**A channel in Go is a typed, thread-safe queue** that lets goroutines send and receive values. The runtime handles all the synchronization — you never lock a mutex manually. Channels are how goroutines talk to each other without sharing memory.

Under the hood, a channel is a pointer to an `hchan` struct on the heap. That struct holds a circular buffer (for buffered channels), plus two wait queues: one for goroutines waiting to send, one for waiting to receive.

---

## 2. Core Insight (TL;DR)

**Channels are synchronized queues backed by a circular buffer and two goroutine wait queues.** When you send or receive, the runtime locks the channel, moves data, and wakes waiting goroutines. **Unbuffered channels force handoff**: sender blocks until receiver takes the value (or vice versa). **Buffered channels decouple**: sender blocks only when buffer is full, receiver blocks only when buffer is empty.

**The interview gold:** explain the `hchan` struct (buffer + two `sudog` queues), the direct-copy optimization for unbuffered channels, and why closing a closed channel panics.

---

## 3. Mental Model (Lock this in)

### The Post Office Mailbox

Think of a buffered channel as a **mailbox with N slots**. Goroutines are people trying to drop off letters (send) or pick up letters (receive).

```
Buffered channel (capacity 3):

Sender goroutine               Channel                Receiver goroutine
┌──────────────┐               ┌─────────────┐        ┌──────────────┐
│ G1: ch <- x  │ ────────────→ │ Buffer:     │ ─────→ │ G2: y := <-ch│
└──────────────┘               │ [x][ ][ ]   │        └──────────────┘
   (drop letter)               │             │           (pick up)
                               │ sendq: [G3] │  ← blocked senders
If buffer FULL:                │ recvq: [ ]  │  ← blocked receivers
→ sender blocks                └─────────────┘
```

**Unbuffered channel** (capacity 0) is a **direct handoff** — no mailbox, just two people meeting. If sender arrives first, they wait. If receiver arrives first, they wait. Only when both are ready does the exchange happen.

### The Mistake That Teaches You

```go
package main

import "fmt"

func main() {
	ch := make(chan int)  // unbuffered
	ch <- 42              // BUG: deadlock!
	fmt.Println(<-ch)
}
```

**What you'd expect:** The program sends 42 into the channel, then receives it.

**What actually happens:**
```
fatal error: all goroutines are asleep - deadlock!
```

**Why:** Unbuffered channels require a receiver to be ready when you send. Here, `ch <- 42` blocks forever because no other goroutine is running to receive. `main` is stuck at the send, so it never reaches the receive. The runtime detects all goroutines are blocked → deadlock.

**Fix:** Use a goroutine for the send OR use a buffered channel:

```go
// Fix 1: Goroutine
go func() { ch <- 42 }()
fmt.Println(<-ch)

// Fix 2: Buffered
ch := make(chan int, 1)
ch <- 42
fmt.Println(<-ch)
```

---

## 4. How It Actually Works (Internals) [INTERMEDIATE → ADVANCED]

### 4.1 The `hchan` Struct — What a Channel Actually Is

Every channel in Go is a pointer to an `hchan` (heap channel) struct allocated on the heap when you call `make(chan T, n)`.

```go
// file: src/runtime/chan.go
type hchan struct {
	qcount   uint           // number of elements currently in buffer
	dataqsiz uint           // capacity of buffer (from make(chan T, n))
	buf      unsafe.Pointer // pointer to circular buffer array
	elemsize uint16         // size of one element in bytes
	closed   uint32         // 0 = open, 1 = closed
	elemtype *_type         // element type (for GC)
	sendx    uint           // send index in buffer (where next send writes)
	recvx    uint           // receive index in buffer (where next receive reads)
	recvq    waitq          // queue of goroutines waiting to receive
	sendq    waitq          // queue of goroutines waiting to send
	lock     mutex          // protects all fields above
}

type waitq struct {
	first *sudog  // linked list of waiting goroutines
	last  *sudog
}
```

```
┌─────────────────────────────────────────────────────────────────────────┐
│ type hchan struct {                                                     │
│     qcount   uint           // how many items in buffer now             │
│     dataqsiz uint           // max capacity                             │
│     buf      unsafe.Pointer // → circular buffer array                  │
│     elemsize uint16         // bytes per element                        │
│     closed   uint32         // 0 or 1                                   │
│     sendx    uint           // next write position                      │
│     recvx    uint           // next read position                       │
│     recvq    waitq          // blocked receivers                        │
│     sendq    waitq          // blocked senders                          │
│     lock     mutex          // guards everything                        │
│ }                                                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

**MEMORY TRACE: Creating a buffered channel**

```go
// file: main.go
package main

func main() {
	ch := make(chan int, 3)  // buffered channel, capacity 3
	_ = ch
}
```

```
Step 1: make(chan int, 3) allocates hchan on heap

  stack (main):
    ┌─────────────────────────────────────────┐
    │ storage for variable ch                 │
    │ 0xC000010080                            │──────┐
    └─────────────────────────────────────────┘      │
                                                      ▼
  heap 0xC000010080:
    ┌────────────────────────────────────────────────────────┐
    │ hchan{                                                 │
    │   qcount:   0                   ← empty now            │
    │   dataqsiz: 3                   ← capacity 3           │
    │   buf:      0xC0000100C0 ───────┼─────┐               │
    │   elemsize: 8                   │     │ (int is 8 bytes)│
    │   closed:   0                   │     │                │
    │   sendx:    0                   │     │                │
    │   recvx:    0                   │     │                │
    │   recvq:    {first: nil, last: nil}   │                │
    │   sendq:    {first: nil, last: nil}   │                │
    │   lock:     <mutex>             │     │                │
    │ }                               │     │                │
    └─────────────────────────────────┼─────┼────────────────┘
                                      │     │
    Points to circular buffer ────────┘     ▼
                          heap 0xC0000100C0:
                            ┌───────────────────────────┐
                            │ [int][int][int]           │
                            │  [0]  [1]  [2]  ← 3 slots │
                            │ (all empty initially)     │
                            └───────────────────────────┘


KEY INSIGHT:
  ch is NOT the channel — it's a POINTER to hchan on the heap.
  sizeof(ch) = 8 bytes (one pointer).
  The actual channel struct is ~96 bytes + buffer size.
```

> **In plain English:** A channel is a box with a rotating conveyor belt inside (the circular buffer). Two lines of goroutines wait outside: senders on one side, receivers on the other. A lock on the door ensures only one goroutine enters at a time to touch the belt.

---

### 4.2 Send Operation — `ch <- x`

When you write `ch <- value`, the runtime calls `chansend`. Here's what happens:

```go
// file: main.go
package main

func main() {
	ch := make(chan int, 2)
	ch <- 10
	ch <- 20
	ch <- 30  // blocks — buffer full
}
```

**MEMORY TRACE: Send operation step by step**

```
Initial state: ch = make(chan int, 2)
  hchan at 0xC000010080:
    qcount:  0
    dataqsiz: 2
    buf:      0xC0000100C0 → [slot0][slot1]
    sendx:    0
    recvx:    0
    sendq:    empty
    recvq:    empty


Step 1: ch <- 10
  1. Lock hchan.lock (acquire mutex)
  2. Check: is buffer full? qcount < dataqsiz? 0 < 2 → YES, space available
  3. Check: any waiting receivers in recvq? NO → write to buffer
  4. Copy value 10 to buf[sendx]:
       buf[0] = 10
  5. Increment sendx: sendx = (0 + 1) % 2 = 1
  6. Increment qcount: qcount = 1
  7. Unlock hchan.lock

  hchan at 0xC000010080:
    qcount:  1               ← 1 item now
    sendx:    1              ← next write at slot 1
    recvx:    0
    buf → [10][ ]


Step 2: ch <- 20
  1. Lock hchan.lock
  2. Check: qcount < dataqsiz? 1 < 2 → YES
  3. Copy value 20 to buf[sendx]:
       buf[1] = 20
  4. sendx = (1 + 1) % 2 = 0  ← wraps around (circular)
  5. qcount = 2
  6. Unlock hchan.lock

  hchan at 0xC000010080:
    qcount:  2               ← buffer FULL now
    sendx:    0              ← next write would be slot 0 (wrapped)
    recvx:    0
    buf → [10][20]


Step 3: ch <- 30 (buffer is full!)
  1. Lock hchan.lock
  2. Check: qcount < dataqsiz? 2 < 2 → NO, buffer FULL
  3. Check: any waiting receivers in recvq? NO
  4. Current goroutine must BLOCK:
       a. Create a sudog (goroutine descriptor) wrapping current G
       b. sudog.elem = pointer to value 30 (to send later)
       c. Add sudog to sendq (tail of linked list)
       d. goparkunlock(&hchan.lock) → parks G, unlocks mutex
          Current goroutine is now SLEEPING, waiting to send

  hchan at 0xC000010080:
    qcount:  2
    sendq:   [G1:30]  ← main goroutine waiting to send 30
    buf → [10][20]

  Goroutine state:
    main goroutine: BLOCKED (parked, waiting on channel)


When another goroutine receives (<-ch):
  1. Lock hchan.lock
  2. Check sendq: is anyone waiting to send? YES → G1
  3. Dequeue G1 from sendq
  4. Copy value 30 from G1's sudog directly to receiver
  5. Wake G1 (schedule it to run again)
  6. Unlock hchan.lock


KEY INSIGHTS:
  - Send blocks if buffer is full AND no receiver is waiting
  - sendx wraps around: it's a circular buffer
  - Blocked senders are stored in a linked list (sendq)
  - Each blocked goroutine has a sudog struct holding the value to send
```

> **In plain English:** Sending is like dropping a letter in the mailbox. If there's space, you drop it and leave. If the mailbox is full, you wait in line (sendq) until someone empties a slot. The moment a slot opens, the post office calls you forward and takes your letter.

---

### 4.3 Receive Operation — `x := <-ch`

When you read `<-ch`, the runtime calls `chanrecv`. Logic is symmetric to send:

```go
// file: main.go
package main

func main() {
	ch := make(chan int, 2)
	ch <- 10
	ch <- 20

	x := <-ch  // receives 10
	y := <-ch  // receives 20
	z := <-ch  // blocks — buffer empty
}
```

**MEMORY TRACE: Receive operation step by step**

```
Initial state after two sends:
  hchan at 0xC000010080:
    qcount:  2
    dataqsiz: 2
    sendx:    0
    recvx:    0
    buf → [10][20]


Step 1: x := <-ch
  1. Lock hchan.lock
  2. Check: is buffer empty? qcount > 0? 2 > 0 → NO, has data
  3. Check: any waiting senders in sendq? NO → read from buffer
  4. Copy buf[recvx] to receiver:
       x = buf[0] = 10
  5. Increment recvx: recvx = (0 + 1) % 2 = 1
  6. Decrement qcount: qcount = 1
  7. Unlock hchan.lock

  hchan at 0xC000010080:
    qcount:  1               ← 1 item left
    recvx:    1              ← next read at slot 1
    buf → [ ][20]            (slot 0 logically empty, will be overwritten)


Step 2: y := <-ch
  1. Lock hchan.lock
  2. Check: qcount > 0? 1 > 0 → YES
  3. Copy buf[recvx] to receiver:
       y = buf[1] = 20
  4. recvx = (1 + 1) % 2 = 0  ← wraps around
  5. qcount = 0
  6. Unlock hchan.lock

  hchan at 0xC000010080:
    qcount:  0               ← buffer EMPTY now
    recvx:    0
    buf → [ ][ ]


Step 3: z := <-ch (buffer is empty!)
  1. Lock hchan.lock
  2. Check: qcount > 0? 0 > 0 → NO, buffer EMPTY
  3. Check: any waiting senders in sendq? NO
  4. Current goroutine must BLOCK:
       a. Create a sudog wrapping current G
       b. sudog.elem = pointer to local variable z (where to store received value)
       c. Add sudog to recvq (tail of linked list)
       d. goparkunlock(&hchan.lock) → parks G, unlocks mutex
          Current goroutine is now SLEEPING, waiting to receive

  hchan at 0xC000010080:
    qcount:  0
    recvq:   [G1]  ← main goroutine waiting to receive into z
    buf → [ ][ ]

  Goroutine state:
    main goroutine: BLOCKED (parked, waiting on channel)


When another goroutine sends (ch <- 99):
  1. Lock hchan.lock
  2. Check recvq: is anyone waiting to receive? YES → G1
  3. Dequeue G1 from recvq
  4. Copy value 99 directly into G1's sudog.elem (which points to z)
  5. Wake G1 (schedule it to run again)
  6. Unlock hchan.lock

  After wake:
    z = 99  (direct copy, bypassed buffer)


KEY INSIGHTS:
  - Receive blocks if buffer is empty AND no sender is waiting
  - recvx wraps around (circular)
  - Blocked receivers are stored in a linked list (recvq)
  - Direct copy optimization: if a receiver is waiting, sender copies directly to receiver's variable (bypasses buffer)
```

> **In plain English:** Receiving is like checking the mailbox. If there's a letter, you take it. If empty, you wait in line (recvq) until someone drops one off. The moment a letter arrives, the post office calls you and hands it directly to you.

---

### 4.4 Unbuffered Channels — The Direct Handoff Optimization

When you create `make(chan int)` (no capacity), `dataqsiz = 0` and `buf = nil`. There's **no buffer**. This forces a **synchronous handoff**: sender and receiver must rendezvous.

```go
// file: main.go
package main

import "fmt"

func main() {
	ch := make(chan int)  // unbuffered

	go func() {
		ch <- 42  // sender
	}()

	x := <-ch  // receiver
	fmt.Println(x)
}
```

**MEMORY TRACE: Unbuffered send/receive**

```
Initial state: ch = make(chan int) — unbuffered
  hchan at 0xC000010080:
    qcount:  0
    dataqsiz: 0               ← NO buffer
    buf:      nil             ← no circular buffer allocated
    sendx:    0
    recvx:    0
    sendq:    empty
    recvq:    empty


Scenario A: Sender arrives first (ch <- 42 before receiver ready)
  
  Step 1: G2 (goroutine) executes ch <- 42
    1. Lock hchan.lock
    2. Check: dataqsiz == 0 → unbuffered, no buffer to write to
    3. Check: any waiting receivers in recvq? NO
    4. G2 must BLOCK:
         a. Create sudog for G2
         b. sudog.elem = pointer to value 42
         c. Add sudog to sendq
         d. goparkunlock(&hchan.lock) → parks G2, unlocks mutex
    
    hchan at 0xC000010080:
      sendq: [G2:42]  ← G2 waiting, holding value 42
      recvq: empty


  Step 2: main goroutine executes x := <-ch
    1. Lock hchan.lock
    2. Check: dataqsiz == 0 → unbuffered
    3. Check: any waiting senders in sendq? YES → G2
    4. DIRECT COPY from G2's sudog.elem to main's x:
         x = 42  (no buffer involved!)
    5. Dequeue G2 from sendq
    6. Wake G2 (schedule to run)
    7. Unlock hchan.lock
    
    Result:
      x = 42
      G2 unblocked, continues execution
      Channel is empty again


Scenario B: Receiver arrives first (<-ch before sender ready)
  
  Symmetric: receiver blocks in recvq, sender later copies directly to receiver's variable.


KEY INSIGHT:
  Unbuffered channels do DIRECT COPY from sender's stack to receiver's stack.
  No buffer allocation. No intermediate copy.
  This is why unbuffered channels are called "synchronous" — they force synchronization.
```

> **In plain English:** Unbuffered channels are like two people passing a baton. They must both be present for the handoff. If sender arrives first, they wait holding the baton. If receiver arrives first, they wait with an empty hand. Only when both are ready does the baton pass directly between them — no table to set it on (no buffer).

---

### 4.5 Close Operation — `close(ch)`

Closing a channel sets `hchan.closed = 1` and wakes ALL goroutines waiting in `sendq` and `recvq`.

```go
// file: main.go
package main

import "fmt"

func main() {
	ch := make(chan int, 2)
	ch <- 10
	close(ch)
	x := <-ch      // 10
	y := <-ch      // 0 (zero value)
	z, ok := <-ch  // 0, false
	fmt.Println(x, y, z, ok)
}
```

**MEMORY TRACE: Close operation**

```
Initial state:
  hchan at 0xC000010080:
    qcount:  1
    dataqsiz: 2
    closed:   0  ← open
    buf → [10][ ]


Step 1: close(ch)
  1. Lock hchan.lock
  2. Check: is closed already? closed == 0 → NO
  3. Set closed = 1
  4. Wake ALL goroutines in recvq:
       for each sudog in recvq:
         - copy zero value to sudog.elem
         - mark as "closed channel receive"
         - wake goroutine
  5. Wake ALL goroutines in sendq:
       - each sender panics: "send on closed channel"
  6. Unlock hchan.lock

  hchan at 0xC000010080:
    qcount:  1
    closed:   1  ← CLOSED
    buf → [10][ ]


Step 2: x := <-ch (first receive after close)
  1. Lock hchan.lock
  2. Check: closed == 1 AND qcount > 0? YES
       → still have buffered data, return it
  3. Copy buf[recvx] to x: x = 10
  4. Decrement qcount: qcount = 0
  5. Unlock hchan.lock

  Result: x = 10 (data from buffer)


Step 3: y := <-ch (second receive, buffer now empty)
  1. Lock hchan.lock
  2. Check: closed == 1 AND qcount == 0? YES
       → channel closed and empty, return zero value
  3. y = 0 (zero value for int)
  4. Unlock hchan.lock

  Result: y = 0 (zero value)


Step 4: z, ok := <-ch (third receive with ok idiom)
  1. Lock hchan.lock
  2. Check: closed == 1 AND qcount == 0? YES
  3. z = 0, ok = false
  4. Unlock hchan.lock

  Result: z = 0, ok = false (closed indicator)


KEY INSIGHTS:
  - close() drains existing buffered data first
  - After drain, all receives return zero value + ok=false
  - Sending to closed channel panics immediately
  - Closing closed channel panics: "close of closed channel"
  - Receiving from closed channel NEVER blocks (returns zero value)
```

> **In plain English:** Closing a channel is like closing a store. If there are still items on the shelf (buffer), customers can take them. Once the shelf is empty, the store hands out free "closed" signs (zero values) to anyone who enters. Trying to deliver new stock (send) after closing causes an alarm (panic).

---

## 5. Key Rules & Behaviors

### 5.1 Unbuffered channels block until both sender and receiver are ready

```go
ch := make(chan int)  // unbuffered

// This ALWAYS blocks until another goroutine receives:
ch <- 42
```

```
  Unbuffered send flow:
  
  Step 1: G1 executes ch <- 42
    → No buffer to write to
    → Check recvq: empty
    → G1 parks in sendq
    
  Step 2: G2 executes <-ch
    → Check sendq: G1 is waiting
    → Direct copy: 42 from G1's stack to G2's stack
    → Wake G1
```

**Why (Section 4.4):** Unbuffered channels have `dataqsiz = 0` and `buf = nil`. There's no place to store the value. The runtime must park the sender in `sendq` until a receiver arrives. This is the **synchronization guarantee**: sender and receiver rendezvous.

---

### 5.2 Buffered channels decouple sender and receiver

```go
ch := make(chan int, 3)  // capacity 3

ch <- 1  // doesn't block
ch <- 2  // doesn't block
ch <- 3  // doesn't block
ch <- 4  // BLOCKS — buffer full
```

```
  Buffer state after 3 sends:
  
  hchan:
    qcount:  3
    dataqsiz: 3
    buf → [1][2][3]  ← FULL
    
  Fourth send:
    → qcount == dataqsiz → buffer full
    → G parks in sendq
```

**Why (Section 4.2):** The circular buffer acts as a queue. Sends only block when `qcount == dataqsiz`. This decouples timing: sender can run ahead of receiver (up to buffer capacity).

---

### 5.3 Receiving from a closed channel returns zero value immediately

```go
ch := make(chan int, 1)
ch <- 42
close(ch)

x := <-ch       // 42 (from buffer)
y := <-ch       // 0 (zero value, never blocks)
z, ok := <-ch  // 0, false
```

```
  After close():
    closed = 1
    
  Receive behavior:
    if qcount > 0 → return buffered data
    if qcount == 0 → return zero value, never block
```

**Why (Section 4.5):** When `closed == 1`, the runtime checks `qcount`. If buffer has data, drain it. Once empty, return zero value with `ok = false`. This guarantees receivers never block on a closed channel.

---

### 5.4 Sending to a closed channel panics

```go
ch := make(chan int)
close(ch)
ch <- 42  // panic: send on closed channel
```

```
  close(ch) sets closed = 1
  
  Next send:
    1. Lock hchan.lock
    2. Check: closed == 1? YES
    3. Unlock hchan.lock
    4. panic("send on closed channel")
```

**Why (Section 4.5):** The runtime explicitly checks `hchan.closed` before any send operation. If `closed == 1`, it panics immediately. This prevents corrupting the channel state or waking receivers with unexpected data.

---

### 5.5 Closing a closed channel panics

```go
ch := make(chan int)
close(ch)
close(ch)  // panic: close of closed channel
```

```
  Second close(ch):
    1. Lock hchan.lock
    2. Check: closed == 1? YES
    3. panic("close of closed channel")
```

**Why (Section 4.5):** Double-close is a logic error. If allowed, it could wake the same receivers twice or corrupt `sendq`/`recvq` state. The runtime detects it early and panics.

---

### 5.6 Nil channels block forever

```go
var ch chan int  // nil

ch <- 42   // blocks forever (no panic)
x := <-ch  // blocks forever (no panic)
close(ch)  // panic: close of nil channel
```

```
  Nil channel means ch == nil (no hchan allocated)
  
  Send/receive on nil:
    → runtime checks if ch == nil → blocks forever (parks goroutine permanently)
  
  Close on nil:
    → panic immediately
```

**Why:** This is intentional. Nil channels let you "disable" a case in `select` without removing it. Sending/receiving blocks forever (select will skip that case). Closing nil is undefined → panic.

---

## 6. Interview Practice (MANDATORY — Active Recall Format)

### 6.1. MCQs (Multiple Choice Questions)

**Q1.** What is the size of a channel variable `ch := make(chan int, 100)` on a 64-bit system?

A) 8 bytes (one pointer)  
B) 100 * 8 bytes (buffer size)  
C) 96 bytes (hchan struct size)  
D) 808 bytes (hchan + buffer)

> [!success]- Answer
> **A** — The channel variable `ch` is a **pointer** to the `hchan` struct on the heap. `sizeof(ch) = 8 bytes` (64-bit pointer). The `hchan` struct itself (~96 bytes) + buffer (100 * 8 = 800 bytes) live on the heap, but `ch` is just a pointer to that. (Section 4.1)

**Q2.** In a buffered channel `ch := make(chan int, 3)`, after sending 3 values, where is the fourth send operation blocked?

A) In the circular buffer at index 3  
B) In the `sendq` linked list  
C) The operation panics  
D) It wraps around and overwrites index 0

> [!success]- Answer
> **B** — When the buffer is full (`qcount == dataqsiz`), the runtime creates a `sudog` for the blocked goroutine and adds it to the `sendq` (sender wait queue). The goroutine is then parked until a receiver takes a value and wakes it. (Section 4.2)

**Q3.** What happens when you receive from a closed buffered channel that still has data in its buffer?

A) Immediate zero value return  
B) Panic: receive from closed channel  
C) Return the buffered data normally  
D) Block until buffer is drained

> [!success]- Answer
> **C** — The runtime checks `closed == 1 AND qcount > 0`. If true, it returns buffered data normally. Only after the buffer is fully drained (`qcount == 0`) do receives start returning zero values with `ok = false`. (Section 4.5)

**Q4.** Why do unbuffered channels use direct copy instead of going through a buffer?

A) Performance optimization to avoid memory allocation  
B) Because the hchan struct has no `buf` field for unbuffered  
C) Both: `dataqsiz = 0` means no buffer, so direct copy is the only option  
D) To enforce FIFO ordering

> [!success]- Answer
> **C** — Unbuffered channels have `dataqsiz = 0` and `buf = nil` (no buffer allocated). When sender and receiver rendezvous, the runtime copies the value directly from sender's `sudog.elem` to receiver's variable. This is both a consequence of no buffer AND a performance win (no intermediate allocation). (Section 4.4)

**Q5.** In the `hchan` struct, what does `sendx` represent?

A) Number of sends performed on the channel  
B) Index in the circular buffer where the next send writes  
C) Pointer to the next sender in `sendq`  
D) Size of the send queue

> [!success]- Answer
> **B** — `sendx` is the **write index** in the circular buffer. After each successful send, `sendx = (sendx + 1) % dataqsiz`. It wraps around when reaching capacity. `recvx` is the symmetric read index. (Section 4.1)

**Q6.** Which operation on a nil channel causes a panic (rather than blocking)?

A) Send: `ch <- 42`  
B) Receive: `<-ch`  
C) Close: `close(ch)`  
D) All of the above

> [!success]- Answer
> **C** — Sending and receiving on a nil channel block forever (the goroutine is parked). Only `close(nil)` panics immediately with "close of nil channel" because closing nil is undefined behavior. (Section 5.6)

**Q7.** After `close(ch)`, what happens to goroutines already waiting in `recvq`?

A) They stay blocked until new sends arrive  
B) They panic  
C) They are woken and receive zero values  
D) They are removed from the queue and discarded

> [!success]- Answer
> **C** — The `close()` operation wakes ALL goroutines in `recvq`. Each receives the zero value for the channel's element type with `ok = false`. This ensures receivers don't block forever when a channel is closed. (Section 4.5)

**Q8.** When does `qcount` in the `hchan` struct decrease?

A) On every send operation  
B) On every receive operation that reads from the buffer  
C) When the channel is closed  
D) When a goroutine is added to `sendq`

> [!success]- Answer
> **B** — `qcount` tracks the number of elements currently in the buffer. It increments on successful sends (when data goes into buffer) and decrements on successful receives (when data is taken from buffer). It does NOT change when goroutines block in `sendq`/`recvq` or when the channel is closed. (Section 4.1)

**Q9.** What is the `sudog` struct used for in channel operations?

A) It's the internal name for the circular buffer  
B) It wraps a goroutine waiting in `sendq` or `recvq`, holding metadata like the value to send/receive  
C) It's a debugging structure for race detection  
D) It stores the channel's lock state

> [!success]- Answer
> **B** — A `sudog` (pseudo-goroutine) wraps a blocked goroutine when it's parked in `sendq` or `recvq`. It holds fields like `elem` (pointer to the value being sent/received) and links to form a linked list. When the goroutine is woken, the runtime uses the `sudog` to complete the operation. (Section 4.2, Section 4.3)

**Q10.** Why does sending to a closed channel panic instead of returning an error?

A) For performance — checking closed status on every send would be too slow  
B) Because Go channels don't return errors  
C) To catch programming bugs early — sending after close is always a logic error  
D) Historical accident

> [!success]- Answer
> **C** — Sending to a closed channel is a logic error in your program flow. Go panics immediately to surface the bug. If it returned an error, developers might accidentally ignore it, leading to silent data loss or race conditions. Panicking forces you to fix the coordination between sender and closer. (Section 5.4)

**Q11.** In a buffered channel with capacity 5, if `sendx = 3` and `recvx = 1`, where is the data stored?

A) Only at index 1-3  
B) Wrapped: indices 1, 2, 3  
C) Depends on `qcount`  
D) Cannot determine without `qcount`

> [!success]- Answer
> **D** — You need `qcount` to know how full the buffer is. If `qcount = 2`, data is at indices 1, 2. If `qcount = 4`, data wraps: indices 1, 2, 3, 4. `sendx` and `recvx` alone don't tell you occupancy — they're just write/read cursors. The buffer is a circular array. (Section 4.1, Section 4.2)

**Q12.** Which of the following is true about the `hchan.lock` mutex?

A) It's only used for buffered channels  
B) It's held for the entire duration of a blocked send/receive  
C) It's locked before any operation and unlocked before parking a goroutine  
D) It's a read-write lock for performance

> [!success]- Answer
> **C** — The runtime locks `hchan.lock` at the start of every send/receive/close operation to safely check channel state. If the goroutine needs to block, the runtime parks it using `goparkunlock()`, which unlocks the mutex before parking. This prevents holding the lock while blocked (deadlock). (Section 4.2, Section 4.3)

---

### 6.2. Predict the Output

**Problem 1:**

```go
package main
import "fmt"

func main() {
	ch := make(chan int, 2)
	ch <- 1
	ch <- 2
	close(ch)
	fmt.Println(<-ch)
	fmt.Println(<-ch)
	fmt.Println(<-ch)
}
```

> [!success]- Output
> ```
> 1
> 2
> 0
> ```
> **Why:** First two receives drain the buffered data (1, 2). Third receive sees `closed == 1` and `qcount == 0`, so it returns the zero value for `int` (0). Receiving from a closed empty channel never blocks. (Section 4.5)

**Problem 2:**

```go
package main

func main() {
	ch := make(chan int)
	ch <- 42
}
```

> [!success]- Output
> ```
> fatal error: all goroutines are asleep - deadlock!
> ```
> **Why:** Unbuffered send blocks until a receiver is ready. Here, `main` goroutine blocks at `ch <- 42` because no other goroutine exists to receive. The runtime detects all goroutines are blocked → deadlock panic. (Section 3 — mistake example, Section 4.4)

**Problem 3:**

```go
package main
import "fmt"

func main() {
	var ch chan int
	fmt.Println(ch == nil)
	close(ch)
}
```

> [!success]- Output
> ```
> true
> panic: close of nil channel
> ```
> **Why:** `var ch chan int` is a nil channel (no `make`). `ch == nil` is true. Attempting `close(ch)` on nil panics immediately. (Section 5.6)

**Problem 4:**

```go
package main
import "fmt"

func main() {
	ch := make(chan int, 1)
	ch <- 10
	close(ch)
	ch <- 20
	fmt.Println(<-ch)
}
```

> [!success]- Output
> ```
> panic: send on closed channel
> ```
> **Why:** After `close(ch)`, the channel's `closed` field is set to 1. The next send (`ch <- 20`) checks `closed == 1` and panics before reaching the receive. (Section 5.4)

**Problem 5:**

```go
package main
import "fmt"

func main() {
	ch := make(chan int, 3)
	go func() {
		for i := 1; i <= 5; i++ {
			ch <- i
		}
		close(ch)
	}()
	
	for v := range ch {
		fmt.Print(v, " ")
	}
}
```

> [!success]- Output
> ```
> 1 2 3 4 5 
> ```
> **Why:** The `for v := range ch` loop receives until the channel is closed. The goroutine sends 5 values then closes. After the buffer drains and `close` is detected, the range loop exits cleanly. No deadlock because the sender closes the channel. (Section 4.5, Section 5.3)

**Problem 6:**

```go
package main
import "fmt"

func main() {
	ch := make(chan int)
	go func() {
		ch <- 42
		close(ch)
	}()
	
	v, ok := <-ch
	fmt.Println(v, ok)
	v, ok = <-ch
	fmt.Println(v, ok)
}
```

> [!success]- Output
> ```
> 42 true
> 0 false
> ```
> **Why:** First receive gets the value 42 (channel is open, `ok = true`). The goroutine then closes the channel. Second receive sees `closed == 1` and `qcount == 0` (buffer empty), returns zero value with `ok = false`. (Section 4.5, Section 5.3)

**Problem 7:**

```go
package main

func main() {
	ch := make(chan int)
	close(ch)
	<-ch
}
```

> [!success]- Output
> ```
> (program exits successfully, no panic)
> ```
> **Why:** Receiving from a closed channel doesn't panic — it returns the zero value immediately. The program receives 0 (zero value for int), then main exits. No deadlock because receives from closed channels never block. (Section 5.3)

**Problem 8:**

```go
package main
import "fmt"

func main() {
	ch := make(chan int, 2)
	ch <- 1
	ch <- 2
	fmt.Println(len(ch), cap(ch))
	<-ch
	fmt.Println(len(ch), cap(ch))
}
```

> [!success]- Output
> ```
> 2 2
> 1 2
> ```
> **Why:** `len(ch)` returns `hchan.qcount` (current number of elements). `cap(ch)` returns `hchan.dataqsiz` (max capacity). After first two sends, `qcount = 2`. After one receive, `qcount = 1`. Capacity never changes. (Section 4.1)

---

### 6.3. Trick Questions (Interview Traps)

**Trap #1:** What's wrong with this producer-consumer pattern?

```go
func produce(ch chan int) {
	for i := 0; i < 100; i++ {
		ch <- i
	}
	// BUG: forgot to close(ch)
}

func main() {
	ch := make(chan int)
	go produce(ch)
	
	for v := range ch {  // BUG: deadlock after 100 receives
		fmt.Println(v)
	}
}
```

> [!success]- Answer
> **Bug:** The `produce` function never calls `close(ch)`. The `for v := range ch` loop in main will receive all 100 values, then block forever waiting for more (or for the channel to close). The runtime detects deadlock after `produce` goroutine exits.
>
> **Why:** `for range ch` only exits when the channel is closed. Without `close(ch)`, the receiver blocks indefinitely after the last send.
>
> **Fix:**
> ```go
> func produce(ch chan int) {
>     for i := 0; i < 100; i++ {
>         ch <- i
>     }
>     close(ch)  // signal done
> }
> ```
> (Section 4.5, Section 5.3)

**Trap #2:** Why does this code panic?

```go
func broadcast(ch chan int, value int) {
	close(ch)
	ch <- value  // BUG: send after close
}
```

> [!success]- Answer
> **Bug:** You can't send to a closed channel. After `close(ch)`, the `ch <- value` operation checks `hchan.closed == 1` and panics immediately with "send on closed channel."
>
> **Why:** Sending after close is a logic error. The runtime enforces this by panicking to prevent data corruption.
>
> **Pattern to avoid:** Don't close channels from the sender side if other senders might still be active. Close only from a coordinator goroutine or the last sender.
> (Section 5.4)

**Trap #3:** What's the race condition in this buffered channel usage?

```go
func worker(ch chan int, wg *sync.WaitGroup) {
	defer wg.Done()
	v := <-ch
	process(v)
}

func main() {
	ch := make(chan int, 10)
	var wg sync.WaitGroup
	
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go worker(ch, &wg)
		ch <- i
	}
	
	close(ch)  // BUG: race with workers still receiving
	wg.Wait()
}
```

> [!success]- Answer
> **Bug:** There's no race in the channel itself (channels are thread-safe), but there's a logic bug: `close(ch)` is called immediately after the loop, potentially before all workers have received their values. If a worker is slow, it might try to receive after close, getting zero value instead of its assigned work.
>
> **Why:** The sends (`ch <- i`) are non-blocking (buffer has capacity 10), so the loop completes fast. But workers run concurrently — no guarantee they've all received yet.
>
> **Fix:** Close the channel only after all sends are complete AND you want workers to exit:
> ```go
> for i := 0; i < 10; i++ {
>     ch <- i  // all sends first
> }
> close(ch)   // signal done
> 
> for i := 0; i < 10; i++ {
>     wg.Add(1)
>     go worker(ch, &wg)
> }
> wg.Wait()
> ```
> Or better: don't close if you know the exact count — let `wg.Wait()` handle synchronization.
> (Section 4.5)

**Trap #4:** Why does this select block forever?

```go
func main() {
	var ch chan int  // nil channel
	
	select {
	case ch <- 42:
		fmt.Println("sent")
	case <-ch:
		fmt.Println("received")
	}
}
```

> [!success]- Answer
> **Bug:** Both cases operate on a nil channel. Sending and receiving on nil channels block forever. Since BOTH cases block, the `select` has no unblocked case to choose → the goroutine parks forever (deadlock).
>
> **Why:** Nil channels are intentionally designed to block forever so you can disable a select case by setting the channel to nil.
>
> **Fix:** Initialize the channel: `ch := make(chan int)` (though this would still deadlock without a goroutine on the other side). Or use a default case:
> ```go
> select {
> case ch <- 42:
>     fmt.Println("sent")
> default:
>     fmt.Println("channel not ready")
> }
> ```
> (Section 5.6)

**Trap #5:** What's wrong with this error handling?

```go
func fetchData(ch chan int) error {
	defer close(ch)  // BUG: panics if called multiple times
	
	for i := 0; i < 10; i++ {
		ch <- i
	}
	return nil
}

func main() {
	ch := make(chan int, 10)
	go fetchData(ch)
	go fetchData(ch)  // BUG: double close
	
	for v := range ch {
		fmt.Println(v)
	}
}
```

> [!success]- Answer
> **Bug:** Two goroutines both call `defer close(ch)`. The second `close(ch)` panics with "close of closed channel."
>
> **Why:** Closing a closed channel is a runtime panic. If multiple goroutines can call `close()`, you have a coordination problem.
>
> **Fix pattern — single closer:**
> ```go
> func main() {
>     ch := make(chan int, 10)
>     var wg sync.WaitGroup
>     wg.Add(2)
>     
>     worker := func() {
>         defer wg.Done()
>         for i := 0; i < 10; i++ {
>             ch <- i
>         }
>     }
>     
>     go worker()
>     go worker()
>     
>     go func() {
>         wg.Wait()
>         close(ch)  // single closer after all workers done
>     }()
>     
>     for v := range ch {
>         fmt.Println(v)
>     }
> }
> ```
> **Rule:** Only one goroutine should close a channel, typically the producer or a coordinator.
> (Section 5.5)

---

### 6.4. Coding Problems (Hands-On)

**Problem 1:** Bounded Worker Pool (Medium — 15 min)

Implement a worker pool that processes jobs from a channel with a maximum of `N` concurrent workers. Jobs should be sent to a buffered channel, and workers should process them concurrently.

```go
type Job func()

// TODO: Implement WorkerPool
func WorkerPool(jobs <-chan Job, numWorkers int) {
	// Your code here:
	// - Launch numWorkers goroutines
	// - Each worker receives jobs from the channel
	// - Workers exit when channel is closed
}

// Example usage:
func main() {
	jobs := make(chan Job, 100)
	
	// Start worker pool
	WorkerPool(jobs, 5)
	
	// Send jobs
	for i := 0; i < 20; i++ {
		i := i
		jobs <- func() {
			fmt.Printf("Processing job %d\n", i)
			time.Sleep(100 * time.Millisecond)
		}
	}
	
	close(jobs)
	time.Sleep(3 * time.Second)  // Wait for workers
}
```

> [!success]- Solution
> ```go
> func WorkerPool(jobs <-chan Job, numWorkers int) {
>     var wg sync.WaitGroup
>     
>     for i := 0; i < numWorkers; i++ {
>         wg.Add(1)
>         go func(workerID int) {
>             defer wg.Done()
>             for job := range jobs {  // receive until channel closed
>                 job()
>             }
>         }(i)
>     }
>     
>     // Wait for all workers to finish in a separate goroutine
>     go func() {
>         wg.Wait()
>     }()
> }
> ```
>
> **Key points:**
> - Use `for job := range jobs` to receive until the channel is closed (Section 4.5, Section 5.3)
> - Each worker is a goroutine that processes jobs concurrently
> - `defer wg.Done()` ensures worker count decrements even if job panics
> - The channel acts as a job queue — workers pull from shared channel (Section 4.3)

**Problem 2:** Timeout Receiver (Medium — 15 min)

Write a function that receives from a channel with a timeout. If no value arrives within the timeout duration, return an error.

```go
import "time"

// ReceiveWithTimeout receives from ch with a timeout.
// Returns the received value and nil error on success.
// Returns zero value and error on timeout.
func ReceiveWithTimeout(ch <-chan int, timeout time.Duration) (int, error) {
	// Your code here
}

// Test:
func main() {
	ch := make(chan int)
	
	// Case 1: Timeout (no sender)
	val, err := ReceiveWithTimeout(ch, 100*time.Millisecond)
	fmt.Println(val, err)  // Should print: 0 timeout error
	
	// Case 2: Success (sender)
	go func() {
		time.Sleep(50 * time.Millisecond)
		ch <- 42
	}()
	val, err = ReceiveWithTimeout(ch, 200*time.Millisecond)
	fmt.Println(val, err)  // Should print: 42 <nil>
}
```

> [!success]- Solution
> ```go
> func ReceiveWithTimeout(ch <-chan int, timeout time.Duration) (int, error) {
>     select {
>     case val := <-ch:
>         return val, nil
>     case <-time.After(timeout):
>         return 0, fmt.Errorf("timeout after %v", timeout)
>     }
> }
> ```
>
> **Key points:**
> - `select` waits on multiple channel operations, taking the first that's ready
> - `time.After(timeout)` returns a channel that sends after the duration
> - If `ch` receives first → return value; if timer fires first → timeout error
> - This uses `select` (covered in T17), but the underlying channel behavior is from Section 4.3

**Problem 3:** Fan-In Pattern (Medium-Hard — 20 min)

Implement a fan-in function that merges multiple input channels into a single output channel. The output channel should close when all input channels are closed.

```go
// FanIn merges multiple channels into one.
// Closes the output channel when all inputs are closed.
func FanIn(channels ...<-chan int) <-chan int {
	// Your code here
}

// Test:
func main() {
	ch1 := make(chan int)
	ch2 := make(chan int)
	ch3 := make(chan int)
	
	out := FanIn(ch1, ch2, ch3)
	
	// Senders
	go func() {
		ch1 <- 1
		ch1 <- 2
		close(ch1)
	}()
	go func() {
		ch2 <- 3
		ch2 <- 4
		close(ch2)
	}()
	go func() {
		ch3 <- 5
		ch3 <- 6
		close(ch3)
	}()
	
	// Receiver
	for v := range out {
		fmt.Println(v)
	}
}
```

> [!success]- Solution
> ```go
> func FanIn(channels ...<-chan int) <-chan int {
>     out := make(chan int)
>     var wg sync.WaitGroup
>     
>     // Launch a goroutine for each input channel
>     for _, ch := range channels {
>         wg.Add(1)
>         go func(c <-chan int) {
>             defer wg.Done()
>             for v := range c {  // receive until c is closed
>                 out <- v        // forward to output
>             }
>         }(ch)
>     }
>     
>     // Close output when all inputs are drained
>     go func() {
>         wg.Wait()
>         close(out)
>     }()
>     
>     return out
> }
> ```
>
> **Key points:**
> - Each input channel gets a dedicated goroutine that forwards values to `out`
> - `for v := range c` exits when input channel `c` is closed (Section 4.5)
> - `wg.Wait()` ensures all input channels are fully drained before closing `out`
> - Closing `out` allows the main receiver's `for range out` to exit cleanly (Section 5.3)

**Problem 4:** Rate Limiter with Channels (Hard — 25 min)

Implement a rate limiter that allows at most `N` operations per second using a buffered channel as a token bucket.

```go
type RateLimiter struct {
	tokens chan struct{}
}

// NewRateLimiter creates a limiter allowing n operations per second.
func NewRateLimiter(n int) *RateLimiter {
	// Your code here
}

// Allow blocks until a token is available, then consumes it.
func (rl *RateLimiter) Allow() {
	// Your code here
}

// Test:
func main() {
	limiter := NewRateLimiter(5)  // 5 ops/sec
	
	for i := 0; i < 20; i++ {
		limiter.Allow()
		fmt.Printf("Request %d at %v\n", i, time.Now())
	}
}
```

> [!success]- Solution
> ```go
> type RateLimiter struct {
>     tokens chan struct{}
> }
> 
> func NewRateLimiter(n int) *RateLimiter {
>     rl := &RateLimiter{
>         tokens: make(chan struct{}, n),  // buffered channel, capacity n
>     }
>     
>     // Fill the bucket initially
>     for i := 0; i < n; i++ {
>         rl.tokens <- struct{}{}
>     }
>     
>     // Refill tokens at rate n per second
>     go func() {
>         ticker := time.NewTicker(time.Second / time.Duration(n))
>         defer ticker.Stop()
>         for range ticker.C {
>             select {
>             case rl.tokens <- struct{}{}:
>                 // Token added
>             default:
>                 // Bucket full, skip
>             }
>         }
>     }()
>     
>     return rl
> }
> 
> func (rl *RateLimiter) Allow() {
>     <-rl.tokens  // blocks if no tokens available
> }
> ```
>
> **Key points:**
> - Buffered channel acts as token bucket (Section 4.2, Section 5.2)
> - Initial fill gives burst capacity
> - Ticker goroutine refills tokens at constant rate (1/n seconds per token)
> - `select` with `default` prevents blocking if bucket is full (skip refill)
> - `Allow()` blocks on receive until token available — natural backpressure (Section 4.3)

---

### 6.5. What Would You Do? (Scenario Questions)

**Scenario 1:** Your HTTP server uses a worker pool with 100 goroutines pulling from an unbuffered channel. Under load, you notice p99 latency spikes. Profiling shows goroutines spending significant time blocked on channel send operations in the handler.

What would you do?

A) Increase worker count to 200  
B) Switch to a buffered channel with capacity 1000  
C) Use `select` with `default` to drop requests when workers are busy  
D) Add a timeout to the send operation

> [!success]- Model Answer
> **B is the pragmatic fix.** Switching to a buffered channel decouples the handler (sender) from the workers (receivers). The handler can drop work into the buffer and return immediately instead of blocking until a worker is ready.
>
> **Why the others are less ideal:**
> - A: More workers help throughput but don't solve the blocking send issue. If all 200 workers are busy, senders still block.
> - C: Dropping requests under load might be acceptable for non-critical endpoints, but most services prefer queueing + backpressure over silent drops.
> - D: Timeouts help prevent indefinite blocking, but you'd still need to handle the timeout (retry? error?). Buffering is simpler.
>
> **Production pattern:**
> ```go
> jobs := make(chan Job, 1000)  // buffer decouples sender and receiver
> 
> func handler(w http.ResponseWriter, r *http.Request) {
>     select {
>     case jobs <- extractJob(r):
>         w.WriteHeader(202)  // Accepted
>     case <-time.After(100 * time.Millisecond):
>         w.WriteHeader(503)  // Service Unavailable (queue full)
>     }
> }
> ```
> This combines buffering (B) with timeout (D) for best of both: non-blocking fast path + graceful degradation when overloaded.
> (Section 5.2, Section 4.2)

**Scenario 2:** You have a producer goroutine that sends 1000 items to a channel, then closes it. Multiple consumer goroutines range over the channel. Occasionally, you see "send on closed channel" panics.

What's the bug?

A) Consumers are still receiving when producer closes  
B) Producer is sending after calling `close(ch)`  
C) Multiple producers are closing the same channel  
D) Channel capacity is too small

> [!success]- Model Answer
> **B** — The panic "send on closed channel" means `ch <- value` is executed after `close(ch)`. This is a sequencing bug in the producer.
>
> **Possible causes:**
> 1. Producer has a loop AFTER close: `close(ch); ch <- x` — obvious bug
> 2. Producer has concurrent sends (e.g., goroutines inside producer) that outlive the close call
> 3. Multiple producers where one closes while others are still sending (variant of C)
>
> **Debug steps:**
> - Add logging before/after `close(ch)` to confirm it's called only once
> - Check if producer launches goroutines that send — they might race with close
> - Use `sync.WaitGroup` to ensure all producer goroutines finish before close
>
> **Fix pattern:**
> ```go
> func producer(ch chan int) {
>     var wg sync.WaitGroup
>     for i := 0; i < 10; i++ {
>         wg.Add(1)
>         go func(val int) {
>             defer wg.Done()
>             ch <- val
>         }(i)
>     }
>     wg.Wait()   // wait for all sends to complete
>     close(ch)   // now safe to close
> }
> ```
> (Section 5.4, Section 5.5)

**Scenario 3:** You're building a request cancellation system. When a user cancels, you want to stop all workers processing that request. You're considering closing a `done` channel to broadcast cancellation.

Is this a good pattern? What are the tradeoffs?

> [!success]- Model Answer
> **Yes, closing a channel to broadcast is a standard Go pattern.**
>
> **Why it works:**
> - Closing a channel wakes ALL goroutines waiting to receive (Section 4.5)
> - Workers can check `case <-done:` in a `select` to detect cancellation
> - No need for sync primitives — channel close is broadcast by design
>
> **Pattern:**
> ```go
> done := make(chan struct{})
> 
> // Workers
> for i := 0; i < 10; i++ {
>     go func() {
>         for {
>             select {
>             case <-done:
>                 return  // cancel detected
>             case job := <-jobs:
>                 process(job)
>             }
>         }
>     }()
> }
> 
> // Cancellation
> close(done)  // broadcasts to all workers
> ```
>
> **Tradeoffs:**
> - ✅ **Pro:** Simple, idiomatic, no race conditions
> - ✅ **Pro:** Works with arbitrary number of goroutines (dynamic)
> - ⚠️ **Con:** Channel can only be closed once — not reusable. For multi-use cancellation, use `context.Context` instead (covered in T19).
> - ⚠️ **Con:** Workers must explicitly check the `done` channel — if a worker is blocked on a long operation (e.g., I/O), it won't see cancellation until that operation completes.
>
> **When to use:**
> - One-shot cancellation (request-scoped)
> - Broadcasting "stop" signal to workers
>
> **When NOT to use:**
> - Need hierarchical cancellation (parent cancels children) → use `context.Context`
> - Need to carry cancellation reason/deadline → use `context.Context`
> (Section 4.5)

**Scenario 4:** Your service has a metrics collector that receives counter updates from 500 goroutines via an unbuffered channel. You notice the collector is a bottleneck — senders are blocking frequently.

What would you change?

A) Make the channel buffered with large capacity  
B) Have each goroutine aggregate locally and send batches  
C) Use atomic counters instead of channels  
D) All of the above are valid depending on requirements

> [!success]- Model Answer
> **D** — All three are valid depending on your requirements.
>
> **Option A: Buffered channel**
> - Quick fix: `ch := make(chan CounterUpdate, 10000)`
> - Pros: Minimal code change, senders rarely block
> - Cons: High memory if updates are large, doesn't reduce collector load
> - Use when: Updates are small, collector can keep up with average rate (just needs buffer for bursts)
>
> **Option B: Local batching**
> - Each goroutine batches updates locally, sends every 1 second or 100 updates
> - Pros: Reduces channel traffic 100x, collector processes fewer messages
> - Cons: More complex, delayed visibility of metrics
> - Use when: Exact real-time metrics aren't critical, collector is CPU-bound
>
> **Option C: Atomic counters**
> - Replace `ch <- CounterUpdate{name, delta}` with `atomic.AddInt64(&counters[name], delta)`
> - Pros: Zero blocking, lowest overhead, fastest
> - Cons: Global shared state (contention on hot counters), harder to extend (e.g., histograms)
> - Use when: Metrics are simple counters, contention is low
>
> **Production recommendation:**
> Start with **A** (buffered) for quick win. If collector is still overloaded, add **B** (batching). Reserve **C** (atomics) for ultra-hot paths (e.g., request counters in a 100k RPS service).
>
> **Hybrid pattern:**
> ```go
> // Local batch per goroutine
> type LocalMetrics struct {
>     counts map[string]int64
>     mu     sync.Mutex
> }
> 
> func (lm *LocalMetrics) Flush(ch chan<- CounterUpdate) {
>     lm.mu.Lock()
>     batch := lm.counts
>     lm.counts = make(map[string]int64)
>     lm.mu.Unlock()
>     
>     for name, delta := range batch {
>         ch <- CounterUpdate{name, delta}  // buffered ch
>     }
> }
> 
> // Flush every 1 second per goroutine
> ```
> (Section 5.2, Section 4.2)

---

## 7. Gotchas & Interview Traps (Table Format)

| Trap | Why it happens | How to spot it | Fix |
|------|----------------|----------------|-----|
| Unbuffered send blocks forever in `main` | Section 4.4 — unbuffered channels require receiver to be ready; `main` blocks at send, no other goroutine exists | `fatal error: all goroutines are asleep - deadlock!` | Launch sender in a goroutine: `go func() { ch <- x }()` OR use buffered channel |
| Sending to closed channel panics | Section 5.4 — `close(ch)` sets `closed = 1`; next send checks `closed` and panics | `panic: send on closed channel` in stack trace | Coordinate close: only one goroutine closes, after all senders are done |
| Closing closed channel panics | Section 5.5 — double `close()` is a logic error; runtime panics on second call | `panic: close of closed channel` | Use `sync.Once` to ensure close is called only once OR have a single designated closer |
| `for range ch` never exits | Section 4.5 — `for range` only exits when channel is closed; if producer never closes, receiver blocks forever after last send | Deadlock after producer exits; `for range` still waiting | Producer must `close(ch)` after all sends: `defer close(ch)` |
| Nil channel blocks forever | Section 5.6 — `ch == nil` means no `hchan` allocated; send/receive parks goroutine permanently | Goroutine hangs indefinitely; no panic | Initialize with `make`: `ch := make(chan T)` OR use in `select` to disable a case intentionally |
| Receiving after close returns zero value silently | Section 5.3 — closed empty channel returns zero value with `ok = false`; easy to miss if not using `, ok` idiom | Logic bug: receiver processes zero value as real data (e.g., `0` for int) | Use `, ok` idiom: `v, ok := <-ch; if !ok { break }` OR use `for range` which auto-detects close |
| Close from receiver instead of sender | Channel idiom: sender should close (knows when data ends); if receiver closes, other receivers panic on next send | `panic: send on closed channel` from sender after receiver closes | **Rule:** Only the sender (or coordinator) should close. Never close from receiver |
| Multiple senders, one closes | If multiple goroutines send, one calling `close()` causes others to panic on next send | `panic: send on closed channel` from one of the senders | Use a coordinator: `wg.Wait()` for all senders, then a single goroutine closes |

> **In plain English:** Channels are like doors with locks. Unbuffered channels need both sender and receiver at the door simultaneously (handshake). Buffered channels have a queue behind the door — sender can drop items and leave if space, receiver can take items and leave if available. Closing the door means "no more items coming" — anyone still trying to deliver items (send) trips an alarm (panic). Anyone checking for items (receive) sees the "closed" sign and gets a free "nothing here" token (zero value).

---

## 8. Performance & Tradeoffs (Production-Grounded)

### 8.1. The Production Scenario

Your order service does **10k RPM**. Every request spawns a goroutine that sends order data to a validation channel (`ch := make(chan Order, 100)`). Validators receive from the channel and write to the database. Here's the question: **is a buffered channel capacity of 100 enough, and what happens when it fills up?**

---

### 8.2. The Cost Comparison Table

| Pattern | What it costs | You'd see this in... | When it matters |
|---------|---------------|---------------------|-----------------|
| Unbuffered channel | ~200-500ns per send/receive (mutex lock + goroutine park/wake if no match) | Request/response pattern: `result := <-rpc.Call(req)` | Only matters if you're doing 100k+ ops/sec AND profiling shows channel contention. At 10k RPM, it's noise. |
| Buffered (capacity 100) | ~100-200ns per send/receive when buffer not full (mutex lock + copy to buffer); ~500ns+ when blocking | Job queue: `jobQueue := make(chan Job, 1000)` | Buffer cost is negligible. The blocking cost matters: if producers are HTTP handlers, blocking = tail latency spike. |
| Channel allocation (`make`) | ~96 bytes (hchan) + `capacity * elemsize` (buffer), 1 heap alloc | Created once per request: `ch := make(chan T)` in handler | Matters if you're allocating millions of channels/sec. Most services create channels sparingly (connection-level, not request-level). |
| Sending pointer vs value | Pointer: 8 bytes copied; Value: full struct copied | `ch <- &Order{}` vs `ch <- Order{}` (120-byte struct) | For small structs (<64 bytes), value is fine. For large (>128 bytes), pointer avoids copy cost. Profile before optimizing. |

---

### 8.3. What Actually Hurts (The Anti-Pattern)

The anti-pattern: **unbuffered channels in latency-sensitive hot paths.** Your handler sends a validation request to a worker via an unbuffered channel:

```go
func (h *Handler) Validate(w http.ResponseWriter, r *http.Request) {
    ch := make(chan bool)  // unbuffered
    h.validator <- ValidationRequest{Order: extractOrder(r), Result: ch}
    ok := <-ch  // blocks until validator responds
    if !ok {
        http.Error(w, "invalid", 400)
    }
}
```

At 5k RPM, if the validator pool is saturated (all workers busy), the handler blocks at `<-ch` waiting for a worker to become available. Each blocked handler holds a goroutine (4-8KB stack). Under load, you see:

- **p99 latency spikes:** handlers waiting for validator availability
- **Goroutine count climbs:** `runtime.NumGoroutine()` grows as handlers pile up
- **pprof shows:** goroutines parked in `chan receive`

The cost isn't the channel itself — it's the **synchronous blocking coupling handler latency to validator latency**.

**The fix:** Use a buffered channel for the request queue, decoupling handler from validator availability:

```go
// Global validator queue
validatorQueue := make(chan ValidationRequest, 1000)

func (h *Handler) Validate(w http.ResponseWriter, r *http.Request) {
    req := ValidationRequest{Order: extractOrder(r)}
    
    select {
    case validatorQueue <- req:
        w.WriteHeader(202)  // Accepted (async)
    default:
        http.Error(w, "queue full", 503)
    }
}
```

Now handlers return immediately (202 Accepted). Validators pull from the queue at their own pace. Under overload, the buffer absorbs burst traffic. If the buffer fills, you fail fast with 503 instead of accumulating blocked goroutines.

---

### 8.4. What to Measure (Concrete Commands)

```bash
# Benchmark channel send/receive cost
go test -bench=BenchmarkChannel -benchmem

# Example benchmark:
func BenchmarkUnbuffered(b *testing.B) {
    ch := make(chan int)
    go func() {
        for i := 0; i < b.N; i++ {
            <-ch
        }
    }()
    for i := 0; i < b.N; i++ {
        ch <- i
    }
}

func BenchmarkBuffered(b *testing.B) {
    ch := make(chan int, 100)
    go func() {
        for i := 0; i < b.N; i++ {
            <-ch
        }
    }()
    for i := 0; i < b.N; i++ {
        ch <- i
    }
}

# Profile goroutine blocking on channels
go tool pprof http://localhost:6060/debug/pprof/goroutine
# Look for: runtime.chan send, runtime.chan recv

# Count goroutines waiting on channels at runtime
curl http://localhost:6060/debug/pprof/goroutine?debug=2 | grep "chan send\|chan receive"

# Check channel buffer usage (if using buffered channels):
// Add metrics in your code:
fmt.Printf("Channel len: %d, cap: %d\n", len(ch), cap(ch))
// If len == cap frequently → buffer too small, senders blocking
// If len << cap always → buffer too large, wasting memory
```

**Minimal benchmark comparing unbuffered vs buffered:**

```go
package main

import (
	"testing"
)

func BenchmarkUnbuffered(b *testing.B) {
	ch := make(chan int)
	done := make(chan bool)
	
	go func() {
		for i := 0; i < b.N; i++ {
			<-ch
		}
		done <- true
	}()
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		ch <- i
	}
	<-done
}

func BenchmarkBuffered100(b *testing.B) {
	ch := make(chan int, 100)
	done := make(chan bool)
	
	go func() {
		for i := 0; i < b.N; i++ {
			<-ch
		}
		done <- true
	}()
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		ch <- i
	}
	<-done
}
```

Run: `go test -bench=. -cpu=1`

Typical results:
```
BenchmarkUnbuffered     5000000    300 ns/op
BenchmarkBuffered100   10000000    150 ns/op
```

Buffered is ~2x faster when sender and receiver are balanced (no blocking). The gap widens when sender is bursty.

---

## 9. Common Misconceptions

| Misconception | Reality |
|---------------|---------|
| "Channels are slow" | Channels are ~100-500ns per operation. That's "slow" compared to atomic ops (~5ns) but fast enough for most coordination. Don't optimize before profiling. |
| "Always use buffered channels for performance" | Buffering helps decouple sender/receiver timing, but adds memory cost and can hide backpressure. Use unbuffered for synchronization, buffered for queueing. |
| "Channel capacity is the max queue size" | Correct, but remember: when buffer is full, senders block. If you need guaranteed non-blocking sends, use `select` with `default`. |
| "Closing a channel stops sends immediately" | No — close only prevents NEW sends. Buffered data is still drained by receivers. Close is a "no more coming" signal, not "stop receiving." |
| "Can reuse a closed channel by reopening it" | No — once closed, a channel stays closed forever. You must allocate a new channel. |
| "`make(chan T, 0)` and `make(chan T)` are different" | They're identical. Both create unbuffered channels (`dataqsiz = 0`, `buf = nil`). |
| "Channels leak memory if not closed" | No — channels are garbage collected like any heap object when unreferenced. Close is for signaling "done," not for cleanup. |
| "Sending on nil channel panics" | No — it blocks forever (goroutine is parked). Only `close(nil)` panics. |

---

## 10. When to Use (Decision Tree)

**Use unbuffered channel when:**
- You need **synchronization** (sender and receiver must rendezvous)
- Example: RPC request/response, handoff confirmation

**Use buffered channel when:**
- You need **decoupling** (sender shouldn't wait for receiver)
- Example: job queue, event stream, rate limiting

**Use channel capacity as a semaphore:**
- Limit concurrency: `sem := make(chan struct{}, 10)` (max 10 concurrent ops)

**Close a channel when:**
- Signaling "no more data" to multiple receivers (broadcast)
- Example: cancel signal, producer done

**Don't use channels when:**
- Simple atomic counters suffice (`sync/atomic`)
- Protecting shared state already covered by mutex (`sync.Mutex`)
- Fire-and-forget with no coordination needed (just launch goroutine)

---

## 11. Real Interview Stories

**Story 1:** "I was asked to debug a deadlock. The code had `ch := make(chan int); ch <- 42; fmt.Println(<-ch)` in main. I explained that unbuffered send blocks until a receiver is ready, but here main is the only goroutine — it blocks at send, so it never reaches receive. The interviewer asked how to fix it. I said either launch the send in a goroutine (`go func() { ch <- 42 }()`) or use a buffered channel (`ch := make(chan int, 1)`). They followed up: 'Which is idiomatic?' I said buffered is safer here because you're not coordinating between goroutines — you're just passing a value to yourself. The unbuffered goroutine fix works but is overkill for this case."

**Story 2:** "They gave me code where a worker pool ranged over a channel, but the producer never closed the channel. The `for range` loop hung after all items were sent. I explained that `for range ch` only exits when the channel is closed — without `close(ch)`, the receivers wait indefinitely for more data. The fix was adding `defer close(ch)` in the producer. The interviewer then asked: 'What if there are multiple producers?' I said you need a coordinator goroutine that waits for all producers (via `sync.WaitGroup`), then closes the channel once. Only one closer."

**Story 3:** "I was asked why their HTTP handler had p99 latency spikes. They showed me code where the handler sent a job to a worker via an unbuffered channel and waited for the result on another unbuffered channel. I explained that when workers are busy, the handler blocks on the send — unbuffered channels force synchronous handoff. The fix was using a buffered channel for the job queue so handlers could drop work and return immediately. They asked about capacity — I said start with 10x peak RPS as a rule of thumb, then tune based on monitoring `len(ch) == cap(ch)` frequency."

---

## 12. Final Verbal Answer (If Interviewer Says: "Explain Channels")

Go channels are typed, thread-safe queues that let goroutines communicate without sharing memory. Under the hood, a channel is a pointer to an `hchan` struct on the heap. That struct has three main parts: a circular buffer for holding values, a queue of goroutines waiting to send, and a queue of goroutines waiting to receive. Every operation locks a mutex, checks state, and either moves data or parks the goroutine.

Unbuffered channels have no buffer — they force a synchronous handoff. When you send, the runtime checks if a receiver is waiting. If yes, it copies the value directly from sender to receiver and wakes the receiver. If no receiver, the sender blocks in the send queue until one arrives. It's a rendezvous.

Buffered channels have a circular buffer. Sends only block when the buffer is full. Receives only block when the buffer is empty. This decouples timing — sender can run ahead of receiver up to the buffer capacity.

Closing a channel sets a flag and wakes all waiting goroutines. Receivers still drain any buffered data, then start getting zero values with `ok = false`. Sending to a closed channel panics because it's a logic error — your code tried to deliver data after signaling "no more data coming."

The big trap is forgetting to close. If a producer never closes and a consumer is ranging over the channel, the consumer blocks forever after the last item. The idiom is: sender closes. Another trap is closing from multiple goroutines — double close panics. Use a coordinator with `sync.WaitGroup` if you have multiple senders.

---

## 13. Preview: What's Next

You now understand **how channels work internally** (hchan, circular buffer, wait queues) and **when to use buffered vs unbuffered** (synchronization vs decoupling).

**Next topics that build on this:**
- [[T16 Buffered vs Unbuffered Channels]] — deeper dive on semantics, performance, and when to use which
- [[T17 Select Statement Internals]] — how `select` multiplexes channel operations, random case selection, and compiler optimizations
- [[T19 Context Package Internals]] — how `context.Context` uses channels for cancellation and timeout propagation

**Questions you should be able to answer after this note:**
1. What are the three main fields in the `hchan` struct? (buffer, sendq, recvq)
2. Why does sending to a closed channel panic? (prevents data corruption after "done" signal)
3. What's the direct-copy optimization for unbuffered channels? (sender copies value directly to receiver's variable, bypassing buffer)
4. When would you use a buffered channel over unbuffered? (when you need to decouple sender and receiver timing)

**Try explaining to a friend:**
"Channels are like mailboxes with locks. Unbuffered channels are direct handoffs — sender and receiver must meet. Buffered channels have slots — you can drop letters in if there's space, pick up letters if there are any. Closing the mailbox means 'no more mail coming' — you can still take what's left, but trying to deliver new mail after that is an error."

---

> See [[Glossary]] for term definitions.
