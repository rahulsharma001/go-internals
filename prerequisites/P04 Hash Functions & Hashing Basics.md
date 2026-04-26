# P04 Hash Functions & Hashing Basics

> **Prerequisite note** — complete this before starting **T08 Map Internals**.
> Estimated time: ~15 min

---

## 1. Concept

A **hash function** turns a key of arbitrary size into a fixed-size integer in a bounded range. The same key must always yield the same integer so lookups stay consistent.

> **In plain English:** A library **card catalog** does not store every book on one giant shelf in random order. You pick a **label** from the book, run it through a **simple rule** that picks a **drawer number**, then you open that drawer. The rule is repeatable. Two different books can land in the same drawer. That overlap is normal. The whole system still works because the drawer stores **multiple cards**, not one.

---

## 2. Core Insight (TL;DR)

**Hashing is how maps turn “find this key” into “jump near the answer fast.”** A **good** hash spreads keys **evenly** across buckets so drawers stay balanced. **Collisions** are expected; the map **resolves** them with extra structure inside buckets, not by pretending they never happen. **Go** combines **hash bits**, **bucket indexing**, and **small-scale probing inside a bucket** so lookups stay **amortized fast** while staying **safe** against some attacks.

---

## 3. Mental Model (Lock this in)

Expand the catalog picture. The **key** is the book title. The **hash** is the computed drawer hint. The **bucket** is the physical drawer. The **bucket index** picks which drawer row you open first. If two keys hint at the same drawer, you still find the right card because the drawer holds **multiple entries** organized so you can scan the small pile.

```
MEMORY TRACE:

Step 1: key literal "go" lives in the program (read-only data @0x10_4000)
  stack: (no local vars yet for this story)
  heap: (map root appears in Step 4)
  shared memory: KEY @0x10_4000 ──→ bytes: [0x67, 0x6F]  ("g","o")

Step 2: key ──→ hash(seed, key) ──→ H (fixed-width integer)
  stack: (ephemeral mixer / return registers)
  heap: (none for hash computation itself)
  shared memory: same bytes @0x10_4000 fed into runtime hash with map seed
  H = 0x9F2E_4B1C_77A3_....   (fixed-width word; many bits; same key ⇒ same H for same seed)

Step 3: number H ──→ bucket index i — toy power-of-two: bucket = H % numBuckets  ==  H & (numBuckets-1)
  stack: i = 3 (illustrative local)
  heap: (bucket array pointer loaded next)
  shared memory: (unchanged)
  mask example: numBuckets=8 ──→ i = H % 8 = H & 0x7  ──→  i = 3
  ◄── "which row of drawers" is just an integer in [0, buckets-1]

Step 4: follow pointer from map root to bucket array
  stack: (iterator / index i)
  heap:
    hmap ──→ [ count | B | hash0 | buckets ──→ [bucket0][bucket1]...[bucket_i]... ]
  shared memory: (read-only key data still @0x10_4000 for comparisons later)
  bucket_i @0xC0_0000 ──→ first bucket in chain for index i

Step 5: inside bucket i (8 cells + overflow pointer — conceptual layout)
  heap: bucket @0xC0_0000:
    tophash: [0x..|0x..|_|_|_|_|_|_]   ◄── quick filter bytes from hash
    keys:    [k0 | k1 | _ | _ | _ | _ | _ | _]
    values:  [v0 | v1 | _ | _ | _ | _ | _ | _]
    overflow ──→ nil  (or ──→ next bucket @0xC0_0080 if chain continues)
  stack: (slot index while scanning)
  shared memory: key material for k0,k1 may point into string backing / scalar storage
```

Collision in one picture:

