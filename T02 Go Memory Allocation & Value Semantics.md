
> **Reading Guide**: Sections 1-3 and 6 are essential first read (20 min).
> Sections 4-5 deepen understanding (15 min).
> Sections 7-12 are interview-specific — read closer to interview day.
> Section 13 is your comprehensive interview Q&A bank → [[questions/T02 Go Memory Allocation - Interview Questions]]
> Something not clicking? → [[simplified/T02 Go Memory Allocation & Value Semantics - Simplified]]

---

## 0. Prerequisites

Complete these before starting this topic:

- [[prerequisites/P01 Structs & Struct Memory Layout]]
- [[prerequisites/P06 Function Call Stack]]

---

## 1. Concept

**Go Memory Allocation & Value Semantics** is about where your values live (stack or heap), what happens when you pass them into functions, and how goroutines share them.

> **Naming trap**: The official "Go Memory Model" (go.dev/ref/mem) is about **happens-before ordering** across goroutines, not stack/heap allocation. If an interviewer hears "Go Memory Model," they'll expect you to talk about visibility guarantees. Use "memory allocation" or "value semantics" when discussing this topic. See [[Go Memory Model (Happens-Before)]] for that topic.

---

## 2. Core Insight (TL;DR)

**Go is strictly pass-by-value.** Every assignment, every function call copies the value. No exceptions.

You don't hand-pick stack vs heap. The compiler does. **Stack** is fast, private, and it tears down when the function returns. **Heap** is shared; the GC owns cleanup. `new()` and `&T{}` do not promise the heap. **Escape analysis** decides.

---

## 3. Mental Model (Lock this in)

### Stack → "Your Desk"

- Private, fast, auto-cleaned on function return
- Each goroutine has its own stack (~2-8 KB initial)

### Heap → "Shared Storage"

- Used when data outlives function or can't stay on stack
- Managed by GC (Garbage Collector) — every heap allocation creates future GC work
- ~12-25x slower than stack allocation

### Pass-by-value → "Everything is a photocopy"

- Even pointers are copied (the address itself, not the data)
- Sharing happens only through internal pointers within copied values

> **In plain English:** The stack is fast, private memory that gets cleaned up automatically when a function returns. The heap is shared memory that sticks around until the garbage collector finds it's no longer needed — every heap allocation creates future cleanup work.

```
  Goroutine 1 — STACK (private, auto-freed)     HEAP (shared, GC-managed)
  ┌─────────────────────────────┐                ┌─────────────────────────┐
  │ x := 42                     │                │ User{Name:"Alice"}      │
  │ buf [64]byte                │                │  ← escaped via &u       │
  │ ptr ──────────────────────────────────────────▶                        │
  └─────────────────────────────┘                └─────────────────────────┘
    ~2-8 KB initial per goroutine                  GC cleans up when
    Torn down on function return                   no references remain
```

> Stack: ~1-2ns alloc, auto-freed on return. Heap: ~25-50ns alloc + GC scan cost.

### The mistake that teaches you

```go
func NewUser(name string) *User {
    u := User{Name: name}
    return &u // returning a pointer to a local variable
}
```

**What you'd expect:** "I'm returning a pointer to a stack variable — you'd expect that address to go stale, like giving someone directions to a room that's been cleared when you left."

**What actually happens:** It works perfectly. Go's escape analysis detects that `u` outlives the function (because you return `&u`) and moves it to the heap automatically. The pointer you get still points at valid storage — no crash.

**Why this matters:** In Go, the compiler decides stack vs heap — not you. You never hand-pick "should this live on the quick shelf or in long-term storage?" yourself. But every time the compiler escapes a variable to the heap, it adds GC work. Run `go build -gcflags="-m"` to see: `moved to heap: u`. That's the trade-off: safety is automatic, but the cost shows up in tail latency under load.

---

## 4. How It Actually Works (Internals) [INTERMEDIATE → ADVANCED]

### Escape Analysis: The Compiler's Decision Engine

The Go compiler is like a smart warehouse manager. Before your code runs, it looks at every variable and asks: "Will this box be needed after this function returns? If yes, put it in long-term storage (heap). If no, keep it on the quick shelf (stack) and toss it when we're done."

We call that **escape analysis**. At compile time, the compiler follows how values move. It asks: can this stay on the stack, or must it "escape" to the heap?

> [!question]- Before reading on, predict: what will this print / what does memory look like here?
> Try to answer from memory before expanding the walkthrough below.

**Does it escape? Walk this checklist:**

1. Returned as pointer from function? → **HEAP** (outlives the function)
2. Sent to another goroutine / channel / stored in global? → **HEAP** (shared across scopes)
3. Size unknown at compile time? → **HEAP** (e.g., `make([]byte, n)` where `n` is a variable)
4. Assigned to an interface and value is larger than a pointer? → **USUALLY HEAP** (boxing)
5. None of the above? → **STACK**

