# P04 Hash Functions & Hashing Basics

> **Prerequisite note** — complete this before starting [[T08 Map Internals]].
> Estimated time: ~15 min

---

## 1. Concept

A **hash function** takes any key (a string, a number, anything) and turns it into a number. That number decides **which bucket** to look in. Same key always gives the same number.

That's it. That's the whole idea behind every `map[string]int` in Go.

> **In plain English:** Imagine a school with 8 classrooms. Every new student gets assigned a classroom based on their name: take the letters, do some math, get a number between 0 and 7. "Rahul" always gets classroom 3. "Priya" always gets classroom 6. Now when someone asks "where is Rahul?" — you don't check all 8 rooms. You do the math, get 3, walk straight there.

---

## 2. Core Insight (TL;DR)

**Hashing turns "search everywhere" into "jump to the right spot."** Without hashing, finding a key in 1 million entries means checking up to 1 million entries. With hashing, you jump to one bucket and check maybe 5-10 entries.

**Collisions are normal.** Two different keys CAN land in the same bucket. That's not a bug. The bucket just holds multiple entries, and you scan the small list inside.

**Go's map** uses this: hash the key, pick a bucket, scan 8 slots inside that bucket.

---

## 3. Mental Model (Lock this in)

Think **apartment building with 8 floors**. You're the doorman assigning people to floors.