```
MEMORY TRACE:

Step 1: KEY "go" — shared memory @0x10_4100 ──→ hash(seed, "go") ──→ H_go = 0x...B10110110
  stack: (ephemeral) H_go in register / temp
  heap: (target bucket not yet shown)
  shared memory: "go" bytes @0x10_4100
  bucket index: i_go = H_go % N = 6   ◄── illustrative N = 16 buckets (hash → number → bucket = hash % numBuckets)

Step 2: KEY "no" — shared memory @0x10_4200 ──→ hash(seed, "no") ──→ H_no = 0x...C00110110
  stack: H_no, i_no = H_no % N = 6
  heap: (same bucket index as Step 1)
  shared memory: "no" bytes @0x10_4200
  i_no = 6   ◄── AHA: distinct keys, same bucket ⇒ COLLISION (chained / same drawer)

Step 3: BEFORE insert "no" — only "go" in bucket chain head @ index 6
  stack: (insert path holds slot search cursor)
  heap: buckets[6] @0xC0_0600
    tophash: [0xB1|_|_|_|_|_|_|_]
    keys:    ["go"|_|_|_|_|_|_|_]
    values:  [1   |_|_|_|_|_|_|_]
    overflow* ──→ nil
  shared memory: string data for "go"

Step 4: AFTER insert "no" — same bucket index; in-bucket scan finds empty cell slot 1
  stack: (lookup will recompute i=6, then scan)
  heap: buckets[6] @0xC0_0600
    tophash: [0xB1|0xC0|_|_|_|_|_|_]
    keys:    ["go"|"no"|_|_|_|_|_|_]
    values:  [1   |2   |_|_|_|_|_|_]
    overflow* ──→ nil
  shared memory: "go" and "no" backing bytes
  ◄── aha: both keys share i=6; lookup hashes to bucket 6 then compares keys in keys[]/values[] (tophash filters first)
```

> **In plain English:** Collisions are not disasters. They mean “same drawer.” The map’s job is to make each drawer **small** and **searchable** so checking the drawer stays cheap.

---

## 4. How It Works

### 4.1 What makes a hash “good” for maps

Four properties interviewers like to hear, in plain terms.

**Deterministic**

The hash of a key is the same every time you compute it for a given map state and algorithm inputs. If this broke, you could store a value and never find it again.

**Fast**

Hashing runs on the **hot path** for map reads and writes. Slow hashing makes every map operation expensive.

**Uniform distribution**

Keys should scatter across buckets so **no single bucket** becomes a long chain. Bad spread turns average **O(1)** behavior into “often linear in the worst bucket.”

**Avalanche effect**

A tiny change in the key should change many bits of the hash output. If neighboring keys tended to produce neighboring hashes, real data patterns could **pile into the same buckets**.

ASCII intuition for avalanche:

```
MEMORY TRACE:

Step 1: key A — comparable scalar / bit pattern in memory
  shared memory: key A word @0x20_0000 ──→ ...0000001000...
  stack: (none for this static story)
  heap: (none)

Step 2: key A ──→ hash(seed, A) ──→ H_A
  heap: (none; result lives in register / stack temp)
  shared memory: same @0x20_0000
  stack: H_A temp
  cpu: H_A @conceptual ──→ ...1110100110...

Step 3: key B — flip one low bit vs A
  shared memory: key B @0x20_0004 ──→ ...0000001001...
  stack: (none)
  heap: (none)
  ◄── AHA: single-bit input tweak

Step 4: key B ──→ hash(seed, B) ──→ H_B  (many bits differ from H_A)
  shared memory: @0x20_0004
  stack: H_B temp
  heap: (none)
  cpu: H_B ──→ ...0011011001...
  ◄── avalanche: H_A vs H_B not "locally similar" ⇒ bucket = H % numBuckets scatters under small key edits
```

### 4.2 Collisions: inevitable, designed for

A hash maps a **large** key space into a **smaller** index space. **Pigeonhole principle:** some distinct keys **must** share outputs. Your implementation’s quality shows up in **how often** and **how badly** collisions cluster, and in **how you resolve** them.

### 4.3 Collision resolution: chaining vs open addressing

**Chaining**

Each bucket holds **multiple entries**. If a bucket fills, you add **overflow storage** linked from the first bucket. Think “drawer got full, attach a **satellite drawer**.”

