> **Reading Guide**: Sections 1-3 and 6 are essential first read (20 min).
> Sections 4-5 deepen understanding (15 min).
> Sections 7-12 are interview-specific — read closer to interview day.
> Section 13 is your comprehensive interview Q&A bank → [[questions/T04 Arrays & Slice Internals - Interview Questions]]
> Something not clicking? → [[simplified/T04 Arrays & Slice Internals - Simplified]]

---

## 1. Concept

An **array** in Go is a fixed-size list. The size is part of the type — `[3]int` and `[5]int` are completely different types that cannot be swapped.

A **slice** is a lightweight "window" into an array. It doesn't own the data — it just describes where to look: a pointer to the start, how many elements are visible (length), and how much room exists (capacity).

Most Go code uses slices, not arrays.

> **In plain English:** An array is a row of boxes bolted to the floor — you can't add more boxes. A slice is a sticky note that says "look at boxes 3 through 7 on that shelf." The sticky note is cheap to copy. The shelf is the real data.

---

## 2. Core Insight (TL;DR)

**A slice is NOT the data. It is a 24-byte "window descriptor" that sits on top of an array.**

Three fields, that's all:

```
┌──────────────────────────────────────┐
│  Slice Header (24 bytes on 64-bit)   │
├──────────┬──────────┬────────────────┤
│ pointer  │  length  │   capacity     │
│ (8 bytes)│ (8 bytes)│  (8 bytes)     │
└────┬─────┴──────────┴────────────────┘
     │
     ▼
┌────┬────┬────┬────┬────┬────┐
│ e0 │ e1 │ e2 │ e3 │  _ │  _ │  ◄── backing array in memory
└────┴────┴────┴────┴────┴────┘
 ◄── visible (len=4) ──►
 ◄────── available (cap=6) ──────►
```

Two things will bite you if you don't internalize this:
1. **`append` can move the data to a new array** — only the returned slice knows where the new array is
2. **Copying a slice copies the window, not the data** — two slices can look at the same array

> **In plain English:** Think of a slice as a TV remote with three buttons: "where does the channel list start", "how many channels am I showing", and "how many channels could I show before I need a bigger list." The remote is tiny and cheap to duplicate — but every copy of the remote still controls the same TV.

---

## 3. Mental Model (Lock this in)

**Array = a brick.** Fixed size, fixed shape. Copy it and you get a completely independent second brick.

**Slice = a sticky note on a whiteboard.** The sticky note says "look at columns 3 through 7." The whiteboard is the real data. Many sticky notes can point at the same whiteboard. Sometimes `append` runs out of whiteboard space and copies everything to a bigger whiteboard — but only the sticky note that `append` returns knows about the new whiteboard.

### See it — arrays are independent copies

```go
a := [3]int{10, 20, 30}
b := a         // full copy of all 3 elements
b[0] = 999
fmt.Println(a) // [10 20 30] — a is untouched
fmt.Println(b) // [999 20 30]
```

```
MEMORY:

a  ──→  stack: ┌────┬────┬────┐
               │ 10 │ 20 │ 30 │   ◄── a's own memory
               └────┴────┴────┘

b := a copies ALL bytes into a new independent block:

b  ──→  stack: ┌─────┬────┬────┐
               │ 999 │ 20 │ 30 │   ◄── b's own memory (separate)
               └─────┴────┴────┘

Changing b[0] only touches b's memory. a doesn't know, doesn't care.
```

### See it — slices share the backing array

```go
s := []int{10, 20, 30}
t := s         // copies the 24-byte header, NOT the elements
t[0] = 999
fmt.Println(s) // [999 20 30] — s sees the change!
fmt.Println(t) // [999 20 30]
```

```
MEMORY:

s header: [ ptr | len=3 | cap=3 ]──┐
                                    ▼
                          heap: ┌─────┬────┬────┐
                                │ 999 │ 20 │ 30 │
                                └─────┴────┴────┘
                                    ▲
t header: [ ptr | len=3 | cap=3 ]──┘

Both s and t point to the SAME backing array.
t[0] = 999 writes to that shared array → s sees it too.
```

### The mistake that teaches you value semantics forever

```go
func tryToModify(arr [3]int) {
    arr[0] = 999  // modifies the LOCAL copy only
}

func main() {
    a := [3]int{10, 20, 30}
    tryToModify(a)
    fmt.Println(a) // [10 20 30] — unchanged!
}
```

```
MEMORY TRACE:

main():
  a  ──→  stack: ┌────┬────┬────┐
                 │ 10 │ 20 │ 30 │
                 └────┴────┴────┘

tryToModify(a) — Go copies ALL 3 elements onto the function's own stack:

tryToModify():
  arr ──→ stack: ┌────┬────┬────┐   ◄── brand new copy, costs O(n)
                 │ 10 │ 20 │ 30 │
                 └────┴────┴────┘

  arr[0] = 999:
  arr ──→ stack: ┌─────┬────┬────┐
                 │ 999 │ 20 │ 30 │   ◄── only THIS copy changes
                 └─────┴────┴────┘

Function returns → its stack frame is gone.
main's 'a' was never touched. The 999 dies with the function.
```

