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
KEY "go" -----> HASH FUNCTION -----> huge integer H
                                         |
                                         | keep low bits / mask
                                         v
                               BUCKET INDEX i  (which row of drawers)
                                         |
                                         v
                 +-----------------------+-----------------------+
                 |  BUCKET i             |  overflow chain     |
                 |  [k0,v0][k1,v1]...    |----> next bucket    |
                 +-----------------------+-----------------------+
```

Collision in one picture:

```
KEY "go"  --hash-->  ...10110110...  --index-->  bucket 6
KEY "no"  --hash-->  ...00110110...  --index-->  bucket 6   (same bucket: collision)

Inside bucket 6 (conceptual):
  slot0: "go" -> 1
  slot1: "no" -> 2
  slot2: empty
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
key A:  ...0000001000...  -->  hash: ...1110100110...
key B:  ...0000001001...  -->  hash: ...0011011001...
              ^one bit flip          many bits flip
```

### 4.2 Collisions: inevitable, designed for

A hash maps a **large** key space into a **smaller** index space. **Pigeonhole principle:** some distinct keys **must** share outputs. Your implementation’s quality shows up in **how often** and **how badly** collisions cluster, and in **how you resolve** them.

### 4.3 Collision resolution: chaining vs open addressing

**Chaining**

Each bucket holds **multiple entries**. If a bucket fills, you add **overflow storage** linked from the first bucket. Think “drawer got full, attach a **satellite drawer**.”

```
bucket 3:  [a][b][c] ---> overflow ---> [d][e]
```

**Open addressing**

Every entry lives **in the table array itself**. On collision, you **probe** for another empty cell using a rule such as linear probing, quadratic probing, or double hashing.

```
try index 3: occupied
try index 4: occupied
try index 5: empty  <-- insert here
```

**What Go does**

Go’s map is **not** “one slot per key with probing across the whole table” in the classic open-addressing sense. It uses **buckets** that each hold **eight key/value cells** in current implementations. Overflow buckets chain when a bucket runs out of room. So the mental model for interviews: **bucket-level chaining** with **in-bucket placement** rules.

Interview-safe one-liner:

```
hash --> pick bucket --> small fixed arena (bucket) --> overflow chain if needed
```

### 4.4 Load factor: fullness vs growth

**Load factor** means “how crowded the table is.” One common textbook definition:

```
load factor = number_of_entries / number_of_buckets
```

High load factor means **more collisions** and **longer chains** unless you resize.

**Go’s trigger**

Go grows the map when the **average entries per bucket** crosses about **6.5**. That number is an implementation detail, but it is the usual **interview answer** for “when does a Go map grow?”

ASCII before and after growth:

```
Before growth, crowded:
buckets: 4
entries: 22
avg per bucket ~ 5.5
This toy average is only a sketch. Real growth decisions use finer internal bookkeeping.

After growth, roomier:
buckets: 8
entries: 22
avg per bucket ~ 2.75
```

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
"go" --> toy hash h --> h mod 8 --> bucket index
"no" --> toy hash h2 --> h2 mod 8 --> maybe same as "go"
```

### Collision demonstration with ASCII

Assume buckets = 4.

```
toyHash("ab", 4) -> 1
toyHash("cd", 4) -> 1   (collision at bucket 1)

bucket 1 chain or cells:
  entry1: "ab" -> 10
  entry2: "cd" -> 20
```

Lookup path:

```
key "cd" --> hash --> bucket 1 --> scan bucket 1 --> find "cd"
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

ASCII reason:

```
slice header = (ptr, len, cap)
              ^
              two slices can point at same data; header compare is the wrong model
              language forbids the footgun
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
