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
MEMORY TRACE:

Step 1: var counter int
  shared memory:
    counter ──→ [ 0 ]  at addr 0xC000

Step 2: goroutine G1 reads counter, goroutine G2 reads counter (both see 5 before either writes)
  goroutine G1:  reads 0xC000 → gets 5
  goroutine G2:  reads 0xC000 → gets 5   ◄── BOTH read 5; ++ is read/add/write, not one atomic step

Step 3: both compute 5 + 1 = 6 and write back
  shared memory:
    counter ──→ [ 6 ]  ◄── should be 7; LOST UPDATE (one bump vanished)

Step 4: pattern repeats under scheduling → fmt.Println(counter) often < 1000
  shared memory:
    counter ──→ [ nondeterministic ]  ◄── final value = last write wins, not true sum
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
MEMORY TRACE:

Step 1: var counter int, var mu sync.Mutex
  shared memory:
    counter ──→ [ 0 ]  at addr 0xC000
    mu (lock word / state) ──→ [ unlocked ]  at addr 0xC010

Step 2: G1 calls mu.Lock()
  shared memory:
    mu ──→ [ locked, owner G1 ]
  goroutine G2:  mu.Lock() ──→ blocks in scheduler wait queue   ◄── mutual exclusion

Step 3: G1 runs counter++ then mu.Unlock()
  shared memory:
    counter ──→ [ 1 ]
    mu ──→ [ unlocked ]

Step 4: G2 wakes, Lock, increments, Unlock — strict turns for every inc()
  ...
  final after 1000 completions:
    counter ──→ [ 1000 ]  at addr 0xC000   ◄── matches number of serialized critical sections
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
MEMORY TRACE:

Step 1: before Lock — balance update is the critical section
  shared memory:
    mu ──→ [ unlocked ]  at addr 0xC010
    balance ──→ [ ... ]  at addr 0xC100

Step 2: G1 executes mu.Lock()
  shared memory:
    mu ──→ [ locked, owner G1 ]
  stack (G1):  about to run balance += amount   ◄── only G1 inside critical section

Step 3: G2 executes mu.Lock() while G1 holds
  shared memory:
    mu ──→ [ locked, owner G1 ]
  goroutine G2:  parked ◄── cannot observe or mutate balance until Unlock

Step 4: G1 executes mu.Unlock()
  shared memory:
    mu ──→ [ unlocked ]
  goroutine G2:  Lock() succeeds, enters critical section   ◄── handoff; total order on balance
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
MEMORY TRACE:

Step 1: enter transfer, mu.Lock()
  stack (transfer):
    defer stack ──→ [ mu.Unlock scheduled ]
  shared memory:
    mu ──→ [ locked ]  at addr 0xC010

Step 2: body runs (from.balance, to.balance, early return paths)
  stack:
    defer Unlock still pending   ◄── not run until function actually returns

Step 3: return (including if from.balance < amount)
  stack:  deferred mu.Unlock() runs
  shared memory:
    mu ──→ [ unlocked ]  ◄── mutex released on every exit path; no forgotten Unlock
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
MEMORY TRACE:

Step 1: var data map[string]int, var rw sync.RWMutex
  heap:
    map header / buckets for data ──→ [ ... ]  at addr 0xD000
  shared memory:
    rw (reader/writer state) ──→ [ no writer, readers: 0 ]  at addr 0xC020

Step 2: G1..G4 call Read → rw.RLock()
  shared memory:
    rw ──→ [ no writer, readers: 4 ]   ◄── many readers overlap; all read same map snapshot rules

Step 3: writer calls Write → rw.Lock() while readers still hold RLock
  goroutine GW:  blocks until last RUnlock completes   ◄── writer exclusive; no concurrent map mutation

Step 4: GW mutates data[key], then Unlock()
  heap:
    0xD000 ──→ updated entry for key
  shared memory:
    rw ──→ [ unlocked for write path ]

Step 5: new Read callers RLock again while no writer holds Lock
  shared memory:
    rw ──→ [ readers: N ]   ◄── read crowd resumes; writer slot was exclusive
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
MEMORY TRACE:

Step 1: mu.Lock()
  stack (bad):
    about to check err
  shared memory:
    mu ──→ [ locked ]  at addr 0xC010

Step 2: if err != nil { return } — early exit without Unlock on this path
  shared memory:
    mu ──→ [ locked ]   ◄── still held; lock leaked for this goroutine's logical scope