**Now contrast — pass a slice and modify it:**

```go
func modifySlice(s []int) {
    s[0] = 999  // modifies the SHARED backing array
}

func main() {
    a := []int{10, 20, 30}
    modifySlice(a)
    fmt.Println(a) // [999 20 30] — changed!
}
```

```
MEMORY TRACE:

main():
  a header: [ ptr=0xc000 | len=3 | cap=3 ]
                    │
                    ▼
          heap: ┌────┬────┬────┐
                │ 10 │ 20 │ 30 │
                └────┴────┴────┘

modifySlice(a) — Go copies the 24-byte HEADER only (cheap!):

modifySlice():
  s header: [ ptr=0xc000 | len=3 | cap=3 ]   ◄── copy of header
                    │
                    ▼
          heap: ┌────┬────┬────┐              ◄── SAME backing array!
                │ 10 │ 20 │ 30 │
                └────┴────┴────┘

  s[0] = 999 → writes through the pointer to shared memory:

          heap: ┌─────┬────┬────┐
                │ 999 │ 20 │ 30 │             ◄── main's 'a' will see this
                └─────┴────┴────┘

Back in main: a[0] is now 999.
```

> **In plain English:** Passing an array to a function is like handing someone a photocopy of your document — they can scribble all over it, your original is safe. Passing a slice is like handing someone the address of your house — they walk in and rearrange your furniture, and you come home to the changes.

---

## 4. How It Actually Works (Internals)

### 4.1 The slice struct in the runtime

Under the hood, a slice is this struct (from `src/runtime/slice.go`):

```go
type slice struct {
    array unsafe.Pointer  // address of element 0
    len   int             // how many elements you can read
    cap   int             // how many elements exist from that pointer
}
```

On a 64-bit machine: 8 + 8 + 8 = **24 bytes**. That's all that gets copied when you pass a slice to a function.

- **`array`** (pointer): points at element index 0 of the backing array for this slice's view. After re-slicing, this may not be the original allocation's start.
- **`len`**: count of elements you can index — valid indices are `0` to `len-1`. Accessing `s[len]` panics.
- **`cap`**: total elements available from the pointer onward. This is the room for `append` before reallocation kicks in.

When you pass a slice to a function, Go copies these 24 bytes. The copy still points to the same backing array — that's why element modifications are visible across function boundaries, but `append` that reallocates creates a new array that only the callee sees.

> **In plain English:** The slice header is like a library card that says "Shelf B, books 3 through 7, shelf holds 20 books total." Photocopying the card doesn't duplicate the books.

### 4.2 Array internals

An array `[N]T` is literally `N * sizeof(T)` bytes. There's no header, no pointer — the variable IS the data.

```
[3]int on a 64-bit machine:

Total size = 3 x 8 = 24 bytes

Memory: ┌──────────┬──────────┬──────────┐
        │ int (8B) │ int (8B) │ int (8B) │
        └──────────┴──────────┴──────────┘
        ◄──────── 24 bytes ──────────────►
```

Key rules:
- `[3]int` and `[4]int` are **different types**. You cannot assign one to the other.
- Copying or passing an array copies **every single element**. No sharing, ever.

```go
var a [3]int
var b [4]int
a = b // COMPILE ERROR: cannot use b (type [4]int) as type [3]int
```

> **In plain English:** An array's size is literally part of its name tag. A box-of-3 and a box-of-4 are different products — you can't swap them any more than you can return a 6-pack when you bought an 8-pack.

### 4.3 What `make` and literals do

**`make([]T, length, capacity)`** — allocate and build a slice:

```go
s := make([]int, 3, 5)
```

```
What happens step by step:
1. Runtime allocates a backing array of 5 ints (40 bytes) on the heap
2. Zeros all 5 slots
3. Returns a 24-byte header on the stack: [ ptr → backing | len=3 | cap=5 ]

Memory (with addresses):
  stack 0xC000060000: s header
    [ ptr=0xC000080000 | len=3 | cap=5 ]    ← 24 bytes on the stack
           │
           ▼
  heap 0xC000080000: backing array (40 bytes)
    ┌──────────┬──────────┬──────────┬──────────┬──────────┐
    │ 0 (8B)   │ 0 (8B)   │ 0 (8B)   │ 0 (8B)   │ 0 (8B)   │
    └──────────┴──────────┴──────────┴──────────┴──────────┘
    0x...80000  0x...80008  0x...80010  0x...80018  0x...80020
      ◄──── visible (len=3) ────►
      ◄──────────── available (cap=5) ──────────────►

  How s[i] finds the element:
    s[0] → ptr + 0*8 = 0xC000080000 → valid (within len)
    s[1] → ptr + 1*8 = 0xC000080008 → valid
    s[2] → ptr + 2*8 = 0xC000080010 → valid
    s[3] → ptr + 3*8 = 0xC000080018 → panic (index >= len), but slot exists (within cap)
    s[5] → ptr + 5*8 = 0xC000080028 → panic: index out of range (beyond cap)
```

**Slice literal `[]T{...}`** — creates a backing array and a header over it:

```go
s := []int{10, 20, 30}  // equivalent to: make + fill
// len=3, cap=3, backing array holds [10, 20, 30]
```

