# Arrays & Slice Internals — Interview Questions

#qa #go #interview

Back to: [[Arrays & Slice Internals]]

A compact bank of Go array and slice questions, ordered from most to least common at high-signal (FAANG and Go-heavy) companies.

---

## Q1: What's the difference between an array and a slice in Go? [COMMON]

**Answer:**

**In one line:** An array is a fixed-size, value-typed block of elements; a slice is a small dynamic descriptor (pointer, length, capacity) that refers to a backing array.

**Visualize it:**

```
ARRAY [5]int on stack or as value     SLICE: header + optional heap array
+---+---+---+---+---+                 header (stack):  ptr, len, cap
| 0 | 0 | 0 | 0 | 0 |  (size fixed)          |
+---+---+---+---+---+                        v
    type includes "5"                 +---+---+---+ ... backing array
                                      |   |   |   |
Size is part of the type.             +---+---+---+
Comparing two [5]int is allowed
(if comparable elements).
```

**Key facts:**
- `array [N]T` has `N` baked into the type; two arrays differ in type if `N` differs.
- Slices are reference-like: copying a slice copies the header, not the whole sequence.
- Arrays are passed by value (full copy) unless you use a pointer; slices pass the 24-byte header cheaply.
- Slices are the idiomatic way to work with variable-length data in Go.

**Interview tip:** State clearly that the array length is a type parameter, so `[3]int` and `[4]int` are different types. Then connect slices to the backing array and shared mutation.

> [!example]- Full Story: Arrays fix size; slices are flexible views
>
> **The problem:** You need to explain why Go has both, and when each shows up in APIs, memory, and the type system.
>
> **How it works:** Arrays hold elements inline (or in the array value) with a compile-time or constant size. Slices are implemented as a struct: pointer to first element, `len`, and `cap`. The slice’s “variable length” is the `len` field; capacity is how many elements exist in the backing array from that pointer forward.
>
> **What to watch out for:** Conflating “array” with “list.” In Go, only slices give you the familiar grow/shrink and sub-range behavior; arrays are for fixed, often small, buffers (hashes, coordinates, small matrices).

---

## Q2: What is the internal representation of a Go slice? [COMMON]

**Answer:**

**In one line:** A slice is a three-field struct: pointer to the backing array, length, and capacity (typically 24 bytes on 64-bit); passing a slice copies that header, not the elements.

**Visualize it:**

```
slice header (value, copied on pass)
+------------------+----------------+---------------+
| data *T (8B)     | len int (8B)  | cap int (8B)  |
+------------------+----------------+---------------+
         |
         v
backing array:  [e0, e1, e2, ... e_{cap-1}]
                 ^<---- len valid ---->
                 ^<---------- cap reserved -------->
```

**Key facts:**
- The official mental model: `struct { ptr unsafe.Pointer; len, cap int }` (element type determines stride).
- `len` is how many elements you may read with `s[i]`. `cap` is how many exist from `ptr` without stepping past the allocation.
- Assigning or passing a slice duplicates the header; two slices can share one backing array.
- Growing beyond `cap` requires a new array (see `append`).

**Interview tip:** Draw the three fields first, then the backing array, then “copy header vs share data.” If asked about 32-bit, note smaller pointer width changes header size but not the model.

> [!example]- Full Story: The slice header and shared backing
>
> **The problem:** You need to explain why slice parameters are cheap, why two variables can “see” the same data, and why `len` can differ between them.
>
> **How it works:** The runtime and compiler treat the slice as that triple. Indexing and bounds checks use `len`. `append` may write between `len` and `cap-1` if there is room, or grow. GC keeps the whole backing array alive while any slice header points into it.
>
> **What to watch out for:** Forgetting that `s[:0]` can leave a huge backing array live if a sub-slice is saved but the “rest” of the data is unneeded. Also confusing “slice is reference” with “slice is a reference type” in the Java sense. Go’s slice is a small struct with a pointer inside.

---

## Q3: What happens when you pass a slice to a function and modify it? [COMMON]

**Answer:**

