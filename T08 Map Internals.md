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

This section is what interviewers expect you to know: `hmap`, `bmap`, load factor, evacuation. The goal is not to recite `runtime/map.go` line by line, but to know what each piece *does* and why it matters when you are debugging latency, memory, or a prod panic.

### 4.1 The hmap Struct

Every `map[K]V` variable is a pointer to an `hmap` struct. hmap is the brain of the map — it knows how many items there are, where the buckets live, whether a grow is in progress, and what seed to use for hashing.

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

**Trace it through a real scenario.** You're building a session store for an HTTP server:

```go
sessions := make(map[string]*Session)
```

```
Step 1: Runtime allocates an hmap struct on the heap
Step 2: Generates a random hash seed (hash0 = 0x7A3E) for THIS map instance
Step 3: Sets B=0 → 2^0 = 1 bucket (minimum)
Step 4: Allocates 1 bucket (bmap) with 8 empty slots
Step 5: Returns a POINTER to this hmap

What's in memory now:

  sessions (stack variable, 8 bytes — it's just a pointer):
  ┌───────────────┐
  │ ptr = 0xC0001 │──────┐
  └───────────────┘      │
                         ▼
  hmap (heap):
  ┌───────────────────────────────────────────┐
  │ count: 0       │ B: 0 (1 bucket)          │
  │ hash0: 0x7A3E  │ flags: 0                 │
  │ buckets ──→ [bucket0 (8 empty slots)]     │
  │ oldbuckets: nil (not growing)              │
  └───────────────────────────────────────────┘
```

Now a user logs in and you store their session:

```go
sessions["abc-123"] = &Session{UserID: 42}
```

```
Step 1: Hash the key using this map's seed
  hash("abc-123", seed=0x7A3E) → 0xA3F7_8B2C_4D1E_0042

Step 2: Pick the bucket
  bucket_index = hash & (2^B - 1) = 0x0042 & 0 = 0
  → bucket #0 (only one bucket exists right now)

Step 3: Find an empty slot in bucket #0
  Scan tophash array: [0][0][0][0][0][0][0][0]  ← all empty
  → use slot 0

Step 4: Write the entry
  tophash[0] = top 8 bits of hash = 0xA3
  keys[0]    = "abc-123"
  values[0]  = pointer to Session{UserID: 42} on heap
  hmap.count++ → count = 1

After the insert:

  hmap: count=1, B=0
  bucket #0:
  ┌────────────────────────────────────────────────────────┐
  │ tophash: [0xA3][ 0 ][ 0 ][ 0 ][ 0 ][ 0 ][ 0 ][ 0 ]  │
  │ keys:    ["abc-123"][ - ][ - ][ - ][ - ][ - ][ - ][ - ]│
  │ values:  [ptr→Session{42}][ - ][ - ][ - ][ - ][ - ][ - ][ - ]│
  │ overflow: nil                                           │
  └────────────────────────────────────────────────────────┘
```

**Why `sessions` behaves like a reference when you pass it to a function:**

```go
func RegisterSession(store map[string]*Session, id string, s *Session) {
    store[id] = s
}
```

```
main's sessions variable:   [ptr = 0xC0001] ──┐
                                               ├──▶ SAME hmap on heap
RegisterSession's store:    [ptr = 0xC0001] ──┘

Both are 8-byte pointer copies. Both point to the same hmap.
Modification through either pointer updates the same bucket array.
That's why changes inside RegisterSession are visible to the caller.
```

**Why each map gets its own random seed (hash0):**

```go
m1 := map[string]int{"a": 1, "b": 2}  // hash0 = 0x7A3E
m2 := map[string]int{"a": 1, "b": 2}  // hash0 = 0xB1D4

m1 hashing "a": hash("a", 0x7A3E) = 0x...F2 → bucket #2, tophash 0xC1
m2 hashing "a": hash("a", 0xB1D4) = 0x...A1 → bucket #1, tophash 0x8F

Same key, different bucket, different tophash.
→ Iteration walks buckets sequentially from a random start
→ m1 and m2 yield "a" and "b" in different orders
→ Even re-ranging the SAME map can differ (random start bucket each time)

WHY: If an attacker could predict bucket placement, they could craft
thousands of keys that all land in bucket #0 → O(n) lookup per request
→ denial of service. Random seed per map makes this unpredictable.
```