If you omit capacity from `make`, it defaults to length: `make([]int, 5)` gives `len=5, cap=5`.

### 4.4 Growth algorithm — what happens when `append` runs out of room (Go 1.18+)

When `append` needs more space than `cap` allows, Go allocates a new, bigger backing array and copies everything over. The old array becomes garbage.

**The growth formula:**

| Old capacity | Growth rule                              | Approximate multiplier |
|-------------|------------------------------------------|----------------------|
| < 256       | Double it: `newcap = oldcap * 2`         | 2.0x                 |
| >= 256      | `newcap = oldcap + (oldcap + 768) / 4`   | ~1.3x to ~1.6x      |

After computing `newcap`, the runtime rounds up to fit the memory allocator's size classes (predefined bucket sizes that reduce fragmentation).

**Watch it grow — real example:**

```go
s := make([]int, 0)
for i := 0; i < 10; i++ {
    s = append(s, i)
    fmt.Printf("len=%-2d  cap=%d\n", len(s), cap(s))
}
```

```
Output (approximate, 64-bit):
len=1   cap=1    ← started at 0, grew to 1
len=2   cap=2    ← doubled from 1
len=3   cap=4    ← doubled from 2
len=4   cap=4
len=5   cap=8    ← doubled from 4
len=6   cap=8
len=7   cap=8
len=8   cap=8
len=9   cap=16   ← doubled from 8
len=10  cap=16
```

**What happens at len=5 (cap jumps from 4 to 8):**

```
BEFORE append(s, 4):
  stack 0xC000060000: s = [ ptr=0xC000080000 | len=4 | cap=4 ]
                                   │
                                   ▼
  heap 0xC000080000: ┌───┬───┬───┬───┐
                     │ 0 │ 1 │ 2 │ 3 │   ◄── FULL (len == cap)
                     └───┴───┴───┴───┘

  append needs 1 more slot but cap is maxed out...

  Step 1: Allocate new array at 0xC000090000 with cap=8 (64 bytes)
  Step 2: Copy elements 0,1,2,3 from 0x...80000 to 0x...90000
  Step 3: Write element 4 at 0xC000090000 + 4*8 = 0xC000090020
  Step 4: Return NEW header → overwrite s at 0xC000060000

AFTER:
  stack 0xC000060000: s = [ ptr=0xC000090000 | len=5 | cap=8 ]
                                   │
                                   ▼
  heap 0xC000090000: ┌───┬───┬───┬───┬───┬───┬───┬───┐
                     │ 0 │ 1 │ 2 │ 3 │ 4 │ _ │ _ │ _ │
                     └───┴───┴───┴───┴───┴───┴───┴───┘

  OLD array at 0xC000080000 → no references → GC eligible
```

**Historical note (pre-1.18):** The old formula doubled below 1024, then grew by 1.25x above 1024. The current formula uses 256 as the threshold with a smoother transition. Don't rely on exact capacity values in code — they can change between Go versions.

> **In plain English:** When your bookshelf is full and you need to add one more book, Go doesn't squeeze — it buys a bigger shelf, moves all books over, and throws away the old shelf. The new shelf is roughly double the size (for small collections) so you don't have to move again too soon.

---

## 5. Key Rules & Behaviors

### Rule 1: Slice headers copy by value. Backing arrays share by pointer.

```go
s := []int{1, 2, 3}
t := s       // t gets its own copy of the header
t[0] = 999   // but both headers point to the same array → s sees the change
```

> **In plain English:** Two remotes, same TV. Change the channel from one remote, the other remote sees it too.

### Rule 2: Valid indices are `0` to `len-1`. Period.

```go
s := make([]int, 3, 10)
s[3] = 5  // PANIC — even though cap is 10, len is 3
```

```
  s: [ ptr | len=3 | cap=10 ]
            │
            ▼
  heap: ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
        │ 0 │ 0 │ 0 │ _ │ _ │ _ │ _ │ _ │ _ │ _ │
        └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
          ◄─ ok ──►│ ◄─── exists but can't touch ──►
                   ↑
               s[3] = PANIC here
```

The slots from `len` to `cap-1` exist in memory but you cannot touch them until `len` grows via `append`.

> **In plain English:** A hotel booked 10 rooms on a floor, but only handed out keys to 3 guests. Guest #4 can't walk in just because the room exists — they need to be checked in first (via `append`).

### Rule 3: `append` might stay in place, or might move everything

```
If len < cap  →  stays in place, writes to next slot, increments len
If len == cap →  allocates new array, copies everything, returns new header
```

This is why you **always** write `s = append(s, x)`:

```go
// WRONG — append's return value is thrown away
func addItem(s []int, item int) {
    append(s, item)  // if realloc happens, caller never sees it
}

// RIGHT — return the new header
func addItem(s []int, item int) []int {
    return append(s, item)
}
```

**See the disaster in memory:**

