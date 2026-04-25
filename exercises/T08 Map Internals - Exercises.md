# T08 Map Internals — Exercise Solutions
> Complete solutions for Practice Checkpoint exercises from [[T08 Map Internals]].

---
## Tier 2: Fix the Bug — Solution

**Bug:** A nil map is not the same as an empty map. The zero value of `map[string]int` is `nil`. On a nil map, **reads** return the zero value, but **writes** (`m[k] = v` or `m[k]++`) **panic** at runtime. `countWords` must initialize the map with `make(map[string]int)` before incrementing.

### Task

`countWords` is supposed to count how many times each word appears. Find and fix the bug.

### Solution

**Broken (panics on first `counts[w]++`):**
```go
package main

import (
	"fmt"
	"strings"
)

func countWords(s string) map[string]int {
	var counts map[string]int // nil map
	for _, w := range strings.Fields(s) {
		counts[w]++ // runtime panic: assignment to entry in nil map
	}
	return counts
}
```

**Fixed — allocate the map’s backing store before any assignment:**
```go
package main

import (
	"fmt"
	"strings"
)

func countWords(s string) map[string]int {
	// `make` allocates the hash table. Without this, `counts` is nil and writes panic.
	counts := make(map[string]int)
	for _, w := range strings.Fields(s) {
		counts[w]++ // read-modify-write: safe on a made map
	}
	return counts
}

func main() {
	m := countWords("go maps go and maps go go")
	for k, v := range m {
		fmt.Println(k, v)
	}
	// order of range over map is not defined; compare sets of lines if automating
}
```

### Why this works

- **`make(map[string]int)`** creates a non-nil map with an empty ready-to-use hash table.
- **`nil` map** can be read (e.g. `counts["x"]` yields `0`) but cannot be written to; the runtime enforces that.
- This ties directly to how maps are **references** to `hmap` under the hood: `nil` means “no hmap,” so there is nothing to grow or update.

### Output

(Exact key order may vary; content is what matters.)
```
and 1
go 3
maps 2
```

**Stable check** (if you need deterministic output in tests, sort keys first; not required for the fix).

### What to observe

- Run the **broken** version: panic message **`assignment to entry in nil map`**. That is the tell for write-on-nil.
- A **return type** of `map[string]int` does not automatically allocate storage; the caller of `countWords` still gets a valid map only if the function `make`s it (or `append`s to a non-nil result from another path).
- Optional: you can also write `counts := map[string]int{}` for the same “non-nil empty map” effect.

---
## Tier 3: Build It — Solution

### Task

Build a **thread-safe LRU cache** using a `map` for O(1) key lookup and a **doubly linked list** for O(1) recency (move to front) and O(1) eviction at capacity. Expose at least `Get`, `Put`, and enforce `max` entries; on overflow, evict the **least recently used** item. Use `sync.RWMutex` and document how lock kinds map to read vs. write paths.

### Solution