**In one line:** Writes to elements within the shared backing array are visible to the caller, but reassigning `len`/`cap` or replacing the `data` pointer in the callee only updates a local copy of the header unless you return a new slice or use a pointer to slice.

**Visualize it:**

```
caller: s1  ----header copy---->  func param s2
                 same ptr ----------------->   backing array
                                                    [2][3][4]
Update s2[i] (in range)  -----------------------> both see change

s2 = append with room     updates s2's len only  caller's len unchanged
s2 = append, must grow     new array; s2 points there; s1 may still
                           point at OLD array
```

**Key facts:**
- Index assignment `f(s); ... func f(x []T) { x[0] = 99 }` is visible: same underlying storage.
- `len` and `cap` in the function are the parameter’s own fields. Appending in the callee can leave the caller with a shorter `len` and stale “view” of growth.
- If `append` reallocates, the callee’s slice may point to new memory; the caller’s slice still points at the old array until reassigned.
- For mutating the slice “identity” (length, re-slice) as seen by the caller, return `[]T` or use `*[]T`.

**Interview tip:** Give the two-sentence story: (1) same backing = shared element updates; (2) header is by value, so `append` and reslicing the parameter do not update the caller’s header without a return or pointer.

> [!example]- Full Story: Shared array vs copied header
>
> **The problem:** A candidate said “slices are passed by reference” and got contradicted by a question about `append` not updating the caller.
>
> **How it works:** The slice value is passed by value (the header). That value contains a pointer. Mutating `*ptr` through the pointer is visible. Mutating the header fields in the callee is not.
>
> **What to watch out for:** Suggesting `func f(s *[]T)` for normal code. It is valid for APIs that must resize the slice in place, but idiomatic code usually returns a new `[]T` from the function that may grow.

---

## Q4: How does the `append` function work? What happens when capacity is exceeded? [COMMON]

**Answer:**

**In one line:** `append` writes into the backing array from `len` if there is spare capacity, updating `len`; if not, it allocates a larger array, copies old elements, then appends, and the new slice’s pointer and capacity point at the new storage.

**Visualize it:**

```
Before:  cap=4 len=2   [A][B][ | spare ][ spare ]
        append: room in cap -> write C at index 2, new len=3, same array

After cap exceeded:
old [A][B][C][D]  --copy-->  new [A][B][C][D][?][?]...  (bigger; size class)
caller must use returned slice: s = append(s, x)
```

**Key facts:**
- The contract is: always use `s = append(s, e)` — even if capacity is sufficient, the return value is the authoritative header with the updated length.
- If `len < cap`, new elements are placed in `[len:cap)` and `len` increases.
- If more room is needed, a new array is allocated, length grows, and the old array becomes collectable if nothing references it.
- The growth algorithm (Go 1.18+) is documented in the runtime; capacity increases follow size-class rules after the formula (see Q12 in this set for growth details).

**Interview tip:** Always mention “assign the result of append to the same variable.” That leads naturally into the append trap question.

> [!example]- Full Story: Append and reallocation
>
> **The problem:** Explain why a loop that `append`s without assignment can silently drop data or use the wrong underlying array.
>
> **How it works:** `append` returns a new slice header. The compiler rewrites the call and may optimize, but the semantic rule is: use the returned slice. When reallocating, the algorithm picks a new `cap` (see growth formula), copies `min(old.len+1, etc.)` bytes of elements, and returns a slice with updated `len` and new `cap`.
>
> **What to watch out for:** Holding on to a slice with `cap` exactly equal to `len` in a long-running loop. Each `append` may allocate. Preallocate with `make([]T, 0, n)` when `n` is known.

---

## Q5: Explain the “append trap” — why does the caller not see appended elements? [COMMON]

**Answer:**

**In one line:** The callee receives a copy of the slice header; it updates its own `len` (and maybe `data`/`cap` after grow), so the caller’s header still has the old length and pointer until you return the slice and reassign.

**Visualize it:**