You can see the compiler's decisions with:

```bash
go build -gcflags="-m"       # basic: what escapes
go build -gcflags="-m -m"    # verbose: WHY it escapes
```

**What each flag means:** You pass `-gcflags` through to the Go compiler. Add `-m` and you get escape and inlining lines on **stderr** — look for `moved to heap: x` or `&x escapes to heap`. Add another `-m` and the compiler also prints **why**. Run it from your module folder. The build just mixes those lines into the log. There is no separate output file.

### Stack Internals

- Starts small (~2-8 KB per goroutine)
- **Contiguous stack model** (since Go 1.4)
- Growth = allocate **new larger stack** + **copy old data** + **adjust all pointers**

> [!question]- Before reading on, predict: what will this print / what does memory look like here?
> Try to answer from memory before expanding the walkthrough below.

```
BEFORE (~2 KB)              AFTER (~4 KB)
  frame: C()                  frame: C()
  frame: B()   ── copy ──▶    frame: B()
  frame: A()                  frame: A()
                              (room to grow)

ALL pointers into old stack are REWRITTEN.
This is why Go bans pointer arithmetic.
```

### Heap + GC (Garbage Collector)

- **Tri-color concurrent mark-and-sweep** GC (since Go 1.5)
- STW (Stop-The-World) phases: typically **sub-millisecond** (< 100 microseconds)
- Real latency killer: **mark assist** — goroutines allocating during GC are forced to help mark before their allocation proceeds

**How tri-color marking works:**

```
1. Start: all objects are WHITE (unvisited)
2. Mark roots (globals, stack variables) as GREY
3. Pick a GREY object → scan its pointers → mark children GREY → mark it BLACK
4. Repeat step 3 until no GREY objects remain
5. Remaining WHITE objects = garbage → freed

BLACK = fully scanned (safe)
GREY  = visited, children still being scanned
WHITE = not reached yet (will be freed if still white at end)
```

### Write Barrier

Imagine a librarian reorganizing shelves (the GC scanning objects). While the librarian works, you're allowed to keep reading books — but if you move a book to a different shelf, you have to leave a note saying "I moved this." That note is the **write barrier**.

During a GC cycle, every **pointer write to the heap** goes through a write barrier — a small runtime check that tells the garbage collector "this pointer changed, you need to re-check it." This preserves the tri-color rule (no black object may point to a white object) so the GC doesn't accidentally free something you're still using.

```go
type RequestNode struct {
    Next *RequestNode
    Data []byte
}

var head *RequestNode = &RequestNode{}
head.Next = &RequestNode{Data: []byte("POST /api/orders")}
// during GC, this pointer write goes through the barrier
```

**What happens at `head.Next = &RequestNode{...}`:** The runtime intercepts this pointer assignment, marks the new `RequestNode` as "still reachable" in the GC's bookkeeping, then completes the write. Without the barrier, the GC might think the new `RequestNode` is unreachable and free it.

> **The takeaway:** Pointer writes are more expensive than value writes during GC — each one triggers the barrier. This is one reason why fewer pointers means less GC overhead.

---

## 5. Key Rules & Behaviors

### Rule 1: Everything is pass-by-value

No exceptions. Even pointers, slices, maps, and interfaces are copied when passed to a function.

```go
func updateAge(u User) { u.Age = 30 }

user := User{Name: "Alice", Age: 25}
updateAge(user)
fmt.Println(user.Age) // 25 — unchanged! updateAge got a copy.
```

```
main stack: user = { Name:"Alice", Age:25 }
             ↓ COPY (pass-by-value)
updateAge stack: u = { Name:"Alice", Age:25 }  ← independent copy
  u.Age = 30 → modifies the COPY only
  main's user is untouched
```

**Why:** Go doesn't have reference semantics. If you want a function to modify your original, pass a pointer explicitly. This makes mutation visible in the function signature.

### Rule 2: `new()` and `&T{}` do NOT guarantee heap

Escape analysis decides where memory lives. These just allocate — the compiler picks stack or heap.

```go
func noEscape() {
    u := &User{Name: "Alice"} // &T{} here
    fmt.Println(u.Name)       // u never leaves this function → STACK
}
```

```
u := &User{...} → compiler asks: does u escape?
  - Not returned
  - Not sent to goroutine
  - Not stored in global
  → stays on stack. The & does NOT force heap.
```

**Why (Section 4.1):** The compiler's escape analysis tracks where every pointer goes. If it can prove the pointer doesn't outlive the function, stack allocation is safe and much faster.

### Rule 3: Returned pointer → heap

If a function returns `&x`, `x` must survive after the function's stack frame is torn down. The compiler moves it to the heap.

```go
func NewSession(token string) *Session {
    s := Session{Token: token}
    return &s  // s escapes to heap
}
```

