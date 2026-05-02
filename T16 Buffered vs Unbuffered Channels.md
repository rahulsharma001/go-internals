# T16 Buffered vs Unbuffered Channels

> **Reading Guide**: Sections 1-3 and 6 are essential first read (20 min).
> Sections 4-5 deepen understanding (15 min).
> Sections 7-12 are interview-specific — read closer to interview day.
> Section 13 is your comprehensive interview Q&A bank → [[questions/T16 Buffered vs Unbuffered Channels - Interview Questions]]
> Something not clicking? → [[simplified/T16 Buffered vs Unbuffered Channels - Simplified]]
> Full runtime send/recv paths live in → [[T15 Channel Internals]]

---

## 0. Prerequisites

Complete these before this topic (or read them in parallel if you only need a refresher):

- [[T15 Channel Internals]] — same `hchan` struct for both variants; this note is about **semantics and choosing capacity**
- [[prerequisites/P03 Mutex & Concurrency Safety Basics]] — channels use an internal mutex; you compare channel vs mutex in design questions
- [[prerequisites/P08 OS Threads vs Green Threads]] — why decoupling producers and consumers matters at all

---

## 1. Concept

**Buffered and unbuffered channels are the same runtime type (`hchan`) with different capacities.**  

`make(chan Order, 0)` (or `make(chan Order)` — zero is default) builds a channel **with no ring buffer**. Every send waits for a matching receive, and vice versa. That is **synchronization by meeting in the middle**.

`make(chan Order, k)` where `k > 0` builds **k slots** in a ring buffer. Send only blocks when all `k` slots are full; receive only blocks when the buffer is empty. That is **decoupling in time**, up to `k` steps.

---

## 2. Core Insight (TL;DR)

**Capacity is `dataqsiz` on the heap struct:** `dataqsiz == 0` means **unbuffered** (`buf == nil`). **`dataqsiz > 0` means buffered** — a real buffer array holds values until somebody receives them.  

**Interview gold:** Explain **blocking conditions** precisely (full vs empty vs closed). Explain **coordination**: unbuffered for "we both must be ready," buffered for **bounded queues, bursts, semaphores, and backlog with a ceiling**. Admit **latency vs memory** trade-offs — a big buffer hides slow consumers until it fills, then your producers stall hard.

---

## 3. Mental Model (Lock this in)

### The shelf vs the handshake

**Unbuffered** is **hand-to-hand.** The worker handing a package **stands still** until the next worker grabs it. Nobody drops the box on the floor — there **is no floor**.

**Buffered** is **a finite shelf.** You can stack up to `k` boxes. If the shelf is full, **you stop loading** until someone takes something off.

### The Mistake That Teaches You — "buffer solves deadlock"

```go
package main

func main() {
	ch := make(chan int, 1)
	ch <- 1
	ch <- 2 // blocks forever if nobody receives
}
```

**What you'd expect:** Size 1 means "never block — one slot absorbs everything."

**What actually happens:** After one send fills the shelf, **the second send blocks** until someone receives. Capacity is not background magic — it's a **bounded queue**.

---

## 4. How It Actually Works (Internals) [INTERMEDIATE → ADVANCED]

Everything below shares the **`hchan` layout from [[T15 Channel Internals]]**. The behavioral split is **`dataqsiz` and `buf`**.

```go
// file: src/runtime/chan.go (conceptual excerpt)
type hchan struct {
	qcount   uint
	dataqsiz uint   // 0 = unbuffered, >0 = buffered
	buf      unsafe.Pointer // nil when dataqsiz == 0
	recvq    waitq
	sendq    waitq
	lock     mutex
}
```

### 4.1 Same header, different storage

**Concept-first:** When `dataqsiz` is zero, **`qcount` stays zero** — there is no ring buffer counting elements sitting between sender and receiver. The channel still has `sendq` and `recvq` lists for goroutines waiting to handshake.