```
caller: s  len=2 cap=2  -->  [A][B]
         |
         | pass by value (header copy)
         v
callee: s  same ptr, len=2
append(s, C)  -> reallocate, callee s now len=3, new array
caller's s still len=2, old ptr  -->  [A][B]   (or dangling view)

Fix:  s = f(s)   or   return s from f
```

**Key facts:**
- The trap often appears in helpers like `addItem(s, x)` that `append` but do not return `[]T`.
- If `append` fits in `cap`, the callee can increase `len` on the copy, but the caller’s `len` still does not change: the caller will not “see” new elements in range loops using their own `s`.
- Correct patterns: `s = add(s, x)` where `add` returns the result of `append`, or pass `*[]T` for in-place growth (less idiomatic in application code).
- The append trap and “must assign append” are the same class of gotcha.

**Interview tip:** State that the bug is a stale `len` in the caller, not a failure of the backing array. Then give the one-line fix: return and reassign.

> [!example]- Full Story: Stale len after append
>
> **The problem:** After `f(s)` that appends, `s` in main still looks unchanged when printed with `len` or when ranged.
>
> **How it works:** `append` returns a new slice. If you ignore the return in the helper, the caller’s binding is never updated. Even when no reallocation happens, the callee’s header `len` changed on a copy, not on the caller’s variable.
>
> **What to watch out for:** Suggesting that `append` must always allocate. The trap is about assignment and header copies, not only allocation.

---

## Q6: What is a `nil` slice vs an `empty` slice, and when do they differ in practice? [COMMON]

**Answer:**

**In one line:** A `nil` slice has a nil data pointer and `len == cap == 0`; a non-nil “empty” slice has a non-nil data pointer to a real (sometimes zero-size) array allocation, also with `len == 0`, and they serialize differently in some APIs (e.g. JSON).

**Visualize it:**

```
nil:     ptr=nil, len=0, cap=0
         +------+-----+-----+
         | null |  0  |  0  |
         +------+-----+-----+

empty:   ptr -> valid pointer (may point to zerobase for cap 0)
         +--------+
         |  (no)  |  len=0, cap=0, but 'sptr' is non-nil
         +--------+
         append/len both fine;  json: [] vs null (encoding/json)
```

**Key facts:**
- `var s []int` and `s == nil` is true. `s := []int{}` or `make([]int, 0)` is not nil, though both have length 0.
- In most code, `len`/`cap` and `for range` treat them the same. `== nil` distinguishes them.
- `encoding/json`: `nil` encodes to `null`, non-nil empty slice to `[]`.
- `reflect` and some CGo boundaries care about the pointer; prefer matching your API’s expectations.

**Interview tip:** Mention JSON when the interviewer works on APIs. Mention `== nil` when the question is about comparison or map keys of slices (slices are not map keys, but the distinction often appears next to that discussion).

> [!example]- Full Story: Nil pointer vs empty length
>
> **The problem:** Tests fail because `null` was expected in JSON, or a database driver treats `nil` slice as SQL NULL.
>
> **How it works:** The extra word in the header is the data pointer. No allocation for `var s []T`. Sometimes `[]T{}` still avoids heap allocation; implementation details are compiler-specific, but the pointer bit is what matters to `== nil` and to some encoders.
>
> **What to watch out for:** Using `s == nil` to mean “no result.” Sometimes you want a non-nil empty slice for stable API shape; sometimes you need `nil` for “absent” in wire formats. Document the contract.

---

## Q7: How does `make([]T, len)` differ from `make([]T, 0, cap)?` [COMMON]

**Answer:**

**In one line:** `make([]T, len)` sets both length and capacity to `len` and gives you that many zero-valued, addressable elements; `make([]T, 0, cap)` is length-0 with reserved capacity, so you start with an empty “view” but room for `append` without reallocation up to `cap`.

**Visualize it:**

```
make([]int, 5)          make([]int, 0, 5)
len=5 cap=5            len=0 cap=5
+--+--+--+--+--+        backing: [ _ _ _ _ _ ]
|0 |0 |0 |0 |0 |              ^
indices 0..4 valid     no index valid yet; append adds from 0
```