```
MEMORY TRACE:

Step 1: KEY "a" @0x10_5000 ──→ hash(seed,"a") ──→ H_a ──→ bucket = H_a % N ──→ i = 3
  stack: H_a, index i=3 (temps)
  heap: buckets[] root (insert will touch buckets[3])
  shared memory: "a" bytes @0x10_5000

Step 2: insert "b","c" in same bucket i = 3 (toy: first bucket not yet full)
  stack: slot cursor 0..2
  heap: buckets[3] head @0xC0_0300
    tophash: [t_a|t_b|t_c|_|_|_|_|_]
    keys:    ["a"|"b"|"c"|_|_|_|_|_]
    values:  [va|vb|vc|_|_|_|_|_|_]
    overflow* ──→ nil
  shared memory: string / key bytes for "b","c"

Step 3: insert "d" — all 8 cells in head bucket occupied ◄── chain extends
  stack: allocate overflow, relink
  heap: head.overflow @0xC0_0300 ──→ overflow bucket @0xC0_0380
    overflow tophash: [t_d|t_e|_|_|_|_|_|_]
    overflow keys:    ["d"|"e"|_|_|_|_|_|_]
    overflow values:  [vd|ve|_|_|_|_|_|_]
    overflow.overflow* ──→ nil
  shared memory: keys "d","e"

Step 4: lookup "e" — hash(seed,"e") ──→ i = 3 ──→ scan head tophash/keys @0xC0_0300 ──→ follow overflow* ──→ find "e" @0xC0_0380
  stack: probe index within bucket chain
  heap: head + overflow as above
  shared memory: "e" for final key compare
  ◄── aha: same bucket index, multiple buckets linked; collision resolution by chaining
```

**Open addressing**

Every entry lives **in the table array itself**. On collision, you **probe** for another empty cell using a rule such as linear probing, quadratic probing, or double hashing.

```
MEMORY TRACE:

Step 1: hash(seed, KEY) ──→ H ──→ j0 = H % numBuckets = 3
  stack: H, j0=3
  heap: open-address table slots [0..N-1] @0xC0_4000 (each slot: key+value+meta)
  shared memory: KEY material @0x10_6500

Step 2: probe j0 = 3 — slot OCCUPIED (different key)
  stack: probe trail [3]
  heap: slot[3] holds other entry
  shared memory: (compare fails — not our key)
  ◄── collision at home index

Step 3: linear probe ──→ j1 = 4 — OCCUPIED
  stack: probe trail [3,4]
  heap: slots[4] @0xC0_4010 full
  shared memory: (other key)

Step 4: probe ──→ j2 = 5 — EMPTY @0xC0_4018
  stack: chosen index j2=5
  heap: INSERT key/value here
  shared memory: KEY stored into slot
  ◄── aha: stored index ≠ j0; lookup must repeat same probe sequence until match or empty
```

**What Go does**

Go’s map is **not** “one slot per key with probing across the whole table” in the classic open-addressing sense. It uses **buckets** that each hold **eight key/value cells** in current implementations. Overflow buckets chain when a bucket runs out of room. So the mental model for interviews: **bucket-level chaining** with **in-bucket placement** rules.

Interview-safe one-liner:

```
MEMORY TRACE:

Step 1: KEY bytes @0x10_6000 ──→ runtime hash(seed, key) ──→ H @cpu (wide integer)
  stack: spill temps for mixer
  heap: (hash alone doesn’t allocate)
  shared memory: key bytes @0x10_6000

Step 2: H ──→ bucket index i via mask/shift for current 2^B size (Go: not “only H % N” in source, but same idea: reduce H to an index)
  stack: i in register
  heap: hmap @0xC0_7000 ──→ buckets* ──→ array of bucket structs
  shared memory: (unchanged)

Step 3: bucket i @0xC0_7i00 — internal arena: tophash[8] + keys[8] + values[8]
  stack: cell offset 0..7 while scanning
  heap: bucket struct layout as above
  shared memory: keys may reference string/data backing
  ◄── small fixed cell count per bucket (8 in current implementations)

Step 4: in-bucket placement / scan (deterministic local order); on full bucket ──→ overflow* ──→ next bucket @0xC0_7i80
  stack: follow overflow pointer
  heap: chained overflow bucket @0xC0_7i80
  shared memory: (overflow keys)
  ◄── aha: bucket-level chaining + bounded in-bucket search = Go’s mental model for interviews
```

### 4.4 Load factor: fullness vs growth

**Load factor** means “how crowded the table is.” One common textbook definition:

```
MEMORY TRACE:

Step 1: read live entry count and bucket count from map bookkeeping
  stack: load_factor ≈ number_of_entries / number_of_buckets  ◄── textbook sketch
  heap: hmap fields hold count, B, buckets*
  shared memory: (n/a — metadata in heap)

Step 2: high load factor ──→ more keys per bucket on average ──→ longer in-bucket fill + overflow chains
  stack: (scheduler / grow decision uses averages)
  heap: conceptual pressure on buckets[0..N-1] @0xC0_8000
  shared memory: (entries referenced from bucket cells)
```

High load factor means **more collisions** and **longer chains** unless you resize.

**Go’s trigger**

Go grows the map when the **average entries per bucket** crosses about **6.5**. That number is an implementation detail, but it is the usual **interview answer** for “when does a Go map grow?”

ASCII before and after growth:

```
MEMORY TRACE:

Step 1: BEFORE growth — crowded (toy numbers match section prose)
  stack: (bookkeeping reads count, B)
  heap: numBuckets = 4, bucket array @0xC0_A000
  shared memory: keys/values reachable from old buckets only
  entries = 22  ──→ avg ≈ 22 / 4 ≈ 5.5 entries per bucket (illustrative; real Go uses ~6.5 threshold and finer counts)
  ◄── long chains / full buckets more likely

Step 2: threshold crossed — Go allocates larger bucket table (size grows by increasing B; count ≈ 2^B buckets)
  stack: grow / evac control flow
  heap: NEW bucket array @0xC0_B000 with numBuckets = 8  ◄── load factor improved by doubling buckets (conceptual)
  shared memory: (keys stable during rehash)

Step 3: same entries = 22 — avg ≈ 22 / 8 ≈ 2.75 per bucket after spread
  stack: per-entry rehash temps
  heap: entries migrate from @0xC0_A000 layout into @0xC0_B000 cells
  shared memory: each key’s bytes unchanged; only bucket index changes
  each (key,value): hash(seed,key) ──→ H ──→ new_index = H % 8 (toy) / mask for new 2^B  ◄── rehash into wider table

Step 4: incremental evac completes — old @0xC0_A000 retired
  stack: (iterator / concurrent map rules still apply in real runtime)
  heap: only @0xC0_B000 bucket table valid
  shared memory: (unchanged)
  ◄── aha: addresses from before grow are stale; unsafe pointer games see wrong buckets
```

This toy average is only a sketch. Real growth decisions use finer internal bookkeeping.

Growth **rehashes** entries into a bigger bucket array. Pointers to map internals can make old addresses stale; that is why unsafe games around maps are dangerous.

### 4.5 Go-specific hashing mechanics

**Key to hash**

For each map operation, Go computes a **hash code** for the key type using runtime support.

**Hash to bucket**

Go does **not** use only “hash mod number_of_buckets” as the whole story. It uses **bits of the hash** to pick a bucket in a way that cooperates with power-of-two sizing and incremental expansion. The interview point: **bucket selection is a bit-masking and shifting story**, not a single textbook formula you must memorize.

**Inside the bucket**

A bucket holds **multiple slots**. If the natural slot sequence is busy, the algorithm searches **within the bucket** in a **deterministic pattern** to find an empty cell or a matching key. This is why people say **linear probe within the bucket**: it is **local**, bounded, and keeps the hot path cache-friendly compared to scanning unbounded chains for every lookup.

**Per-map random seed**

Go mixes a **random seed** into hashing for maps so attackers cannot craft many keys that collide on purpose. This mitigates **hash-flooding** slowdowns.

### 4.6 Hashing different Go types

**Integers**

Integer keys hash in a way that effectively treats the bit pattern as the basis for mixing. Think “identity-ish at the bit level,” then still passed through the runtime mixer with the map seed.

**Strings**

String hashing walks the bytes and mixes them with a fast **memhash** family. Interviewers often say **aeshash** for historical and platform-specific reasons. The stable idea: **not** “first byte only,” **not** “length only,” but a **full-byte mixing** hash.

**Structs**

Structs hash **field by field** in order. Field boundaries matter. Two different structs with different types or different layouts are not interchangeable keys just because their human-readable print looks similar.

---

## 5. Key Rules & Behaviors

### Same key always produces the same hash