```
Caller: s = [ ptr=A | len=3 | cap=3 ]

addItem(s, 42):
  local copy: in = [ ptr=A | len=3 | cap=3 ]

  append needs cap=4 but only has 3 → REALLOCATE

  append returns: [ ptr=B | len=4 | cap=6 ]  ← new array B

  BUT addItem ignores this return value!
  The new header with ptr=B is thrown away.

Back in caller: s is still [ ptr=A | len=3 | cap=3 ]
  The value 42 is sitting in array B... which nobody points to anymore.
  It will be garbage collected. Gone.
```

> **In plain English:** You ask a moving company to add furniture to your house. The house is too small, so they build a new house and put everything there — but if you don't ask for the new address, you'll keep going to the old empty house wondering where your stuff went.

### Rule 4: Three-index slice limits how far `append` can reach

```go
original := []int{0, 1, 2, 3, 4, 5, 6, 7}
//                                          len=8, cap=8

sub := original[2:5]    // sub = [2, 3, 4], len=3, cap=6
safe := original[2:5:5] // safe = [2, 3, 4], len=3, cap=3
```

```
original: ┌───┬───┬───┬───┬───┬───┬───┬───┐
          │ 0 │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │
          └───┴───┴───┴───┴───┴───┴───┴───┘

sub = original[2:5]     (no cap limit)
              ◄── sub ──►◄─ DANGER: append can overwrite 5,6,7 ──►

safe = original[2:5:5]  (cap capped at index 5)
              ◄─ safe ─►|  append MUST reallocate → original is protected
```

The third index caps capacity so `append` on the sub-slice can't silently overwrite elements that belong to the original. Formula: `result len = high - low`, `result cap = max - low`.

> **In plain English:** Without the third index, your sub-slice has a long leash and can scribble into your original's territory. With the third index, you put up a fence — the sub-slice has to get its own paper if it wants to grow.

### Rule 5: `nil` slice vs empty slice — behave the same, but aren't equal

```go
var nilSlice []int          // nil — ptr is nil, len=0, cap=0
emptySlice := []int{}       // NOT nil — ptr is non-nil, len=0, cap=0
madeSlice := make([]int, 0) // NOT nil — same as above

len(nilSlice)  == 0   // true
len(emptySlice) == 0  // true
nilSlice == nil        // true
emptySlice == nil      // false  ← this catches people
```

Both work identically with `append`, `range`, `len`, and `cap`. The difference matters for JSON encoding (`nil` may serialize as `null`, empty as `[]`) and explicit nil checks in API contracts.

> **In plain English:** A nil slice is "I never even thought about this list." An empty slice is "I thought about it, and the answer is: nothing." They look the same from the outside but some systems (like JSON) care about the difference.

### Rule 6: Deleting from a pointer slice can leak memory

When you "remove" an element from `[]*SomeStruct` using slice tricks, the removed pointer can still live in the backing array's unused capacity — keeping the pointed-to object alive for the garbage collector.

```go
users := []*User{alice, bob, charlie}
users = append(users[:1], users[2:]...)  // "remove" bob
// users is now [alice, charlie], len=2, BUT cap=3
// The old slot at index 2 still holds a pointer → GC leak
```

```
Before delete:
  backing: ┌───────┬─────┬─────────┐
           │ alice │ bob │ charlie │    len=3, cap=3
           └───────┴─────┴─────────┘

After append(users[:1], users[2:]...):
  backing: ┌───────┬─────────┬─────────┐
           │ alice │ charlie │ charlie │    len=2, cap=3
           └───────┴─────────┴─────────┘
                                 ↑
                    still points to charlie's memory!
                    GC thinks it's in use. Memory leak.

Fix: nil out the abandoned slot
  users[len(users)] = nil
  backing: ┌───────┬─────────┬─────┐
           │ alice │ charlie │ nil │    now GC can reclaim charlie's old copy
           └───────┴─────────┴─────┘
```

> **In plain English:** You "deleted" a name from your address book by shifting entries up, but the old entry at the bottom of the page is still readable. The mailman (garbage collector) sees it and keeps delivering to that address. Erase it explicitly.

### Rule 7: `copy` copies elements, not headers, and never extends length

```go
src := []int{1, 2, 3, 4, 5}
dst := make([]int, 3)
n := copy(dst, src) // copies min(len(dst), len(src)) = 3 elements
// dst = [1, 2, 3], n = 3
// elements 4 and 5 from src are NOT copied — dst is too short
```

`copy` never grows `dst`. It copies the minimum of both lengths and returns how many it copied.

> **In plain English:** `copy` is like a person manually moving books from one shelf to another. They stop when either shelf runs out of space. They don't build a bigger shelf for you.

---

## 6. Code Examples (Show, Don't Tell)

### 6.1 Array vs slice basics

```go
var a [3]int = [3]int{1, 2, 3}
b := a
b[0] = 9

s := []int{1, 2, 3} // len=3 cap=3
t := s
t[0] = 9
```