**Key facts:**
- `make([]T, n)` is equivalent in capacity to `make([]T, n, n)`.
- `make([]T, 0, n)` is the usual pattern when you know an upper bound and want to `append` in a loop.
- `s[i]` is only valid for `i < len`, not for reserved capacity beyond `len`.
- Zero length with extra capacity is how you avoid N reallocations in builders.

**Interview tip:** Contrast with `new([n]T)` and slicing a full array if you go deeper; for interviews, the “5 zeros vs 0 length with 5 reserved slots” story is enough.

> [!example]- Full Story: Length vs capacity in make
>
> **The problem:** A `bytes.Buffer`-style loop reallocated on every `append` because the slice was created with `[]byte{}` and no preallocation.
>
> **How it works:** `len` is what the language considers “present” for `range` and `len`. `cap` is the allocation bound from the slice’s pointer. `append` can grow `len` without a new array until `len == cap` (then reallocation, unless a larger cap was reserved).
>
> **What to watch out for:** `make([]T, n, m)` with `m < n` is invalid. Also, confusing `new`+slice of full array with `make` for clarity.

---

## Q8: How do you safely copy a slice? Why is assignment not enough? [COMMON]

**Answer:**

**In one line:** Assignment copies the header only, so two variables alias the same backing array; a deep, independent copy uses `copy(dst, src)` into a new slice or `slices.Clone` in Go 1.21+ (which allocates and copies for you).

**Visualize it:**

```
a := s        (assignment)
s ----\
       \--->  [1][2][3]   a and s share

b := make([]T, len(s))
copy(b, s)  ----->  [1][2][3]  independent storage

slices.Clone(s)  --> new allocation + copy (idiomatic 1.21+)
```

**Key facts:**
- `copy` copies the minimum of `len(dst)` and `len(src)` elements.
- Slicing: `d := s[2:4]` is still a view; not a copy of elements.
- For structs containing slices, a shallow copy of the struct still shares inner slices; use `copy` or clone per field if ownership matters.
- `slices.Clone` documents that it returns a new slice with the same `len` and `cap == len` and new backing store.

**Interview tip:** If they ask about concurrency, add that copying the slice header is not a data race if two goroutines only read; but mutating the same backing array from two goroutines without synchronization is still racy.

> [!example]- Full Story: Aliasing vs true copy
>
> **The problem:** Mutating a “copy” in one place breaks another use of the data because they share storage.
>
> **How it works:** The slice is a small struct. `=` duplicates it. `copy` (or a loop) duplicates elements. For pointer elements, you still have shared pointed-to data unless you clone deeply.
>
> **What to watch out for:** Using `append([]T(nil), s...)` as a one-liner clone pre-1.21; it is fine but easy to get wrong for nil. Prefer `slices.Clone` in new code for clarity.

---

## Q9: When should you use an array instead of a slice? [COMMON]

**Answer:**

**In one line:** Use fixed-size arrays when the length is a stable part of the problem (hashes, fixed coordinates, small matrices, protocol fields) to get stack allocation, no extra indirection, and comparable value semantics where needed.

**Visualize it:**

```
[32]byte digest        vs    []byte of len 32
on stack, value         heap backing + slice header, dynamic identity
[3]byte RGB
comparable, pass by value, map key (if all comparable sub-fields)

[...]T composite literal: compiler infers array length
```

**Key facts:**
- Arrays with suitable size can live on the stack; helps hot paths. Slices are still idiomatic for most variable-length I/O.
- Arrays are comparable if the element type is comparable; you can use `[k]K` as a `map` key, unlike `[]T`.
- `[n]T` in struct provides fixed padding known to the compiler.
- A pointer to a large array (e.g. `*[1<<20]byte`) is often worse than a slice; arrays are for small, fixed, known `n`.

**Interview tip:** Name `[32]byte` for SHA-256 and `[3]uint8` for RGB. Mention that large arrays in structs bloat value copies, so a pointer to array or a slice is sometimes better for big buffers.