```
NewSession stack: s = Session{Token: "abc"}
  return &s → s must survive after NewSession returns
  → compiler moves s to heap
  heap: s = Session{Token: "abc"} at 0xC000080000
  caller gets ptr = 0xC000080000
```

**Why:** The stack frame for `NewSession` is destroyed on return. If `s` stayed on the stack, the returned pointer would point at freed memory.

### Rule 4: Shared across goroutines or stored in globals → heap

If a value is sent to another goroutine, stored in a channel, or assigned to a global variable, it escapes.

```go
var globalConfig *Config

func init() {
    cfg := Config{Port: 8080}
    globalConfig = &cfg  // cfg escapes — stored in global
}
```

```
cfg is referenced by globalConfig → outlives init() → heap
Any variable reachable from another goroutine → heap
```

**Why:** The compiler can't guarantee when another goroutine or package will access it, so it must live until the GC determines no one references it.

### Rule 5: Unknown size at compile time → heap

If the compiler can't determine the size at compile time, it can't reserve stack space.

```go
func readBody(r *http.Request) []byte {
    n := r.ContentLength              // runtime value
    buf := make([]byte, n)            // size unknown at compile time → HEAP
    io.ReadFull(r.Body, buf)
    return buf
}
```

```
make([]byte, n) where n is a variable → compiler can't reserve stack space
  → backing array allocated on heap

BUT: make([]byte, 128) where 128 is a constant → compiler CAN stack-allocate
```

**Why:** Stack frames have fixed sizes determined at compile time. Variable-length data can't fit in a fixed-size frame.

### Rule 6: Slice is passed by value — elements are shared, append may not be

When you pass a slice, the 24-byte header (`ptr`, `len`, `cap`) is copied. Both copies point to the same backing array. But `append` may create a new array.

```go
func modify(s []int) { s[0] = 999 }       // visible to caller
func grow(s []int)   { s = append(s, 4) }  // NOT visible to caller (if cap exceeded)
```

```
modify: s[0] = 999 → writes to shared backing array → caller sees it
grow:   append(s, 4) → cap exceeded → new array → local s updated → caller's copy unchanged
```

**Why (Section 6):** The slice header is a value. `append` may replace the `ptr` field in the local copy. The caller's copy still has the old `ptr`. This is the #1 Go gotcha for newcomers.

### Rule 7: Map is already a pointer

`make(map[K]V)` returns a pointer to a `runtime.hmap` struct. No need for `*map`.

```go
func populate(m map[string]int) {
    m["users"] = 42  // modifies caller's map — m is a pointer
}
```

```
m = pointer to hmap → passing m copies the 8-byte pointer
Both caller and callee point to the same hmap → changes are shared
```

**Why:** The `map` type is already a pointer under the hood. Writing `*map[K]V` would be a pointer-to-a-pointer — unnecessary and confusing.

### Rule 8: More pointers = more GC work

Every pointer the GC encounters is an edge it must follow during the mark phase. Fewer pointers means faster GC cycles.

```go
// HIGH GC pressure: 10M pointer edges
cache := map[string]*User{}

// LOW GC pressure: values stored inline in buckets
cache := map[string]User{}
```

```
map[string]*User → each entry has a pointer → GC must follow 10M edges
map[string]User  → values inline in buckets → GC scans bucket memory directly

10M pointers ≈ measurable difference in GC mark phase duration
```

**Why (Section 4.3):** During tri-color marking, the GC follows every pointer from grey objects to find reachable data. More pointers = more work per cycle = higher tail latency under load.

---

## 6. Code Examples (Show, Don't Tell)

### Escape vs no escape

```go
func foo() *int {
    x := 10
    return &x
}

func bar() int {
    x := 10
    p := &x
    return *p
}
```

**What Go does:** In `foo`, the returned `*int` outlives the function, so `x` **escapes to the heap**; the stack frame cannot hold the only copy of the value. In `bar`, `p` and `x` are used only inside the function, so `x` can **stay on the stack**. A `go build -gcflags="-m"` on a package containing these functions shows the compiler’s escape decisions line by line.

```
foo() — ESCAPES to heap:
  Step 1: x := 10          stack: [ x = 10 ]
  Step 2: return &x         caller gets a pointer to x
          BUT foo() is about to return — its stack frame will be destroyed!
          So x MUST move to the heap to survive.
          heap: [ x = 10 ] ◄── returned pointer points here

bar() — STAYS on stack:
  Step 1: x := 10          stack: [ x = 10 ]
  Step 2: p := &x          stack: [ x = 10, p ──▶ x ]
  Step 3: return *p         returns the VALUE 10, not the pointer
          p and x are never needed after bar() returns → stack is fine
```

### Pass-by-value with pointer

```go
func update(x *int) {
    *x = 20
}

func main() {
    val := 42
    update(&val)
    fmt.Println(val) // 20
}
```