```
Step 1: a := [3]int{1,2,3}
  a (value on stack): ┌───┬───┬───┐
                      │ 1 │ 2 │ 3 │
                      └───┴───┴───┘

Step 2: b := a  (full value copy — independent storage)
  a: ┌───┬───┬───┐    b: ┌───┬───┬───┐
     │ 1 │ 2 │ 3 │       │ 1 │ 2 │ 3 │
     └───┴───┴───┘       └───┴───┴───┘

Step 3: b[0] = 9
  a: ┌───┬───┬───┐    b: ┌───┬───┬───┐
     │ 1 │ 2 │ 3 │       │ 9 │ 2 │ 3 │   ◄── a untouched
     └───┴───┴───┘       └───┴───┴───┘

--- slices ---

Step 1: s := []int{1,2,3}
  stack: s at 0xC000060000 = [ ptr=0xC000080000 | len=3 | cap=3 ]
  heap 0xC000080000: [1|2|3]

Step 2: t := s   (copies 24-byte header — same pointer, same backing)
  stack: t at 0xC000060018 = [ ptr=0xC000080000 | len=3 | cap=3 ]
  Both s.ptr and t.ptr = 0xC000080000 → same backing array

Step 3: t[0] = 9
  t.ptr + 0*8 = 0xC000080000 → write 9
  s[0] reads s.ptr + 0*8 = 0xC000080000 → reads 9 (same address!)
  heap 0xC000080000: [9|2|3]
```

### 6.2 Append within vs beyond capacity (the append trap)

**Within `cap` — stays on the same backing array:**

```go
s := make([]int, 0, 4)
s = append(s, 1, 2, 3) // len=3, cap=4, same backing
s = append(s, 4)       // len=4, cap=4, fills it completely
s = append(s, 5)       // len must exceed cap → REALLOCATE
```

```
After appending 1,2,3,4 (all fits within cap=4):
  stack 0xC000060000: s = [ ptr=0xC000080000 | len=4 | cap=4 ]
  heap 0xC000080000: [1|2|3|4]  ◄── full (len == cap)

After append(s, 5) — no room, must reallocate:
  Step 1: New array at 0xC000090000, cap=8
  Step 2: Copy 4 elements from 0x...80000 to 0x...90000
  Step 3: Write 5 at 0xC000090000 + 4*8 = 0xC000090020

  stack 0xC000060000: s = [ ptr=0xC000090000 | len=5 | cap=8 ]   ◄── new pointer
  heap 0xC000090000: [1|2|3|4|5|_|_|_]
  OLD  0xC000080000: [1|2|3|4] → no references → GC eligible
```

**Stale alias — reallocation splits two slices apart:**

```go
a := []int{1, 2, 3} // len=3, cap=3
b := a               // header copy — same backing
a = append(a, 4)     // realloc: a gets NEW backing, b still points to OLD
a[0] = 999
fmt.Println(b[0])    // still 1 — b is looking at the old array
```

```
Before append:
  a = [ ptr=0xC000080000 | len=3 | cap=3 ]
  b = [ ptr=0xC000080000 | len=3 | cap=3 ]   ← same pointer, same backing
  heap 0xC000080000: [1|2|3]

After a = append(a, 4):  (cap full → reallocate)
  a = [ ptr=0xC000090000 | len=4 | cap=6 ]   ← NEW array
  b = [ ptr=0xC000080000 | len=3 | cap=3 ]   ← still OLD array
  heap 0xC000090000: [1|2|3|4|_|_]
  heap 0xC000080000: [1|2|3]  ← kept alive only because b still points here

After a[0] = 999:
  a.ptr + 0*8 = 0xC000090000 → write 999
  heap 0xC000090000: [999|2|3|4|_|_]
  b[0] reads b.ptr + 0*8 = 0xC000080000 → still 1 (different array!)
```

**The classic mistake — ignoring `append`'s return value:**

```go
func bad(in []int) { append(in, 99) }            // WRONG: result thrown away
func good(in []int) []int { return append(in, 99) } // RIGHT: return new header
```

```
Caller: s = [ptr=nil, len=0, cap=0]  at stack 0xC000060000

bad(s):
  local copy 'in' at 0xC000070000 = [ptr=nil, len=0, cap=0]
  append allocates: returns [ptr=0xC000080000, len=1, cap=1]
  ...but bad() drops this return value
  Caller's s at 0xC000060000 is still [ptr=nil, len=0, cap=0] → 99 is lost

good(s):
  same thing, but returns [ptr=0xC000080000, len=1, cap=1]
  Caller does: s = good(s) → s at 0xC000060000 = [ptr=0xC000080000, len=1, cap=1]
  s[0] reads 0xC000080000 → 99 ✓
```

### 6.3 Sub-slice sharing (GC retention + aliasing)

```go
buf := make([]int, 1_000_000) // 1 million ints = ~8 MB
win := buf[0:3]                // tiny 3-element window
buf = nil                      // you THINK you freed the big buffer...
// ...but win still holds a pointer to the SAME 8 MB backing array
// The garbage collector cannot free it
```

```
buf header ──▶ ┌──────────────────────────────────────┐
               │  1,000,000 ints  (~8 MB)             │
               └──────────────────────────────────────┘
win header ──▶      ↑ (same backing, just len=3, cap=1000000)

Even though buf = nil, win keeps the ENTIRE 8 MB alive.

Fix — copy into a tight slice:
  tight := make([]int, 3)
  copy(tight, win)      // copies just 3 elements into a new 24-byte backing
  win = tight           // now the 8 MB array can be garbage collected

OR — use three-index to limit cap:
  win = buf[0:3:3]      // cap=3, not 1000000
  // This doesn't free memory immediately, but append on win will
  // allocate a new small array instead of reusing the 8 MB one
```