Within one map’s lifetime and hashing context, the same key value must keep mapping to the same bucket choice logic. If you mutate a key **in place** where mutation is possible, you break the map. That is why **string** keys are safe as immutable byte sequences, but **slice** headers are not valid keys.

**In plain English:** The map remembers where it put your entry using the key’s hash. Change the key’s bits after insertion and you orphan the entry.

### Different keys can produce the same hash

Collision is **normal**. It is not proof of a bad hash by itself. It is proof you compressed a big world into a smaller index.

**In plain English:** Two people can get the same locker number in a broken gym system. In a good map system, the locker is a **small bin** that can hold multiple name tags.

### Load factor crosses Go’s threshold and the map grows

When buckets get too full on average, Go allocates a bigger table and **rebalances** entries.

**In plain English:** If every drawer is stuffed, you buy a wider cabinet and redistribute cards.

### Only comparable types can be map keys

Map keys must be **comparable** because equality decides “is this the same entry.” Slices, maps, and functions are not comparable for map keys.

**In plain English:** The map must answer “is this the same key?” Slices point at data; comparing the headers is not what people mean by slice equality in this context, and the language disallows it.

### Go uses a per-map random seed for hashing

The seed defeats collision attacks that rely on knowing exact bucket placement.

**In plain English:** You cannot cheaply precompute a million keys that all slam the same drawer on purpose.

---

## 6. Code Examples (Show, Don't Tell)

### Toy hash with modulo

This is **pedagogical**, not “Go’s real map hash.”

```go
package main

import "fmt"

func toyHash(s string, buckets int) int {
	h := 0
	for i := 0; i < len(s); i++ {
		h = h*31 + int(s[i])
	}
	if buckets <= 0 {
		return 0
	}
	// remainder picks an index; negative h in real life needs care
	return ((h % buckets) + buckets) % buckets
}

func main() {
	fmt.Println(toyHash("go", 8))
	fmt.Println(toyHash("no", 8))
}
```

ASCII mapping:

```
MEMORY TRACE:

Step 1: call toyHash("go", 8) — string data @0x10_7000 ('g'=0x67,'o'=0x6F)
  stack: frame toyHash — s string header (ptr,len) ──→ 0x10_7000, len=2; buckets=8; h=0
  heap: (string bytes live in read-only / string backing; ptr in header points @0x10_7000)
  shared memory: @0x10_7000 ──→ [0x67, 0x6F]

Step 2: loop i=0 — h = 0*31 + int('g') = 103
  stack: h = 103 (accumulator in toyHash frame)
  heap: (unchanged)
  shared memory: (string bytes as above)

Step 3: loop i=1 — h = 103*31 + int('o') = 3304
  stack: h = 3304
  heap: (unchanged)
  shared memory: (unchanged)

Step 4: return ((3304 % 8) + 8) % 8 = 0  ◄── toy bucket index for "go" (key → h → h % buckets → index)
  stack: return value 0 to main’s print path
  heap: (unchanged)

Step 5: call toyHash("no", 8) — @0x10_7010 ('n'=0x6E,'o'=0x6F)
  stack: h: 0→110→3521; return 3521 % 8 = 1
  shared memory: @0x10_7010 ──→ [0x6E, 0x6F]

Step 6: compare indices — 0 vs 1 (this run: different buckets). If h2 % 8 == h % 8, both keys land in same bucket ◄── collision case for this pedagogical hash
  stack: (two return values consumed by fmt.Println)
  heap: (no map; hash is pure arithmetic)
```

### Collision demonstration with ASCII

Assume buckets = 4.

```
MEMORY TRACE:

Step 1: toyHash("ab", 4) — 'a','b' ──→ h = 3105 ──→ bucket = 3105 % 4 = 1
  stack: h=3105; buckets=4
  shared memory: "ab" bytes @0x10_7100
  heap: (toy table not allocated yet)

Step 2: toyHash("cd", 4) — 'c','d' ──→ h = 3169 ──→ bucket = 3169 % 4 = 1
  stack: h=3169; bucket index 1
  shared memory: "cd" bytes @0x10_7110
  ◄── AHA: distinct keys, same bucket index ⇒ collision

Step 3: toy map bucket 1 @0xC0_1000 (conceptual two-slot story)
  heap:
    tophash: [t_ab|t_cd]
    keys:    ["ab"|"cd"]
    values:  [10|20]
    overflow* ──→ nil
  stack: (lookup will hold running index / hash scratch)

Step 4: lookup "cd" — hash("cd") ──→ bucket 1 ──→ scan keys[] — compare "cd" — return 20
  stack: return value 20
  heap: bucket 1 unchanged
  ◄── aha: chain or parallel arrays; equality disambiguates colliding keys
```

