# T08 Map Internals — Interview Questions

#qa #go #interview

Back to: [[T08 Map Internals]]

A compact bank of Go map (`hmap` / bucket / growth) questions, **ordered from most to least common** at high-signal (FAANG and Go-heavy) companies. Tags: [COMMON], [ADVANCED], [TRICKY].

**C + D (concise + deep):** each answer is layered — quick line, ASCII, bullets, tip — with a **collapsible Full Story** for the interview-length version.

---

## Q1: Why is Go's map not safe for concurrent access? [COMMON]

**Answer:**

**In one line:** The runtime mutates a shared hash table in place (buckets, growth, flags); unsynchronized readers/writers race on that memory, so the runtime may **fatal** rather than allow corruption.

**Visualize it:**

```
G1: grow / write bucket B          G2: read / write same map
     |                                    |
     +--------> same hmap.buckets  <-------+
     fatal: concurrent map read / write   (or concurrent map writes)
```

**Key facts:**
- A `map` variable is a small header pointing at one `hmap`; two goroutines share the same table unless you synchronize.
- Concurrent **writes** are always invalid; the runtime can also detect some invalid **read + write** mixes (depends on build/runtime; do not rely on "mostly reads" without docs-level guarantees).
- **Fixes:** `sync.Mutex` / `sync.RWMutex` around a plain map, `sync.Map` for the niche workloads it is tuned for, or message-passing / ownership (one writer goroutine).
- The failure mode is an intentional **hard stop** (e.g. `fatal error: concurrent map writes`), not silent data loss.

**Interview tip:** Open with "shared mutable hash table" and "no lock inside the type," then one legal fix. Avoid claiming maps are "like channels" (they are not synchronized).

> [!example]- Full Story: Concurrent access and the runtime guarantee
>
> **The problem:** In production, teams sometimes treat maps like a concurrent cache without locks because "we only have one writer" or "reads are safe" — interviews want you to know the real rule: **the map is not** thread-safe **unless the language/runtime explicitly says so** (it does not for `map[K]V`).
>
> **How it works:** Lookups, inserts, and growth can touch bucket arrays, overflow chains, and growth/evacuation state. Even if *your* keys look disjoint, the implementation may restructure the table, set flags, or inspect metadata shared across the whole map. The runtime includes checks that detect some races and **stop the process** to avoid using corrupted pointers or counts.
>
> **What to watch out for:** Suggesting `sync.Map` for every case — it is specialized (e.g. stable key sets, read-heavy, or sharded use cases). A `map` + `RWMutex` is often simpler and clear. Also avoid implying `range` is safe concurrently; it is not without external synchronization.

---

## Q2: Explain the internal structure of a Go map (hmap, bmap, buckets). [COMMON]

**Answer:**

**In one line:** A `map` value is a pointer to an **`hmap`** (header) that points at an array of **`2^B` buckets**; each **bucket (`bmap`)** holds 8 entries (`tophash` + keys + values) plus a chain of **overflow** buckets.

**Visualize it:**

```
hmap
+------------------+     buckets[] (2^B entries)
| count, B, hash0, |---> [ b0 ][ b1 ] ... [ b_{2^B-1} ]
| oldbuckets,      |     each bucket (bmap):
| nevacuate, ...   |       tophash[8]  ->  quick filter
+------------------+       keys[8]     ->  key K at slot i
                          values[8]   ->  value V at slot i
                          overflow*   ->  next bmap or nil
```

**Key facts:**
- **`B`:** log₂ of the bucket count; double table size when growth happens (conceptually 2x buckets).
- **Top bits / low bits:** low bits of the hash pick the bucket; **tophash** (upper bits) narrows the slot in the bucket before full key `==` (see your deep dive in [[T08 Map Internals]]).
- **Overflow:** more than 8 items landing in the same bucket chain with extra `bmap` nodes.
- **Growth:** `oldbuckets` + `nevacuate` support incremental rehashing (not all-at-once; see Q11).

