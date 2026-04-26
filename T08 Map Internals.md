# T08 Map Internals

> **Reading Guide**: Sections 1-3 and 6 are essential first read (20 min).
> Sections 4-5 deepen understanding (15 min).
> Sections 7-12 are interview-specific — read closer to interview day.
> Section 13 is your comprehensive interview Q&A bank → [[questions/T08 Map Internals - Interview Questions]]
> Something not clicking? → [[simplified/T08 Map Internals - Simplified]]

---

## 0. Prerequisites

Complete these before starting this topic:

- [[prerequisites/P01 Structs & Struct Memory Layout]]
- [[prerequisites/P04 Hash Functions & Hashing Basics]]

---

## 1. Concept

A **map** in Go is a hash table. You give it a key, it gives you a value in O(1) average time.

That is the mechanism behind a session store (`map[string]*Session`), an in-memory order cache (`map[OrderID]*Order`), a per-endpoint hit counter (`map[string]int`), or a startup feature-flag table (`map[string]bool`). Same data structure, different production jobs.

Under the hood, a map is backed by an `hmap` struct that manages an array of **buckets**. Each bucket holds up to 8 key-value pairs. When a bucket is full, it chains to **overflow buckets**.

> **In plain English:** A map is like a library card catalog. You look up the book title (key), the card tells you the shelf number (hash), you go to that shelf (bucket), and find the book (value). Each shelf has room for 8 books. If the shelf is full, there's an overflow rack next to it.

---

## 2. Core Insight (TL;DR)

**Go maps are NOT safe for concurrent access.** Reading and writing from multiple goroutines without a lock will crash your program. This is the single most asked map question in interviews — and it shows up in real services when two HTTP handlers touch the same in-memory session map.

Internally, each bucket holds **8 key-value pairs** (not one). Go uses the **low bits** of the hash to pick the bucket, and the **top 8 bits** as a fast filter within the bucket. When the load factor exceeds **6.5**, the map doubles in size and gradually evacuates old buckets.

---

## 3. Mental Model (Lock this in)

### The Filing Cabinet Model

Think of a map as a filing cabinet with numbered drawers (buckets).

1. You hash the key to get a number
2. The low bits of the number tell you which drawer to open
3. Each drawer has 8 slots
4. The top 8 bits of the hash are written on a tiny label on each slot for quick matching
5. When all 8 slots are full, you tape an overflow tray to the drawer

```
hits["/api/users"]++  →  map[string]int  →  hash = 0xA3F7...42

Low bits (42 in binary) → bucket #2
Top 8 bits (0xA3) → tophash filter

Bucket #2:
┌──────────────────────────────────────────────────┐
│ tophash: [0xA3][0x5B][0x12][ 0 ][ 0 ][ 0 ][ 0 ][ 0 ] │
│ keys:    [/api/users][/api/orders][/health][ - ][ - ][ - ][ - ][ - ] │
│ values:  [ 120 ][ 87 ][ 4000 ][ - ][ - ][ - ][ - ][ - ] │
│ overflow: nil                                          │
└──────────────────────────────────────────────────┘

Lookup "/api/users":
  1. Hash → bucket #2
  2. Scan tophash for 0xA3 → match at slot 0
  3. Compare full key "/api/users" == "/api/users" → match
  4. Return value at slot 0 → 120 (request count for that route)
```

> **In plain English:** Imagine a library with numbered shelves. Each shelf has 8 book slots. To find a book, you hash its title to get a shelf number, then scan labels on that shelf. If the shelf is full, check the overflow cart next to it.

### The Mistake That Teaches You

Picture a toy HTTP server: every request goroutine writes into the same `map[string]*Session` without a lock. That is not a theoretical race — it is `fatal error: concurrent map writes` in production.

```go
type Session struct{ UserID int }

func main() {
    sessions := make(map[string]*Session)

    // Two request goroutines writing to the same map — CRASH
    go func() {
        for i := 0; i < 1000; i++ {
            sessions["sess-a"] = &Session{UserID: i}
        }
    }()
    go func() {
        for i := 0; i < 1000; i++ {
            sessions["sess-b"] = &Session{UserID: i}
        }
    }()

    time.Sleep(time.Second)
}
```