> [!example]- Full Story: Fixed shape vs dynamic sequence
>
> **The problem:** A map needs keys that are 64-byte public keys, or you want a zero-allocation 3-vector on the stack in a game or graphics loop.
>
> **How it works:** Array length is part of the type, so `[64]byte` and `[65]byte` are different types. For slices, the length is a runtime int on the value.
>
> **What to watch out for:** Passing huge arrays by value. That copies the whole value; use a pointer, slice, or re-design.

---

## Q10: What is the three-index slice expression, and when do you use it? [ADVANCED]

**Answer:**

**In one line:** `a[low:high:max]` sets the resulting slice’s capacity to `max - low` (not `cap(a) - low`), capping `append` so it cannot clobber data past `max` in the shared backing array.

**Visualize it:**

```
full:  [0 1 2 3 4 5 6]   cap=7
a[1:4:4]  -> starts at 1, len=3 (indices 1,2,3), cap=3-0? no:
low=1 high=4 max=4
len = high-low = 3
cap = max-low = 3   (so append has no room: next append will allocate)

Without max:  a[1:4] would cap=6, appends could overwrite index 4,5,6...
```

**Key facts:**
- The third index is the maximum in the *underlying array’s* index space, exclusive: full slice expression `s[lo:hi:max]`.
- After `a[1:4:4]`, `cap` is `3`, so a single `append` without growth cannot happen in-place from that slice; you get a new array, protecting neighbors.
- The full form requires `0 <= lo <= hi <= max <= cap(a)`.
- Used when sharing a backing array but handing out a “safe window” to another piece of code.

**Interview tip:** Pair this with the “append overwrites after len” class of bug. Show a concrete overwrite scenario if the interviewer looks unconvinced.

> [!example]- Full Story: Limiting capacity for safety
>
> **The problem:** A sub-slice of a big buffer is passed to a parser that `append`s, corrupting the rest of the buffer.
>
> **How it works:** The two-index form sets `cap` to the end of the parent’s accessible region from `lo`. The three-index form shortens that so `append` cannot fill past `max-1` without reallocating.
>
> **What to watch out for:** You still must not race with concurrent writers; this is a logical isolation tool, not synchronization.

---

## Q11: How does sub-slicing work, and what is the memory leak risk? [ADVANCED]

**Answer:**

**In one line:** A sub-slice reuses the same backing array and keeps the entire array alive; holding a small sub-slice to a sliver of a huge buffer pins the full allocation until the sub-slice is gone.

**Visualize it:**

```
big := make([]byte, 1<<20)
window := big[0:8]  // only 8 bytes "used" logically

GC graph:
window ----->  [  1 MiB object still live  ]  (cannot reclaim)
drop big ref; 'window' alone keeps 1 MiB

fix:  small := make([]byte, 8)
      copy(small, big[0:8])   // or slices.Clone(big[0:8])
      // big can be collected if unreferenced
```

**Key facts:**
- `s[lo:hi]` shares the backing array; `cap` is usually `cap(s) - lo` in the 2-index form, so a big tail may remain in capacity.
- The leak is “logical” from holding references, not a GC bug.
- `copy` into a new slice, `append([]T(nil), s...)`, or `slices.Clone` (Go 1.21+) to shrink retention.
- Three-index slicing can also reduce `cap` to avoid accidental append overwrites, but GC retention depends on the pointer: if `cap` still spans a huge object, the whole object stays.

**Interview tip:** Mention `strings` vs `[]byte` when discussing headers and substrings; same pinning idea for `string` headers (substring shares backing byte array in modern Go for subslices of a string, but the story is for slice in this file).

> [!example]- Full Story: Pinning a giant backing store
>
> **The problem:** A server caches 8-byte message IDs from a 100 MB read buffer. Memory use stays at 100 MB per cached ID.
>
> **How it works:** Slices are pointers with length. GC marks the object containing all bytes reachable from the pointer in `Data`. No partial collection of a single allocation in the usual runtime model.
>
> **What to watch out for:** Reslicing to “shrink” without `copy` does not shrink live memory if `cap` still includes unused tail you no longer need; three-index and `copy` both address different aspects (overwrite vs lifetime).