**Interview tip:** Draw `hmap → bucket array → one bmap` in three lines before field trivia. If pressed, mention `hash0` (per-map seed) and hash-dos mitigation at a high level.

> [!example]- Full Story: hmap, bmap, and the pointer header
>
> **The problem:** Candidates often say "hash map" but cannot separate **the variable you hold** (map header) from **the object on the heap** — interviewers use that to probe whether you know Go passes the map by copying a **pointer-sized** descriptor to the same `hmap`.
>
> **How it works:** The compiler treats `map[K]V` as a **pointer type** in practice: assignment copies the pointer, not the whole table. The `hmap` stores `count`, `B`, pointers to the current and old bucket slices during growth, and other bookkeeping (`runtime/map.go`). Each bucket is a `bmap` with an 8-wide `tophash` array and packed key and value **arrays** (not interleaved; see Q12) followed by an overflow pointer.
>
> **What to watch out for:** Memorizing every field name matters less than the **data path**: hash → bucket index → scan `tophash` → compare key → return value, else overflow.

---

## Q3: What is the load factor and when does a map grow? [COMMON]

**Answer:**

**In one line:** The runtime approximates "how full" the table is (average entries per bucket via count and `2^B`) and also watches overflow pressure; when the **load factor ≈ 6.5** (documented in Go source) is exceeded, or there are too many overflow buckets, the map **grows** (doubles buckets, rehashing incrementally).

**Visualize it:**

```
load ≈ count / (2^B * 8)   (each bucket holds up to 8)

too heavy / long overflow chains
        |
        v
  allocate 2x buckets, evacuate from oldbuckets in pieces
```

**Key facts:**
- The exact trigger ties **element count**, **bucket count**, and **overflow** — not a single C-style `α` you configure in app code.
- **Growth = larger `B`** → new bucket array; old data moves via **evacuation** (see Q11), not one giant STW copy in user code.
- A **capacity hint** in `make(map[K]V, hint)` can reduce how often you pay growth early; it is a hint, not a hard cap.
- After many deletes, memory may not shrink; long-lived huge maps with churn can retain backing storage (a separate memory interview theme).

**Interview tip:** Quote **6.5** as "from the implementation" and immediately say **overflow** can force growth even if the raw average load looks borderline. Show you know the public contract is "implementation-defined," not a tunable `loadFactor` field in your program.

> [!example]- Full Story: Load, overflow, and apparent complexity
>
> **The problem:** People expect `len(m)/cap` style reasoning; maps expose `len` but not a public "capacity" — you need the runtime story: **buckets** and **overflow chains**.
>
> **How it works:** The implementation tracks how packed buckets are and how many extra overflow buckets build up. When thresholds are hit, the table grows. The **6.5** average load factor (per official commentary in `map.go` across Go versions) is the headline number, but the full condition includes overflow, so the exact moment can differ from a naive `count/2^B/8` napkin check.
>
> **What to watch out for:** Claiming *exact* growth timing across Go versions. Say "per current runtime, roughly 6.5 average load plus overflow heuristics" and point to the source in [[T08 Map Internals]] if asked to go deeper.

---

## Q4: What happens when you write to a nil map? [COMMON]

**Answer:**

**In one line:** A **read** on a `nil` map is safe and returns the zero value (and `ok` is false in the two-value form), but a **write** to a `nil` map **panics** because there is no `hmap` to mutate.

**Visualize it:**

```
var m map[string]int   // nil

m["a"]  ->  v, ok   OK (v=0, ok=false)     |  m["a"]=1  ->  panic
```

**Key facts:**
- `nil` and an **empty** made map are different for **writes**; only `make` (or a literal) allocates the runtime structure for mutation.
- Pattern: `if m == nil { m = make(...) }` before first store, or build maps with `make` at declaration time.
- Reads use a fast path: no allocation, no `hmap` required.

**Interview tip:** Pair with: "read is a no-op; write needs storage." This often appears as a **trick** in init-order questions (`map` field never initialized).