When `dataqsiz` is `k`, **`qcount`** runs from `0` to `k` as values sit in **`buf`**. Indices advance with **`sendx` / `recvx`** and wrap with **`(i + 1) % dataqsiz`**.

**MEMORY TRACE: `make` unbuffered vs buffered**

```go
// file: main.go — two channels in one process
package main

type Order struct{ ID int }

func main() {
	ub := make(chan Order)    // capacity 0
	bf := make(chan Order, 2) // capacity 2
	_, _ = ub, bf
}
```

```
Step 1: ub := make(chan Order)

  stack (main):                          heap 0xC000010040:
┌─────────────────────────────┐         ┌─────────────────────────────┐
│ storage for ub              │         │ hchan                       │
│ pointer:  0xC000010040  ────────────► │ qcount:   0                 │
└─────────────────────────────┘         │ dataqsiz: 0  ← UNBUFFERED  │
                                          │ buf:      nil ← no shelf   │
                                          │ recvq/sendq empty          │
                                          └─────────────────────────────┘


Step 2: bf := make(chan Order, 2)

  stack (main):                          heap 0xC000010080:
┌─────────────────────────────┐         ┌─────────────────────────────┐
│ storage for bf              │         │ hchan                       │
│ pointer:  0xC000010080  ────────────► │ qcount:   0                 │
└─────────────────────────────┘         │ dataqsiz: 2  ← BUFFERED    │
                                          │ buf:  0xC000010100 ──────┐ │
                                          └──────────────────────────┼─┘
                                                                       ▼
                                                   heap ring at 0xC000010100:
                                                   [slot0 Order{}][slot1 Order{}]

KEY INSIGHT:
  Unbuffered: no shelf — only waiting lines (sendq/recvq) matter for progress.
  Buffered: shelf exists — blocking depends on fill level, not on instant meet.
```

> **In plain English:** Capacity is how many packages fit on the shelf. Zero means nobody stores anything — packages move hand to hand only.

---

### 4.2 When does send block? Receive block?

Walk this checklist (same mutex story as [[T15 Channel Internals]] — one goroutine edits `hchan` at a time):

**Send (`ch <- v`) — after lock acquired**

1. If **closed** → panic (`send on closed channel`).
2. If **matching receiver** waits in **`recvq`** → **direct copy** path (see [[T15 Channel Internals]]). No buffer slot consumed for that pairing.
3. Else if **`dataqsiz > 0` and `qcount < dataqsiz`** → write into ring at **`sendx`**, bump `qcount`, wake waiters if needed. Send **does not block**.
4. Else → enqueue current goroutine in **`sendq`**, **`goparkunlock`** → send **blocks** until somebody receives space.

**Receive (`<-ch`)**

1. If **matching sender** in **`sendq`** → pair, copy value, wake sender.
2. Else if **`qcount > 0`** → take from ring at **`recvx`**, decrement `qcount`.
3. Else if **closed && `qcount == 0`** → return zero value (and **`ok == false`** in two-value receive). **Never blocks.**
4. Else → park in **`recvq`**.

Without a buffer, progress means **someone must be waiting on the other side** or you park.

---

### 4.3 Unbuffered: coordination — `done` handshake

```go
// file: main.go — pattern only
done := make(chan struct{}) // capacity 0: rendezvous signal
go func() {
	processPayment()
	done <- struct{}{}
}()
<-done
```

**MEMORY TRACE snapshot (meet-in-the-middle):**

```
Step 1: sender reaches done <- struct{}{} before main receives

  hchan.dataqsiz = 0, qcount = 0, buf = nil
  recvq empty → sender enqueued on sendq, parked

Mid-state (example addresses):
  heap hchan 0xC000030000:
  sendq head → sudog[elem → empty struct token]
  recvq: empty

Step 2: main runs <-done

  Locks channel, sees sender waiting → direct-copy handshake
  Wakes payment goroutine, main continues
```

