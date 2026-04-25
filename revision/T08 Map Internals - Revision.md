# T08 Map Internals — Revision Card

> Drill-down from [[Daily Revision]] | Full notes → [[T08 Map Internals]]
> Q&A bank → [[questions/T08 Map Internals - Interview Questions]]

---

## Recall Grid

| # | Prompt | Check |
|---|--------|-------|
| 1 | What struct backs a map? | **hmap** |
| 2 | How many KV pairs per bucket? | **8** |
| 3 | What triggers map growth? | Load factor **> 6.5** or **too many overflow** buckets |
| 4 | Is growth done all at once? | **No** — **incremental** evacuation (1–2 buckets per op) |
| 5 | Are maps safe for concurrent access? | **No** — **concurrent read+write** (any unsync **write** race) can **panic** |
| 6 | Can you take address of map value? | **No** — values **not addressable** |
| 7 | What does tophash do? | **Top 8 bits** of hash for **fast filter** within bucket |
| 8 | What happens writing to nil map? | **panic: assignment to entry in nil map** |
| 9 | Is map iteration order guaranteed? | **No** — **deliberately randomized** |
| 10 | Does deleting from a map free memory? | **No** — buckets **never shrink**; **re-create** map to release |

---

## Core Visual (bucket / bmap layout)

One bucket = **8 cells**: `tophash` slot first, then keys and values in separate contiguous regions (as in runtime `bmap`).

```
  bmap (one bucket, 8 slots)
  ┌────────────────────────────────────────────────────┐
  │  tophash[0..7]  each byte: top-8 of hash, or      │
  │                 empty/EVACUATED/... sentinels       │
  ├────────────────────────────────────────────────────┤
  │  keys[0] keys[1] ... keys[7]   (typed key array)   │
  ├────────────────────────────────────────────────────┤
  │  values[0] ... values[7]       (aligned per type)  │
  └────────────────────────────────────────────────────┘
        │
        └── overflow *bmap ──► next bucket in chain (if chain too long)
```

- **tophash**: cheap reject before key compare.  
- **8 slots/bucket**; **overflow** list when a bucket’s chain is saturated.

---

## Top Interview Questions (quick-fire)

**1. Are Go maps safe for concurrent use?**

**No** for read+write (or any write) without synchronization. The runtime can **detect** bad races and **panic** (“concurrent map writes”). Safe patterns: `sync.Mutex` / `sync.RWMutex` around a regular map, or **`sync.Map`** for specific cache-like workloads, or **no sharing**.

**2. When does a map grow, and is it atomic (one big copy)?**

Growth triggers when the **load factor** exceeds **6.5** (avg **> 6.5** keys per bucket) or there are **too many overflow** buckets. Growth is **not** one giant stop-the-world copy: **incremental evacuation** — each map op may **evacuate 1–2 buckets** from `oldbuckets` into the new table.

**3. Why can’t you `&m[k]`?**

**Map values aren’t addressable** — a lookup is not a stable lvalue; **growth/evacuation** can **move** entries, so a pointer would dangle. Copy to a var, or use pointers **as the value type** (`map[K]*V`).

---

## Verbal Answer (say this out loud)

Go maps are **hash tables** backed by **`hmap`**. **2^B** buckets; each holds **8** K/V pairs with **tophash** for fast in-bucket filtering. **Growth** at **load factor 6.5** (or overflow pressure), with **incremental** evacuation, **not** concurrent-safe — Go **panics** on **races**. **Map values not addressable** because **growth** moves entries. For concurrency, use **`sync.RWMutex`** (or `sync.Map` when appropriate).

---
