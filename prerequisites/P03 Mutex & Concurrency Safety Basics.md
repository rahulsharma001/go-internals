# P03 Mutex & Concurrency Safety Basics

> **Prerequisite note** — complete this before starting [[T07 Pointers & Pointer Semantics]] or [[T18 Mutex & RWMutex Internals]].
> Estimated time: ~20 min

---

## 1. Concept

A **mutex** is a lock that lets **one** goroutine at a time enter a **critical section** of code that touches **shared memory**.

> **In plain English:** Picture a single bathroom with one lock on the door. If the door is locked, everyone else waits in the hall. When someone leaves, they unlock. Only one person is inside at a time. That is mutual exclusion.

---

## 2. Core Insight (TL;DR)

**Shared variables plus concurrent reads and writes without coordination produce races.** The compiler and CPU may reorder work; goroutines interleave unpredictably. **A mutex serializes access** so updates look atomic from the rest of the program. **Pair every `Lock()` with `Unlock()`**, usually via **`defer`**, and **never copy** a `sync.Mutex` or `sync.RWMutex`.

---

## 3. Mental Model (Lock this in)

The bathroom lock analogy maps cleanly to Go. The **critical section** is the bathroom interior. **`Lock()`** is turning the bolt. **`Unlock()`** is opening it for the next person. If two people "share" the stall without a lock, you get chaos. With a lock, behavior is orderly.

Two goroutines, one shared counter, **no mutex**:

```go
var counter int

func inc() {
    counter++ // read, add, write — not one atomic step
}

func main() {
    var wg sync.WaitGroup
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            inc()
        }()
    }
    wg.Wait()
    fmt.Println(counter) // often < 1000 — wrong
}
```

```
  time →
  G1:  read counter (= 5)
  G2:           read counter (= 5)
  G1:  write 6
  G2:                    write 6   ← both thought "next is 6"; one update lost
```

> **In plain English:** Two people both read "5" on a whiteboard, both write "6", and nobody writes "7". You expected a thousand bumps; you got lost updates.

**Fix:** one mutex, one critical section around the update.

```go
var (
    counter int
    mu      sync.Mutex
)

func inc() {
    mu.Lock()
    counter++
    mu.Unlock()
}
```

```
  G1: Lock acquired
  G1: read/write counter
  G1: Unlock
            G2: Lock acquired
            G2: read/write counter
            G2: Unlock
  ... strict turns at the whiteboard ...
```

> **In plain English:** Only one goroutine may touch the counter at a time. The rest wait at the door. The final value matches the number of completed increments.

---

## 4. How It Works

### 4.1 `sync.Mutex`: `Lock()`, `Unlock()`, critical section

`Lock()` blocks until the mutex is free, then marks it owned by the calling goroutine. `Unlock()` releases it. The **critical section** is the code between them.

```go
mu.Lock()
// critical section: only this goroutine may run this code path
balance += amount
mu.Unlock()
```

```
     [ mu: free ]
          |
   G1 Lock()
          v
     [ mu: held by G1 ]
   G2 Lock() ──blocks──> (waiting)
          |
   G1 Unlock()
          v
     [ mu: free ]  ──> G2 wakes, Lock(), proceeds
```

> **In plain English:** `Lock()` is "my turn or I wait." `Unlock()` is "next." Anything that must not run two at a time goes between them.

### 4.2 `defer mu.Unlock()`

```go
func transfer(from, to *Account, amount int) {
    mu.Lock()
    defer mu.Unlock()

    if from.balance < amount {
        return // defer still runs — mutex released
    }
    from.balance -= amount
    to.balance += amount
}
```

```
  enter function
  Lock()
  defer registered: Unlock at return
  ... work ...
  return triggers deferred Unlock
```

> **In plain English:** Every return path, including errors and panics after `Lock()`, still runs deferred calls. You avoid forgetting `Unlock()` on an early `return`.

### 4.3 `sync.RWMutex`: many readers **or** one writer

- **`RLock()` / `RUnlock()`:** shared **read** lock. Many goroutines can hold it at once **if nobody holds a write lock**.
- **`Lock()` / `Unlock()`:** exclusive **write** lock. Like a normal mutex for writers. **Blocks all readers and writers** until released.

```go
var (
    data map[string]int
    rw   sync.RWMutex
)

func Read(key string) int {
    rw.RLock()
    defer rw.RUnlock()
    return data[key]
}

func Write(key string, v int) {
    rw.Lock()
    defer rw.Unlock()
    data[key] = v
}
```

