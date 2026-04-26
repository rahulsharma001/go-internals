# P03 Mutex & Concurrency Safety Basics

> **Prerequisite note** — complete this before starting [[T07 Pointers & Pointer Semantics]] or [[T18 Mutex & RWMutex Internals]].
> Estimated time: ~20 min

---

## 1. Concept

A **mutex** is a lock. You use it when **more than one goroutine** might touch the **same memory** (a counter, a map, a pool struct) at the same time.

Picture **one bathroom, one bolt on the door**. If someone is inside, everyone else waits in the hall. When they leave, they unbolt. Only one person is in there at a time. That is what the lock enforces: **only one goroutine at a time** runs the bit of code that updates your shared state.

When you call `mu.Lock()` and later `mu.Unlock()`, the **code in between** is special: **only one goroutine runs it at a time**. If you hear "critical section," that's all it means — **the code between Lock and Unlock**.

---

## 2. Core Insight (TL;DR)

**Shared fields + concurrent goroutines + no coordination = wrong answers.** Your HTTP handlers might interleave in any order. The compiler and CPU can reorder things. **`sync.Mutex` forces turns**: one goroutine finishes its update before the next one starts.

**Rules that save you:** pair **`Lock()` with `Unlock()`**, almost always with **`defer mu.Unlock()`** right after `Lock()`. **Never copy** a value that embeds `sync.Mutex` or `sync.RWMutex` — the copy gets a **second lock** that does not protect the original data.

---

## 3. Mental Model (Lock this in)

Your service has a **`RequestCounter`** (hits per path), a **`RateLimiter`** (tokens in a bucket), an in-memory **`Cache`** (map of session or computed data), maybe a **`ConnectionPool`** (idle vs in-use counts). These are all **shared structs**. Every incoming request might spawn or run logic in a goroutine. If two requests bump the same counter or read/write the same map **without** a lock, you get **races**: lost increments, corrupt maps, limits that lie.

The bathroom maps to Go like this:

- **`Lock()`** — bolt the door; your goroutine enters the protected bit of code.
- **`Unlock()`** — open the door; the next waiter can enter.
- The **protected bit** — only this goroutine runs it until `Unlock()`.

Two handlers both doing `count++` on a shared `int` **without** a mutex is like two people both reading the whiteboard, both writing the same wrong total. You **lose** request counts in production; dashboards lie; rate limits slip.

---

## 4. How It Works

### 4.1 `sync.Mutex`: `Lock()`, `Unlock()`, and the protected region

`Lock()` waits until no one else holds the mutex, then your goroutine owns it. `Unlock()` releases it. **Everything between them runs alone** — no other goroutine that uses the same `mu` runs that region at the same time.

```go
type RequestCounter struct {
    mu    sync.Mutex
    byPath map[string]int64 // path -> request count
}

func (c *RequestCounter) Record(path string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.byPath[path]++
}
```

**Typical failure without a lock:** two goroutines handle `/api/users` at once. Both read the same count, both add one, both write back the same number. **You expected +2; you got +1.** That's a **lost update** on your metrics.

```
MEMORY TRACE — race on shared request count (no mutex):

Step 1: shared state for path "/api/users" shows count 100

Step 2: goroutine G1 (request A) and G2 (request B) both read count → both see 100
        ◄── each does read / add 1 / write; those steps are not one atomic instruction

Step 3: both compute 101 and store
        shared count becomes 101
        ◄── should be 102; one request never showed up in the counter (lost bump)

Step 4: under real load, scheduling varies → final count wrong and non-deterministic
```

**Fix:** one `sync.Mutex` on the struct, **`Lock()` / `defer Unlock()`** around the map update. Only one goroutine at a time runs `c.byPath[path]++`.

```
MEMORY TRACE — same counter with mutex:

Step 1: G1 calls Lock → holds mutex; G2 calls Lock → waits

Step 2: G1 runs c.byPath[path]++, then Unlock

Step 3: G2 wakes, Lock succeeds, increments, Unlock
        ◄── updates happen in strict order; no two goroutines overlap the protected code

Step 4: after both complete, count reflects both requests (e.g. 100 → 102)
```

### 4.2 `defer mu.Unlock()`

Early `return` must still release the lock. **`defer` runs when the function returns**, including error paths (and after `panic` recovery boundaries — still prefer small critical sections).

```go
func (lim *RateLimiter) Take() bool {
    lim.mu.Lock()
    defer lim.mu.Unlock()

    if lim.tokens <= 0 {
        return false // defer still unlocks
    }
    lim.tokens--
    return true
}
```

Without `defer`, a `return` after `Lock()` **leaves the mutex held**. The next `Take()` blocks forever — classic **self-inflicted deadlock** for that limiter.

### 4.3 Rate limiter shape (tokens + mutex)

```go
type RateLimiter struct {
    mu     sync.Mutex
    tokens int // refill logic omitted — focus is concurrent Take/Refill
}

// Take tries to consume one token; Refill adds tokens — both must lock the same mu.
```