### 6.4 `nil` vs empty slice

```go
var n []int          // nil slice
e := []int{}         // empty but non-nil
m := make([]int, 0)  // empty but non-nil
```

```
n:  [ ptr=nil   | len=0 | cap=0 ]   →  n == nil  is true
e:  [ ptr=0xa.. | len=0 | cap=0 ]   →  e == nil  is false
m:  [ ptr=0xb.. | len=0 | cap=0 ]   →  m == nil  is false

All three: len(x)==0 ✓  cap(x)==0 ✓  append works ✓  range works ✓
Difference: nil check, JSON encoding, reflect behavior
```

**JSON encoding difference:**

```go
type Response struct {
    Items []int `json:"items,omitempty"`
}

a := Response{}               // Items is nil
b := Response{Items: []int{}} // Items is empty, non-nil

// json.Marshal(a) → {"items":null} or omits "items" entirely
// json.Marshal(b) → {"items":[]}
// This matters when your API consumer expects [] vs missing field
```

### 6.5 `make([]T, len)` vs `make([]T, 0, cap)`

```go
a := make([]int, 5)    // len=5, cap=5 — can read/write a[0:5] right now
b := make([]int, 0, 5) // len=0, cap=5 — nothing visible yet, append to fill
```

```
a:  ptr▶ ┌───┬───┬───┬───┬───┐   len=5, cap=5
         │ 0 │ 0 │ 0 │ 0 │ 0 │   all accessible now (zero-valued)
         └───┴───┴───┴───┴───┘

b:  ptr▶ ┌───┬───┬───┬───┬───┐   len=0, cap=5
         │ _ │ _ │ _ │ _ │ _ │   backing exists but b[0] panics until len grows
         └───┴───┴───┴───┴───┘
```

**When to use which:**
- `make([]T, n)` — you know the exact size and will fill by index: `s[i] = value`
- `make([]T, 0, n)` — you'll build it with `append` and know roughly how many items to expect

### 6.6 Pointer slice "delete" leak — the full picture

```go
type Node struct{ Name string; Next *Node }

n1 := &Node{Name: "A"}
n2 := &Node{Name: "B"}
n3 := &Node{Name: "C"}

s := []*Node{n1, n2, n3}  // len=3, cap=3
```

**Remove index 1 (n2) — the naive way:**

```go
i := 1
s = append(s[:i], s[i+1:]...)
// s is now [n1, n3], len=2
```

```
Before:
  backing: ┌────┬────┬────┐
  index:   │  0 │  1 │  2 │   len=3, cap=3
  value:   │ *A │ *B │ *C │
           └────┴────┴────┘

After append(s[:1], s[2:]...):
  backing: ┌────┬────┬────┐
  index:   │  0 │  1 │  2 │   len=2, cap=3
  value:   │ *A │ *C │ *C │
           └────┴────┴────┘
                       ↑
            Hidden slot still points to Node "C"!
            (the old *B was overwritten by the shift, but
             the LAST slot duplicated *C instead of being cleared)

  This means the backing array holds an extra reference that
  prevents garbage collection of that Node until the slot
  is overwritten or the entire backing array is freed.
```

**The fix — nil out the tail:**

```go
s[len(s)] = nil  // clear the stale pointer in the hidden capacity
```

### 6.7 Slice interview tricks: filter in-place, reverse, rotate

**Filter in-place (two-pointer compact, O(n) time, O(1) space):**

```go
func keepPositives(s []int) []int {
    w := 0
    for _, v := range s {
        if v > 0 {
            s[w] = v
            w++
        }
    }
    return s[:w]
}
```

```
Input:   [0, 2, 0, 5, 0]   len=5
          r→              (read pointer walks every element)
          w→              (write pointer only advances on positive)

Step by step:
  r=0: 0 is not positive → skip        w stays at 0
  r=1: 2 is positive → s[0]=2, w=1
  r=2: 0 is not positive → skip        w stays at 1
  r=3: 5 is positive → s[1]=5, w=2
  r=4: 0 is not positive → skip        w stays at 2

Result:  [2, 5, 0, 5, 0]   return s[:2] → [2, 5]
                  ↑ ↑ ↑
               stale — don't read past len
               (nil these out if elements are pointers)
```

**Reverse in-place (two-pointer swap):**

```go
func reverse(s []int) {
    for i, j := 0, len(s)-1; i < j; i, j = i+1, j-1 {
        s[i], s[j] = s[j], s[i]
    }
}
```

**Rotate left in-place (3-reverse trick — classic interview pattern):**

To rotate `k` steps left: reverse first k, reverse the rest, reverse all.

```go
func rotLeft(s []int, k int) {
    if len(s) == 0 { return }
    k %= len(s)
    if k < 0 { k += len(s) }
    reverse(s[:k])
    reverse(s[k:])
    reverse(s)
}
```