### Why slices cannot be map keys

```go
package main

func main() {
	// var m map[[]int]int
	// invalid: []int is not comparable
	_ = 0
}
```

Compiler error you should expect:

```
invalid map key type []int
```

```
MEMORY TRACE:

Step 1: hypothetical map[[]int]int — key type is slice header (ptr,len,cap) @stack 0xE0_0010
  stack: would hold slice triples as keys
  heap: (no hmap — type invalid)
  shared memory: (n/a at compile fail)
  ◄── comparability required for map keys; []int is not comparable in Go

Step 2: type checker rejects before any heap hmap — no bucket array allocated
  stack: compile error; no runtime frame
  heap: (none for this declaration)

Step 3: why slice header is the wrong equality object — two headers @0xE0_0020 vs @0xE0_0030 can point at same backing array @0xC0_2000 with different len
  heap: backing array @0xC0_2000 shared by two different (ptr,len,cap) views
  ◄── aha: map needs stable key identity; slice “value” is a triple, not deep array contents — slices can’t be map keys
```

Structs inherit the same rule when a field is not comparable:

```go
package main

type S struct {
	X []int
}

func main() {
	var _ map[S]string
}
```

Expected failure:

```
invalid map key type S
```

```
MEMORY TRACE:

Step 1: struct S layout — field X is []int; inner slice header embedded in S @0xE0_0040
  stack: local S would carry nested slice header (ptr,len,cap) inside struct bytes
  heap: (backing array of X could live here if constructed)
  shared memory: (n/a for type check)

Step 2: map[S]string — key type S must be fully comparable; comparability does not propagate if any field fails
  stack: (type checker only)
  heap: (no map allocated)
  ◄── AHA: one []int field poisons whole struct for map keys (same slice rule)

Step 3: compiler error before runtime — no hash(seed,S) / bucket placement ever runs
  heap: (no hmap for invalid key type)
  stack: (no runnable main frame past type error)
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

```go
package main

import "fmt"

func main() {
	m := map[string]int{}
	m["a"] = 1
	m["b"] = 2
	x := m["a"]
	y := m["missing"]
	fmt.Println(x, y)
}
```

```
MEMORY TRACE:

Step 1: m := map[string]int{} — runtime allocates empty hmap @0xC0_3000, buckets* may be nil/small
  stack: m map header (ptr to hmap) @0xE0_00F0
  heap: hmap @0xC0_3000 — count=0, buckets* small or lazy
  shared memory: (no keys yet)

Step 2: m["a"] = 1 — hash(seed,"a") ──→ H ──→ bucket i — place in cell: tophash/keys/values updated; count++
  stack: temporaries for hash + index
  heap: bucket @0xC0_3100 gains slot: tophash[k], keys[k]="a", values[k]=1
  shared memory: "a" @0x10_7200

Step 3: m["b"] = 2 — hash(seed,"b") ──→ H' ──→ bucket i' — second cell (same or different bucket vs "a")
  stack: same pattern as Step 2
  heap: another slot filled; count=2
  shared memory: "b" @0x10_7202

Step 4: x := m["a"] — hash(seed,"a") ──→ same i as insert ──→ scan tophash/keys ──→ key equal "a" ──→ x = 1
  stack: x = 1 @0xE0_0100
  heap: unchanged
  shared memory: "a" for compare

Step 5: y := m["missing"] — hash(seed,"missing") ──→ bucket ──→ scan: no equal key ──→ y = 0 (zero value)
  stack: y = 0 @0xE0_0108
  heap: unchanged (no insert)
  shared memory: "missing" literal @0x10_7210
  ◄── aha: missing key returns value-type zero; no panic