```
Step 1: main — val := 42
  main stack: [ val = 42 ]

Step 2: update(&val) — Go copies the ADDRESS (not the data)
  main stack:   [ val = 42 ] ◄──┐
  update stack: [ x = 0xABC ] ──┘  x is a COPY of the pointer
                                    both point to the same val

Step 3: *x = 20 — dereference and write
  main stack:   [ val = 20 ] ◄──┐  val is modified!
  update stack: [ x = 0xABC ] ──┘

Step 4: update returns — its stack frame is destroyed
  main stack: [ val = 20 ]   the change persists
```

> **In plain English:** In Go, nothing is shared unless you explicitly pass a pointer. When you pass a value, the function gets its own independent copy. When you pass a pointer, the function can read and modify the original.

### Slice header copy

```go
func modify(s []int) {
    s[0] = 100
}

func grow(s []int) {
    s = append(s, 4)
}

func main() {
    data := []int{10, 20, 30}
    modify(data)
    fmt.Println(data[0]) // 100 — change visible!

    grow(data)
    fmt.Println(len(data)) // 3 — append NOT visible!
}
```

```
What IS a slice? A 24-byte header (ptr + len + cap) on the stack:

  stack 0xC000060000: data = [ ptr=0xC000080000 | len=3 | cap=3 ]
  heap  0xC000080000: [10, 20, 30]

Step 1: modify(data) — header is COPIED (24 bytes), but ptr still points to same array
  main stack   0xC000060000: [ ptr=0xC000080000 | len=3 | cap=3 ]
  modify stack 0xC000070000: [ ptr=0xC000080000 | len=3 | cap=3 ]  ← copy of header
                                      ↑ SAME heap address!
  modify does s[0] = 100:
    s.ptr + 0*8 = 0xC000080000 → write 100
  main reads data[0]: data.ptr + 0*8 = 0xC000080000 → reads 100 ← visible!

Step 2: grow(data) — header is COPIED again
  main stack 0xC000060000: [ ptr=0xC000080000 | len=3 | cap=3 ]
  grow stack 0xC000070000: [ ptr=0xC000080000 | len=3 | cap=3 ]  ← copy
  
  append needs cap=4 but cap=3 → allocates NEW array at 0xC000090000:
  grow stack 0xC000070000: [ ptr=0xC000090000 | len=4 | cap=6 ] ← NEW array!
  main stack 0xC000060000: [ ptr=0xC000080000 | len=3 | cap=3 ] ← still old array!
                                                                  <-- THIS is why append isn't visible
  heap 0xC000080000: [100, 20, 30]       ← main still reads here
  heap 0xC000090000: [100, 20, 30, 4, _, _] ← grow's new array (only grow knows)
```

> **In plain English:** When `append` needs more room than the current backing array has, it allocates a new, bigger array and copies everything over. The function that called `append` gets the updated slice header pointing to the new array, but the caller's copy still points to the old one. That's why you must return and reassign the new slice.

### Map is a pointer

```go
m := make(map[string]int)
```

```
Under the hood, m is a pointer to a runtime.hmap struct:

  stack 0xC000060000: m = [ ptr=0xC000010000 ]  ← 8-byte pointer on the stack
                                  │
                                  ▼
  heap 0xC000010000: hmap{ count:0, B:0, hash0:0x7A3F, buckets → 0xC000020000 }
                                                                      │
                                                                      ▼
  heap 0xC000020000: [bucket0 — 8 empty slots]

  When you insert m["key"] = val:
    hash("key", hash0) → bucket = hash & (2^B - 1) → find slot → store key+val

Passing m to a function copies the 8-byte pointer, NOT the hmap.
  caller:  m = 0xC000010000
  callee:  m = 0xC000010000  ← same address, same hash table
No need for *map — it's already a pointer.
```

### Interface internals

```go
type iface struct {
    tab  *itab
    data unsafe.Pointer
}

type eface struct {
    _type *_type
    data  unsafe.Pointer
}
```

**What each field means:** `tab` (on `iface`) points at an **itab**: concrete type plus method addresses. `data` is a single pointer to the **boxed** value, usually on the heap. On `eface` (`any`), `_type` is the type descriptor only; `data` is the same second word—a pointer to the stored value. Two fields: **metadata** (which type) + **data** (where the bits live).

```
iface (interface with methods, e.g., io.Reader):
  [ tab ──▶ itab{type info + method addresses} | data ──▶ actual value ]

eface (empty interface / any):
  [ _type ──▶ type descriptor | data ──▶ actual value ]

Key insight: an interface is a TWO-FIELD struct, not only a pointer.
This is why a "nil pointer inside an interface" is NOT a nil interface.
```

- **iface** = interface with methods — runtime struct holding {pointer to method table (itab), pointer to actual data}
- **eface** = empty interface (`any` / `interface{}`) — runtime struct holding {pointer to type info, pointer to data}
- **itab** = Interface Table — cached mapping of concrete type to interface method addresses

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