```
Output: fatal error: concurrent map writes

WHY: The map's internal bucket array is being modified by two goroutines
simultaneously. One goroutine might be in the middle of growing the map
(moving buckets) when the other writes — corrupted memory.

Go detects this at runtime and kills the program immediately.
It doesn't silently corrupt data — it panics.
```

**Fix: Use sync.RWMutex or sync.Map** — or stop sharing a plain map across goroutines without synchronization.

---

## 4. How It Actually Works (Internals) [INTERMEDIATE → ADVANCED]

This section is still the material interviewers expect (`hmap`, `bmap`, load factor, evacuation). The goal is not to recite `runtime/map.go` line by line, but to know what each piece *does* and why it matters when you are debugging latency, memory, or a prod panic.

### 4.1 The hmap Struct

Every `map[K]V` is a pointer to an `hmap` struct. **hmap is basically the brain of the map** — it knows how many items there are, where the buckets live, whether a grow is in progress, and what seed to use for hashing.

```go
// runtime/map.go (simplified)
type hmap struct {
    count     int            // number of key-value pairs
    flags     uint8          // concurrent read/write flags
    B         uint8          // log2 of bucket count (2^B buckets)
    noverflow uint16         // approximate number of overflow buckets
    hash0     uint32         // random hash seed (per-map, prevents hash flooding)
    buckets   unsafe.Pointer // pointer to bucket array (2^B buckets)
    oldbuckets unsafe.Pointer // pointer to old bucket array during growth
    nevacuate uintptr        // progress counter for evacuation
    extra     *mapextra      // overflow bucket pool
}
```

```
hmap (header, sits on stack or heap):
┌─────────────────────────────────────────┐
│ count: 5     │ B: 2 (4 buckets)         │
│ hash0: 0x7A3E │ flags: 0                │
│ buckets ──→ [bucket0][bucket1][bucket2][bucket3] │
│ oldbuckets: nil (not growing)           │
└─────────────────────────────────────────┘
```

**Why you care:** `count` and `B` are what drive growth decisions. When someone asks "why did my map allocation spike mid-request?", the answer often starts here: the table got fuller than the runtime liked, so it doubled buckets and started incremental work.