> **In plain English:** The map variable is like a business card with the address of a filing cabinet. Passing it to a function copies the card, not the cabinet. Everyone holding a copy of the card goes to the same cabinet.

### 4.2 The Bucket (bmap) Struct

Each bucket stores 8 entries. bmap is the physical drawer — the thing you actually scan when looking up a session or an order.

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
│ tophash: [h0][h1][h2][h3][h4][h5][h6][h7] │  ← 8 bytes, fits one cache line
├──────────────────────────────────┤
│ keys:    [k0][k1][k2][k3][k4][k5][k6][k7] │  ← all keys together
├──────────────────────────────────┤
│ values:  [v0][v1][v2][v3][v4][v5][v6][v7] │  ← all values together
├──────────────────────────────────┤
│ overflow: *bmap (or nil)                    │  ← chain to next bucket
└──────────────────────────────────┘

WHY keys and values are separated (not key0,val0,key1,val1,...):
  If key is int64 (8B) and value is bool (1B):
    Interleaved: [8B key][1B val][7B pad][8B key][1B val]... ← wasted padding
    Separated:   [8B][8B][8B]...[1B][1B][1B]...              ← no padding waste
```

**Trace an INSERT into bucket #0.** Continuing from 4.1, a second user logs in:

```go
sessions["xyz-789"] = &Session{UserID: 99}
```

```
Step 1: hash("xyz-789", seed=0x7A3E) → 0x5B12_..._0000
Step 2: bucket_index = 0x0000 & 0 = 0 → bucket #0 (same bucket as "abc-123")
Step 3: tophash = 0x5B
Step 4: Scan tophash: [0xA3][0][0][0][0][0][0][0]
         Slot 0 is taken (0xA3). Slot 1 is empty (0). → use slot 1.

Step 5: Write:
  tophash[1] = 0x5B
  keys[1]    = "xyz-789"
  values[1]  = ptr → Session{99}

bucket #0 after two inserts:
┌────────────────────────────────────────────────────────┐
│ tophash: [0xA3][0x5B][ 0 ][ 0 ][ 0 ][ 0 ][ 0 ][ 0 ]  │
│ keys:    ["abc-123"]["xyz-789"][ - ][ - ][ - ][ - ][ - ][ - ]│
│ values:  [ptr→{42}][ptr→{99}][ - ][ - ][ - ][ - ][ - ][ - ]│
│ overflow: nil                                           │
└────────────────────────────────────────────────────────┘
```

**Trace a LOOKUP.** A request comes in with session ID "abc-123":

```go
sess, ok := sessions["abc-123"]
```

```
Step 1: hash("abc-123", seed=0x7A3E) → 0xA3F7_..._0042
Step 2: bucket #0 (same hash as before → same bucket)
Step 3: tophash to find = 0xA3

Step 4: Scan tophash array:
  slot 0: tophash[0] = 0xA3 → MATCH! (fast — just 1 byte comparison)
  
Step 5: Compare full key:
  keys[0] = "abc-123" == "abc-123" → MATCH!
  
Step 6: Return values[0] = ptr → Session{UserID: 42}
  sess = &Session{UserID: 42}, ok = true

If tophash didn't match (say we looked up "def-456" with tophash 0x77):
  Scan: [0xA3] no → [0x5B] no → [0] empty → STOP. Key not found.
  No full string comparisons needed. The tophash filter saved us.
```

> **In plain English:** Instead of alternating shirts and socks in a drawer (wasting space with padding), you put all shirts on one side and all socks on the other. And each slot has a color-coded label — you glance at labels first before reading the full nametag.

### 4.3 Hash Function and Bucket Selection

This is the pipeline every map operation runs through. Let's trace two different keys landing in different buckets.

```go
hits := make(map[string]int, 8) // B=1, 2 buckets to start (runtime picks based on hint)

hits["/api/users"]++   // key 1
hits["/api/orders"]++  // key 2
```

```
Map state: B=1, so 2 buckets. Mask = 2^1 - 1 = 0b1 (last 1 bit selects bucket).

Key "/api/users":
  hash("/api/users", seed) → 0xC1F3_..._00A2
  bucket = 0x00A2 & 0b1 = 0  → bucket #0
  tophash = 0xC1
  Find empty slot in bucket #0, write tophash=0xC1, key="/api/users", value=1