Many goroutines calling `Take()` for API traffic **must** serialize updates to `tokens`. Same idea as the request counter: **read, decide, write** is multiple steps; without a lock, two callers both think a token exists.

### 4.4 `sync.RWMutex`: many readers **or** one writer

Use this when **lots of HTTP GETs** read a cache and **invalidation or refresh** writes rarely.

- **`RLock()` / `RUnlock()`** — shared read lock. Many goroutines can hold it **if** no writer holds `Lock()`.
- **`Lock()` / `Unlock()`** — exclusive. **Blocks everyone** until the writer finishes.

```go
type Cache struct {
    mu   sync.RWMutex
    data map[string]string
}

func (c *Cache) Get(key string) (string, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    v, ok := c.data[key]
    return v, ok
}

func (c *Cache) Invalidate(key string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    delete(c.data, key)
}
```

**When `RWMutex` helps:** read-heavy cache, reads are safe to overlap, writes are infrequent. **When a plain `Mutex` is enough:** writes are common, or the protected code is so tiny that reader lock bookkeeping does not pay off.

### 4.5 Connection pool (mental picture)

A **`ConnectionPool`** might track `idle` and `active` slices or counts. **`Borrow()`** and **`Return()`** from different request goroutines **must** update those structures under **one mutex**. Otherwise two goroutines might hand out the same connection, or lose one on the free list.

---

## 5. Key Rules & Behaviors

### Always pair `Lock()` with `defer Unlock()`

```go
func bad(mu *sync.Mutex) {
    mu.Lock()
    if err != nil {
        return // BUG: forgot Unlock
    }
    mu.Unlock()
}
```

```go
func good(mu *sync.Mutex) {
    mu.Lock()
    defer mu.Unlock()
    if err != nil {
        return // OK
    }
}
```

Treat `Lock()` like a resource you **always** release on exit — **`defer`** is the usual pattern.

### Never copy a mutex — the copy trap

If you **pass your cache or counter struct by value** into a handler helper, **the mutex is copied too**. Each copy has **its own lock**. Goroutines lock **different** mutexes. **Your real map or counter is not protected.**

```go
type Cache struct {
    mu   sync.Mutex
    data map[string]string
}

func brokenRefresh(c Cache) { // BY VALUE — copies mu and map header
    c.mu.Lock()
    defer c.mu.Unlock()
    c.data["x"] = "y" // mutating the copy's map field — subtle and dangerous
}
```

**Correct:** pointer receiver, pass `*Cache`, one mutex per live object.

```
MEMORY TRACE — copy trap:

Step 1: you have one Cache value in the caller; it holds the real map and one mutex

Step 2: you pass Cache by value into a function → Go copies the whole struct
        the copy contains a second mutex word and a copy of the map descriptor

Step 3: the callee locks the copy's mutex only
        the original's mutex is never held by that path

Step 4: another goroutine can mutate the original cache while the first goroutine
        thinks it is "safe" — you now have two unrelated locks; shared data is unprotected
```

```go
func (c *Cache) Refresh(key, val string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.data[key] = val
}
```

### Pointer receivers for types that embed `sync.Mutex`

Methods that mutate shared state should use **`func (c *Cache)`** style **pointer receivers** so every call shares **one** mutex and **one** backing map.

### Do not `Lock()` twice on the same `sync.Mutex` in one goroutine

`sync.Mutex` is **not re-entrant**. Second `Lock()` blocks until `Unlock()`, which you never reach — **deadlock**.

### Mutex vs channel (quick guide)

- **Protecting fields on a struct** (counter, limiter, cache, pool stats)? **Mutex** (or `RWMutex`) with clear methods.
- **Handing off work or signaling** between goroutines? Often a **channel**.
- Hot path shared state? **Mutex** is normal and idiomatic in Go.

---

## 6. Code Examples (Show, Don't Tell)

### 6.1 Broken: shared counter, no lock

```go
package main

import (
    "fmt"
    "sync"
)

func main() {
    var total int64
    var wg sync.WaitGroup
    const handlers = 10000
    for i := 0; i < handlers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            total++ // race: simulates each HTTP handler bumping a global request count
        }()
    }
    wg.Wait()
    fmt.Println(total) // often < 10000
}
```

### 6.2 Fixed: `sync.Mutex` around the bump

```go
package main

import (
    "fmt"
    "sync"
)

func main() {
    var total int64
    var mu sync.Mutex
    var wg sync.WaitGroup
    const handlers = 10000
    for i := 0; i < handlers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            mu.Lock()
            total++
            mu.Unlock()
        }()
    }
    wg.Wait()
    fmt.Println(total) // 10000
}
```

### 6.3 `RequestCounter` with pointer receiver

```go
type RequestCounter struct {
    mu     sync.Mutex
    byPath map[string]int64
}

func NewRequestCounter() *RequestCounter {
    return &RequestCounter{byPath: make(map[string]int64)}
}

func (c *RequestCounter) Record(path string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.byPath[path]++
}
```