---

### 4.4 Buffered: bursts and back-pressure

```go
// file: ingest.go — simplified
type AuditLog struct{ ID int }

jobs := make(chan AuditLog, 100) // burst slack up to 100
```

```
After 100 sends without any receive:

  hchan (example 0xC000050000):
    qcount:   100
    dataqsiz: 100  ← FILLED

  Next producer send → §4.2 step 4 → parks in sendq

If consumer drains 1 slot:
    qcount: 99 → a blocked sender (if any) can proceed
```

**Before / after backlog warning:**

```
BEFORE (healthy): qcount low, producers rarely wait

AFTER (consumer stalled): qcount → dataqsiz, producer latency jumps
```

> **In plain English:** A buffer buys time until it runs out — then producers feel the slowdown all at once.

---

### 4.5 Capacity as a semaphore — limit concurrent Redis calls

```go
sem := make(chan struct{}, 8) // eight tickets
for _, sessionID := range sessions {
	go func(id string) {
		sem <- struct{}{}        // acquire
		defer func() { <-sem }() // release
		redisTouch(ctx, id)
	}(sessionID)
}
```

**Buffer fullness tracks how many goroutines hold a ticket** (paired with **`defer` release**).

---

## 5. Key Rules & Behaviors

### 5.1 `make(chan T)` means capacity zero

```go
errs := make(chan error)             // every send needs a reader ready
errs := make(chan error, len(ids))   // can batch until buffer fills
```

```
  errs := make(chan error)
  Pitfall: handler sends before listener starts → sender blocks forever
  Fix: start listener first OR add buffer on purpose
```

**Why (Section 4.2):** With `dataqsiz == 0`, every send needs a synchronous partner.

---

### 5.2 Buffered send is non-blocking only while `qcount < dataqsiz`

Full buffer means **`qcount == dataqsiz`** — next send parks.

---

### 5.3 Bigger buffers do not fix slow consumers forever

Large `dataqsiz` stores backlog in RAM. When full, producers stall the same as any throttle.

**Why:** Buffer is **`k` deferred handoffs**, not an infinite queue.

---

### 5.4 Close semantics are the same — buffer changes how draining feels

```go
ch := make(chan int, 2)
ch <- 1
close(ch)
x := <-ch // 1
y := <-ch // 0, never blocks once empty
```

**Why:** [[T15 Channel Internals]] — **`closed`** plus **`qcount`** controls returns.

---

## 6. Interview Practice (MANDATORY — Active Recall Format)

### 6.1. MCQs (Optional Warm-Up — 3 Questions Max)

**Q1.** After `ch := make(chan int, 2)` and sends `1` then `2` with no receivers, does a third send block?

A) Never — buffered channels never block sends  
B) Yes — third send finds `qcount == dataqsiz`  
C) Panic — buffered channels reject third send  
D) Only blocks if GC is running  

> [!success]- Answer
> **B** — **`qcount` reaches capacity**. Next send waits on **`sendq`**. Section 4.2.

---

**Q2.** Which fits **unbuffered** `chan struct{}` for shutdown coordination?

A) Absorb telemetry bursts without blocking  
B) Force writer and reader to meet so ordering is explicit  
C) Semaphore limiting DB connections  
D) Store last N errors  

> [!success]- Answer
> **B** — Rendezvous. Bursts need **`dataqsiz > 0`** or external queue. Sections 4.3 and 5.1.

---

**Q3.** What does increasing buffer size do if consumers are **always** slower than producers?

A) Fixes throughput forever  
B) Delays the stall until the buffer fills; then producers still block  
C) Doubles consumer speed  
D) Empties the buffer automatically  

> [!success]- Answer
> **B** — Buffer reshapes latency until saturated. Sections 4.4 and 5.3.

---

### 6.2. Predict the Output

**Problem 1**