Key "/api/orders":
  hash("/api/orders", seed) → 0x8F27_..._00B3
  bucket = 0x00B3 & 0b1 = 1  → bucket #1   ← different bucket!
  tophash = 0x8F
  Find empty slot in bucket #1, write tophash=0x8F, key="/api/orders", value=1

After both inserts:

  bucket #0:                              bucket #1:
  ┌─────────────────────────────┐         ┌─────────────────────────────┐
  │ tophash: [0xC1][0]...[0]   │         │ tophash: [0x8F][0]...[0]   │
  │ keys:    ["/api/users"][…]  │         │ keys:    ["/api/orders"][…] │
  │ values:  [1][…]             │         │ values:  [1][…]             │
  └─────────────────────────────┘         └─────────────────────────────┘

Now hits["/api/users"]++:
  1. Hash → same hash → bucket #0
  2. Scan tophash → slot 0 matches 0xC1
  3. Compare key → "/api/users" == "/api/users" ✓
  4. Read value (1), increment, write back (2)
```

> **In plain English:** Think of the low bits as a floor number and the tophash as a room label. You go to floor 0, scan room labels for 0xC1, and when you find it, check the full guest name to be sure.

### 4.4 Map Growth and Evacuation

When the **load factor** (count / 2^B, roughly entries per bucket) exceeds **6.5**, or there are too many overflow buckets, the map grows. Let's watch it happen with a session store.

```go
sessions := make(map[string]*Session) // B=0, 1 bucket, 8 slots
```

```
Filling up the single bucket:

Insert session 1: bucket #0, slot 0. count=1
Insert session 2: bucket #0, slot 1. count=2
...
Insert session 7: bucket #0, slot 6. count=7

Load factor = count / 2^B = 7 / 1 = 7.0  ← EXCEEDS 6.5!

Insert session 8 triggers GROWTH:

  BEFORE (B=0, 1 bucket):
  hmap: count=7, B=0
  ┌──────────────────────┐
  │ buckets ──→ [bucket0] │  ← 7 entries crammed in, load=7.0
  │ oldbuckets: nil       │
  └──────────────────────┘

  Step 1: Allocate new bucket array with B=1 → 2 buckets
  Step 2: hmap.oldbuckets = hmap.buckets (save old array)
  Step 3: hmap.buckets = new 2-bucket array
  Step 4: hmap.B = 1
  Step 5: hmap.nevacuate = 0 (nothing evacuated yet)

  DURING GROWTH (B=1, old + new arrays both exist):
  hmap: count=7, B=1
  ┌────────────────────────────────────────────┐
  │ oldbuckets ──→ [old-bucket0 (7 entries)]   │
  │ buckets    ──→ [new-bucket0][new-bucket1]   │
  │ nevacuate: 0                                │
  └────────────────────────────────────────────┘

  Step 6: Insert session 8.
    Runtime first evacuates old-bucket0:
    - Rehash each of the 7 keys with the NEW mask (0b1 instead of 0b0)
    - Keys whose low bit = 0 → new-bucket0
    - Keys whose low bit = 1 → new-bucket1
    Then insert session 8 into the appropriate new bucket.

  Step 7: hmap.nevacuate = 1. Old bucket0 is done.
    Since that was the only old bucket, oldbuckets = nil. Growth complete.

  AFTER GROWTH:
  hmap: count=8, B=1
  ┌────────────────────────────────────────────┐
  │ oldbuckets: nil (freed, eligible for GC)    │
  │ buckets ──→ [new-bucket0][new-bucket1]      │
  │              ~4 entries     ~4 entries       │
  │ Load factor: 8/2 = 4.0 ← healthy again     │
  └────────────────────────────────────────────┘
```

Growth is **incremental** — if there were many old buckets, Go only evacuates 1-2 per map operation, spreading the work. You might see extra CPU in profiles during a traffic spike that fills a big map. That's the runtime migrating entries from `oldbuckets` into the wider table — normal, not a leak.

> **In plain English:** When the filing cabinet is overflowing, you buy a bigger one. But you don't move everything at once — every time someone opens a drawer, you move one old drawer's contents to the new cabinet. Eventually, the old cabinet is empty and gets thrown away.

### 4.5 Iteration Internals

Go **deliberately randomizes** map iteration order. Understanding the mechanism matters because it explains Rule 4 (why adding keys during iteration is undefined).

```go
endpoints := map[string]int{
    "/api/users":  120,
    "/api/orders": 87,
    "/health":     4000,
}
for k, v := range endpoints {
    fmt.Println(k, v)
}
// Run 1: /health, /api/users, /api/orders
// Run 2: /api/orders, /health, /api/users
```

**How the iterator works internally:**

```
When you write `for k, v := range endpoints`:

Step 0: Follow the pointer chain to find the buckets
  endpoints on the stack is a pointer → hmap on the heap
  Read hmap.B → B=2, so 2^2 = 4 buckets
  Read hmap.buckets → pointer to bucket array at 0xC000090000
    0xC000090000: [bucket0][bucket1][bucket2][bucket3]
  Read hmap.hash0 → 0xAB12 (the per-map random seed)

Step 1: Pick random starting position using hash0
  Runtime calls fastrand() (seeded from hash0):
    startBucket = fastrand() & (2^B - 1) = fastrand() & 3 → e.g. 2
    offset      = fastrand() & 7                           → e.g. 5
  Now the iterator knows: start at bucket #2, slot 5

Step 2: Walk forward sequentially from that position
  bucket #2 slots 5,6,7 → bucket #3 slots 0-7 →
  bucket #0 slots 0-7 → bucket #1 slots 0-7 →
  bucket #2 slots 0,1,2,3,4 → DONE (wrapped back to start)

  At each slot: check tophash[slot]
    - 0 (empty) → skip
    - evacuated marker → skip (growth in progress)
    - valid → read key from keys[slot], value from values[slot] → yield to loop body

The iterator tracks:
  - startBucket: where we began (so we know when to stop)
  - offset:      starting slot within each bucket
  - currentBucket + currentSlot: where we are right now

It walks ALL buckets exactly once, wrapping around.
```

This prevents code from accidentally depending on insertion order. If you need sorted output (for metrics labels, API responses), collect the keys into a slice and sort them.

> **In plain English:** Imagine you're in a library and you start scanning shelves, but each time you visit, you start at a random shelf and walk around until you're back where you started. You always see every book, but never in the same order twice.

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

### Rule 4: Delete During Iteration Is Safe; Adding Is Not

**Deleting** keys during `for range` is safe. Go guarantees the deleted key won't reappear.

```go
pending := map[string]struct{}{
    "idemp-aaa": {},
    "idemp-bbb": {},
    "idemp-ccc": {},
}
for k := range pending {
    if k == "idemp-bbb" {
        delete(pending, k) // safe — won't see "idemp-bbb" again
    }
}
```

```
WHY delete is safe:
  delete() marks the slot's tophash as "evacuated empty" (special value).
  The iterator checks tophash before yielding a key.
  Marked slot → skip it. Simple.
```

**Adding** keys during iteration is undefined — the new key **may or may not** appear. Here's **why**:

```go
m := map[string]int{"a": 1, "b": 2, "c": 3}  // B=1, 2 buckets
for k, v := range m {
    if k == "a" {
        m["z"] = 99  // will "z" appear in this loop?
    }
    fmt.Println(k, v)
}
```

```
Recall from §4.5: the iterator picks a random starting bucket and walks
forward until it circles back. It tracks "I'm at bucket X, slot Y."