---

## Q12: What is the slice growth formula in modern Go (1.18+)? [ADVANCED]

**Answer:**

**In one line:** `nextslicecap` in `runtime/slice.go` doubles `oldCap` while it is below 256; if `oldCap` is still below `newLen` after doubling, it uses `newLen` when `newLen` exceeds `2*oldCap`; otherwise, for `oldCap >= 256` it increases `newcap` in a loop with `newcap += (newcap + 3*256) >> 2` until the capacity fits `newLen` (a smooth move from 2x toward the large-slice growth style), then `growslice` rounds up to a size class.

**Visualize it:**

```
nextslicecap(newLen, oldCap):
  if newLen > 2*oldCap  --------->  return newLen   (big jump, e.g. one-off huge append)
  if oldCap < 256        --------->  return 2*oldCap
  else loop:
         newcap += (newcap + 3*256) >> 2     // i.e. (newcap + 768) / 4
         until newcap >= newLen
  (then growslice rounds to allocator size class)
```

**Key facts:**
- The threshold is 256: below it, the next capacity is `2 * oldCap` (after the `newLen` vs `2*oldCap` check at the top of `nextslicecap`).
- At and above 256, each loop iteration does `newcap += (newcap + 3*256) / 4` (shift-right by 2), not a single closed-form multiply; the loop runs until `newcap` is large enough for the requested `newLen`.
- `growslice` then rounds `newcap` to a size class (`roundupsize`); the `cap` you read in user code is after that rounding, not the raw `nextslicecap` value.
- Rely on `len` and your own `make` for correctness; use `append` in a loop with assignment; never hard-code assumptions about the numeric `cap` return from `append`.

**Interview tip:** Say you would verify exact constants in the installed `GOROOT` if asked in a take-home, but for an onsite, the threshold and the shift from 2x to sublinear are the intended takeaway.

> [!example]- Full Story: From doubling to sublinear
>
> **The problem:** Someone prints `cap` after a few appends, sees non-power-of-two numbers, and claims standard libraries are “wrong.”
>
> **How it works:** The `newLen > 2*oldCap` branch avoids repeated doublings when a single `append` requires a huge step. The loop with `(newcap + 3*threshold) >> 2` is the smooth transition the runtime comments refer to, between the small-slice 2x rule and a milder growth rate for large backing arrays. After `nextslicecap`, `growslice` runs allocation rounding.
>
> **What to watch out for:** Basing application logic on the exact `cap` after one `append`. Only `len` and explicit `make` are stable contracts; `cap` is an implementation and rounding detail.

---

## Q13: What is the memory layout of a slice of structs vs a slice of pointers to structs? [ADVANCED]

**Answer:**

**In one line:** `[]Struct` stores elements contiguously, each struct value inline, which is cache-friendly and avoids extra indirection; `[]*Struct` is a slice of pointers, with each element pointing to possibly scattered heap objects, so iteration may incur more cache misses and pointer-chasing but can be cheaper to move or share one large struct from many sites.

**Visualize it:**

```
[]struct{ a,b int }          []*struct{ a,b int }
+---+---+---+---+---+         +------+  +------+
| s0| s1| s2| s3|...|         | ptr0 |  | ptr0 |---> { } on heap
+---+---+---+---+---+         +------+  +------+
|cache line friendly|         | ptr1 |  | ptr1 |---> (maybe far)
| one allocation for array|  +------+
```

**Key facts:**
- `[]T` for large `T` can mean copying big struct values on re-slice or `append` if the grown array copies. Measure.
- `[]*T` can share a single `T` from many places and allows `nil` to mean “optional.”
- For read-heavy, dense iteration over small-mid `T`, `[]T` is often faster.
- For interface-heavy graphs or many optional entries, `[]*T` is idiomatic but has GC pointer scan costs.

**Interview tip:** Mention false sharing in parallel programs if the interviewer is systems-oriented: two goroutines on adjacent small structs in one slice can ping cache lines. Splitting with padding or by careful layout is a follow-up.