> [!example]- Full Story: Nil map read vs write paths
>
> **The problem:** Code paths that lazily build a map sometimes forget the first assignment when the field starts `nil` — first write panics, often in a rare branch, in tests.
>
> **How it works:** A `nil` map variable has a nil pointer to `hmap`. Read operations synthesize a missing entry without touching buckets. A write would need to allocate buckets, set `count`, etc., and the spec instead defines that a store to `nil` **panics** so you do not get silent allocation side effects in surprising places.
>
> **What to watch out for:** Comparing to `var s []T` (nil slice reads/writes) — slices and maps differ on write behaviors; maps need `make` for mutation.

---

## Q5: What types can be used as map keys? [COMMON]

**Answer:**

**In one line:** Map keys must be **comparable** in Go: anything `==` works on for key types, which includes the usual comparable scalars, arrays of comparable element type, pointers, channels, interfaces (dynamic comparability), and structs of comparable fields — but **slices, maps, and funcs** are not valid map keys (except via pointers to them).

**Visualize it:**

```
OK:     int, string, [3]int, *T, struct{ A int; B string }
NOT OK:  []byte (slice), map[K]V, func()
Pointer to slice:  *[]byte is OK as a key, but *slice contents* are not compared by deep equality
```

**Key facts:**
- The compiler enforces comparability; using an incomparable type as `K` is a **compile error**.
- `interface{}` / `any` as key type: the **stored dynamic type** at runtime must support `==` or comparisons panic at runtime in some cases — avoid unless you are careful.
- **String** vs `[]byte`: `string` keys are common; `[]byte` is not a key (use `string(b)` or struct pointer workarounds).
- **Floating-point** keys: NaN is not equal to itself — subtle and rarely wise as keys.

**Interview tip:** State the spec phrase **comparable** first, then list the three big "no" families: slice, map, func. If advanced: NaN and interface pitfalls.

> [!example]- Full Story: Comparability, interfaces, and NaN
>
> **The problem:** Teams sometimes use `map[interface{}]T` for "any key" — then a non-comparable value stored as interface can break at **runtime** when the map tries to hash/compare.
>
> **How it works:** Key operations require equality. Slices and maps are incomparable; functions are incomparable. Structs are comparable if all their fields are. Arrays are comparable if element type is. Pointers compare by address, not by pointed-to aggregate value.
>
> **What to watch out for:** `reflect.DeepEqual` vs `==` — maps use the **latter** for keys. For `float64`, remember **NaN** makes maps awkward (NaN != NaN). For `any` keys, prefer generics with a known comparable constraint when possible.

---

## Q6: What's the difference between sync.Map and sync.RWMutex + map? [COMMON]

**Answer:**

**In one line:** A **plain map** with **`sync.RWMutex`** (or `Mutex`) is the general, explicit model: you choose lock granularity; **`sync.Map`** is a **specialized** concurrent `map` with internal sharding/atomic fast paths, tuned for **read-heavy, write-once or stable key sets**, and is **not** a drop-in faster `map` for every workload.

**Visualize it:**

```
RWMutex + map:          sync.Map
------------            --------
mu.Lock/RLock         internal unsafe + atomics, read paths avoid global lock
wrap every access     optimized for particular patterns
simple mental model   easy to misuse if pattern wrong
```

**Key facts:**
- **Default choice:** `map` + `RWMutex` for many services — clear invariants, easy profiling.
- **`sync.Map`:** Good when keys are long-lived, many read-mostly cache hits, or you have profiled and proven it wins; **bad** when you have heavy churn, unbounded keys, or need transactional multi-key updates.
- Neither removes the need to think about **iterator** semantics, **size**, or **atomicity of composite operations** — design APIs carefully.
- For simple counters by key, sometimes **sharding** (array of `map`+lock) beats both.

**Interview tip:** Say: "`sync.Map` is not 'the concurrent map' — it's an optimization with narrow wins." Then one sentence on when the stdlib comment suggests it.

