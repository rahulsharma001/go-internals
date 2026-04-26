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

Under the hood, a map is backed by an `hmap` struct that manages an array of **buckets**. Each bucket holds up to 8 key-value pairs. When a bucket is full, it chains to **overflow buckets**.

> **In plain English:** A map is like a library card catalog. You look up the book title (key), the card tells you the shelf number (hash), you go to that shelf (bucket), and find the book (value). Each shelf has room for 8 books. If the shelf is full, there's an overflow rack next to it.

---

## 2. Core Insight (TL;DR)

**Go maps are NOT safe for concurrent access.** Reading and writing from multiple goroutines without a lock will crash your program. This is the single most asked map question in interviews.

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
map["alice"] → hash = 0xA3F7...42

Low bits (42 in binary) → bucket #2
Top 8 bits (0xA3) → tophash filter

Bucket #2:
┌──────────────────────────────────────────────────┐
│ tophash: [0xA3][0x5B][0x12][ 0 ][ 0 ][ 0 ][ 0 ][ 0 ] │
│ keys:    [alice][bob][carol][ - ][ - ][ - ][ - ][ - ] │
│ values:  [ 100 ][ 200][ 300][ - ][ - ][ - ][ - ][ - ] │
│ overflow: nil                                          │
└──────────────────────────────────────────────────┘

Lookup "alice":
  1. Hash → bucket #2
  2. Scan tophash for 0xA3 → match at slot 0
  3. Compare full key "alice" == "alice" → match
  4. Return value at slot 0 → 100