```
Start:   [A B C D E F], k=2
Step 1:  [B A C D E F]   reverse first 2 elements
Step 2:  [B A F E D C]   reverse remaining 4 elements
Step 3:  [C D E F A B]   reverse entire slice → left rotate by 2 ✓
```

**Memory note:** in-place tricks do NOT shrink `cap`. A huge backing with tiny `len` still retains all that storage until garbage collected. Use three-index or `copy` to an exact-sized slice if memory matters.

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the output (2 min)

**Predict before running** — then verify with `go run` or the [Go Playground](https://go.dev/play/).

```go
package main

import "fmt"

func main() {
	s := make([]int, 0, 2)
	a := s
	s = append(s, 1)
	b := s
	s = append(s, 2)
	c := s
	s = append(s, 3)
	fmt.Println("a:", a, "len", len(a), "cap", cap(a))
	fmt.Println("b:", b, "len", len(b), "cap", cap(b))
	fmt.Println("c:", c, "len", len(c), "cap", cap(c))
	fmt.Println("s:", s, "len", len(s), "cap", cap(s))
}
```

**After you run, trace each header:** Draw four boxes for `a`, `b`, `c`, `s`. Which ones point at the old `cap=2` backing array after the final `append`? The last `append` (adding `3`) is the one that reallocates because `cap=2` is full. Only `s` gets the new header — `a`, `b`, `c` are frozen at their capture time.

### Tier 2: Fix the bug (5 min)

**Buggy** — function appends but reallocation silently loses updates for the caller:

```go
func consume(lines []string, grow []string) {
    lines = append(lines, grow...)
}
```

**Tasks:**
1. Return `[]string` and assign at call site.
2. If keeping only a prefix from a huge buffer, re-slice with three-index to drop backing retention.

### Tier 3: Build it (15 min)

1. **Implement in-place `removeAt(s []T, i int) []T` without leaking pointers.**
2. **Implement `rotate` by reverses (3-reverse trick) in-place.**
3. **Implement safe line reader using `data[:pos:pos]` to prevent append stomp in reused buffer.**

> Full solutions with explanations → [[exercises/T04 Arrays & Slice Internals - Exercises]]

---

## 7. Edge Cases & Gotchas

| # | Gotcha | Why | Fix |
|---|--------|-----|-----|
| 1 | **Append trap** — caller not updated | `append` may allocate a new array; only the returned header knows the new address | Always `s = append(s, x)`. Functions that append must return the new slice. |
| 2 | **Sub-slice retains huge backing array** | A tiny sub-slice still holds a pointer to the original (potentially massive) array. GC can't free any of it. | `copy` into a new `make` slice of exact length, or use three-index `s[low:high:high]` |
| 3 | **Three-index needed to protect originals** | Without a cap limit, `append` on a sub-slice overwrites elements in the original slice | Use `s[low:high:max]` to fence off the sub-slice's capacity |
| 4 | **`nil` vs `[]T{}` semantics differ** | `== nil` returns different results; JSON encoding may differ (`null` vs `[]`) | Use explicit contracts. Test your JSON serialization. |
| 5 | **Pointer in backing not cleared after delete** | "Removed" pointer element still occupies a capacity slot → GC can't collect the object it points to | Set abandoned slots to `nil` after compacting |
| 6 | **Append split — two slices diverge silently** | Before reallocation, two slices share data. After, they're independent. This transition is invisible. | Document ownership. Only one variable should "own" the right to append. |

> **In plain English:** Most slice bugs come from forgetting that the slice is a small card, not the data. Two cards can describe the same data, cards can go stale, and the data can move without telling all the card holders.

```
The append split — visualized:

  BEFORE realloc:
    p = [ ptr=0xC000080000 | len=2 | cap=2 ]
    q = [ ptr=0xC000080000 | len=2 | cap=2 ]   ← same backing
    heap 0xC000080000: [1|2]

  q = append(q, 3)  →  cap full → realloc!

  AFTER realloc:
    p = [ ptr=0xC000080000 | len=2 | cap=2 ]   ← still old array (STALE)
    q = [ ptr=0xC000090000 | len=3 | cap=4 ]   ← new array, only q knows
    heap 0xC000080000: [1|2]         ← p reads from here
    heap 0xC000090000: [1|2|3|_]     ← q reads from here

  p and q have silently diverged. Writes to q[0] don't affect p[0].
```

---

## 8. Performance & Tradeoffs

| Pattern | CPU / copies | Heap / GC pressure | When to prefer |
|---------|-------------|-------------------|----------------|
| Array `[N]T` on stack | Zero indirection, but O(N) copy on pass/assign | Stack allocation (no GC) | Small fixed-size, value semantics, crypto buffers |
| Slice `[]T` | Header copy is O(1), data shared via pointer | Shared backing, aliasing risks | Default for variable-length sequences |
| Pre-allocate `make([]T, 0, estimate)` | Fewer reallocations and copies | Slightly over-provisioned | Know approximate count upfront (e.g., `len(input)`) |
| Exact-size `make([]T, n)` | No hidden capacity waste | Tight memory | Known exact length, fill by index |
| Defensive copy `append([]T(nil), s...)` | O(len) copy | New independent backing | Break aliasing, safe to pass to goroutines |
| Three-index `s[low:high:high]` | May force earlier realloc on append | Frees most of huge backing sooner | Keep small view from big buffer |
| Filter in-place (two-pointer) | O(n) single pass, minimal allocs | Reuses same backing | Large datasets where copies are too expensive |

**Performance tip:** Reallocation storms from `append` in tight loops show up as high allocation rates in `pprof`. Pre-size from estimates or do a counting pass first.

---

## 9. Common Misconceptions

| Misconception | Reality |
|--------------|---------|
| "Slices are reference types" | Slices are small **struct values** (24 bytes). The sharing comes from the pointer field inside the struct, not from the slice itself being a reference. |
| "Copying a slice deep-copies elements" | Only the 24-byte header is copied. Elements are shared until you explicitly `copy` or `append` to a fresh slice. |
| "`append` mutates the slice variable" | `append` returns a new header. In-place modification is an optimization, not a guarantee. Always capture the return. |
| "Sub-slicing to smaller `len` frees memory" | The GC sees the entire backing array as one allocation. A tiny sub-slice keeps the whole thing alive. |
| "Capacity equals length" | `len` is what you can read. `cap` is how much room exists before reallocation. They only match when the slice is exactly full. |
| "Arrays and slices are interchangeable" | `[3]int` and `[]int` are completely different types. You can't assign one to the other. |
| "Deleting from a slice reclaims memory immediately" | For pointer elements, the slot in backing capacity may still reference a heap object until you nil it out. |

---

## 10. Related Tooling & Debugging

- **`go test -bench -benchmem`**: See allocations per operation and bytes/op for slice-heavy code.
- **`pprof`** (Go profiling): Use `go test -memprofile` to generate heap profiles. Look at `alloc_space` to spot append churn.
- **`go build -gcflags="-m"`** (escape analysis): Shows which variables escape to the heap. Large array/slice literals often escape.
- **Delve debugger**: Inspect a `[]T` and see `ptr`, `len`, `cap` fields separately. Confirm which backing array a slice points to.
- **Race detector** (`go test -race`): Concurrent append or re-slice without synchronization is a data race. Use `sync.Mutex` or channels for shared slices.
- **`runtime/debug.SetGCPercent`**: For local experiments only — tune GC aggressiveness to observe how slice retention affects memory behavior.

---

## 11. Interview Gold Questions

### Q1. "Explain the append trap and why a function that calls `append` on its parameter may not change the caller's view."

**Answer:** Slice parameters are copied by value — the function gets its own header. `append` returns a new header that may point to a completely new backing array (if reallocation happened). If the function doesn't return this new header, the caller's variable still holds the old pointer/len/cap. The fix is always return `[]T` and reassign at the call site, or in rare cases use `*[]T` as the parameter.

**15-second verbal:** "Append returns a new slice header. If realloc happens, the pointer changes. I always capture the return — treating append as an in-place mutator is wrong."

### Q2. "What is a full slice expression `s[low:high:max]` and why is it in the language?"

**Answer:** It sets the result's `cap` to `max - low`, limiting how far `append` on the sub-slice can reach. Without it, `append` on a sub-slice can silently overwrite elements in the original slice's territory. It's essential in APIs where you hand out sub-views of a shared buffer and need to guarantee callers can't corrupt each other's data.

### Q3. "Array vs slice — when do you use `[N]T` and what's the cost of passing each?"

**Answer:** Arrays for small, fixed-size, value-semantic data — crypto hashes, IP addresses, small coordinate tuples. Passing `[N]T` copies all N elements (O(N)). Slices are passed as 24-byte headers (O(1)) sharing the backing array. The tradeoff is type safety and stack-friendliness for small arrays vs. flexibility and cheap passing for slices.

---

## 12. Final Verbal Answer

> *Say this out loud (about 30 seconds).*
>
> A slice in Go is a 24-byte header — pointer, length, and capacity — that sits on top of a contiguous backing array. The header is passed by value, so two slices can share the same underlying data. `append` can reallocate to a new, bigger array, so I always capture the return: `s = append(s, x)`. Since Go 1.18, growth doubles below 256 elements and uses a smoother formula above that, then rounds up to memory allocator size classes. A sub-slice of a huge array keeps the entire array alive for GC, so I copy into a tight slice or use the three-index form to limit capacity. For pointer slices, I nil out abandoned capacity slots to avoid GC leaks. I use fixed-size arrays `[N]T` when the size is part of the type's meaning, and slices `[]T` for everything else.

---

## 13. Comprehensive Interview Questions

> Full interview question bank (10-15 questions) → [[questions/T04 Arrays & Slice Internals - Interview Questions]]

**Preview questions (answers in linked file):**

1. You append inside a helper but the caller's slice never grows — what happened, and what's the idiom to fix it?
2. A micro-service caches a 2 GB read buffer; you store `line := bigBuf[0:lineEnd]`; memory never drops after requests — why, and what two fixes are idiomatic?
3. After deleting `*Node` from a `[]*Node` using slice tricks, `runtime.MemStats` still shows high heap in-use — what class of bug is this and the concrete mitigation?

---

> See [[Glossary]] for term definitions.