```go
package main

import "fmt"

func main() {
	ch := make(chan int)
	go func() { fmt.Println(<-ch) }()
	ch <- 7
	fmt.Println("done")
}
```

> [!success]- Output
> ```
> 7
> done
> ```
> **Why:** Unbuffered send pairs with spawned receiver. Section 4.3.

---

**Problem 2**

```go
package main

import "fmt"

func main() {
	ch := make(chan int, 1)
	go func() { ch <- 1 }()
	go func() { ch <- 2 }()
	fmt.Println(<-ch, <-ch)
}
```

> [!success]- Output
> ```
> (order of 1 and 2 may vary by scheduling; both values print)
> ```
> **Why:** Buffer 1 allows one immediate send; second send waits. Section 5.2.

---

**Problem 3**

```go
package main

import "fmt"

func main() {
	ch := make(chan int, 1)
	close(ch)
	v, ok := <-ch
	fmt.Println(v, ok)
}
```

> [!success]- Output
> ```
> 0 false
> ```
> **Why:** Closed empty buffered channel — zero value, `ok` false, no block.

---

**Problem 4**

```go
package main

func main() {
	ch := make(chan int)
	go func() { ch <- 1 }()
	ch <- 2
}
```

> [!success]- Output
> ```
> fatal error: all goroutines are asleep - deadlock!
> ```
> **Why:** Child blocks on first unbuffered send waiting for a reader. Main blocks on second send. Nobody receives.

---

**Problem 5**

```go
package main

import "fmt"

func main() {
	ch := make(chan int)
	go func() { <-ch }()
	ch <- 1
	ch <- 2
	fmt.Println("end")
}
```

> [!success]- Output
> ```
> fatal error: all goroutines are asleep - deadlock!
> ```
> **Why:** First send completes handshake. Second send has no partner.

---

**Problem 6**

```go
package main

import (
	"fmt"
	"sync"
)

func main() {
	sem := make(chan struct{}, 2)
	var wg sync.WaitGroup
	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			sem <- struct{}{}        // acquire ticket (blocks when 2 already out)
			defer func() { <-sem }() // release
			fmt.Println(i)
		}(i)
	}
	wg.Wait()
}
```

> [!success]- Output
> ```
> (five lines, order nondeterministic; at most two goroutines print at a time)
> ```
> **Why:** Semaphore — only two struct{}{} tokens in the buffer "available" for concurrent holders; others block on `sem <-` until someone runs `defer` release. Section 4.5.

---

### 6.3. Trick Questions (Interview Traps)

**Trap #1:** "`make(chan Task, workers*10)` means we never block."

> [!success]- Answer
> **False** — only **10× slots** of slack; faster producers still fill it.

---

**Trap #2:** Second `close` after drain is harmless.

```go
ch := make(chan int)
close(ch)
close(ch)
```

> [!success]- Answer
> **Panic** — same as all channels.

---

**Trap #3:** Semaphore without `defer` release on error path.

> [!success]- Answer
> **Ticket leak** — capacity never returns; throughput dies.

---

**Trap #4:** "`cap(ch)` tells me backlog depth."

> [!success]- Answer
> **`cap` is `dataqsiz`**, not live occupancy. Track depth with explicit metrics or design.

---

**Trap #5:** Claiming `len(ch)` works.

> [!success]- Answer
> **Invalid** — use counters or drain inspection patterns.**

---

### 6.4. Coding Problems (Hands-On)

**Problem 1 (Easy):** `RunWithPool(logs []AuditLog, workers int, fn func(AuditLog))` with buffered `jobs`. Explain buffer size choice.