```

> [!success]- Answer
> Prints `1 0`.
>
> Reading a missing key returns the **zero value** for the value type. For `int`, that is `0`.

### Tier 2: Fix the Bug (5 min)

```go
package main

import "fmt"

func main() {
	keys := [][]int{{1, 2}, {3, 4}}
	m := map[[]int]string{}
	for _, k := range keys {
		m[k] = "x"
	}
	fmt.Println(len(m))
}
```

```
MEMORY TRACE:

Step 1: keys := [][]int{...} — outer slice header @0xE0_0200; elements point at rows @0xC0_4000, @0xC0_4040
  stack: keys (ptr,len,cap) @0xE0_0200
  heap: backing arrays for {1,2} and {3,4}
  shared memory: (n/a)

Step 2: m := map[[]int]string{} — key type []int (non-comparable)
  stack: (no valid map value — compile fails)
  heap: (no hmap constructed)
  shared memory: (n/a)
  ◄── compile error: []int not comparable — compiler stops; len(m) never reached

Step 3: (if it compiled) k from range — each k is slice header ──→ hash(seed, ptr,len,cap) ──→ bucket index; deep array equality not used
  stack: loop var k per iteration
  heap: would store entries keyed by header bits — wrong model vs “same elements”
  ◄── aha: language forbids []int keys; slices can’t be map keys
```

> [!success]- Answer
> This does not compile. **Slices are not comparable**, so `[]int` cannot be a map key type.
>
> Typical fixes use a comparable surrogate key:
>
> ```go
> package main
>
> import "fmt"
>
> func main() {
> 	m := map[string]string{}
> 	m["1,2"] = "x"
> 	m["3,4"] = "x"
> 	fmt.Println(len(m)) // 2
> }
> ```
>
> Or use a string key, a struct of scalars, or `map[string]...` derived from encoding. Pick a key that matches your equality semantics.

---

## 7. Gotchas & Interview Traps

**Hash flooding**

Attackers or buggy inputs can create many colliding keys if the hash is predictable. Go’s **seeded** hashing is the mitigation story. If someone asks “why not a super simple hash,” the honest answer is **distribution** plus **security tradeoffs**.

**Non-comparable key types**

Interviewers mention slices, maps, functions. **Structs containing non-comparable fields** are also invalid as map keys. The rule propagates.

**Map iteration order**

Iteration order is **not** the sorted order of keys. It is **not** insertion order. Do not rely on order. This behavior is tied to map internals and **randomization** goals.

**“Hash mod buckets” oversimplification**

You can say “hash reduces to bucket index” as a story. If pressed, admit Go uses **bit tricks** tied to **two-sized growth** and **incremental evacuation** in real implementations.

**aeshash naming**

Treat **aeshash** as shorthand for “fast hardware-friendly mixing on some platforms,” not a promise you can name every instruction on every GOARCH.

---

## 8. Interview Gold Questions (Top 3)

**Question 1:** What is a hash function in the context of a hash table, and why must it be deterministic?

**Strong answer shape:** A hash function maps keys to indices in a bounded range. Determinism ensures lookups follow the same path as inserts. Mention **uniformity** and **avalanche** as quality metrics.

**Question 2:** What happens on collision, and how does Go’s map handle overflow?

**Strong answer shape:** Collision means two keys map to the same bucket. Go uses **buckets with multiple cells** and **overflow buckets** chained when needed, keeping searches local and bounded per bucket.

**Question 3:** Why does Go require comparable map keys, and name three types that are disallowed?

**Strong answer shape:** Keys need **equality** for lookup semantics. Disallowed examples: **slice**, **map**, **function**. Mention structs only work if **all fields** are comparable.

---

## 9. 30-Second Verbal Answer

A hash function turns a key into a bucket hint fast and deterministically. A good hash spreads keys evenly and flips many output bits when the input tweaks slightly. Collisions are normal, so the table uses buckets that hold multiple entries and chains overflow when buckets fill. Go keeps average occupancy around a threshold near **six and a half entries per bucket** before growing. Map keys must be comparable so equality is well-defined, which excludes slices, maps, and functions. Go also seeds map hashing to reduce collision attacks.

---

> See **Glossary** for term definitions.