- A new tenant arrives: you take their name, run your "floor formula," and get a floor number (0-7).
- "Rahul" → floor 3. "Priya" → floor 6. "Amit" → floor 3. (Same floor as Rahul — that's a collision. No big deal, floor 3 has room for both.)
- When someone visits looking for Amit: run the formula → floor 3 → go to floor 3 → check the names on that floor → found.

```
The apartment building:

Floor 0: [ empty ]
Floor 1: [ "Priya" → 100 ]
Floor 2: [ empty ]
Floor 3: [ "Rahul" → 42 | "Amit" → 77 ]   ◄── collision! Two people, same floor. That's fine.
Floor 4: [ empty ]
Floor 5: [ "Neha" → 55 ]
Floor 6: [ empty ]
Floor 7: [ "Deepak" → 88 ]

Lookup "Amit":
  formula("Amit") → 3 → go to floor 3 → scan: "Rahul"? no. "Amit"? YES → return 77
```

**Error-driven: what if the formula was bad?**

```
BAD formula (just uses first letter: A=0, B=1, ...):

Floor 0: [ "Amit", "Ankit", "Arjun", "Aarav", "Aditya", "Akash"... ]  ◄── ALL A-names pile up!
Floor 1: [ empty ]
Floor 2: [ empty ]
...

Now looking for "Akash" means scanning 50 people on floor 0.
That's basically the same as no hash at all.
A GOOD hash spreads people evenly across all floors.
```

> **In plain English:** Collisions aren't disasters — they mean "same floor." The hash function's job is to spread people across floors so no single floor gets overcrowded.

---

## 4. How It Works

### 4.1 Four properties of a good hash function

Interviewers love this question. Remember it as: **"DFUA" — Deterministic, Fast, Uniform, Avalanche.**

**Deterministic** — Same key, same number. Every time. If "Rahul" gives you 3 today and 5 tomorrow, you'll never find Rahul again.

**Fast** — Every map read and write runs the hash function. If it's slow, every `m["key"]` is slow.

**Uniform distribution** — Keys should spread evenly across all buckets. If 80% of your keys land in bucket 0, you've basically built a linked list, not a hash map.

**Avalanche effect** — Changing one tiny bit of the key should completely change the output. If "cat" → 5 and "bat" → 5, that's bad. Similar keys should NOT get similar bucket numbers.

```
Good avalanche:
  "cat" → hash → 481729
  "bat" → hash → 937164   ◄── totally different number. Good.

Bad avalanche:
  "cat" → hash → 481729
  "bat" → hash → 481730   ◄── almost the same. Bad! Similar keys clump together.
```

> **In plain English:** A good hash is like a blender — even a tiny change in input makes the output look completely different.

---

### 4.2 Collisions: completely normal, not a bug

You're mapping a huge world (every possible string) into a small space (8 buckets). Of course two different keys will sometimes land in the same bucket. This is the **pigeonhole principle**: if you have 100 pigeons and 8 holes, some holes will have multiple pigeons.

The question isn't "do collisions happen?" — they always do. The question is **how you handle them**.

---

### 4.3 How Go handles collisions: buckets with 8 slots + overflow chains

Go's approach is simple:

1. Each bucket holds **8 key-value pairs** (not just 1)
2. If all 8 slots are full, Go attaches an **overflow bucket** (like adding an extra drawer)
3. To find a key: hash it → pick the bucket → scan up to 8 slots → if not found, follow overflow chain

```
MEMORY TRACE:

Step 1: m := make(map[string]int) — Go creates the map structure
  heap:
    hmap ──→ [ count: 0 | buckets ──→ [bucket0][bucket1]...[bucket7] ]
                                        each bucket has 8 slots

Step 2: m["Rahul"] = 42
  hash("Rahul") → some big number → bucket index: 3
  heap:
    bucket 3: [ slot0: "Rahul"→42 | slot1: empty | ... | slot7: empty ]

Step 3: m["Amit"] = 77
  hash("Amit") → some big number → bucket index: 3   ◄── same bucket as Rahul!
  heap:
    bucket 3: [ slot0: "Rahul"→42 | slot1: "Amit"→77 | slot2: empty | ... ]
              ◄── both fit. Bucket has 8 slots, only 2 used. No problem.

Step 4: bucket fills up — all 8 slots occupied, new key also hashes to bucket 3
  heap:
    bucket 3: [ slot0..slot7: all full ] → overflow ──→ [ new bucket with 8 more slots ]
              ◄── chain extends. Lookup must follow the chain. Still fast if chains are short.

Step 5: lookup m["Amit"]
  hash("Amit") → bucket 3 → scan slot0: "Rahul"? no → slot1: "Amit"? YES → return 77
```

> **In plain English:** Each floor of the apartment has 8 rooms. If all 8 are taken, you build a small extension. When someone visits, they go to the right floor and check rooms one by one. With only 8 rooms per floor, that's fast.

---

### 4.4 Load factor: when does the map grow?

**Load factor** = total entries / total buckets. It measures how full the map is.

- **Low load factor** (few entries, many buckets): fast lookups, wasted memory.
- **High load factor** (many entries, few buckets): overflow chains get long, lookups get slow.

**Go's trigger:** When the average entries per bucket crosses about **6.5**, Go doubles the number of buckets and redistributes all entries.

```
BEFORE growth (4 buckets, 26 entries):
  avg = 26/4 = 6.5 per bucket   ◄── threshold hit!
  bucket 0: [8 slots full] → overflow → [2 more]
  bucket 1: [8 slots full]
  bucket 2: [6 slots used]
  bucket 3: [2 slots used]

AFTER growth (8 buckets, same 26 entries):
  avg = 26/8 = 3.25 per bucket   ◄── much roomier
  Each entry gets re-hashed into the new 8-bucket layout.
  Overflow chains shrink or disappear.
```

> **In plain English:** When every floor is packed, you build a taller building with more floors and move everyone to their new floor assignment. The formula changes slightly because there are more floors now.

---

### 4.5 Go-specific hashing details (interview extras)

**Per-map random seed** — Every map gets a random number mixed into its hash function. This prevents attackers from crafting millions of keys that all land in the same bucket (hash-flooding attack).

**String hashing** — Go walks through all bytes of the string and mixes them. On modern CPUs with AES hardware, Go uses **aeshash** for speed. The interview-safe answer: "Go hashes all bytes of the string with a fast runtime hash function seeded per map."

**Integer hashing** — Integer keys use their bit pattern as the basis, mixed with the map seed.

**Struct hashing** — Structs hash field by field. If any field isn't comparable (like a slice), the struct can't be a map key.

---

## 5. Key Rules & Behaviors

### Same key → same bucket (deterministic)

```go
m := map[string]int{}
m["hello"] = 1
fmt.Println(m["hello"]) // 1 — hash("hello") gives the same bucket both times
```

> **In plain English:** You asked the doorman "which floor is hello on?" twice. Same answer both times. If it wasn't, the map would be broken.

---

### Different keys CAN land in the same bucket (collision)

```go
m := map[string]int{}
m["Rahul"] = 42
m["Amit"] = 77  // might hash to the same bucket — that's fine
```

> **In plain English:** Two tenants on the same floor. Normal. The floor has 8 rooms.

---

### Only comparable types can be map keys

Go needs `==` to work on keys (to check "is this the same key?"). These types are NOT comparable and CANNOT be map keys:
- **Slices** (`[]int`, `[]string`)
- **Maps** (`map[string]int`)
- **Functions** (`func()`)

```go
// var m map[[]int]string  // COMPILE ERROR: invalid map key type []int
```

```
MEMORY TRACE:

Why slices can't be keys:

  s1 := []int{1, 2, 3}
  s2 := []int{1, 2, 3}

  stack:
    s1 ──→ [ ptr: 0xA000 | len: 3 | cap: 3 ]   ──→ backing array [1, 2, 3]
    s2 ──→ [ ptr: 0xB000 | len: 3 | cap: 3 ]   ──→ backing array [1, 2, 3]

  Same contents, but different backing arrays.
  Should s1 == s2? Go says: "I refuse to answer. Slices aren't comparable."
  Without clear equality, hashing is meaningless. So: no slice keys.
```

> **In plain English:** The doorman needs to answer "is this the same person?" If two people show up with photocopies of the same ID but different originals, the doorman can't tell. So Go bans them as map keys.

---

### Map never iterates in the same order

```go
m := map[string]int{"a": 1, "b": 2, "c": 3}
for k, v := range m {
    fmt.Println(k, v)  // order changes between runs!
}
```

> **In plain English:** The doorman shuffles the guest list every time you ask. This is intentional — Go randomizes iteration order so you never accidentally depend on it.

---

### Per-map random seed prevents attacks

```go
m1 := map[string]int{}
m2 := map[string]int{}
// m1 and m2 have DIFFERENT seeds
// same key might hash to different buckets in each map
```

> **In plain English:** Each apartment building has its own secret floor-assignment formula. An attacker who figured out building 1's formula can't use it against building 2.

---

## 6. Code Examples (Show, Don't Tell)

### How a simple hash function works

This is a toy example to show the concept. Go's real hash is much fancier.

```go
func toyHash(name string, numBuckets int) int {
    total := 0
    for _, ch := range name {
        total = total*31 + int(ch)
    }
    return total % numBuckets
}

func main() {
    fmt.Println(toyHash("Rahul", 8))  // some number 0-7
    fmt.Println(toyHash("Priya", 8))  // some number 0-7
    fmt.Println(toyHash("Rahul", 8))  // same as first — deterministic
}
```

```
MEMORY TRACE:

Step 1: toyHash("Rahul", 8)
  Walk each character, multiply and add:
    'R' (82):  total = 0*31 + 82 = 82
    'a' (97):  total = 82*31 + 97 = 2639
    'h' (104): total = 2639*31 + 104 = 81913
    'u' (117): total = 81913*31 + 117 = 2539420
    'l' (108): total = 2539420*31 + 108 = 78722128

Step 2: bucket = 78722128 % 8 = 0
  "Rahul" always lands in bucket 0 (for 8 buckets)

Step 3: toyHash("Priya", 8)
  Same math with different letters → different total → bucket = 5
  "Priya" lands in bucket 5

Step 4: toyHash("Rahul", 8) again
  Same input → same math → same total → same bucket 0   ◄── deterministic
```

---

### Collision in action

```go
// Suppose both "Rahul" and "Kiran" hash to bucket 3
m := map[string]int{}
m["Rahul"] = 42
m["Kiran"] = 99
fmt.Println(m["Kiran"]) // 99
```

```
MEMORY TRACE:

Step 1: m["Rahul"] = 42
  hash("Rahul") → bucket 3
  heap:
    bucket 3: [ slot0: "Rahul"→42 | slot1: empty | ... | slot7: empty ]

Step 2: m["Kiran"] = 99
  hash("Kiran") → bucket 3   ◄── collision! Same bucket.
  heap:
    bucket 3: [ slot0: "Rahul"→42 | slot1: "Kiran"→99 | slot2: empty | ... ]
              ◄── both stored. Bucket has room for 8 entries.

Step 3: lookup m["Kiran"]
  hash("Kiran") → bucket 3
  scan: slot0 key="Rahul" → not a match
        slot1 key="Kiran" → MATCH → return 99
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

```go
m := map[string]int{}
m["a"] = 1
m["b"] = 2
fmt.Println(m["a"])
fmt.Println(m["c"])
```

> [!success]- Answer
> Prints:
> ```
> 1
> 0
> ```
> `m["a"]` finds the key and returns 1. `m["c"]` doesn't exist, so Go returns the zero value for `int`, which is `0`. No panic. Reading a missing key is safe.

### Tier 2: Fix the Bug (5 min)

```go
type User struct {
    Name    string
    Friends []string  // slice field!
}

var cache map[User]int  // what's wrong?
```

> [!success]- Answer
> **Won't compile.** `User` has a `[]string` field (slice), which makes `User` non-comparable. Non-comparable types can't be map keys.
>
> Fix options:
> 1. Use a comparable key: `map[string]int` (key by `Name`)
> 2. Remove the slice field from the key struct
> 3. Create a separate key type: `type UserKey struct { Name string }` and use `map[UserKey]int`

---

## 7. Gotchas & Interview Traps

| Trap | What happens | What to say |
|------|-------------|-------------|
| "Hash functions never collide" | Wrong. Collisions are mathematically guaranteed | "Collisions are normal. The map resolves them with multi-slot buckets and overflow chains." |
| Slice as map key | Compile error | "Slices aren't comparable. Use a string or struct of comparable fields." |
| Relying on map iteration order | Order changes between runs | "Go randomizes iteration order. Sort keys if you need stable order." |
| "Go uses open addressing" | Not exactly | "Go uses 8-slot buckets with overflow chaining. It's closer to chaining than classic open addressing." |
| Hash flooding attack | Attacker crafts keys that all collide | "Go seeds each map with a random value, preventing predictable collisions." |

---

## 8. Interview Gold Questions (Top 3)

**Q1: What is a hash function and why must it be deterministic?**

A hash function maps a key to a bucket index. It must be deterministic because if "Rahul" hashes to bucket 3 during insert but bucket 5 during lookup, you'll never find the value. Mention that good hashes also spread keys evenly (uniform distribution) and change output drastically for small input changes (avalanche effect).

**Q2: What happens when two keys hash to the same bucket?**

That's a collision. Go handles it by storing up to 8 key-value pairs per bucket. If a bucket fills up, it chains an overflow bucket. Lookup scans the bucket sequentially, comparing keys. Because buckets are small (8 entries), this stays fast.

**Q3: Why can't slices be map keys in Go?**

Map keys need the `==` operator to determine "is this the same key?" Slices, maps, and functions aren't comparable in Go. Even a struct with a single slice field becomes non-comparable. Use a string, integer, or all-comparable-fields struct instead.

---

## 9. 30-Second Verbal Answer

A hash function takes a key and turns it into a bucket number — same key always gives the same number. A good hash spreads keys evenly across buckets so no single bucket gets overcrowded. Collisions happen when two different keys land in the same bucket — that's normal, not a bug. Go's map handles collisions with 8-slot buckets and overflow chains. When the average entries per bucket hits about 6.5, Go doubles the buckets and redistributes. Map keys must be comparable — no slices, maps, or functions. Each map gets a random seed to prevent hash-flooding attacks.

---

> See [[Glossary]] for term definitions.