```
  Readers (RLock):
    R R R R   ← all concurrent

  Writer (Lock):
    W  blocks everyone until done

  Timeline:
    R R R | W | R R
          ^ exclusive slot
```

> **In plain English:** Either a crowd may **look** together, or **one** person may **change** the room. Not both at once.

**When to use `RWMutex`:** read-heavy workloads on a shared structure, reads are safe to overlap, writes are rare but must be exclusive. If writes are frequent or the critical section is tiny, a plain `Mutex` may be simpler and fast enough.

---

## 5. Key Rules & Behaviors

### Always pair `Lock()` with `defer Unlock()`

```go
func bad() {
    mu.Lock()
    if err != nil {
        return // BUG: forgot Unlock — deadlock or leak
    }
    mu.Unlock()
}
```

```
  bad():
    Lock ──> held
    return ──> mutex still held forever for this path
```

```go
func good() {
    mu.Lock()
    defer mu.Unlock()
    if err != nil {
        return // OK: defer unlocks
    }
}
```

> **In plain English:** Treat `Lock()` like opening a file: use `defer` to close on every exit.

### Never copy a mutex — the copy trap

```go
type SafeCounter struct {
    mu    sync.Mutex
    value int
}

func Broken(c SafeCounter) { // receives a COPY
    c.mu.Lock()
    defer c.mu.Unlock()
    c.value++ // increments the COPY's field — caller unchanged
}
```

```
  caller's SafeCounter     copy inside Broken()
  ┌──────────────┐         ┌──────────────┐
  │ mu  (real)   │         │ mu  (copy)   │  ← different locks!
  │ value: 0     │         │ value: 1     │
  └──────────────┘         └──────────────┘
```

> **In plain English:** Copying duplicates the lock. Two locks protect two different imaginary bathrooms. The real counter is unprotected.

### Mutex must be a pointer field or embedded on a pointer receiver — never pass the struct by value

```go
type SafeCounter struct {
    mu    sync.Mutex
    value int
}

func (c *SafeCounter) Inc() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.value++
}
```

```
  *SafeCounter ──> one struct in memory, one mu, one truth
```

> **In plain English:** Methods that mutate shared state should take a **pointer receiver** so there is only one `sync.Mutex` in the program for that object.

### `RWMutex`: multiple `RLock()` concurrent, but `Lock()` is exclusive

```go
// Many goroutines: rw.RLock() ... RUnlock()  — OK in parallel
// One goroutine:  rw.Lock() ... Unlock()    — blocks all readers and writers
```

```
  R R R R   OK
  R W       W waits for R's to finish
  W R       R waits for W
  W W       second W waits
```

> **In plain English:** Readers may pack the balcony. When a writer enters, the balcony clears.

### Deadlock: locking twice without unlocking

```go
func oops(mu *sync.Mutex) {
    mu.Lock()
    mu.Lock() // same goroutine, same mutex — blocks forever
    mu.Unlock()
    mu.Unlock()
}
```

```
  G1: Lock (count 1)
  G1: Lock (wants 2nd lock on same mutex) ──> waits on itself
```

> **In plain English:** You hold the only key and you are waiting for yourself to hand it over. The program hangs.

### Mutex vs channel — quick decision guide

1. **Protect a small shared variable or struct with invariants?** Prefer a **mutex** inside a type with clear methods.
2. **Pass ownership of work or results between goroutines?** Prefer a **channel**.
3. **Fan-in events or signals?** Often a **channel**.
4. **Hot path, one shared counter or cache?** Often a **mutex** or `RWMutex`.
5. **Unsure and the state fits one owner goroutine?** **Channel** may simplify reasoning.

> **In plain English:** Mutexes are for **shared memory with rules**. Channels are for **communication and handoff**. The Go proverb favors channels when they clarify design; mutexes remain normal and idiomatic for many structures.

---

## 6. Code Examples (Show, Don't Tell)

### 6.1 Race without mutex — broken output

```go
package main

import (
    "fmt"
    "sync"
)

func main() {
    var n int
    var wg sync.WaitGroup
    const workers = 10000
    for i := 0; i < workers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            n++
        }()
    }
    wg.Wait()
    fmt.Println(n)
}
```

```
  sample stdout: 7234  ← varies; not 10000

  snapshot A: two goroutines both load n=100
  snapshot B: both store n=101
  snapshot C: expected +2, got +1 — repeat thousands of times
```

### 6.2 Same logic with `sync.Mutex` — correct output