Scenario A: "z" APPEARS
  Iterator started at bucket #0, walking → bucket #1.
  "z" hashes to bucket #1 (not visited yet).

  Walk order:  [#0 (current)] → [#1]
                                  ↑ "z" lands here → WILL be visited → "z" APPEARS

Scenario B: "z" does NOT appear
  Iterator started at bucket #1, walking → bucket #0.
  "z" hashes to bucket #1 (already visited).

  Walk order:  [#1 (already done)] → [#0 (current)]
                ↑ "z" lands here → already passed → "z" SKIPPED

Scenario C: "z" triggers GROWTH
  Adding "z" pushes count past load factor 6.5 → map doubles buckets.
  ALL entries rehash to new positions (old bucket → could split into
  two new buckets). The iterator has logic to handle growth
  (checks oldbuckets), but "z"'s position in the new layout is
  unpredictable relative to where the iterator is.
```

The outcome depends on three runtime factors:
1. Which bucket the iterator randomly started at
2. Which bucket the new key hashes to (depends on the random seed)
3. Whether the insert triggers growth (rehashes everything)

Since all three are unpredictable, the language spec says: **don't rely on it.**

```go
// SAFE pattern: collect keys to add, then add after the loop
var toAdd []string
for k := range m {
    if shouldExpand(k) {
        toAdd = append(toAdd, k+"-expanded")
    }
}
for _, k := range toAdd {
    m[k] = computeValue(k)
}
```

> **In plain English:** You're scanning a library shelf by shelf, starting at a random shelf and going forward. If someone adds a book to a shelf you already passed, you won't see it. If they add it ahead of you, you will. Since you started at a random shelf and the book could land anywhere, you genuinely can't predict the answer.

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

### Example 1: Basic Map Operations Traced Through Memory

This is the foundation. If you understand what happens in memory for these four operations, everything else (concurrency, struct values, size hints) builds on top.

```go
// Create
hits := make(map[string]int)

// Insert
hits["/api/users"] = 120

// Update (read + increment + write back internally)
hits["/api/users"]++

// Lookup with comma-ok
count, exists := hits["/metrics"]
```

```
Step 1: hits := make(map[string]int)
  stack: [ hits = ptr → hmap at 0xC000010000 ]
  heap:  hmap{ count:0, B:0, hash0:0xAB12, buckets→ 0xC000020000 }
         0xC000020000: [bucket0 — all 8 slots empty]

  B=0 means 2^0 = 1 bucket. Every key lands in bucket #0.

Step 2: hits["/api/users"] = 120
  Follow pointer chain: hits → hmap → read B=0, hash0=0xAB12
  hash("/api/users", 0xAB12) → 0xC1A2...F7
  Bucket selection: 0xC1A2...F7 & (2^0 - 1) = 0xC1A2...F7 & 0x0 = 0 → bucket #0
  Tophash extraction: top byte of 0xC1A2...F7 = 0xC1

  bucket #0 at 0xC000020000: find first empty slot → slot 0
    tophash[0] = 0xC1
    keys[0]    = "/api/users"
    values[0]  = 120
  hmap.count = 1

  bucket #0: [0xC1][0][0][0][0][0][0][0]
             ["/api/users"][-][-][-][-][-][-][-]
             [120][-][-][-][-][-][-][-]

Step 3: hits["/api/users"]++
  hash("/api/users", 0xAB12) → 0xC1A2...F7 (same key, same hash)
  Bucket: 0xC1A2...F7 & 0x0 = 0 → bucket #0
  Scan tophash array: tophash[0] = 0xC1 matches top byte → compare full key → match
  Read values[0] (120) → write values[0] = 121. No new slot used.

  bucket #0: [0xC1][0][0][0][0][0][0][0]
             ["/api/users"][-][-][-][-][-][-][-]
             [121][-][-][-][-][-][-][-]
                ↑ changed from 120 to 121

Step 4: count, exists := hits["/metrics"]
  hash("/metrics", 0xAB12) → 0x77B3...4E
  Bucket: 0x77B3...4E & 0x0 = 0 → bucket #0
  Tophash to find: 0x77
  Scan tophash array: [0xC1] ≠ 0x77, [0] = empty → STOP
  Key not found. Return zero value (0) and exists = false.
  count = 0, exists = false
```

### Example 2: Struct Values — the Copy-Edit-Write Pattern

You can't modify a struct field through a map lookup. Here's why and how to work around it.

```go
type OrderSummary struct {
    LineItems  int
    TotalCents int64
}

cache := map[string]OrderSummary{
    "ord-1001": {LineItems: 3, TotalCents: 4999},
}

// cache["ord-1001"].LineItems++  // COMPILE ERROR
```

```
WHY the compile error — traced through memory (connects to §4.4):

  BEFORE growth (B=0, 1 bucket at 0xC000080000):
    hmap.buckets → 0xC000080000
    bucket0, slot 0:
      tophash[0] = 0xA3
      keys[0]    = "ord-1001"
      values[0]  = {LineItems: 3, TotalCents: 4999}  ← lives at 0xC000080048

  Suppose Go allowed: ptr := &cache["ord-1001"]
    ptr = 0xC000080048 (address of values[0] inside bucket0)

  Now insert 7 more orders → all 8 slots full → load factor exceeded:

  GROWTH triggers (B=0 → B=1, 1 bucket → 2 buckets):
    New bucket array allocated at 0xC000090000: [bucket0 | bucket1]
    Runtime evacuates entries from old bucket to new buckets:
      hash("ord-1001") & (2^1 - 1) = hash & 1 → e.g. 1 → new bucket1, slot 2
      "ord-1001" now lives at 0xC000090158 (new address)
    hmap.buckets → 0xC000090000
    Old array at 0xC000080000 freed after evacuation completes

  ptr is still 0xC000080048 → old bucket → DANGLING POINTER
  Reading *ptr gives garbage. Writing *ptr corrupts freed memory.

  Go prevents this at compile time: map values are not something you can
  take the address of with &. You can't get a pointer into a bucket slot,
  so you can't end up with a dangling pointer after growth.
```

The fix — copy, edit, write back:

```go
sum := cache["ord-1001"]    // copy out
sum.LineItems++             // edit the copy
cache["ord-1001"] = sum     // write back
```

```
Step 1: sum := cache["ord-1001"]
  sum is a COPY on the stack: OrderSummary{LineItems: 3, TotalCents: 4999}
  The map still has its own copy in the bucket.

Step 2: sum.LineItems++
  stack: sum = OrderSummary{LineItems: 4, TotalCents: 4999}
  bucket: still OrderSummary{LineItems: 3, ...}  ← UNCHANGED

Step 3: cache["ord-1001"] = sum
  Overwrites the value in the bucket slot.
  bucket: OrderSummary{LineItems: 4, TotalCents: 4999}  ← now updated

Alternative: use map[string]*OrderSummary (pointers as values)
  cache["ord-1001"].LineItems++  // OK — pointer stays valid even if map grows
  The pointer doesn't move when the map grows. Only the pointer itself
  (8 bytes) is stored in the bucket. The struct lives separately on the heap.
```

### Example 3: Size Hint for Performance

```go
// Without hint: map grows multiple times as entries are added
orders := make(map[string]*Order)

// With hint: pre-allocates enough buckets for ~10k entries
orders = make(map[string]*Order, 10_000)
```

```
Without hint:
  B=0 → 1 bucket → grow at ~7 entries → B=1 → grow at ~13 → B=2 → ...
  Each growth: allocate new array, evacuate old entries incrementally.
  For 10k entries: ~14 growth events, each with CPU cost.

With hint (10,000):
  B=11 → 2048 buckets → room for ~13k entries before first growth
  Zero growths during initial filling → faster bulk load.

When it matters:
  - Hydrating a cache from a DB snapshot at startup
  - Building an index after a batch import
  - Any time you know the approximate count upfront
```

### Example 4: Safe Concurrent Map Access

This is the pattern you'll use for any shared map (session store, feature flags, metrics). It builds on everything above — you need to understand why maps aren't safe (§4 — bucket array is being modified) before the lock pattern makes sense.

```go
type SessionStore struct {
    mu   sync.RWMutex
    data map[string]*Session
}

func NewSessionStore() *SessionStore {
    return &SessionStore{data: make(map[string]*Session)}
}

func (s *SessionStore) Get(id string) (*Session, bool) {
    s.mu.RLock()
    defer s.mu.RUnlock()
    sess, ok := s.data[id]
    return sess, ok
}

func (s *SessionStore) Put(id string, sess *Session) {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.data[id] = sess
}
```

```
Multiple readers (many GET /session requests):
  goroutine 1: RLock ✓ → read bucket → RUnlock
  goroutine 2: RLock ✓ → read bucket → RUnlock  (concurrent reads OK)
  goroutine 3: RLock ✓ → read bucket → RUnlock

Single writer (POST /login creates session):
  goroutine 4: Lock ✓
    → all readers blocked until Unlock
    → all other writers blocked until Unlock
    → write to bucket safely
    → Unlock → readers resume

WHY RWMutex and not plain Mutex:
  Feature flags, session lookups, config reads happen on EVERY request.
  Writes happen rarely (login, config reload). RWMutex lets the common
  case (reads) stay fast and concurrent. Plain Mutex would serialize
  all reads too — unnecessary bottleneck.
```

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

| Gotcha | What Happens | Because (§4 link) | Fix |
|--------|-------------|-------------------|-----|
| Concurrent read + write | `fatal error: concurrent map read and map write` | hmap.flags detects overlap; bucket array is being modified mid-read (§4.1) | sync.RWMutex or sync.Map |
| Concurrent writes | `fatal error: concurrent map writes` | Two goroutines writing to the same bucket can corrupt tophash/keys/values (§4.2) | sync.Mutex |
| Write to nil map | `panic: assignment to entry in nil map` | nil map means the hmap pointer is nil — no bucket array exists to write into (§4.1) | Initialize with `make()` |
| Struct field assignment | `cannot assign to struct field in map` | Values live in bucket slots that move during growth — can't take a stable address (§4.4) | Copy-edit-write or pointer values |
| Relying on iteration order | Order changes between runs | Iterator picks random start bucket + offset each time; hash0 differs per map (§4.5) | Sort keys if order matters |
| Large map never shrinks | Memory stays after mass deletion | Growth allocates a bigger bucket array (§4.4). Delete marks slots empty but the array stays. No reverse operation exists. | Re-create the map |
| Map of pointers hides nil | `m[key].Field` panics if value is nil pointer | Comma-ok returns zero value (nil for pointers); dereferencing nil panics | Check with comma-ok first |

**The "map never shrinks" gotcha — traced through memory:**

```go
m := make(map[string]*Session)
for i := 0; i < 1_000_000; i++ {
    m[fmt.Sprintf("sess-%d", i)] = &Session{}
}

for i := 0; i < 1_000_000; i++ {
    delete(m, fmt.Sprintf("sess-%d", i))
}

// Fix:
m = make(map[string]*Session)
```

```
Step 1: m := make(map[string]*Session)
  stack: [ m = ptr → hmap at 0xC000010000 ]
  heap:  hmap{ count:0, B:0, hash0:0x3F91, buckets → 0xC000020000 }
         0xC000020000: [bucket0 — all 8 slots empty]

Step 2: Insert loop — first 8 keys ("sess-0" through "sess-7")
  Each insert: hash(key, 0x3F91) → bucket = hash & (2^0 - 1) = 0 → bucket #0
  After 8 inserts: bucket0 is full (8/8 slots used)
  hmap{ count:8, B:0 }
  Load factor = 8 / (2^0 × 8) = 1.0 → exceeds 6.5/8 threshold → GROWTH

Step 3: Growth triggers repeatedly as more keys arrive
  B=0 → B=1:  1 bucket  → 2 buckets    (new array at 0xC000030000)
  B=1 → B=2:  2 buckets → 4 buckets    (new array at 0xC000040000)
  ...
  B=16 → B=17: 65,536 → 131,072 buckets (new array at 0xC000100000)

  Each growth: allocate new bucket array, evacuate entries, old array freed.

Step 4: After all 1,000,000 inserts
  hmap{ count:1_000_000, B:17, buckets → 0xC000100000 }
  2^17 = 131,072 buckets × ~128 bytes each ≈ 4MB of bucket memory
  Plus 1,000,000 *Session pointers (8 bytes each) stored in value slots
  Plus 1,000,000 string keys stored in key slots

Step 5: Delete loop — delete(m, "sess-0") through delete(m, "sess-999999")
  For each delete(m, key):
    hash(key, 0x3F91) → bucket = hash & (2^17 - 1) → find the bucket
    Scan tophash → find the slot → mark tophash[slot] = "emptyRest" or "emptyOne"
    Zero out key slot (string header) and value slot (*Session pointer → nil)
    hmap.count--

  The *Session pointer in the value slot is set to nil, so the Session
  on the heap becomes unreferenced → GC can collect it. But the BUCKET
  SLOT ITSELF stays allocated.

  After all deletes:
    hmap{ count:0, B:17, buckets → 0xC000100000 }
                   ↑ B is STILL 17
                         ↑ STILL pointing to 131,072 buckets ≈ 4MB
    Every tophash = "empty", every key/value slot zeroed — but the
    4MB bucket array is not freed and not shrunk.

  WHY no shrink: Growth is one-directional. Reverse evacuation would
  need to re-hash and relocate all entries into a smaller array — the
  runtime doesn't implement this. The design trades memory for simplicity.

Step 6: Fix — m = make(map[string]*Session)
  New hmap at 0xC000200000: { count:0, B:0, buckets → tiny 1-bucket array }
  m on stack now points to 0xC000200000 (new hmap)
  Old hmap at 0xC000010000 → no references → GC eligible
  Old bucket array at 0xC000100000 (4MB) → no references → GC eligible
  Memory reclaimed on next GC cycle.
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