> [!example]- Full Story: sync.Map internals vs a mutex sandwich
>
> **The problem:** Junior code replaces every map with `sync.Map` "for thread safety" and regresses CPU or memory — interviewers want judgment, not brand loyalty.
>
> **How it works:** The standard `map` is not concurrent; a mutex serializes or allows reader parallelism with `RWMutex`. `sync.Map` (see `doc.go`) is built for `Load`/`Store`/`LoadOrStore` with fast paths for entries that become stable, using atomic dirty promotion etc. (details change by release but the **pattern** story stays).
>
> **What to watch out for:** `Range` on `sync.Map` still has complexity; O(n) all-element work is still O(n). Also **type safety** — `sync.Map` stores `any`; generics wrappers are common in application code for clarity.

---

## Q7: Can you delete map entries during iteration? [COMMON]

**Answer:**

**In one line:** You **may delete the current key** (or other keys) during `for k := range m` in recent Go; the **iteration behavior is defined** for deletion — but you must **not** assume safe behavior if you add keys during iteration, and you should not architect logic that depends on subtle iteration + mutation ordering.

**Visualize it:**

```
for k := range m {
    delete(m, k)   // defined: m shrinks, k not visited again
}

for k := range m {
    m["new"] = 1   // not specified / safe to rely on — do not
}
```

**Key facts:**
- The **language spec** evolved; modern Go allows safe deletion during range with defined semantics (entries not yet reached may be skipped as the table changes — design code so you do not depend on a hidden order; see spec for your version).
- **Add** while iterating: still a footgun — rehashing and random start mean tests can flake if you entangle order with growth.
- If you need "collect keys then delete" or "snapshot," copy keys to a **slice** first.
- This pairs with "iteration order is random" (Q8) — you delete by key, not by "position."

**Interview tip:** Lead with: "delete is OK per spec; adding during range is the dangerous discussion." Cite the **spec, not Hacker News** if challenged.

> [!example]- Full Story: Spec semantics vs old folklore
>
> **The problem:** Older blog posts said "never delete in range" — interviewers may test whether you know the **current** rule. Outdated memes cost points.
>
> **How it works:** The `for range` on maps tracks enough state that removing elements you are visiting does not explode the runtime; the spec defines the behavior. Adding can cause rehash, growth, and visits that confuse anyone relying on order.
>
> **What to watch out for:** Concurrent iteration + mutation (still a hard **no** without external sync). The safe subset is **one goroutine** with spec-correct `delete` during range — not concurrent readers.

---

## Q8: Why is map iteration order random in Go? [TRICKY]

**Answer:**

**In one line:** The language **intentionally** randomizes (and may vary by version/arch) the traversal path over buckets/slots so programs cannot rely on a stable order that would make future `map` changes break production or enable hash-flooding / algorithmic dependencies.

**Visualize it:**

```
Run 1:  k3, k1, k2
Run 2:  k2, k3, k1
        ^^^^^ same map literal — different order

(Implementation uses a random start offset / seed — do not depend on it)
```

**Key facts:**
- There is **no** "insertion order" map in the core language.
- Stabilize by copying keys to a `[]K` and `sort.Slice`.
- This is a **portability and security** move (coupled with per-map `hash0`, growth, etc., as discussed in [[T08 Map Internals]]), not a bug.
- **Tests** that `range` a map and compare golden strings are flaky by design.

**Interview tip:** Say: "**Deliberate randomization**" and link to *preventing reliance* and *DoS* — that sounds senior.

> [!example]- Full Story: Randomization and hash seeds
>
> **The problem:** Devs from Python 3.7+ or .NET may expect insertion order. Go made a different trade: simpler runtime guarantees, fewer accidental dependencies on bucket layout, and a harder time building adversarial inputs that pathologically walk structures.
>
> **How it works:** Iteration walks buckets but injects **randomization** in the walk (exact mechanism can change; constant across the process for a given map iteration, not a stable public API). Combined with rehashing and growth, order is unstable across runs and versions.
>
> **What to watch out for:** Suggesting `sort` on `map` — there is no `sort` on `map` directly. Extract keys, sort, then index.

---

## Q9: Why can't you take the address of a map value? [TRICKY]

**Answer:**