> [!example]- Full Story: Density vs indirection
>
> **The problem:** A hot loop over 1M items is slow with `[]*Item` and faster with `[]Item` on benchmarks.
>
> **How it works:** CPUs prefetch sequential memory. A slice of structs is an array; iteration is predictable. A slice of pointers may point all over the heap.
>
> **What to watch out for:** A huge `T` in `[]T` making copies expensive when passed by value. Also, mutating shared `*T` from many slices: aliasing and races.

---

## Q14: How would you implement a `filter` on a slice without allocating a new backing array? [TRICKY]

**Answer:**

**In one line:** Use two indices (read and write), compact kept elements in place from the front of the slice, then reslice to the new `len` (and optionally nil out remaining slots to release pointers for GC).

**Visualize it:**

```
[i j ...]
 r w
 move if pred(s[r]): s[w]=s[r]; w++; r++
 else: r++ only
 end:  return s[:w]

[ A X B X C ]  ->  [A B C] [X X]   (optional: nil the X slots if *T)
        ^w
```

**Key facts:**
- Time O(n), extra space O(1) aside from a few index ints.
- Order of kept elements is usually preserved; if you do not need stability, you can use different read strategies.
- If `T` is a pointer and you drop some elements, nil `s[i]` in the now-unused tail before losing references so GC can collect pointed objects.
- The returned length may be much smaller; `cap` may still be large (same backing array as before).

**Interview tip:** Say you only avoid a *new* allocation; the original allocation remains sized to old `cap`. If you need a smaller final footprint, a new, tight allocation is needed.

> [!example]- Full Story: In-place compaction
>
> **The problem:** A pipeline filters 90% of events and must not allocate a second multi-meg slice per batch.
>
> **How it works:** The w/r walk compacts in one pass, preserving relative order of survivors if coded that way. Deleting in a tight loop is the same family of problem.
>
> **What to watch out for:** Concurrent readers while you compact; and interfaces containing pointers if you do not nil the dead tail.

---

## Q15: How do you delete an element from a slice, and what is the “pointer leak” trap? [TRICKY]

**Answer:**

**In one line:** Shift elements with copy or a loop, then reslice; if the element type is or contains pointers, zero the now-unused last slot (or all freed slots) before shrinking `len` so the GC can reclaim heap objects the slice used to hold.

**Visualize it:**

```
s: [A][B][C][D]  delete B at 1
shift: copy(s[1:], s[2:])   ->  [A][C][D][D]  (duplicate tail)
s = s[:len-1]              ->  [A][C][D]
nil last if []*T: s[len-1] = nil  before reslice (or set whole tail if needed)
         otherwise old D reference kept in hidden slot
```

**Key facts:**
- `append(s[:i], s[i+1:]...)` is a common idiom; be careful to use the return value in case of reallocation in some other variants (this pattern may zero differently by version, but the pointer issue remains).
- After `s = s[:n-1]`, index `n-1` in the full backing array can still store the old pointer, keeping a large object alive. Setting it to the zero value fixes it.
- For non-pointer values, the leak is moot, but the duplicate value may still be visible if you reslice with wrong bounds.
- `slices` package in newer Go may offer helpers, but the interview is testing manual reasoning.

**Interview tip:** Frame it as: “reslice shortens the logical view; capacity tail can hide pointers.” That signals production Go experience.

> [!example]- Full Story: Hidden references after delete
>
> **The problem:** A cache slice of `*Big` has elements removed, but `runtime.MemStats` or heap profiles still show `Big` objects.
>
> **How it works:** A slice of pointers is a slice of pointer slots. Dropping the logical length does not clear slots beyond the new `len` that still exist in the `cap` region if you are not careful. Even at `len-1` after a delete-by-shift, a leftover duplicate pointer can remain in the one overlapping slot; nil-ing matters for the released element’s referent in some shift algorithms.
>
> **What to watch out for:** The exact slot to nil depends on shift strategy; the invariant is: no live pointer in backing array to objects you no longer want retained.

---