### 6.4 Copy trap: helper takes your struct by value

```go
package main

import (
    "fmt"
    "sync"
)

// In-flight requests — field must move only under one real mutex.
type Metrics struct {
    mu         sync.Mutex
    inFlight   int
}

func bumpInFlightByValue(m Metrics) {
    m.mu.Lock()
    defer m.mu.Unlock()
    m.inFlight++
}

func main() {
    var m Metrics
    bumpInFlightByValue(m)
    fmt.Println(m.inFlight) // 0 — only the copy's field changed
    // Real handler code: func(w http.ResponseWriter, r *http.Request, pool *Metrics)
}
```

**Why a `map` in a copy is misleading in a toy:** copying the struct **copies the mutex** but the **map header still points at the same map** — you can "see" writes from a by-value helper and think you're safe. **`int` fields** show the trap in one goroutine. Under **real concurrency**, by-value helpers on **`Cache`** still give you **two lock words** and **racy map writes**.

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the behavior (2 min)

```go
type RequestCounter struct {
    mu     sync.Mutex
    byPath map[string]int64
}

// Bug on purpose: value receiver — each call gets its own mutex copy.
func (c RequestCounter) Record(path string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.byPath[path]++
}

func main() {
    c := RequestCounter{byPath: make(map[string]int64)}
    var wg sync.WaitGroup
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for j := 0; j < 100; j++ {
                c.Record("/api/x")
            }
        }()
    }
    wg.Wait()
    fmt.Println(c.byPath["/api/x"])
}
```

> [!success]- Answer
> **Not `100000`.** The printed value is **wrong and varies run to run** (often **much less** than 100000). The `map` header is still shared, but **each `Record` locks a different `Mutex` copy**, so **nothing serializes** concurrent `c.byPath[path]++` — classic **data race**. Run with **`go run -race`**. Fix: **`func (c *RequestCounter) Record(...)`** so every call shares **one** mutex and the protected code between **`Lock` and `Unlock`** actually runs **one goroutine at a time**.

### Tier 2: Fix the bug (5 min)

```go
type Cache struct {
    mu   sync.RWMutex
    data map[string][]byte
}

func (c Cache) Set(key string, blob []byte) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.data[key] = blob
}
```

> [!success]- Answer
> **Bug:** value receiver **`func (c Cache)`** copies the struct, so **`Lock()` locks a different mutex each call** and **`c.data` updates may not hit the caller's map reliably** — same failure mode as copying `sync.Mutex`.
>
> **Fix:** **`func (c *Cache) Set(key string, blob []byte)`** with pointer receiver. Construct caches as **`&Cache{data: make(...)}`** and pass **`*Cache`** around. Never pass the struct by value into handlers if it contains a mutex.

---

## 7. Gotchas & Interview Traps

| Trap | What happens | What to do |
|------|----------------|------------|
| Copy trap | Two mutexes, **false** sense of safety | Pointer receivers; **`func (c *T)`**; pass pointers |
| Forgotten `Unlock` | Early `return` leaves lock held | **`defer mu.Unlock()`** immediately after `Lock()` |
| Double `Lock` same mutex | Same goroutine blocks itself | One lock per path; split functions |
| `RWMutex` on tiny structs | Reader lock overhead | Benchmark; sometimes plain **`Mutex`** wins |
| Mixing mutex + channel for same invariant | Easy deadlocks | One clear strategy per piece of state |

---

## 8. Interview Gold Questions (Top 3)

**Q1: What is a data race, and how does a mutex help?**

Two goroutines access the same memory, **at least one write**, without ordering rules. The scheduler can interleave their reads and writes. A mutex **queues** those accesses so **only one goroutine at a time** runs the code between **`Lock()` and `Unlock()`** — updates appear **serial**, not tangled.

**Q2: Why must you not copy `sync.Mutex`?**

The lock state lives **inside the struct value**. A copy gets a **new** lock word. Two goroutines can each hold **a different copy's** lock and still stomp the same shared map or counter. **One live object → one mutex.**

**Q3: When pick `RWMutex` over `Mutex`?**

**Many concurrent readers** (GETs from a cache), **rare writers** (invalidation), reads safe to overlap, writer needs **exclusive** access. If writes are frequent, measure — a single **`Mutex`** is often simpler.

---

## 9. 30-Second Verbal Answer

Your handlers run in goroutines. If they share a **counter, rate limiter, cache, or pool struct** without coordination, **updates interleave** and you get **wrong counts, broken maps, or unsafe pools**. A **mutex** is a **turnstile**: **`Lock()`**, do the smallest amount of work on shared fields, **`defer Unlock()`**. **`RWMutex`** when **many readers** and **occasional writers**. **Never copy** structs that embed **`sync.Mutex`** — use **pointer receivers** and **one** object. Use **channels** when the design is about **sending work or signals**; use **mutexes** when the clearest model is **protecting shared fields**.

---

> See [[Glossary]] for term definitions.