> [!success]- Solution
> ```go
> func RunWithPool(logs []AuditLog, workers int, fn func(AuditLog)) {
> 	if workers < 1 {
> 		workers = 1
> 	}
> 	jobs := make(chan AuditLog, workers*2)
> 	var wg sync.WaitGroup
> 	for w := 0; w < workers; w++ {
> 		wg.Add(1)
> 		go func() {
> 			defer wg.Done()
> 			for lg := range jobs {
> 				fn(lg)
> 			}
> 		}()
> 	}
> 	for _, lg := range logs {
> 		jobs <- lg
> 	}
> 	close(jobs)
> 	wg.Wait()
> }
> ```
> **`2×`** absorbs slight skew vs **`1×`** one task per goroutine queued only.

---

**Problem 2 (Medium):** `listen(ctx, events <-chan Event)` — exit on cancel or closed channel.

> [!success]- Solution
> ```go
> func listen(ctx context.Context, events <-chan Event) error {
> 	for {
> 		select {
> 		case <-ctx.Done():
> 			return ctx.Err()
> 		case e, ok := <-events:
> 			if !ok {
> 				return nil
> 			}
> 			handle(e)
> 		}
> 	}
> }
> ```

---

**Problem 3 (Medium-Hard):** Cap **PostgresQuery** concurrency at **8** with channels.

> [!success]- Answer
> Section **4.5** semaphore — stress **`defer`** release and **`context`** cancellation cancelling waiters if you add `select`.

---

**Problem 4 (Hard):** Bound **inflight** Kafka publishes to **500**.

> [!success]- Model Answer
> **`make(chan kafka.Message, 500)`** on hot path plus metrics; overflow policy (block vs drop vs dead-letter).

---

### 6.5. What Would You Do? (Scenario Questions)

**Scenario 1:** Burst load goroutine storm on **unbuffered** request channel.

> [!success]- Model Answer
> **Bounded buffered queue + worker pool** or **`select`/`default`** with rejection — unbuffered fans into blocked goroutines tied to connections.**

---

**Scenario 2:** Teammate wants **buffer 1_000_000**.

> [!success]- Model Answer
> **Memory hazard + delayed alerting** — right-size against SLA; consider **external broker**.**

---

**Scenario 3:** Strict parent waits **two children** — channel design?

> [!success]- Model Answer
> **`sync.WaitGroup`** or **`done := make(chan struct{})`** twice — simplicity beats clever buffer sizing.**

---

## 7. Gotchas & Interview Traps

| Trap | Why it happens | How to spot it | Fix |
|------|----------------|----------------|-----|
| Deadlock single goroutine on unbuffered send | Section 5.1 | `fatal error ... deadlock` | Partner goroutine first or buffer |
| "Buffered never blocks" myth | Section 5.2 | Sudden stalls under load | Size to real burst + drain rate |
| Huge buffer hides dead consumer | Section 5.3 | RSS climbs; lag invisible | Metrics + alerting on saturation |
| Semaphore leak | Section 4.5 | goroutines hang waiting ticket | `defer` release; `context` timeouts |
| `cap` mistaken for backlog | Section 6.3 Trap #4 | Wrong capacity planning | Instrument depth explicitly |
| Channel for hot shared counter | Section 8 | Mutex cheaper in benchmarks | Mutex or `atomic` for simple state |

---

## 8. Performance & Tradeoffs (Production-Grounded)

### 8.1. The Production Scenario

Your **AuditLog** ingester spikes to **40k events/min** during deploys while the **Elasticsearch** sink commits **12k/min**. HTTP handlers enqueue on `chan AuditLog` with **`dataqsiz=5000`** so they return immediately.

### 8.2. The Cost Comparison Table

| Pattern | What it costs | You'd see this in... | When it matters |
|---------|---------------|----------------------|----------------|
| Unbuffered rendezvous | Every value needs pairing — **couples goroutine lifetimes** | `done` after background job | Correctness-first barriers |
| Buffered slack `n` | **RAM ≈ `n × sizeof(elem)`** + wakeup churn | Burst absorption before sink | Controlled overload |
| Oversized buffer | **Memory + invisible lag** until cliff | "Set super high cap" | OOM / surprise p99 |
| Mutex + slice queue | Manual correctness; can win micro-benchmarks | Hot stat cache | Rare first answer in interview |
| External queue | Ops + dollars; true separation | Cross-service | Past in-process limits |