`lru_tier3.go` — single file, runnable:
```go
package main

import (
	"fmt"
	"sync"
)

// Node is a list cell holding key+value. WHY: we need the key on the node so when we
// evict the tail, we can delete the same key from the map (map stores key->node only).
type Node struct {
	key   string
	value int
	prev  *Node
	next  *Node
}

// LRUCache: map gives O(1) lookup; list gives O(1) order updates and tail eviction.
// head = MRU side, tail = LRU side (we evict from tail on overflow after Put).
type LRUCache struct {
	mu     sync.RWMutex
	max    int
	size   int
	bucket map[string]*Node
	head   *Node // dummy; real nodes are between head and tail
	tail   *Node // dummy
}

func NewLRUCache(capacity int) *LRUCache {
	if capacity < 1 {
		capacity = 1
	}
	c := &LRUCache{
		max:    capacity,
		bucket: make(map[string]*Node), // non-nil map required before any store
	}
	c.head = &Node{}
	c.tail = &Node{}
	c.head.next = c.tail
	c.tail.prev = c.head
	return c
}

func (c *LRUCache) addToFront(n *Node) {
	n.next = c.head.next
	n.prev = c.head
	c.head.next.prev = n
	c.head.next = n
}

func (c *LRUCache) removeNode(n *Node) {
	n.prev.next = n.next
	n.next.prev = n.prev
}

func (c *LRUCache) moveToFront(n *Node) {
	c.removeNode(n)
	c.addToFront(n)
}

// evictLRU removes tail.prev (the real LRU node), deletes key from map, decrements size.
func (c *LRUCache) evictLRU() {
	// last real node is before tail
	lru := c.tail.prev
	if lru == c.head {
		return
	}
	c.removeNode(lru)
	delete(c.bucket, lru.key)
	c.size--
}

// Get: if hit, value is returned and node becomes MRU. WHY Lock (not RLock):
// we mutate the list (move to front) — RWMutex read lock is for non-mutating readers only.
func (c *LRUCache) Get(key string) (int, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if n, ok := c.bucket[key]; ok {
		c.moveToFront(n)
		return n.value, true
	}
	return 0, false
}

// Put: insert or update; on new entry at capacity, evict LRU first.
func (c *LRUCache) Put(key string, value int) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if n, ok := c.bucket[key]; ok {
		n.value = value
		c.moveToFront(n)
		return
	}
	if c.size >= c.max {
		c.evictLRU()
	}
	n := &Node{key: key, value: value}
	c.bucket[key] = n
	c.addToFront(n)
	c.size++
}

// Len and Cap use RLock: they only read c.size and c.max; safe for concurrent
// calls with other Len() calls. They will block if a writer holds c.mu.
func (c *LRUCache) Len() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.size
}

func (c *LRUCache) Cap() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.max
}

// Dump prints list order (MRU -> LRU) for the demo. Uses Lock because it reads
// structure consistent with a snapshot under the same rules as Get/Put.
func (c *LRUCache) Dump() {
	c.mu.Lock()
	defer c.mu.Unlock()
	var keys []string
	for x := c.head.next; x != c.tail; x = x.next {
		keys = append(keys, fmt.Sprintf("%s=%d", x.key, x.value))
	}
	fmt.Println("  order (MRU → LRU):", keys)
}

func main() {
	cache := NewLRUCache(3)
	fmt.Println("cap:", cache.Cap(), "len:", cache.Len())
	cache.Put("a", 1)
	cache.Put("b", 2)
	cache.Put("c", 3)
	fmt.Println("after put a,b,c:")
	cache.Dump()
	v, ok := cache.Get("a")
	fmt.Println("Get(a):", v, ok, "| len:", cache.Len())
	fmt.Println("after Get(a) (a should move to front):")
	cache.Dump()
	fmt.Println("Put(d,4) should evict b (LRU):")
	cache.Put("d", 4)
	cache.Dump()
	_, _ = cache.Get("b")
	fmt.Println("Get(b) after evict (miss expected):")
	v2, ok2 := cache.Get("b")
	fmt.Println("  ", v2, ok2)
}
```

### Output

```
cap: 3 len: 0
after put a,b,c:
  order (MRU → LRU): [c=3 b=2 a=1]
Get(a): 1 true | len: 3
after Get(a) (a should move to front):
  order (MRU → LRU): [a=1 c=3 b=2]
Put(d,4) should evict b (LRU):
  order (MRU → LRU): [d=4 a=1 c=3]
Get(b) after evict (miss expected):
   0 false
```

### What to observe

- **Map must be `make`d** before `bucket[key] = n`. Same lesson as Tier 2: a nil `map` panics on assign.
- **Pointer semantics:** `map[string]*Node` stores addresses. `moveToFront` and `evictLRU` only rewire `prev`/`next`; they do not copy `Node` values, so the map still points at the same heap objects — O(1) list surgery.
- **Key on `Node`:** the map is authoritative for “is key present?”, but the list’s tail only gives you a *node*. The node’s `key` field lets `delete(c.bucket, lru.key)` stay O(1) without scanning the map.
- **Why `Get` needs `Lock`, not `RLock`:** `sync.RWMutex` allows many concurrent `RLock` readers **only** when nobody holds a write `Lock`. `Get` **mutates** the doubly linked list (move to front), so it is a write as far as the mutex is concerned. If you used `RLock` in `Get`, two goroutines could corrupt the list.
- **Where `RLock` fits:** `Len()` and `Cap()` are true read-only operations on `size` / `max`, so they use `RLock` to show the idiom. In practice, a cache might still use a single `sync.Mutex` for simplicity; `RWMutex` pays off when you add more read-only observers (e.g. metrics) under `RLock`.
- **Goroutine safety:** all structural changes go through the same `mu`, so the **map and list stay in sync** — important because Go maps are not concurrent-safe; pairing one mutex with one map is the standard pattern from [[T08 Map Internals]].

---
**Back to theory:** [[T08 Map Internals]]