Paste into [Go Playground](https://go.dev/play/) and predict output BEFORE running:

```go
package main

import "fmt"

func change(s []int) {
    s[0] = 999
    s = append(s, 4, 5, 6)
    s[0] = 111
}

func main() {
    data := make([]int, 3, 3)
    data[0] = 1
    data[1] = 2
    data[2] = 3
    change(data)
    fmt.Println(data)
}
```

> [!success]- Answer
> 
> `[999 2 3]` — The `s[0] = 999` is visible (same backing array). But `append` triggers a new array (cap was full), so `s[0] = 111` writes to the NEW array. Main's `data` still points to the old array where `[0]` is `999`.

### Tier 2: Fix the Bug (5 min)

This HTTP handler has a memory leak. Find and fix it:

```go
func handler(w http.ResponseWriter, r *http.Request) {
    body, _ := io.ReadAll(r.Body) // could be 10MB
    prefix := body[:128]          // need only the first 128 bytes
    log.Println(string(prefix))
    // ... rest of handler uses prefix but not body
}
```

> [!success]- Hint
> 
> `prefix` is a sub-slice of `body` — it holds a reference to the entire 10MB backing array even though you only need 128 bytes.

> [!success]- Fix
> 
> ```go
> prefix := make([]byte, 128)
> copy(prefix, body[:128])
> ```
> 
> Now `prefix` has its own 128-byte backing array, and the 10MB `body` array can be garbage collected.

### Tier 3: Build It (15 min)

Write a Go program that:
1. Creates a function returning a pointer to a local variable
2. Creates a function returning a value (no pointer)
3. Run `go build -gcflags="-m"` and verify which escapes and which doesn't
4. Bonus: create a struct larger than 128 bytes and benchmark value receiver vs pointer receiver using `testing.B`

> Full solutions with explanations → [[exercises/T02 Go Memory Allocation - Exercises]]

---

## 7. Edge Cases & Gotchas

### The append trap

```go
func grow(s []int) {
    s = append(s, 4) // cap exceeded → new array
}                     // caller's slice unchanged!
```

**Why**: `append` may allocate a new backing array. The local `s` header updates, but the caller's copy still points to the old array.

**Fix**: return the new slice or pass `*[]int`.

```
BEFORE grow(s):
  caller stack 0xC000060000: s = [ ptr=0xC000080000 | len=3 | cap=3 ]
  heap 0xC000080000: [10, 20, 30]  ← full (len == cap)

INSIDE grow(s):
  grow stack 0xC000070000: s = [ ptr=0xC000080000 | len=3 | cap=3 ]  ← copy
  append: cap exceeded → new array at 0xC000090000
  grow stack 0xC000070000: s = [ ptr=0xC000090000 | len=4 | cap=6 ]  ← updated locally
  heap 0xC000090000: [10, 20, 30, 4, _, _]

AFTER grow returns:
  caller stack 0xC000060000: s = [ ptr=0xC000080000 | len=3 | cap=3 ]  ← UNCHANGED
  heap 0xC000080000: [10, 20, 30]    ← caller still reads here
  heap 0xC000090000: [10, 20, 30, 4] ← orphaned, no one points here → GC

Fix: return the new slice
  func grow(s []int) []int {
      return append(s, 4)
  }
  data = grow(data)  ← now caller has the updated header
```

The key point: when `append` triggers a reallocation, the function's local slice header gets a new `ptr`. But the caller's copy of the header still has the old `ptr`, old `len`, old `cap`. The caller never sees the new element.

### Slice memory leak from sub-slicing

```go
func getFirstThree(data []byte) []byte {
    return data[:3] // LEAK: holds ref to entire backing array
}
```

**Fix**: copy the subset.

```go
func getFirstThree(data []byte) []byte {
    result := make([]byte, 3)
    copy(result, data[:3])
    return result
}
```

```
WITHOUT fix (memory leak):
  stack: data   = [ ptr=0xC000100000 | len=1048576 | cap=1048576 ]
  stack: result = [ ptr=0xC000100000 | len=3       | cap=1048576 ]
                         ↑ SAME address — result still holds entire 1MB alive!
  heap 0xC000100000: [A][B][C][D][E]...[1MB data]
  GC checks: anything still pointing at 0xC000100000? → YES (result) → can't free

WITH fix (independent copy):
  stack: result = [ ptr=0xC000200000 | len=3 | cap=3 ]  ← own tiny array
  heap 0xC000200000: [A][B][C]          ← 3 bytes only
  heap 0xC000100000: 1MB → no references remain → GC eligible
```

### Interface nil trap

```go
var p *MyStruct = nil
var i interface{} = p
fmt.Println(i == nil) // false!
```

```
Step 1: var p *MyStruct = nil
  p = nil  (a nil pointer of type *MyStruct)

Step 2: var i interface{} = p
  An interface is TWO fields: [ type | data ]
  i = [ type: *MyStruct | data: nil ]
       ^^^^^^^^^^^^^^^^
       type is NOT nil! It knows it's holding a *MyStruct.

Step 3: i == nil?
  Go checks: is type == nil AND data == nil?
  type = *MyStruct → NOT nil!
  Result: false
                    <-- THIS is the trap

A truly nil interface has BOTH fields nil:
  var i interface{} = nil
  i = [ type: nil | data: nil ]  → i == nil is true
```

> **In plain English:** An interface in Go is two fields: a type and a data pointer. A truly nil interface has both fields nil. But if you assign a nil pointer of a specific type to an interface, the type field is set (non-nil) even though the data is nil. So `i == nil` returns false — the interface knows it's holding a `*MyStruct`, even though that pointer is nil.

```go
// BAD — returns non-nil interface wrapping a nil pointer
func getUser() error {
    var err *MyError = nil
    return err       // interface{type: *MyError, data: nil} ≠ nil
}

// GOOD — returns actual nil interface
func getUser() error {
    return nil       // interface{type: nil, data: nil} == nil
}
```

### Mutex copy via value receiver

```go
type Cache struct {
    mu   sync.Mutex
    data map[string]string
}

// BUG: value receiver copies the mutex!
func (c Cache) Get(key string) string {
    c.mu.Lock()        // locking a COPY — no protection
    defer c.mu.Unlock()
    return c.data[key]
}
```

```
Step 1: c.Get("foo") is called
  Go COPIES the entire Cache struct (because value receiver)
  original: [ mu = {locked: false} | data ──▶ map ]
  copy:     [ mu = {locked: false} | data ──▶ map ]  ← INDEPENDENT mutex!

Step 2: copy.mu.Lock()
  Locks the COPY's mutex — the original's mutex is still unlocked
  Another goroutine can call Get() and lock ITS OWN copy too
  Result: no mutual exclusion at all!
                                      <-- zero protection

Fix: use pointer receiver
  func (c *Cache) Get(key string) string { ... }
  Now c points to the original — everyone locks the SAME mutex.
```

**Fix**: always use pointer receiver with embedded mutexes.

### Loop variable trap

```go
for _, v := range arr {
    go func() {
        fmt.Println(v) // Pre-1.22: all see final value
    }()
}
```

```
Pre-Go 1.22:
  v is ONE variable reused across all iterations.
  By the time goroutines run, the loop is done and v = last element.

  Iteration 1: v = "a", goroutine captures &v
  Iteration 2: v = "b", goroutine captures &v (same v!)
  Iteration 3: v = "c", goroutine captures &v (same v!)
  Goroutines run: all read v → "c", "c", "c"

Go 1.22+: Fixed — each iteration gets its own v.
```

### Closure escape

```go
func makeAdder(n int) func(int) int {
    return func(x int) int {
        return x + n // n escapes to heap
    }
}
```

```
Step 1: makeAdder(5) is called, n = 5 on makeAdder's stack

Step 2: The closure func(x) captures n
        But the closure will outlive makeAdder (it's returned!)
        So n CANNOT stay on makeAdder's stack

Step 3: Compiler moves n to the heap
        closure = { code: func(x int), env ──▶ [n = 5] }
                                                 ↑ heap-allocated
```

The closure outlives `makeAdder`, so captured `n` must survive → heap-allocated.

---

## 8. Performance & Tradeoffs

Your `OrderService` handles 8k RPM. Each request creates an `Order` struct (~96 bytes), queries the database, maybe wraps an error, and returns JSON. At that scale, where does the memory allocation story actually matter?

| Pattern | What it costs | You'd see this in... | Verdict |
|---|---|---|---|
| Passing `Order` by value (~96 bytes) | One 96-byte stack copy per call | `FindByID() Order` returning a struct from the repo layer | Noise — stack copies of small structs are nanoseconds next to a 2ms DB query |
| Passing `*OrderService` (pointer receiver) | 8-byte pointer, no copy, but may force heap escape | Every handler calling `svc.CreateOrder()` | Correct — `OrderService` holds `*sql.DB`, you don't want copies of that |
| `map[string]User` with 10M entries (value map) | Values stored inline in buckets, no extra pointer edges | User cache in a session store | Better GC — 10M fewer pointer edges for the mark phase to trace |
| `map[string]*User` with 10M entries (pointer map) | 10M pointer edges + scattered heap allocations | Session store with frequent mutation | Easier mutation, but GC mark phase takes measurably longer |
| `make([]byte, n)` where `n` is a runtime variable | Heap allocation — compiler can't determine size | Reading an HTTP request body of unknown size | Expected — you can't avoid this, but `sync.Pool` can amortize it |
| `make([]byte, 128)` with constant size | Compiler can stack-allocate | Fixed-size temp buffer in a hot parsing loop | Free — constant size lets the compiler keep it on the stack |

### What actually hurts

The thing that bites you at 8k RPM isn't the cost of any single allocation — it's the *cumulative* GC pressure from thousands of small heap allocations per second. Your handler allocates an `Order`, wraps it in a `*Order` for the response, serializes it to `[]byte` (heap), and logs the request ID as a `string` (heap). Four heap allocations per request × 8k RPM = 32k allocs/sec. Each one becomes a live object the GC must scan during the mark phase. When the mark phase runs long, goroutines doing allocations get hit with **mark assist** — they're forced to help the GC mark before their allocation proceeds. That's where your p99 latency spike comes from.

The fix isn't to avoid all pointers. It's to find the *hot-path* allocations. In practice, the biggest win is usually `sync.Pool` for serialization buffers and pre-allocated slices with known capacity.

### What to measure

```bash
# See what escapes and why
go build -gcflags="-m -m" ./... 2>&1 | grep "escapes to heap"

# Profile allocation hotspots
go test -bench=BenchmarkHandler -benchmem ./...
go tool pprof -alloc_objects http://localhost:6060/debug/pprof/heap

# Watch GC behavior under load
GODEBUG=gctrace=1 ./myserver
# Look for: high "mark assist" time → goroutines are being taxed

# Set a memory budget (Go 1.19+)
GOMEMLIMIT=512MiB ./myserver
```

Rule of thumb: if your struct is under ~128 bytes and read-heavy, pass it by value. If it holds a connection, a mutex, or is shared across goroutines — pointer, no question. For large caches, `map[string]int32` indexing into a `[]User` slice gives you dense values + cheap map operations.

---

## 9. Common Misconceptions

| Misconception | Reality |
|---|---|
| Go is pass-by-reference | **WRONG** — strictly pass-by-value, always |
| Pointer = always faster | **WRONG** — adds GC pressure, hurts cache locality |
| Slice is a reference type | **HALF TRUE** — header is a value containing a pointer |
| `new()` always allocates on heap | **WRONG** — escape analysis decides |
| You can take the address of map values with & | **WRONG** — `&m["key"]` is illegal; map entries move during growth |
| STW (Stop-The-World) pauses are the GC bottleneck | **OUTDATED** — mark assist is the real latency killer |
| Large struct → always use pointer | **WRONG** — measure first; ~128B is roughly the crossover |
| `make([]byte, 1024)` always heap-allocates | **WRONG** — constant size can be stack-allocated |

> Everything is pass-by-value. Some values contain internal pointers that enable shared access.

---

## 10. Related Tooling & Debugging

### Escape analysis inspection

```bash
go build -gcflags="-m"       # basic: what escapes
go build -gcflags="-m -m"    # verbose: WHY it escapes
go build -gcflags="-m -l"    # disable inlining (clearer output)
```

**What each flag means:** `-m` and `-m -m` are the same escape/inlining **diagnostics** on **stderr** as the `go build -gcflags` example earlier in this document (what escapes, then why). `-l` **turns off inlining** so you see more call sites in the notes and the output is easier to map to your source. Build from the package root; read the compiler messages, not a separate report file.

### Allocation profiling

```bash
go test -bench=. -benchmem           # allocs/op in benchmarks
go test -memprofile mem.prof         # heap profile
go tool pprof -alloc_space mem.prof  # total bytes allocated
go tool pprof -inuse_space mem.prof  # currently live bytes
```

**What each does:** `go test -bench` runs matching benchmarks; `-benchmem` adds **allocs/op** and memory per iteration. `-memprofile` writes a **heap** profile file from that test run. `pprof -alloc_space` attributes **cumulative** bytes allocated; `-inuse_space` shows what was still **live** when the profile was taken—useful for “where are we spending heap” vs “what’s retained.”

### Runtime flags

```bash
GODEBUG=gctrace=1 ./myserver        # GC cycle logging
GOGC=100                             # GC trigger ratio (default)
GOMEMLIMIT=512MiB ./myserver         # soft memory cap (Go 1.19+)
```

**What each does:** `GODEBUG=gctrace=1` prints a **per-cycle GC summary** to stderr (heap size, STW, CPU time). `GOGC` is the **live-heap multiple** that triggers the next collection (100 ≈ when heap is about 2× last live, default). `GOMEMLIMIT` sets a **soft** process memory cap; the scheduler runs GC more aggressively to try to stay under it (Go 1.19+).

### GC tuning

```
GOGC=100 (default): GC at 200MB when live=100MB  → less CPU, more RAM
GOGC=50:            GC at 150MB when live=100MB  → more CPU, less RAM
GOMEMLIMIT=512MiB:  runtime adjusts GC pacing to stay under 512MB
```

> "GOGC trades throughput for memory. GOMEMLIMIT (Go 1.19+) is the modern approach — set a memory budget and the runtime adjusts GC pacing. In production, set GOMEMLIMIT and use high GOGC (or off) to let the limit drive GC."

### Go pointer types (full taxonomy)

| Type | Package | Since | Use Case |
|---|---|---|---|
| `*T` | builtin | 1.0 | Standard pointer |
| `unsafe.Pointer` | unsafe | 1.0 | Type-erased pointer, low-level memory |
| `uintptr` | builtin | 1.0 | Integer holding an address, not traced by GC |
| `atomic.Pointer[T]` | sync/atomic | 1.19 | Lock-free concurrent pointer access |
| `weak.Pointer[T]` | weak | 1.24 | Does not prevent GC collection |

---

## 11. Interview Gold Questions

### Q1: `map[string]User` vs `map[string]*User` for 10M users?

**Answer**: For small structs (< ~128 bytes) with read-heavy access, `map[string]User` — value storage eliminates 10M pointer edges the GC must trace, dramatically reducing mark phase duration and p99 (99th percentile) latency. Tradeoff: map rehash is more expensive (copies all values) and mutation requires copy-out/modify/copy-back. For large structs or write-heavy workloads, `map[string]*User` wins on rehash cost. Advanced: use `map[string]int32` indexing into `[]User` slice for best of both.

### Q2: How would you reduce GC pressure in a high-throughput service?

**Answer**: First, profile — `GODEBUG=gctrace=1` and `go tool pprof -alloc_space` to find allocation hotspots. Then: (1) `sync.Pool` for hot-path buffers, (2) value semantics for small structs, (3) pre-allocate slices with known capacity, (4) avoid interface boxing in tight loops, (5) use `[]byte` instead of `string` in parsing paths to avoid copy, (6) tune `GOMEMLIMIT` for a memory budget rather than relying solely on GOGC. The chain: fewer heap allocs → fewer live objects → shorter mark phase → less mark assist → better p99.

### Q3: Explain why `new()` doesn't always mean heap allocation.

**Answer**: `new(T)` allocates memory for type `T` and returns a pointer, but escape analysis decides where. If the pointer never escapes the function (not returned, not sent to a goroutine, not stored in a long-lived location), the compiler allocates on the stack. Similarly `&T{}`. You can verify with `go build -gcflags="-m"`. The compiler and GC handle where storage lives and when it can be reclaimed — you don't pair manual allocation with manual release.

---

## 12. Final Verbal Answer

> "Go is strictly pass-by-value — every function call copies the value you pass in. Even when you pass a pointer, the pointer itself is copied. The function gets its own copy of the address, but both copies point to the same data.
> 
> The compiler decides stack vs heap through escape analysis. It asks: does this variable's address leave the function? If you return a pointer to a local variable, or send it to another goroutine, it escapes to the heap. Otherwise it stays on the stack. You can see the decisions with `go build -gcflags='-m'`.
> 
> Stack allocation is basically free — a couple nanoseconds. Heap allocation is 25-50 nanoseconds plus it creates work for the garbage collector. Go's GC is a concurrent tri-color mark-and-sweep collector. The Stop-The-World pauses are sub-millisecond, so they're rarely the problem. What actually bites you in production is mark assist — when goroutines are allocating during a GC cycle, they get forced to help with the marking before their allocation proceeds. That's where p99 latency spikes come from.
> 
> Slices, maps, and interfaces look like they're passed by reference, but they're not. A slice is a 24-byte header with a pointer, length, and capacity — the header is copied by value, but both copies point to the same backing array. Maps are already pointers under the hood. Interfaces are a two-field struct with type info and a data pointer. In all cases, the value is copied, but internal pointers enable sharing."

---

## 13. Comprehensive Interview Questions

> Full interview question bank (15 questions) → [[questions/T02 Go Memory Allocation - Interview Questions]]

Preview of most frequently asked:

1. **Explain Go's escape analysis. How does the compiler decide stack vs heap?** `[COMMON]`
2. **What's the difference between `new()` and `make()`? Does `new()` always heap-allocate?** `[COMMON]`
3. **How would you reduce GC pressure in a high-throughput Go service?** `[COMMON]`

---

## Quick Recall (test yourself)

> [!info]- 1. What decides stack vs heap in Go?
> **Escape analysis** — the compiler checks whether a value's **address (or a reference) escapes**; non-escaping locals can live on the **stack**, while escaping data is allocated on the **heap**.

> [!info]- 2. What happens when you return `&localVar`?
> The local **escapes** to the **heap** so the returned pointer remains valid after the function returns; the stack frame alone could not outlive the call.

> [!info]- 3. What is the write barrier?
> It is a **GC mechanism** that records or synchronizes **heap pointer updates** so the **concurrent mark phase** does not miss live objects when other goroutines mutate pointers during marking.

---

> See [[Glossary]] for term definitions.