```

> **In plain English:** Imagine a library with numbered shelves. Each shelf has 8 book slots. To find a book, you hash its title to get a shelf number, then scan labels on that shelf. If the shelf is full, check the overflow cart next to it.

### The Mistake That Teaches You

```go
func main() {
    m := make(map[string]int)

    // Two goroutines writing to the same map — CRASH
    go func() {
        for i := 0; i < 1000; i++ {
            m["a"] = i
        }
    }()
    go func() {
        for i := 0; i < 1000; i++ {
            m["b"] = i
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

**Fix: Use sync.RWMutex or sync.Map.**

---

## 4. How It Actually Works (Internals) [INTERMEDIATE → ADVANCED]

### 4.1 The hmap Struct

Every `map[K]V` is a pointer to an `hmap` struct:

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

Key detail: `map` variables are already pointers. When you pass a map to a function, you're passing a copy of the pointer — both point to the same `hmap`. That's why modifications inside a function are visible to the caller.

> **In plain English:** The map variable is like a business card with the address of the filing cabinet. Everyone who has the business card goes to the same cabinet.

### 4.2 The Bucket (bmap) Struct

Each bucket stores 8 entries, organized for cache efficiency:

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

The **hash0** field is a random seed unique to each map instance. This means identical keys hash to different buckets in different maps, preventing hash-flooding DoS attacks.

### 4.4 Map Growth and Evacuation

When the **load factor** (count / bucket_count) exceeds **6.5**, or there are too many overflow buckets, the map grows.

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

Growth is **incremental** — Go does NOT stop the world to rehash everything. Each map operation (read, write, delete) evacuates 1-2 old buckets. This keeps individual operations fast at the cost of slightly elevated latency during growth.

> **In plain English:** When the filing cabinet is overflowing, you buy a bigger one. But you don't move everything at once — every time someone opens a drawer, you move one old drawer's contents to the new cabinet. Eventually, the old cabinet is empty and gets thrown away.

### 4.5 Iteration Randomness

Go **deliberately randomizes** map iteration order. Each `for range` loop picks a random starting bucket and a random offset within that bucket.

```go
m := map[string]int{"a": 1, "b": 2, "c": 3}

// Run 1: b, c, a
// Run 2: a, b, c
// Run 3: c, a, b
// NEVER rely on map order
```

This prevents code from accidentally depending on a specific order that could change between Go versions or platform architectures. It's a feature, not a bug.

---

## 5. Key Rules & Behaviors

### Rule 1: Maps Are NOT Safe for Concurrent Access

This is the most important rule and the most common interview question.

```go
// CRASH: concurrent map writes
m := make(map[string]int)
var wg sync.WaitGroup
for i := 0; i < 10; i++ {
    wg.Add(1)
    go func(n int) {
        defer wg.Done()
        m[fmt.Sprint(n)] = n  // RACE
    }(i)
}
wg.Wait()
```

```
Goroutine 1: m["3"] = 3
  → writing to bucket #1, mid-operation...
Goroutine 2: m["7"] = 7
  → also writing to bucket #1
  → CORRUPTED: Go detects flag already set → fatal error

Fix: sync.RWMutex for read-heavy, sync.Map for write-once caches
```

> **In plain English:** Two people reaching into the same filing drawer at the same time will jam their hands together and rip the papers. Go panics instead of silently shredding your data.

### Rule 2: Map Values Are NOT Addressable

You cannot take the address of a map value.

```go
m := map[string]User{"a": {Name: "rahul"}}
m["a"].Name = "admin"  // COMPILE ERROR: cannot assign to struct field in map

// Fix: copy, modify, write back
u := m["a"]
u.Name = "admin"
m["a"] = u
```

```
WHY: Maps rehash during growth, moving entries to new buckets.
A pointer to m["a"] could become dangling after growth.
Go prevents this at compile time.

Alternative: use map[string]*User (pointers as values)
m := map[string]*User{"a": {Name: "rahul"}}
m["a"].Name = "admin"  // OK — pointer doesn't move when map grows
```

> **In plain English:** You can't glue a bookmark to a page in a book that might be reprinted tomorrow. The page might end up at a different location. Either make a copy, edit it, and put it back — or store a bookmark (pointer) instead.

### Rule 3: nil Map Reads Are Safe, Writes Panic

```go
var m map[string]int  // nil map

v := m["key"]        // OK: returns zero value (0)
v, ok := m["key"]    // OK: returns 0, false

m["key"] = 1         // PANIC: assignment to entry in nil map
```

```
nil map:  [ hmap pointer = nil ]
  Read → Go checks nil, returns zero value safely
  Write → Go tries to follow nil pointer → PANIC

Fix: m = make(map[string]int)  // or m = map[string]int{}
```

> **In plain English:** Looking at an empty shelf is fine — you see nothing. Trying to put a book on a shelf that doesn't exist crashes. Build the shelf first with `make()`.

### Rule 4: Delete During Iteration Is Safe

Go guarantees that deleting keys during `for range` is safe. The deleted key won't appear in subsequent iterations.

```go
m := map[string]int{"a": 1, "b": 2, "c": 3}
for k := range m {
    if k == "b" {
        delete(m, k)  // safe
    }
}
// m: {"a": 1, "c": 3}
```

But **adding** keys during iteration has undefined behavior — the new key may or may not appear.

> **In plain English:** You can throw books off the shelf while scanning it — you just won't see those books again. But if someone adds books while you're scanning, you might miss them or see them twice.

### Rule 5: The Comma-Ok Idiom Distinguishes Missing from Zero

```go
m := map[string]int{"a": 0}

v := m["a"]     // v = 0
v2 := m["b"]    // v2 = 0 ← same! Can't tell if "b" exists

v, ok := m["a"]   // v = 0, ok = true  → key exists
v2, ok2 := m["b"] // v2 = 0, ok2 = false → key missing
```

> **In plain English:** Asking "what's on shelf B?" and getting "nothing" doesn't tell you if shelf B is empty or doesn't exist. The comma-ok pattern is asking "does shelf B exist?"

---

## 6. Code Examples (Show, Don't Tell)

### Example 1: Safe Concurrent Map Access

```go
type SafeMap struct {
    mu sync.RWMutex
    m  map[string]int
}

func (sm *SafeMap) Get(key string) (int, bool) {
    sm.mu.RLock()
    defer sm.mu.RUnlock()
    v, ok := sm.m[key]
    return v, ok
}

func (sm *SafeMap) Set(key string, val int) {
    sm.mu.Lock()
    defer sm.mu.Unlock()
    sm.m[key] = val
}
```

```
Multiple readers:        Single writer:
  RLock ✓                 Lock ✓
  RLock ✓                 (all readers blocked)
  RLock ✓                 (all other writers blocked)
  (concurrent reads OK)   Unlock → readers resume
```

### Example 2: Map with Struct Values (the copy-edit-write pattern)

```go
type Score struct {
    Points int
}

m := map[string]Score{
    "alice": {Points: 10},
}

// Can't do: m["alice"].Points++ // COMPILE ERROR
// Must do:
s := m["alice"]
s.Points++
m["alice"] = s  // write back
```

```
Step 1: s := m["alice"]
  s is a COPY of Score{Points: 10}

Step 2: s.Points++
  s is now Score{Points: 11}
  map still has Score{Points: 10}

Step 3: m["alice"] = s
  map now has Score{Points: 11}
```

### Example 3: Map Size Hint for Performance

```go
// Without hint: map grows multiple times as entries are added
m1 := make(map[string]int)

// With hint: pre-allocates enough buckets for ~1000 entries
m2 := make(map[string]int, 1000)
```

```
m1 := make(map[string]int):
  B=0 → 1 bucket → grow at 7 entries → grow at 14 → grow at 28 → ...
  Each growth: allocate, evacuate, repeat

m2 := make(map[string]int, 1000):
  B=8 → 256 buckets → room for ~1664 entries before first growth
  Zero growths during initial filling → faster
```

Pre-sizing matters when you know the approximate count (e.g., processing a known-length list).

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

```go
m := map[string]int{"a": 1, "b": 2, "c": 3}
delete(m, "b")
fmt.Println(len(m))

var m2 map[string]int
fmt.Println(m2["x"])
fmt.Println(len(m2))
```

What prints? Think about it before checking.

<details>
<summary>Answer</summary>

```
2
0
0
```
`delete` removes "b", len is 2. Reading from nil map returns zero value. `len` of nil map is 0.

</details>

### Tier 2: Fix the Bug (5 min)

```go
func countWords(words []string) map[string]int {
    var counts map[string]int
    for _, w := range words {
        counts[w]++
    }
    return counts
}
```

This panics. Fix it.

### Tier 3: Build It (15 min)

Build a thread-safe LRU cache using a map and a doubly-linked list. Support `Get(key)`, `Put(key, value)`, and a max capacity. When capacity is exceeded, evict the least recently used entry. Use `sync.RWMutex` for thread safety.

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
m := make(map[int]struct{})
for i := 0; i < 1_000_000; i++ {
    m[i] = struct{}{}
}
for i := 0; i < 1_000_000; i++ {
    delete(m, i)
}
// m is now empty BUT still holds memory for ~1M bucket slots
// Fix: m = make(map[int]struct{}) to reclaim memory
```

> **In plain English:** When you empty all the drawers in a filing cabinet, the cabinet doesn't magically shrink. You need to buy a smaller cabinet (re-create the map) to free the space.

---

## 8. Performance & Tradeoffs

| Operation | Average | Worst (many collisions) | Notes |
|-----------|---------|------------------------|-------|
| Lookup | O(1) | O(n) | Worst case: all keys in one bucket chain |
| Insert | O(1) amortized | O(n) during growth | Growth doubles buckets, evacuates incrementally |
| Delete | O(1) | O(n) | Marks slot empty, doesn't shrink |
| Iteration | O(n) | O(n) | Random order, touches all buckets |

| Approach | When to Use |
|----------|------------|
| `make(map[K]V)` | Default — let Go manage growth |
| `make(map[K]V, hint)` | You know approximate size — avoids early growths |
| `sync.RWMutex` + map | Concurrent access, read-heavy workloads |
| `sync.Map` | Write-once caches, disjoint goroutine key sets |
| Slice instead of map | Small data sets (<~50 items) — linear scan can be faster due to cache locality |

---

## 9. Common Misconceptions

| Misconception | Reality |
|--------------|---------|
| "Maps are passed by reference" | Maps are pointers under the hood. You pass a copy of the pointer. Both copies point to the same hmap. |
| "sync.Map is always better for concurrency" | sync.Map is optimized for write-once, read-many patterns. For general read-write, sync.RWMutex + regular map is faster. |
| "Deleting from a map frees memory" | Buckets are never freed. Only re-creating the map reclaims memory. |
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

**Nuanced answer:** Maps have complex internal state — bucket arrays, overflow chains, growth flags. During growth, the map is actively moving entries between old and new bucket arrays. A concurrent write during this process corrupts the internal structure. Go detects the flag bit set by another goroutine and panics immediately rather than silently corrupting data. The fix depends on the pattern: sync.RWMutex for general concurrent access (allows concurrent reads), sync.Map for write-once-read-many caches.

**Verbal summary:** "Maps aren't concurrent-safe because their internal bucket structure can be mid-growth. Go detects the race via flag bits and panics. Use sync.RWMutex for general access, sync.Map for write-once caches."

### Q2: "Explain the internal structure of a Go map."

**Nuanced answer:** A map is a pointer to an hmap struct containing a count, a random hash seed, and a pointer to a bucket array. There are 2^B buckets. Each bucket (bmap) holds 8 key-value pairs organized as separate arrays — tophash, keys, values — for cache efficiency. The tophash array stores the top 8 bits of each key's hash for fast filtering. When a bucket overflows, it chains to overflow buckets. Growth is triggered at load factor 6.5 and happens incrementally — each operation evacuates 1-2 old buckets.

**Verbal summary:** "Go maps are hash tables backed by hmap. 2^B buckets, each holds 8 KV pairs with tophash filters. Keys and values stored separately for alignment. Growth at load factor 6.5, incremental evacuation. Hash seed randomized per instance for DoS protection."

### Q3: "Why can't you take the address of a map value?"

**Nuanced answer:** Map values are not addressable because maps rehash during growth, physically moving entries to new bucket positions. A pointer to a map value would become dangling after growth. Go catches this at compile time. Workaround: use pointer values (`map[K]*V`) so the pointer itself moves but the data it points to doesn't.

**Verbal summary:** "Maps move entries during growth, so a pointer to a value could dangle. Use pointer values (map[K]*V) if you need in-place modification."

---

## 12. Final Verbal Answer

> "A Go map is a hash table backed by an hmap struct. Each bucket holds 8 key-value pairs with a tophash array for fast filtering. Low hash bits select the bucket, top 8 bits match within it. Keys and values are stored in separate arrays for cache-friendly alignment. Growth triggers at load factor 6.5 and happens incrementally — each operation evacuates old buckets to a doubled array. Maps are NOT safe for concurrent access; Go panics on detected races. Use sync.RWMutex for general concurrency, sync.Map for write-once caches. Map values aren't addressable because growth moves entries. Iteration order is deliberately randomized."

---

## 13. Comprehensive Interview Questions

> Full interview question bank (12 questions) → [[questions/T08 Map Internals - Interview Questions]]

Preview:
1. "Why is Go's map not safe for concurrent access?" [COMMON]
2. "What is the load factor and when does a map grow?" [COMMON]
3. "Why is map iteration order random in Go?" [TRICKY]

---

> See [[Glossary]] for term definitions.