```go
package main

import (
    "fmt"
    "sync"
)

func main() {
    var n int
    var mu sync.Mutex
    var wg sync.WaitGroup
    const workers = 10000
    for i := 0; i < workers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            mu.Lock()
            n++
            mu.Unlock()
        }()
    }
    wg.Wait()
    fmt.Println(n)
}
```

```
10000
```

```
  each n++ runs under the lock — serialized updates
  final n equals number of completed critical sections
```

### 6.3 `sync.RWMutex` for concurrent reads

```go
type PhoneBook struct {
    mu   sync.RWMutex
    data map[string]string
}

func NewPhoneBook() *PhoneBook {
    return &PhoneBook{data: make(map[string]string)}
}

func (p *PhoneBook) Get(name string) string {
    p.mu.RLock()
    defer p.mu.RUnlock()
    return p.data[name]
}

func (p *PhoneBook) Set(name, number string) {
    p.mu.Lock()
    defer p.mu.Unlock()
    p.data[name] = number
}
```

```
  Get Get Get Get  ← overlapping RLocks
       Set         ← exclusive; waits for readers
  Get              ← waits for writer
```

### 6.4 Copy trap in action

```go
package main

import (
    "fmt"
    "sync"
)

type Bag struct {
    mu     sync.Mutex
    coins  int
}

func addByValue(b Bag) {
    b.mu.Lock()
    defer b.mu.Unlock()
    b.coins++
}

func main() {
    var bag Bag
    addByValue(bag)
    fmt.Println(bag.coins) // 0 — copy was modified
}
```

```
  main's bag.coins: 0 ───────────────────> still 0
  addByValue's copy.coins: 1 ────────────> discarded
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

```go
package main

import (
    "fmt"
    "sync"
)

func main() {
    var x int
    var wg sync.WaitGroup
    for i := 0; i < 50; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for j := 0; j < 1000; j++ {
                x++
            }
        }()
    }
    wg.Wait()
    fmt.Println(x)
}
```

> [!success]- Answer
> The program prints a **number less than** `50000` and **not deterministic**. Many increments race on `x`. There is no mutex. Exact value varies run to run.

### Tier 2: Fix the Bug (5 min)

```go
type Stats struct {
    mu    sync.Mutex
    hits  int
}

func (s Stats) RecordHit() {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.hits++
}
```

> [!success]- Answer
> **Bug:** value receiver copies `Stats`, so each call locks a **different** mutex. **Fix:** use a pointer receiver: `func (s *Stats) RecordHit()`. Optionally hide `Stats` construction so callers cannot copy it accidentally.

---

## 7. Gotchas & Interview Traps

| Trap | Why it bites | Safer habit |
|------|----------------|-------------|
| Copy trap | Duplicated `sync.Mutex` gives **false** safety | Pointer receivers; do not pass the struct by value |
| Forgotten `Unlock` | Early `return` leaves mutex held | `defer mu.Unlock()` right after `Lock()` |
| Recursive double `Lock` | Same goroutine blocks itself | Restructure; or use `sync.Mutex` only once per path |
| Mixing mutex and channel for same invariant | Easy to deadlock or race | One coordination strategy per shared state |
| `RWMutex` for tiny data | Reader lock overhead may dominate | Benchmark; sometimes `Mutex` wins |

---

## 8. Interview Gold Questions (Top 3)

1. **What is a data race, and how does a mutex prevent it?**  
   A data race is two unsynchronized accesses, at least one write, to the same memory. A mutex forces those accesses into a **total order** so reads and writes do not interleave unpredictably.

2. **Why must you not copy `sync.Mutex`?**  
   The mutex state lives in the value. A copy gets its **own** lock bit. Two goroutines can then enter the same logical critical section using different copies, and shared fields stay racy.

3. **When would you pick `RWMutex` over `Mutex`?**  
   When reads greatly outnumber writes, reads can run concurrently, and the read-side critical section is non-trivial enough that parallel reads help. Writers still need exclusive access.

---

## 9. 30-Second Verbal Answer

Concurrent goroutines **interleave**. If they share memory without rules, **reads and writes collide** and values become **wrong and non-deterministic**. A **mutex** is a **sleeping bouncer**: one goroutine inside the **critical section** at a time. In Go, call **`Lock()`**, **`defer Unlock()`**, keep the critical section **small**, use **pointer receivers** so the mutex is **not copied**, and use **`RWMutex`** when **many readers** and **rare writers** fit the workload. Prefer **channels** when you are **handing off work or signaling**; prefer **mutexes** when **protecting shared struct fields** is clearest.

---

> See [[Glossary]] for term definitions.