Step 3: later: same mu used elsewhere, or second call to bad()
  goroutine:  mu.Lock() ──→ blocks forever (or program stuck)   ◄── classic forgotten Unlock / deadlock
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
MEMORY TRACE:

Step 1: caller holds one SafeCounter value (by-value variable in caller frame)
  stack (caller):
    SafeCounter at addr 0xE000 ──→  mu at 0xE008, value at 0xE028
  shared memory:
    mu @0xE008 ──→ [ unlocked ]
    value @0xE028 ──→ [ 0 ]

Step 2: Broken(c SafeCounter) receives a struct copy — new stack slot
  stack (Broken):
    copy SafeCounter at addr 0xE100 ──→  mu_copy at 0xE108, value_copy at 0xE128

Step 3: c.mu.Lock() locks only the copy's mutex
  shared memory:
    mu_copy @0xE108 ──→ [ locked ]
    mu @0xE008 ──→ [ unlocked ]   ◄── TWO independent lock words; "real" mutex never held

Step 4: c.value++ updates copy; defer unlocks mu_copy only
  value_copy @0xE128 ──→ [ 1 ]
  value @0xE028 ──→ [ 0 ]   ◄── caller unchanged; false sense of safety
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
MEMORY TRACE:

Step 1: one object (e.g. &SafeCounter{}) allocated — single layout
  heap:
    *SafeCounter at 0xF000 ──→  mu at 0xF008, value at 0xF028

Step 2: (c *SafeCounter) Inc() — receiver is pointer, not a copy
  stack (Inc):
    c ──→ 0xF000   ◄── all calls share this address; one mu, one value field

Step 3: c.mu.Lock(); c.value++; defer Unlock
  shared memory:
    mu @0xF008 ──→ [ locked ] then [ unlocked ]
    value @0xF028 ──→ increments visible to every holder of *SafeCounter   ◄── one truth
```

> **In plain English:** Methods that mutate shared state should take a **pointer receiver** so there is only one `sync.Mutex` in the program for that object.

### `RWMutex`: multiple `RLock()` concurrent, but `Lock()` is exclusive

```go
// Many goroutines: rw.RLock() ... RUnlock()  — OK in parallel
// One goroutine:  rw.Lock() ... Unlock()    — blocks all readers and writers
```

```
MEMORY TRACE:

Step 1: R R R R — only RLock holders
  shared memory:
    rw ──→ [ readers: 4, writer: none ]   ◄── OK concurrent reads

Step 2: R then W — writer tries Lock while readers active
  shared memory:
    rw ──→ [ readers: >0 ]
  goroutine W:  blocked until reader count drops to 0   ◄── W waits for R's to finish

Step 3: W then R — new reader tries RLock during write Lock
  shared memory:
    rw ──→ [ writer held ]
  goroutine R_new:  RLock blocks ◄── R waits for W

Step 4: W W — second writer tries Lock while first still holds
  goroutine W2:  blocked ◄── second W waits behind exclusive writer
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
MEMORY TRACE:

Step 1: first mu.Lock() in oops
  shared memory:
    mu ──→ [ locked by G1 ]  at addr 0xC010
  stack (G1):  inside oops, first critical section entered

Step 2: second mu.Lock() same goroutine, same mutex (sync.Mutex is not reentrant)
  shared memory:
    mu ──→ [ still locked by G1 ]
  goroutine G1:  second Lock() ──→ blocks waiting for Unlock   ◄── but G1 is the one who must Unlock

Step 3: no progress — first Unlock never reached
  shared memory:
    mu ──→ [ locked by G1 ]
  goroutine G1:  self-wait   ◄── permanent deadlock; program hangs
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
MEMORY TRACE:

Step 1: var n int in main
  shared memory:
    n ──→ [ 0 ]  at addr 0xC000

Step 2: two workers interleave — both read same n before either writes (e.g. both see 100)
  goroutine A:  reads 0xC000 → gets 100
  goroutine B:  reads 0xC000 → gets 100   ◄── BOTH read 100; n++ races

Step 3: both compute 100 + 1 = 101 and store
  shared memory:
    n ──→ [ 101 ]  ◄── should be 102; LOST UPDATE (× many interleavings)

Step 4: wg.Wait(); fmt.Println(n)
  sample stdout: 7234 (varies; not 10000)   ◄── non-deterministic final sum
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
MEMORY TRACE:

Step 1: var n int, var mu sync.Mutex
  shared memory:
    n ──→ [ 0 ]  at addr 0xC000
    mu ──→ [ unlocked ]  at addr 0xC010

Step 2: worker goroutine calls mu.Lock() — only one holds lock at a time
  shared memory:
    mu ──→ [ locked, owner Gk ]
  other workers:  Lock() ──→ block until Unlock   ◄── n++ never overlaps

Step 3: critical section n++; mu.Unlock()
  shared memory:
    n ──→ strictly +1 per completed Lock/Unlock pair
    mu ──→ [ unlocked ] then next worker proceeds

Step 4: after 10000 serialized increments, fmt.Println(n)
  shared memory:
    n ──→ [ 10000 ]  at addr 0xC000   ◄── matches 10000 completed critical sections (stdout: 10000)
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
MEMORY TRACE:

Step 1: *PhoneBook — p.mu and p.data on one object (e.g. heap 0xB000)
  heap:
    PhoneBook at 0xB000 ──→  mu at 0xB008, map data at 0xB020
  shared memory:
    p.mu ──→ [ readers: 0, no writer ]  at addr 0xB008

Step 2: four goroutines Get → RLock
  shared memory:
    p.mu ──→ [ readers: 4 ]   ◄── overlapping reads; return p.data[name] under shared lock

Step 3: Set calls Lock while readers still active
  goroutine writer:  blocks until all RUnlock   ◄── exclusive mutation of map

Step 4: writer updates p.data, Unlock()
  heap:
    map at 0xB020 ──→ new key/value visible
  shared memory:
    p.mu ──→ [ writer released ]

Step 5: new Get after write — RLock may proceed
  goroutine reader:  if writer holds Lock, RLock blocks ◄── readers wait for exclusive writer
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
MEMORY TRACE:

Step 1: main — var bag Bag on stack
  stack (main):
    bag at addr 0xA000 ──→  mu at 0xA008, coins at 0xA018
  shared memory:
    coins @0xA018 ──→ [ 0 ]

Step 2: addByValue(bag) passes Bag by value — copy in callee frame
  stack (addByValue):
    b at addr 0xA100 ──→  mu_copy at 0xA108, coins_copy at 0xA118

Step 3: b.mu.Lock(); b.coins++ on the copy only
  shared memory:
    mu_copy ──→ [ locked ] @0xA108
    coins_copy @0xA118 ──→ [ 1 ]
    coins @0xA018 ──→ [ 0 ]   ◄── main's bag never incremented

Step 4: function returns — copy discarded; Unlock released copy's mutex only
  stack (main):
    bag.coins still [ 0 ]   ◄── fmt.Println(bag.coins) → 0
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

```
MEMORY TRACE:

Step 1: var x int
  shared memory:
    x ──→ [ 0 ]  at addr 0xC000

Step 2: 50 goroutines each run 1000× x++; two interleave on one load/store pair
  goroutine G1:  reads 0xC000 → gets k
  goroutine G2:  reads 0xC000 → gets k   ◄── BOTH read k; lost updates across inner loop

Step 3: both write k+1
  shared memory:
    x ──→ [ k+1 ]  ◄── expected +2 from this pair, got +1; repeats often

Step 4: after wg.Wait(), fmt.Println(x)
  shared memory:
    x ──→ [ value < 50000, nondeterministic ]   ◄── no mutex; not 50000
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

```
MEMORY TRACE:

Step 1: first RecordHit — value receiver copies Stats into callee frame
  stack (caller #1):
    Stats at 0xE000 ──→  mu at 0xE008, hits at 0xE018
  stack (RecordHit callee #1):
    copy Stats at 0xE100 ──→  mu' at 0xE108, hits' at 0xE118

Step 2: s.mu.Lock() on copy #1; s.hits++
  mu' @0xE108 ──→ [ locked ]
  hits' @0xE118 ──→ [ 1 ]
  hits @0xE018 ──→ [ 0 ]   ◄── original Stats in caller untouched

Step 3: second RecordHit — brand-new copy, different mu address 0xE208
  shared memory:
    mu'' @0xE208 ──→ [ locked ] independently
  caller's real mu @0xE008 ──→ [ unlocked ]   ◄── each call locks a different mutex; original hits never updated on the shared Stats value

Step 4: logical invariant broken — "protected" field is not serialized under one lock
  hits @0xE018 ──→ [ still 0 or racy ]   ◄── interview trap: value receiver + Mutex
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