**In one line:** `&m[k]` is illegal because `m[k]` is **not addressable** — the implementation may **move** the stored `V` when buckets grow or rehash, so a `*V` into map storage would be **unsafe**; use a local copy, reassign, or `map[K]*V`.

**Visualize it:**

```
&m[k]     compile-time error

v := m[k]      // v is a copy (ok)
m[k] = v       // write back

-- or --

map[string]*T  // address of the heap object is stable; map stores pointer, not struct bytes
```

**Key facts:**
- This is why you cannot do `m[k].Field = ...` for struct values — assign to a local, edit, store back, or use pointers as values.
- A **value** in a `map` is not a long-lived lvalue like a `var` in your stack frame.
- Pointer **values** in the map point at heap data that does not move when the map rebalances **pointer words**; still only safe with proper sync.

**Interview tip:** Two beats: (1) **not addressable**, (2) **moving storage** on growth. Then the practical fix — locals or `*V`.

> [!example]- Full Story: Addressability and relocation
>
> **The problem:** Developers expect C++-style references into containers; Go's map is not that.
>
> **How it works:** On lookup, the runtime may return a copy from bucket memory. The runtime reserves freedom to copy and relocate entries. Letting a `*V` pin a slot would either constrain the GC/radically complicate the implementation or require write barriers you do not have on `&field`.
>
> **What to watch out for:** Conflating this with "maps return copies" in general (true for value types) and with **pointer element types** where you mutate the pointed-to object — that is a different, valid pattern with its own nil/lifetime rules.

---

## Q10: How does Go's map handle hash collisions? [ADVANCED]

**Answer:**

**In one line:** All keys with the same **low `B` bits** share a **bucket**; if more than 8 land in that bucket, **overflow `bmap` chains** hold extras; **linear probing** is *not* the main model (open addressing is not the headline story for Go) — the usual picture is **chained buckets** plus **tophash** to compare keys quickly within the first 8 slots.

**Visualize it:**

```
hash1 -> bucket #5  (same low bits)   hash2 -> also bucket #5
        |
        v
   bmap: tophash[0..7]  keys[0..7]  values[0..7]
        |
   overflow bmap  ->  more keys...
```

**Key facts:**
- "Collision" at the table level: same bucket. Inside the bucket, **8 slots** + **tophash** to filter before full `==` on keys.
- Further collisions → **append overflow buckets** to that bucket's chain; worst case devolves to scanning small chains.
- The **6.5** load factor + growth keeps chains short in the average case; adversarial data still motivates **hash randomization** (`hash0`).
- Different key types have different runtime hash functions, but the bucket/overflow model is shared.

**Interview tip:** If they say "chaining," say **bucket chaining** (or overflow chains), not "linked list of pairs at each slot" — Go is **8-wide blocks**, not classic separate chaining per key without buckets.

> [!example]- Full Story: Tophash, equality, and overflow
>
> **The problem:** A naive "hash then linear probe" story is the wrong language for Go's presentation — you will miss the 8-wide slots and the separate **key and value** arrays in each `bmap`.
>
> **How it works:** Hash picks bucket index. Within the bucket, `tophash` values let the runtime reject most negative comparisons cheaply, then `==` on keys for the real match. Filling 8 entries forces an overflow `bmap` with another 8+8 arrays. Thus collisions hash down to the same micro-chain for that bucket index, not an infinite `next` pointer per entry in the main array.
>
> **What to watch out for:** Claiming O(1) with no big-O caveat — with pathological input you still can degrade without good distribution; the runtime's seeding and growth fight this but are not a formal crypto guarantee.

---

## Q11: How does incremental evacuation work during map growth? [ADVANCED]

**Answer:**

**In one line:** On growth, the `hmap` **allocates a new larger bucket array**, keeps **`oldbuckets`**, and on later operations **migrates a few old buckets at a time** (tracked with **`nevacuate`**) so no single `map` op must rehash the entire table at once.

**Visualize it:**