### 8.3. What Actually Hurts (The Anti-Pattern)

The anti-pattern: **goroutine per HTTP request** does **unbuffered** send to a **global** channel with **one** consumer that OOM-crashed — every handler goroutine blocks on send, FDs exhaust, **Kubernetes** keeps routing traffic. **`pprof goroutine`** shows thousands on `runtime.chansend`. **Fix:** **bounded buffer**, **health check** that fails when queue depth high, **supervisor** restart, or **reject** with **503** using **`select`/`default`**.

### 8.4. What to Measure (Concrete Commands)

```bash
curl -s http://localhost:6060/debug/pprof/goroutine?debug=2 | head -200
go test -bench=BenchmarkChan -benchmem ./...
go test -trace=trace.out ./...
go tool trace trace.out
```

```go
func BenchmarkUnbuffered(b *testing.B) {
	ch := make(chan int)
	go func() {
		for i := 0; i < b.N; i++ {
			<-ch
		}
	}()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		ch <- 1
	}
}

func BenchmarkBuffered(b *testing.B) {
	ch := make(chan int, 8)
	go func() {
		for i := 0; i < b.N; i++ {
			<-ch
		}
	}()
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		ch <- 1
	}
}
```

---

## 9. Common Misconceptions

| Misconception | Reality |
|---------------|---------|
| Buffered always faster | Coupling vs batching — measure |
| Default buffer is 1 | Default **0** |
| Unbuffered avoids locks | `hchan.lock` still serializes progress |
| `len(ch)` exists | No — only **`cap`** for static capacity |
| Big buffer fixes slow sink | **Delays** pain |

---

## 10. Related Tooling & Debugging

- `go test -race` — races if you mix unsynchronized shared fields with channel patterns badly.
- `/debug/pprof/goroutine` — locate `chansend`/`chanrecv` stacks.
- `go tool trace` — blocked goroutine timelines.
- Application metrics: **proxy queue depth** (increment on send, decrement on receive).

---

## 11. Interview Gold Questions

**Q1:** Buffered vs unbuffered — when?

**Answer:** Unbuffered for **handshake** coordination. Buffered for **bounded slack**, **worker queues**, **semaphores** — always know what **`k` means** in product terms.

**Verbal:** "Zero is `dataqsiz` — no shelf. Non-zero is a ring buffer — block on full or empty."

---

**Q2:** Does a buffer remove back-pressure?

**Answer:** **No** — it **moves** back-pressure to producers **after** `k` items pile up.

---

**Q3:** Channel vs mutex?

**Answer:** Channel **includes** mutex-style locking internally for `hchan` fields.** Mutex wins for tiny shared state; channel wins for **staging work** between goroutines.**

---

## 12. Final Verbal Answer

If someone asks me buffered vs unbuffered, I'd say it's the same runtime channel with different **`dataqsiz`**. Zero means **no `buf`** — sends and receives **meet in the middle** or block. Non-zero means **up to k values** sit in memory between sides — sends block when **full**, receives when **empty**. Closing works the same; buffered just might still have values to drain.** I use unbuffered when I care about **who was ready when**, and buffered when I need **bounded decoupling** — and I'm careful with huge buffers because they **lie** about how healthy the consumer is until they **can't** anymore.

---

## 13. Comprehensive Interview Questions

> Full interview question bank → [[questions/T16 Buffered vs Unbuffered Channels - Interview Questions]]

**Preview:**

1. State the send blocking conditions for buffered vs unbuffered channels.
2. Implement a semaphore with `chan struct{}` and explain failure modes.
3. Why might `make(chan T)` deadlock in a handler where `make(chan T, 1)` appears to "fix" it — is that a good fix?

---

> See [[Glossary]] for term definitions.