Key detail: `map` variables are already pointers. When you pass a map to a function, you're passing a copy of the pointer — both point to the same `hmap`. That's why modifications inside a function are visible to the caller (handy for `RegisterRoute`, bad if you forget you're sharing one map across handlers).

> **In plain English:** The map variable is like a business card with the address of the filing cabinet. Everyone who has the business card goes to the same cabinet.

### 4.2 The Bucket (bmap) Struct

Each bucket stores 8 entries, organized for cache efficiency. **bmap is the physical drawer** — the thing you actually scan when a request looks up a session ID or an order ID.

```go
// runtime/map.go (simplified)
type bmap struct {
    tophash [8]uint8  // top 8 bits of hash for each slot (fast filter)
    // followed in memory by:
    // keys   [8]KeyType
    // values [8]ValueType
    // overflow *bmap
}
```

```
Single bucket memory layout (keys and values are SEPARATE arrays):
┌──────────────────────────────────┐
│ tophash: [h0][h1][h2][h3][h4][h5][h6][h7] │  ← 8 bytes, fits one cache line scan
├──────────────────────────────────┤
│ keys:    [k0][k1][k2][k3][k4][k5][k6][k7] │  ← all keys together
├──────────────────────────────────┤
│ values:  [v0][v1][v2][v3][v4][v5][v6][v7] │  ← all values together
├──────────────────────────────────┤
│ overflow: *bmap (or nil)                    │  ← chain to next bucket
└──────────────────────────────────┘

WHY keys and values are separated (not key0,val0,key1,val1,...):
  If key is int64 (8B) and value is bool (1B):
    Interleaved: [8B key][1B val][7B padding][8B key][1B val]... ← wasted padding
    Separated:   [8B][8B][8B]...[1B][1B][1B]...                 ← no padding waste
```

**Why you care:** When you store `map[string]*Order`, the map holds pointers in the value array; the `Order` structs themselves live elsewhere. That layout choice is why pointer-valued maps feel natural for caches — you mutate through the pointer without the map moving your struct.

> **In plain English:** Instead of alternating shirts and socks in a drawer (wasting space with padding), you put all shirts on one side and all socks on the other. Less wasted space.

### 4.3 Hash Function and Bucket Selection

```
Full hash of key: 0xA3F7_8B2C_4D1E_0042  (64 bits)

Step 1: Select bucket
  bucket_index = hash & (2^B - 1)
  If B=2: bucket_index = hash & 0b11 = 0x42 & 0b11 = 2  → bucket #2

Step 2: Fast filter within bucket
  tophash = hash >> 56 = 0xA3
  Scan the 8-byte tophash array for 0xA3 (one cache line, very fast)

Step 3: Full key comparison
  Only if tophash matches → compare full key (avoids expensive comparisons)
```

The **hash0** field is a random seed unique to each map instance. Identical keys hash to different buckets in different maps, which matters if someone tries to craft many keys that collide in *your* idempotency-key map — they cannot reuse a recipe from another process.

**Why you care:** Per-request maps and global singleton maps both pay this hash cost on every access. Hot paths (feature flags read per request) are why people sometimes wrap a `map[string]bool` in `RWMutex` and pre-load once at startup.

### 4.4 Map Growth and Evacuation

When the **load factor** (roughly entries per bucket) exceeds **6.5**, or there are too many overflow buckets, the map grows.

**Load factor is the knob that trades memory for speed.** While the map is overcrowded, lookups walk longer overflow chains — so p99 latency creeps up. After Go grows the table and spreads entries out, **the same code path often gets faster** because chains shrink. That is the "why you care" behind load factor: it is not trivia, it is why a bursty write phase can leave you with a snappier read phase afterward.

```
BEFORE GROWTH (B=2, 4 buckets, load > 6.5):
  buckets: [bucket0][bucket1][bucket2][bucket3]
                                ↑ overflow chains getting long

GROWTH TRIGGERED:
  1. Allocate new bucket array: 2x size (B=3, 8 buckets)
  2. Set oldbuckets = current buckets
  3. Set buckets = new (empty) array
  4. On each subsequent read/write, evacuate 1-2 old buckets → new buckets

DURING GROWTH (incremental evacuation):
  oldbuckets: [bucket0][bucket1][bucket2*][bucket3]
                                    ↑ evacuated
  buckets:    [b0][b1][b2][b3][b4][b5][b6][b7]
                          ↑ entries moved here

AFTER GROWTH:
  oldbuckets: nil (freed)
  buckets:    [b0][b1][b2][b3][b4][b5][b6][b7]
  Load factor back to normal. Overflow chains shortened.
```

Growth is **incremental** — Go does not stop the world to rehash everything. Each map operation evacuates a slice of old work. **Evacuation is the "copying in the background" you might see in CPU profiles** during a traffic spike that fills a big `map[string]int` of endpoint hit counts: a chunk of CPU time is literally migrating entries from `oldbuckets` into the wider table.

> **In plain English:** When the filing cabinet is overflowing, you buy a bigger one. But you don't move everything at once — every time someone opens a drawer, you move one old drawer's contents to the new cabinet. Eventually, the old cabinet is empty and gets thrown away.

### 4.5 Iteration Randomness

Go **deliberately randomizes** map iteration order. Each `for range` loop picks a random starting bucket and a random offset within that bucket.

```go
endpoints := map[string]int{
    "/api/users":  120,
    "/api/orders": 87,
    "/health":     4000,
}

// Run 1: /health, /api/users, /api/orders
// Run 2: /api/orders, /health, /api/users
// NEVER rely on map order when emitting metrics or logs
```

This prevents code from accidentally depending on insertion order when dumping a label set or iterating feature flags. It is a feature, not a bug.

---

## 5. Key Rules & Behaviors

### Rule 1: Maps Are NOT Safe for Concurrent Access

This is the most important rule and the most common interview question.

```go
// CRASH: concurrent map writes (e.g. metrics map updated per request)
hits := make(map[string]int)
var wg sync.WaitGroup
for i := 0; i < 10; i++ {
    wg.Add(1)
    go func(path string) {
        defer wg.Done()
        hits[path]++ // RACE
    }(fmt.Sprintf("/api/req-%d", i))
}
wg.Wait()
```

```
Goroutine 1: hits["/api/users"]++
  → writing to bucket #1, mid-operation...
Goroutine 2: hits["/api/orders"]++
  → also writing to bucket #1
  → CORRUPTED: Go detects flag already set → fatal error

Fix: sync.RWMutex for read-heavy (feature flags), sync.Map for some cache patterns
```

> **In plain English:** Two people reaching into the same filing drawer at the same time will jam their hands together and rip the papers. Go panics instead of silently shredding your data.

### Rule 2: Map Values Are NOT Addressable

You cannot take the address of a map value.

```go
type User struct {
    Name  string
    Email string
}

m := map[string]User{"u1": {Name: "rahul", Email: "r@example.com"}}
m["u1"].Name = "admin"  // COMPILE ERROR: cannot assign to struct field in map

// Fix: copy, modify, write back
u := m["u1"]
u.Name = "admin"
m["u1"] = u
```

```
WHY: Maps rehash during growth, moving entries to new buckets.
A pointer to m["u1"] could become dangling after growth.
Go prevents this at compile time.

Alternative: use map[string]*User (pointers as values)
m := map[string]*User{"u1": {Name: "rahul", Email: "r@example.com"}}
m["u1"].Name = "admin"  // OK — pointer doesn't move when map grows
```

> **In plain English:** You can't glue a bookmark to a page in a book that might be reprinted tomorrow. The page might end up at a different location. Either make a copy, edit it, and put it back — or store a bookmark (pointer) instead.

### Rule 3: nil Map Reads Are Safe, Writes Panic

```go
var flags map[string]bool  // nil map — not loaded yet

enabled := flags["new_checkout_flow"] // OK: returns zero value (false)
enabled, ok := flags["new_checkout_flow"] // OK: false, false

flags["new_checkout_flow"] = true // PANIC: assignment to entry in nil map
```

```
nil map:  [ hmap pointer = nil ]
  Read → Go checks nil, returns zero value safely
  Write → Go tries to follow nil pointer → PANIC

Fix: flags = make(map[string]bool)  // or load from config into a real map
```

> **In plain English:** Looking at an empty shelf is fine — you see nothing. Trying to put a book on a shelf that doesn't exist crashes. Build the shelf first with `make()`.

### Rule 4: Delete During Iteration Is Safe

Go guarantees that deleting keys during `for range` is safe. The deleted key won't appear in subsequent iterations.

```go
pending := map[string]struct{}{
    "idemp-aaa": {},
    "idemp-bbb": {},
    "idemp-ccc": {},
}
for k := range pending {
    if k == "idemp-bbb" {
        delete(pending, k) // safe
    }
}
```

But **adding** keys during iteration has undefined behavior — the new key may or may not appear.

> **In plain English:** You can throw books off the shelf while scanning it — you just won't see those books again. But if someone adds books while you're scanning, you might miss them or see them twice.

### Rule 5: The Comma-Ok Idiom Distinguishes Missing from Zero

```go
// Feature flag exists but is explicitly off
flags := map[string]bool{"dark_mode": false}

v := flags["dark_mode"]     // v = false
v2 := flags["beta_api"]     // v2 = false ← same! Can't tell if "beta_api" exists

v, ok := flags["dark_mode"]   // v = false, ok = true  → key exists
v2, ok2 := flags["beta_api"] // v2 = false, ok2 = false → key missing
```

> **In plain English:** Asking "what's on shelf B?" and getting "nothing" doesn't tell you if shelf B is empty or doesn't exist. The comma-ok pattern is asking "does shelf B exist?"

---

## 6. Code Examples (Show, Don't Tell)

### Example 1: Safe Concurrent Map Access (session or metrics store)

```go
type Session struct {
    UserID int
}

type SessionStore struct {
    mu   sync.RWMutex
    data map[string]*Session
}

func NewSessionStore() *SessionStore {
    return &SessionStore{data: make(map[string]*Session)}
}

func (s *SessionStore) Get(sessionID string) (*Session, bool) {
    s.mu.RLock()
    defer s.mu.RUnlock()
    sess, ok := s.data[sessionID]
    return sess, ok
}

func (s *SessionStore) Put(sessionID string, sess *Session) {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.data[sessionID] = sess
}
```

```
Multiple readers (many GETs):     Single writer (login / refresh):
  RLock ✓                           Lock ✓
  RLock ✓                           (all readers blocked)
  RLock ✓                           (all other writers blocked)
  (concurrent reads OK)             Unlock → readers resume
```

For **feature flags** loaded once at startup and read on every request, the same pattern applies: `RWMutex` + `map[string]bool` is the straightforward production shape unless profiling says you need `sync.Map`.

### Example 2: Map with Struct Values (the copy-edit-write pattern)

```go
type OrderID string

type OrderSummary struct {
    LineItems int
    TotalCents int64
}

cache := map[OrderID]OrderSummary{
    "ord-1001": {LineItems: 3, TotalCents: 4999},
}

// Can't do: cache["ord-1001"].LineItems++ // COMPILE ERROR
// Must do:
sum := cache["ord-1001"]
sum.LineItems++
cache["ord-1001"] = sum // write back
```

```
Step 1: sum := cache["ord-1001"]
  sum is a COPY of OrderSummary{LineItems: 3, TotalCents: 4999}

Step 2: sum.LineItems++
  sum is now OrderSummary{LineItems: 4, TotalCents: 4999}
  map still has OrderSummary{LineItems: 3, ...}

Step 3: cache["ord-1001"] = sum
  map now has OrderSummary{LineItems: 4, ...}
```

### Example 3: Map Size Hint for Performance

```go
type OrderID string
type Order struct { /* line items, totals, etc. */ }

// Without hint: map grows multiple times as entries are added
orders := make(map[OrderID]*Order)

// With hint: pre-allocates enough buckets for ~10k entries
orders = make(map[OrderID]*Order, 10_000)
```

```
orders := make(map[OrderID]*Order):
  B=0 → 1 bucket → grow at 7 entries → grow at 14 → grow at 28 → ...
  Each growth: allocate, evacuate, repeat

orders := make(map[OrderID]*Order, 10_000):
  B=11 → 2048 buckets → room for ~13k entries before first growth
  Zero growths during initial filling → faster bulk load
```

Pre-sizing matters when you know the approximate count — for example hydrating a cache from a nightly snapshot or indexing users after a batch import (`BuildUserIndex`).

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

```go
hits := map[string]int{"/api/users": 1, "/api/orders": 2, "/health": 3}
delete(hits, "/api/orders")
fmt.Println(len(hits))

var idle map[string]int
fmt.Println(idle["/metrics"])
fmt.Println(len(idle))
```

What prints? Think about it before checking.

> [!success]- Answer
> ```
> 2
> 0
> 0
> ```
> `delete` removes `/api/orders`, len is 2. Reading from a nil map returns the zero value (0 for int) — no panic. `len` of a nil map is 0 — also no panic. Only WRITING to a nil map panics.

### Tier 2: Fix the Bug (5 min)

```go
func CountRequestsByEndpoint(paths []string) map[string]int {
    var counts map[string]int
    for _, p := range paths {
        counts[p]++
    }
    return counts
}
```

This panics. Fix it.

> [!success]- Answer
> Initialize the map with `make`:
> ```go
> func CountRequestsByEndpoint(paths []string) map[string]int {
>     counts := make(map[string]int)
>     for _, p := range paths {
>         counts[p]++
>     }
>     return counts
> }
> ```
> `var counts map[string]int` declares a nil map. Reading a nil map returns zero values (safe), but WRITING to a nil map panics with `assignment to entry in nil map`. `make` allocates the underlying hmap struct.

### Tier 3: Build It (15 min)

Build a **simple in-memory cache with TTL** using a `map[string]cacheEntry` (or `map[string]*cacheEntry` if you mutate in place), where `cacheEntry` holds your value and an expiry time. Support `Get(key)` (return value + ok if not expired), `Set(key, value, ttl)`, and periodic or lazy cleanup of expired keys. Protect it with `sync.RWMutex` if you want concurrent safety.

> Full solutions with explanations → [[exercises/T08 Map Internals - Exercises]]

---

## 7. Edge Cases & Gotchas

| Gotcha | What Happens | Fix |
|--------|-------------|-----|
| Concurrent map read + write | `fatal error: concurrent map read and map write` | sync.RWMutex or sync.Map |
| Concurrent map writes | `fatal error: concurrent map writes` | sync.Mutex |
| Write to nil map | `panic: assignment to entry in nil map` | Initialize with `make()` |
| Struct field assignment in map | `cannot assign to struct field in map` | Copy-edit-write or use pointer values |
| Relying on iteration order | Order changes between runs | Sort keys if order matters |
| Large map never shrinks | Memory stays allocated after mass deletion | Re-create the map |
| Map of pointers hides nil | `m[key].Field` panics if value is nil pointer | Check with comma-ok first |

**The "map never shrinks" gotcha:**

```go
m := make(map[string]*Session)
for i := 0; i < 1_000_000; i++ {
    m[fmt.Sprintf("sess-%d", i)] = &Session{}
}
for i := 0; i < 1_000_000; i++ {
    delete(m, fmt.Sprintf("sess-%d", i))
}
// m is empty BUT still holds memory for a huge bucket table
// Fix: m = make(map[string]*Session) to reclaim memory
```

> **In plain English:** When you empty all the drawers in a filing cabinet, the cabinet doesn't magically shrink. You need to buy a smaller cabinet (re-create the map) to free the space.

---

## 8. Performance & Tradeoffs

**Slice vs map for lookups.** If you have a few dozen static routes or metric names, a sorted slice + binary search (or a tiny linear scan) can beat a map because you avoid hashing and one pointer hop — great L1/L2 behavior. Once you have hundreds or thousands of keys, or keys are not sortable in a useful way, the map wins.

**When map overhead is not worth it.** A `map[string]int` for three counters (`"/api/users"`, `"/api/orders"`, `"/health"`) is fine but not free: you pay hashing and indirection on every increment. For *three* fields, three atomic integers or a struct might be simpler and faster — use a map when the key space is dynamic (unknown endpoints, tenant IDs, order IDs).

**Hot read paths.** Feature flags as `map[string]bool` behind an `RWMutex` is a standard pattern: writers take `Lock` rarely (config reload), readers take `RLock` on every request. If writes are extremely rare and keys are stable, benchmark against `atomic.Value` holding an immutable map snapshot.

**Growth and evacuation.** After a large insert burst into `map[OrderID]*Order`, you might see extra CPU while the runtime finishes evacuation — that is normal, not necessarily a leak.

| Operation | Average | Worst (many collisions) | Notes |
|-----------|---------|------------------------|-------|
| Lookup | O(1) | O(n) | Worst case: long overflow chain in one bucket |
| Insert | O(1) amortized | O(n) during growth | Growth doubles buckets, evacuates incrementally |
| Delete | O(1) | O(n) | Marks slot empty; table does not shrink |
| Iteration | O(n) | O(n) | Random order, touches live entries |

| Approach | When to Use |
|----------|------------|
| `make(map[K]V)` | Default — let Go manage growth |
| `make(map[K]V, hint)` | You know approximate size — fewer growths during load |
| `sync.RWMutex` + map | Concurrent access, read-heavy (sessions, flags, read-mostly caches) |
| `sync.Map` | Specialized patterns; benchmark before defaulting to it |
| Slice / struct fields | Tiny fixed key sets where hashing buys you nothing |

---

## 9. Common Misconceptions

| Misconception | Reality |
|--------------|---------|
| "Maps are passed by reference" | Maps are pointers under the hood. You pass a copy of the pointer. Both copies point to the same hmap. |
| "sync.Map is always better for concurrency" | sync.Map is optimized for specific access patterns. For general read-write maps, `RWMutex` + map often wins — measure. |
| "Deleting from a map frees memory" | Buckets are not shrunk. Re-creating the map reclaims the big backing store. |
| "Map iteration is random" | It's deliberately randomized, but not cryptographically random. It's to prevent order-dependency, not for security. |
| "Maps can use any type as key" | Keys must be comparable (==). Slices, maps, and functions cannot be keys. |

---

## 10. Related Tooling & Debugging

| Tool | What It Does |
|------|-------------|
| `go run -race` | Detects concurrent map access at runtime |
| `runtime.NumCPU()` | Shows GOMAXPROCS — more goroutines = more race risk |
| `fmt.Printf("%v\n", m)` | Prints map contents (order will vary) |
| `reflect.TypeOf(m).Key().Comparable()` | Check if a type can be a map key |
| `GODEBUG=hashmap=1` | Debug map operations (Go internal, may change) |

---

## 11. Interview Gold Questions

### Q1: "Why is Go's map not safe for concurrent access?"

**Talk like a human:** Because the runtime is allowed to rearrange the bucket array while you are using it — especially during growth. Imagine one goroutine mid-evacuation while another writes a new session: the internal links between buckets are not meant to be updated by two CPUs at once. Go sets flag bits, notices the overlap, and stops the world with a fatal error instead of letting memory go corrupt.

**If they want mechanism:** hmap has `buckets` and sometimes `oldbuckets` during incremental growth; writers and readers touch the same metadata. There is no fine-grained locking inside the map — **you** supply `Mutex` / `RWMutex` / `sync.Map` / message passing.

### Q2: "Explain the internal structure of a Go map."

**Talk like a human:** Think header + drawers. The header (`hmap`) tracks how full things are, how many buckets you have (`2^B`), the per-map hash seed, and during growth a pointer back to the old table plus a progress counter. Each drawer (`bmap`) stores eight slots: a tiny `tophash` row for quick rejection, then all keys, then all values, then maybe a pointer to an overflow drawer. Lookups hash the key, mask to a bucket, scan `tophash`, then compare keys for real.

**Why interviewers care:** They want to know you understand incremental growth (not one big stop-the-world copy) and why pointer values interact nicely with relocation.

### Q3: "Why can't you take the address of a map value?"

**Talk like a human:** Because the value you think is at `m[k]` might physically move when the map grows. Letting you take `&m[k]` would invite pointers that go stale. So Go forbids it. If you need stable mutation, store a pointer in the map (`map[K]*V`) or copy the struct out, edit, put it back.

---

## 12. Final Verbal Answer

If someone asks cold, I would say: a Go map is a hash table — there's a small header struct tracking size, seeds, and bucket pointers, and a big slice of buckets that each hold eight entries plus overflow links. Lookups hash the key, pick a bucket with the low bits, use the top bits as a quick filter, then compare keys. When the table gets too full, Go allocates a bigger one and **gradually** moves data across operations, which is why you sometimes see extra CPU during spikes. Maps are not safe to share across goroutines without your own synchronization — that's the production panic you get if two HTTP handlers bump the same `map[string]*Session`. Oh, and you can't take the address of a map value because entries move; use pointers as values or copy-edit-write. Iteration order is intentionally random so nobody builds on accidental ordering.

---

## 13. Comprehensive Interview Questions

> Full interview question bank (12 questions) → [[questions/T08 Map Internals - Interview Questions]]

Preview:
1. "Why is Go's map not safe for concurrent access?" [COMMON]
2. "What is the load factor and when does a map grow?" [COMMON]
3. "Why is map iteration order random in Go?" [TRICKY]

---

> See [[Glossary]] for term definitions.