```
Before:  [ old table of 2^B buckets ]

Trigger growth ->  new "buckets" (empty, size 2^{B+1})
                    oldbuckets -> points at former array
                    nevacuate -> progress 0..oldlen

next map op:  evacuate 1-2 more old buckets  ->  spread entries into new table
... until old table drained ->  oldbuckets=nil
```

**Key facts:**
- This **amortizes** the cost and keeps individual operations **bounded** in typical cases, though worst-case can still be heavy during heavy mutation + growth.
- **Reads** must consult both tables while split: "two-phase" lookup (conceptually) until migration completes for relevant indices.
- **Iterators** must account for a split table; randomization and split state are part of why iteration is subtle internally.
- User code cannot observe `nevacuate` — it is pure runtime.

**Interview tip:** Contrast with "stop the world, rebuild entire map" — Go chose **incremental** evacuation. If asked "where," say `oldbuckets` and `nevacuate` in `hmap` (high level).

> [!example]- Full Story: Two bucket arrays and the evacuation pointer
>
> **The problem:** A single giant rehash would cause latency spikes; Go targets low latency for most ops, so the runtime interleaves work.
>
> **How it works:** New bucket count doubles (`B+1`); the old pointer array hangs off `oldbuckets`. As operations hit parts of the key space, the runtime **evacuates** bucket ranges, updating `nevacuate` as it goes. This spreads work across many map operations. Once done, the old array can be released.
>
> **What to watch out for:** Claiming "no extra work on lookup" — while growing, a lookup can be more complex, though still engineered for real-world speed. Also avoid promising exact 1-2 bucket evac count across all Go versions — treat numbers as "small batches."

---

## Q12: Why does Go separate keys and values in bucket storage? [TRICKY]

**Answer:**

**In one line:** `bmap` stores **`tophash[8]`**, then all **`keys[8]`**, then all **`values[8]`** so each region can be tightly packed to **type alignment and size**; interleaving `k,v,k,v` would insert **padding** and waste cache/space when `sizeof(K) ≠ sizeof(V)` (e.g. `int64` + `bool`).

**Visualize it:**

```
Interleave (wasteful if sizes differ):
[ K(8) ][ V(1) ][ pad(7) ][ K(8) ]...

Group keys / values (Go style):
[ K K K K K K K K ][ V V V V V V V V ]   <- fewer alignment holes in many layouts
[ tophash[8] scan fits cache line work ]
```

**Key facts:**
- The runtime generates **per-type** bucket layouts; separation is a **memory layout / padding** and **SIMD / cache** friendly organization choice.
- Tophash first gives a **one-cache-line-ish** filter for empty vs candidate slots in many cases (implementation detail, but a good sound bite).
- This layout is part of *why* you do not get a stable `&m[k]` — values sit in a packed blob that moves with growth, not a named variable per slot in user memory.

**Interview tip:** Lead with **padding / alignment**; secondarily **cache** — most interviewers stop there. Avoid claiming "SIMD" strongly unless you can defend it; "cache line friendly scan of `tophash`" is enough.

> [!example]- Full Story: Struct padding vs grouped arrays
>
> **The problem:** Hand-written `struct { k K; v V }[8]` would force **pair** alignment, sometimes ballooning the bucket. Go instead packs homogenous arrays so the compiler and runtime can compute strides once per `K` and per `V`.
>
> **How it works:** For each map type, the compiler builds a specialized `mapaccess`, `mapassign`, etc., that knows the offsets. Keys are compared in place from the `keys` array; values are read/written from the `values` array. This keeps bucket memory dense when value type is much smaller or larger than key type.
>
> **What to watch out for:** Comparing to Java's `Map.Entry` objects — Go avoids per-entry box overhead in the common case. Also do not over-claim: huge values still make buckets heavy; the layout cannot defeat bad value-type choices (e.g. giant structs as values).

---

*Tags legend:* **[COMMON]** — most panels will touch this. **[ADVANCED]** — intern / mid deep dives. **[TRICKY]** — looks simple; tests precise language. For the full study note, see [[T08 Map Internals]] and [[simplified/T08 Map Internals - Simplified]].
