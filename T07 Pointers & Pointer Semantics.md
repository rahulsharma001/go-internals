# T07 Pointers & Pointer Semantics

> **Reading Guide**: Sections 1-3 and 6 are essential first read (20 min).
> Sections 4-5 deepen understanding (15 min).
> Sections 7-12 are interview-specific — read closer to interview day.
> Section 13 is your comprehensive interview Q&A bank → [[questions/T07 Pointers & Pointer Semantics - Interview Questions]]
> Something not clicking? → [[simplified/T07 Pointers & Pointer Semantics - Simplified]]

---

## 0. Prerequisites

Complete these before starting this topic:

- [[prerequisites/P01 Structs & Struct Memory Layout]]
- [[prerequisites/P02 Methods & Receivers]]
- [[prerequisites/P03 Mutex & Concurrency Safety Basics]]

---

## 1. Concept

A **pointer** is a variable that holds the memory address of another variable. In Go, `*T` is "pointer to T" and `&x` gives you the address of `x`.

Go is **always pass-by-value**. Every function call copies the argument. Pointers let you share data efficiently by copying a small address (8 bytes on 64-bit) instead of copying an entire struct — think of handing someone a sticky note with your house address instead of moving the whole house onto their desk. Anyone with that note can visit the same place and change what's inside.

---

## 2. Core Insight (TL;DR)

**Go has no references — only values.** When you pass a pointer, you're passing a *copy of the address*, not a reference. Caller and callee each hold their own sticky note, but both notes point at the same memory.

The two decisions that show up constantly in services:
1. **Pointer receiver vs value receiver** — whether a method can mutate the struct your handler or repository holds
2. **Return pointer vs return value** — where the data lives (stack vs heap) and what your caller is allowed to keep

---

## 3. Mental Model (Lock this in)

### The Photocopy vs Sticky Note Model

When you pass a **value**, Go photocopies the whole struct. The function gets its own copy.
When you pass a **pointer**, Go passes a sticky note with the shelf location. You and the function are looking at the same `User`, `DB`, or request-scoped struct.

```go
func changeByValue(n int) {
    n = 999  // changes the photocopy only
}

func changeByPointer(n *int) {
    *n = 999  // follows the sticky note, changes the original
}

func main() {
    x := 42
    changeByValue(x)
    fmt.Println(x)  // 42 — original untouched

    changeByPointer(&x)
    fmt.Println(x)  // 999 — original changed
}
```

```
MEMORY TRACE:

main():
  x  ──→  stack: [ 42 ]         address: 0xc0000b6010

changeByValue(x):
  n  ──→  stack: [ 42 ]         address: 0xc0000b6018  ◄── different address, it's a copy
  n = 999:
  n  ──→  stack: [ 999 ]        ◄── only the copy changes, x is untouched

changeByPointer(&x):
  n  ──→  stack: [ 0xc0000b6010 ]  ◄── n holds x's address (8 bytes copied)
  *n = 999:
  follows 0xc0000b6010 ──→ [ 999 ]  ◄── changes x directly through the address

After both calls:
  x  ──→  stack: [ 999 ]        ◄── only changeByPointer affected x
```

Passing by value is handing someone a photocopy — they can scribble on it all day and your original stays clean. Passing a pointer is handing them the address — they show up and rearrange the furniture.

### The Mistake That Teaches You

```go
type User struct {
    Name  string
    Email string
}

func setAdmin(u User) {
    u.Name = "admin"  // BUG: modifies a copy
}

func main() {
    user := User{Name: "rahul"}
    setAdmin(user)
    fmt.Println(user.Name)  // "rahul" — still unchanged!
}
```

```
MEMORY TRACE:

main():
  user ──→ stack: [ Name: "rahul" ]

setAdmin(user) — Go copies the ENTIRE User struct:

setAdmin():
  u    ──→ stack: [ Name: "rahul" ]   ◄── brand new copy
  u.Name = "admin":
  u    ──→ stack: [ Name: "admin" ]   ◄── only this copy changes

Function returns → copy is gone.
main's 'user' was never touched.
```

**Fix:** Pass a pointer.

```go
func setAdmin(u *User) {
    u.Name = "admin"  // follows pointer, modifies original
}

func main() {
    user := User{Name: "rahul"}
    setAdmin(&user)
    fmt.Println(user.Name)  // "admin" — changed!
}
```

---

## 4. How It Actually Works (Internals) [INTERMEDIATE → ADVANCED]

### 4.1 Pointer Size and Layout

On a 64-bit system, every pointer is exactly **8 bytes** regardless of what it points to. A `*User` with twenty fields is still the same 8 bytes as a `*int`.

```go
package main

import (
    "fmt"
    "unsafe"
)

type User struct {
    Name  string // 16 bytes (ptr + len)
    Email string // 16 bytes
    Age   int    // 8 bytes
}

func main() {
    u := User{Name: "rahul", Email: "r@test.com", Age: 28}
    p := &u

    fmt.Println("Size of User:", unsafe.Sizeof(u))   // 40
    fmt.Println("Size of *User:", unsafe.Sizeof(p))   // 8
    fmt.Printf("u lives at: %p\n", &u)               // 0xC000012040
    fmt.Printf("p holds:    %p\n", p)                 // 0xC000012040 (same!)
    fmt.Printf("p lives at: %p\n", &p)                // 0xC000012060 (p itself is elsewhere)
}
```

```
Step 1: u := User{...}
  stack 0xC000012040: [ "rahul" | "r@test.com" | 28 ]    ← 40 bytes

Step 2: p := &u
  stack 0xC000012060: [ 0xC000012040 ]                    ← 8 bytes (just the address of u)
                        │
                        └──→ same 40-byte User above

KEY INSIGHT:
  Passing u to a function:  copies all 40 bytes into callee's stack frame
  Passing p to a function:  copies 8 bytes (the address) → callee sees same struct
```

> **In plain English:** Every sticky note is the same size — a Post-It that says "check locker 5" and one that says "check warehouse building 3" are both tiny slips of paper. The pointer is the Post-It. What it points at might be 40 bytes or 4000 bytes, but the note is always 8.

### 4.2 The & and * Operators Under the Hood

`&x` means "give me the address of x." The CPU generates a `LEA` (Load Effective Address) instruction.
`*p` means "follow this address and read/write what's there." The CPU generates a `MOV` through the pointer.

```go
package main

import "fmt"

func main() {
    x := 42
    p := &x         // p now holds x's address
    fmt.Println(*p) // 42 — dereference: follow the address, read the value
    *p = 100        // dereference + write: follow the address, overwrite
    fmt.Println(x)  // 100 — x changed because p pointed at it
}
```

```
Step 1: x := 42
  stack: [ x = 42 ]  at 0xA0

Step 2: p := &x    (LEA instruction — "load address of x into p")
  stack: [ x = 42 ]  at 0xA0
         [ p = 0xA0 ] at 0xA8       ← p is its own variable, holding x's address

Step 3: *p = 100   (MOV through pointer — "write 100 at the address p holds")
  CPU reads p → gets 0xA0
  CPU writes 100 at 0xA0
  stack: [ x = 100 ] at 0xA0        ← x changed!
         [ p = 0xA0 ] at 0xA8       ← p unchanged — it still points at the same x

Step 4: fmt.Println(x) → reads 0xA0 → prints 100
```

> **In plain English:** `&` is like asking "what's the street address of this building?" You get a number. `*` is like driving to that street address and walking inside. You can read what's there (`*p`) or change what's there (`*p = 100`).

### 4.3 Escape Analysis and Stack vs Heap (Where Pointers Really Matter)

The Go compiler decides whether a variable lives on the **stack** (fast, auto-freed when function returns) or **heap** (slower, garbage-collected). The core rule:

**If a pointer to a local variable outlives the function, the variable is moved to the heap.**

```go
package main

import "fmt"

type Config struct {
    Addr        string
    ReadTimeout int
}

func newConfig() *Config {
    c := Config{Addr: ":8080", ReadTimeout: 30}
    return &c // c escapes! compiler moves it to heap
}

func localOnly() int {
    x := 42
    p := &x   // p does NOT escape — stays within this function
    *p += 8
    return *p // returns the value, not the pointer — x stays on stack
}

func main() {
    cfg := newConfig()
    fmt.Println(cfg.Addr) // ":8080"

    val := localOnly()
    fmt.Println(val) // 50
}
```

```
newConfig() — pointer ESCAPES:

  Step 1: c := Config{...}
    Compiler sees: "you're returning &c — this pointer outlives the function"
    Decision: allocate c on HEAP, not stack

  Step 2: return &c
    heap 0xC000014040: [ Addr: ":8080" | ReadTimeout: 30 ]
    Returns pointer 0xC000014040 to caller
    Stack frame of newConfig() is gone, but the data survives on the heap

  Step 3: main's cfg = 0xC000014040
    cfg ──→ heap: [ Addr: ":8080" | ReadTimeout: 30 ]   ← alive, GC tracks it

localOnly() — pointer does NOT escape:

  Step 1: x := 42, p := &x
    stack: [ x = 42 ] [ p = 0x... (x's stack addr) ]

  Step 2: *p += 8 → x becomes 50

  Step 3: return *p → returns the VALUE 50 (not the pointer)
    Stack frame dies. x and p are gone. No heap allocation needed.

DIFFERENCE:
  newConfig: returned a pointer → heap alloc → GC cost
  localOnly: kept pointer local → stack only → zero GC cost
```

You can verify this yourself:
```bash
go build -gcflags="-m" main.go
# ./main.go:12:2: moved to heap: c       ← newConfig's c escaped
# ./main.go:17:2: x does not escape      ← localOnly's x stayed on stack
```

> **In plain English:** Your function's stack frame is like a hotel room — checkout happens automatically when you return. If you hand someone a key card (pointer) to that room and they try to use it after checkout, the room is gone. So Go moves the data to a permanent apartment (heap) whenever it detects you're handing out keys that outlive your stay. The apartment costs more (GC has to clean it), but the data survives.

### 4.4 Nil Pointers — What Actually Happens at the Hardware Level

Every pointer's zero value is `nil`. Dereferencing `nil` causes a **panic**.

```go
package main

import "fmt"

type User struct {
    Name string
}

func greet(u *User) string {
    return "Hello, " + u.Name // if u is nil → PANIC
}

func main() {
    var u *User // declared but never assigned — nil
    fmt.Println(u == nil) // true
    fmt.Println(greet(u)) // PANIC: nil pointer dereference
}
```

```
Step 1: var u *User
  stack: [ u = nil (0x0) ]     ← u exists, but holds address 0x0

Step 2: greet(u)
  Go copies u (8 bytes: 0x0) into greet's parameter
  greet's u: [ 0x0 ]

Step 3: u.Name
  CPU tries to read memory at address 0x0 + offset_of(Name)
  Address 0x0 is UNMAPPED memory — the OS never assigns real data to address 0
  CPU triggers a SIGSEGV (segmentation fault)
  Go runtime catches the signal → converts to panic:
    "runtime error: invalid memory address or nil pointer dereference"

SAFE PATTERN:
  func greet(u *User) string {
      if u == nil {
          return "Hello, stranger"
      }
      return "Hello, " + u.Name
  }
```

> **In plain English:** A nil pointer is a sticky note that says "check locker 0" — but there is no locker 0. When you walk over and try to open it, the building security (the OS) stops you. Go catches that and turns it into a panic instead of crashing the whole process silently.

### 4.5 Passing Pointers Through Function Calls — A Backend Scenario

Here's what actually happens in memory when your HTTP handler calls a service that calls a repository — all sharing the same `User` via pointers:

```go
package main

import "fmt"

type User struct {
    Name  string
    Email string
}

func handler() {
    u := &User{Name: "rahul", Email: "old@test.com"}
    fmt.Printf("handler: u at %p, u.Email = %s\n", u, u.Email)
    service(u)
    fmt.Printf("handler: u.Email = %s\n", u.Email) // sees the change!
}

func service(u *User) {
    fmt.Printf("service: u at %p (same address!)\n", u)
    u.Email = "new@test.com"
    repo(u)
}

func repo(u *User) {
    fmt.Printf("repo:    u at %p (still same!)\n", u)
    u.Name = "Rahul K"
}

func main() {
    handler()
}
// Output:
// handler: u at 0xC000010030, u.Email = old@test.com
// service: u at 0xC000010030 (same address!)
// repo:    u at 0xC000010030 (still same!)
// handler: u.Email = new@test.com
```

```
Step 1: handler creates User on heap (escape analysis — &User{} literal escapes)
  heap 0xC000010030: [ Name: "rahul" | Email: "old@test.com" ]

  handler's stack: [ u = 0xC000010030 ]   ← 8-byte pointer

Step 2: service(u) — Go copies the 8-byte pointer
  service's stack: [ u = 0xC000010030 ]   ← DIFFERENT stack slot, SAME address
                          │
                          └──→ heap: [ Name: "rahul" | Email: "old@test.com" ]

Step 3: u.Email = "new@test.com" — service writes through the pointer
  heap 0xC000010030: [ Name: "rahul" | Email: "new@test.com" ]   ← changed!
  Both handler's u and service's u point here → both see the change

Step 4: repo(u) — another 8-byte copy
  repo's stack: [ u = 0xC000010030 ]      ← THIRD copy of the address, same target
  u.Name = "Rahul K"
  heap 0xC000010030: [ Name: "Rahul K" | Email: "new@test.com" ]

Step 5: Back in handler
  handler reads u.Email → follows 0xC000010030 → "new@test.com" ← repo + service changes visible

THREE STACK FRAMES, THREE COPIES OF THE POINTER, ONE SHARED USER:
  handler stack: [ u = 0xC000010030 ] ──┐
  service stack: [ u = 0xC000010030 ] ──┤──→ heap: [ "Rahul K" | "new@test.com" ]
  repo    stack: [ u = 0xC000010030 ] ──┘
```

> **In plain English:** Think of a patient's medical chart in a hospital. The chart lives in one place (the heap). When the patient moves from reception → doctor → lab, each person gets a note saying "chart is in room 3." They each have their own copy of the note, but they all read and write the same chart. That's how handler → service → repo shares a `*User`.

---

## 5. Key Rules & Behaviors

### Rule 1: Pointer Receiver vs Value Receiver

A **value receiver** gets a copy of the struct. A **pointer receiver** gets the address and can modify the original.

**WHY this matters (Section 4.1, Section 4.5):** From Section 4.1, we know a struct might be 40+ bytes. A value receiver copies all of it into a new stack slot. A pointer receiver copies 8 bytes (the address). But more importantly — from Section 4.5 — only the pointer receiver writes to the *same* memory the caller holds.

```go
package main

import "fmt"

type Counter struct {
    n int
}

func (c Counter) ValueInc() {
    c.n++
    fmt.Printf("  inside ValueInc: c.n = %d (at %p — this is a COPY)\n", c.n, &c)
}

func (c *Counter) PointerInc() {
    c.n++
    fmt.Printf("  inside PointerInc: c.n = %d (at %p — this is the ORIGINAL)\n", c.n, c)
}

func main() {
    c := Counter{n: 0}
    fmt.Printf("before: c.n = %d (at %p)\n", c.n, &c)

    c.ValueInc()
    fmt.Printf("after ValueInc: c.n = %d\n", c.n) // still 0!

    c.PointerInc()
    fmt.Printf("after PointerInc: c.n = %d\n", c.n) // 1
}
// Output:
// before: c.n = 0 (at 0xC0000A6058)
// inside ValueInc: c.n = 1 (at 0xC0000A6070 — this is a COPY)
// after ValueInc: c.n = 0
// inside PointerInc: c.n = 1 (at 0xC0000A6058 — this is the ORIGINAL)
// after PointerInc: c.n = 1
```

```
c.ValueInc():
  main's c at 0x58: [ n: 0 ]
  ValueInc's c at 0x70: [ n: 0 ] ← COPY (different address!)
  c.n++ → copy becomes [ n: 1 ]
  Return → copy dies, main's c still [ n: 0 ]

c.PointerInc():
  main's c at 0x58: [ n: 0 ]
  PointerInc receives: pointer 0x58 (8 bytes)
  c.n++ → writes at 0x58 → main's c becomes [ n: 1 ]
```

> **In plain English:** Value receiver is like sending someone a photocopy of a form — they fill it in, but your original is untouched. Pointer receiver is like handing them the actual form — what they write stays.

### Rule 2: Method Sets Determine Interface Satisfaction

This is the biggest pointer trap in Go when wiring handlers to interfaces.

- Type `T` (value) can only call methods with **value receivers**
- Type `*T` (pointer) can call methods with **both** value and pointer receivers

**WHY (Section 4.1, Section 4.3):** A pointer receiver needs a *stable memory address* to write through. When you store a bare `T` inside an interface, Go might have placed it somewhere that doesn't have a stable address (e.g., a temporary copy). Go refuses to silently take its address because that would hide a heap allocation and create a pointer the caller doesn't know about.

```go
type UserStore interface {
    Save(name string) error
}

type PostgresStore struct{ dsn string }

func (s *PostgresStore) Save(name string) error {
    fmt.Println("saving", name, "to", s.dsn)
    return nil
}

func main() {
    // var _ UserStore = PostgresStore{dsn: "pg://localhost"}   // COMPILE ERROR
    var _ UserStore = &PostgresStore{dsn: "pg://localhost"}     // OK
}
```

```
Method set of PostgresStore (value):
  { }                    ← Save has a pointer receiver, not included

Method set of *PostgresStore (pointer):
  { Save(string) error } ← pointer type includes BOTH receiver kinds

WHY the compiler rejects PostgresStore{}:

  Step 1: You write:  var s UserStore = PostgresStore{dsn: "pg://localhost"}
  Step 2: Go stores the struct inside the interface value (copies it)
  Step 3: Save needs *PostgresStore — it needs an address to potentially write to
  Step 4: The copy inside the interface doesn't have a stable, known address
  Step 5: Go could silently do &copy — but that would:
          a) Create a heap allocation you didn't ask for
          b) Give Save a pointer to a COPY, not your original
          c) Any mutations would be invisible to the caller
  Step 6: So Go says: COMPILE ERROR — use &PostgresStore{} instead

                   ┌─────────────────────────────┐
  &PostgresStore{} │ iface: [type: *PostgresStore │ data: → heap obj] │  ← address is stable
                   └─────────────────────────────┘
                   ┌─────────────────────────────┐
  PostgresStore{}  │ iface: [type: PostgresStore  │ data: copy]       │  ← no stable address
                   └─────────────────────────────┘
                   Can't call pointer receiver methods on this copy!
```

> **In plain English:** Think of venue security. `*PostgresStore` is a real ID with your home address — the bouncer lets you in because you can be contacted. `PostgresStore` is a photocopy — the bouncer won't let it in because if someone needs to reach you (write to your address), the photocopy doesn't lead anywhere real.

### Rule 3: Don't Return Pointers to Loop Variables (Pre-Go 1.22)

Before Go 1.22, the loop variable was reused across iterations. Taking its address gave you a pointer to the same slot every time.

**WHY (Section 4.2):** `&i` gives you the address of `i`. If there's only ONE `i` variable reused across all iterations (pre-1.22 behavior), every `&i` returns the same address. After the loop, that address holds the final value.

```go
// Go < 1.22: BUG — all pointers alias the same variable
var ptrs []*int
for i := 0; i < 3; i++ {
    ptrs = append(ptrs, &i)
}
fmt.Println(*ptrs[0], *ptrs[1], *ptrs[2]) // 3, 3, 3 — all point to same i

// Go >= 1.22: FIXED — each iteration gets its own i
// Same code prints: 0, 1, 2
```

```
Go < 1.22 — ONE loop variable reused:

  Iteration 0: i = 0 at 0xA0 → ptrs[0] = &i = 0xA0
  Iteration 1: i = 1 at 0xA0 → ptrs[1] = &i = 0xA0  ← SAME address!
  Iteration 2: i = 2 at 0xA0 → ptrs[2] = &i = 0xA0  ← SAME address!
  Loop ends:   i = 3 at 0xA0

  ptrs[0] ──→ 0xA0: [ 3 ]
  ptrs[1] ──→ 0xA0: [ 3 ]   ← all three read the same slot → all get 3
  ptrs[2] ──→ 0xA0: [ 3 ]

Go >= 1.22 — FRESH variable per iteration:

  Iteration 0: i₀ = 0 at 0xA0 → ptrs[0] = 0xA0
  Iteration 1: i₁ = 1 at 0xA8 → ptrs[1] = 0xA8  ← different address!
  Iteration 2: i₂ = 2 at 0xB0 → ptrs[2] = 0xB0  ← different address!

  ptrs[0] ──→ 0xA0: [ 0 ]
  ptrs[1] ──→ 0xA8: [ 1 ]   ← each has its own slot
  ptrs[2] ──→ 0xB0: [ 2 ]
```

Same bug class showed up when scanning database rows: `for rows.Next() { rows.Scan(&row); results = append(results, &row) }` — every pointer aliases the same `row`.

> **In plain English:** Pre-1.22, the `for` loop had ONE locker and kept putting new items in it each iteration. Every sticky note you wrote said "check locker A" — so after the loop, everyone opens locker A and finds whatever was put in last. Go 1.22 gives each iteration its own locker.

### Rule 4: Pointer to Interface Is Almost Always Wrong

You almost never need `*UserStore` (pointer to interface). The interface value is already a small two-word container.

**WHY (Section 4.1):** An interface value is 16 bytes: a type pointer (8B) + a data pointer (8B). It already carries a pointer to your concrete type. Adding `*` wraps a pointer around something that's already pointer-like — useless indirection.

```go
package main

import "fmt"

type UserStore interface {
	Save(name string)
}

type MemStore struct{ data []string }
func (m *MemStore) Save(name string) { m.data = append(m.data, name) }

// WRONG — extra indirection, confuses every reader
func registerWrong(store *UserStore) { (*store).Save("alice") }

// RIGHT — interface already carries a pointer to the concrete store
func registerRight(store UserStore) { store.Save("bob") }

func main() {
	var s UserStore = &MemStore{}
	registerWrong(&s)
	registerRight(s)
	fmt.Println(s.(*MemStore).data) // [alice bob]
}
```

```
What an interface value actually looks like in memory (16 bytes):

  ┌───────────────────┬───────────────────┐
  │ type ptr (8B)     │ data ptr (8B)     │  ← the interface IS a container with a pointer
  │ → *PostgresStore  │ → heap: {dsn...}  │
  └───────────────────┴───────────────────┘

Passing UserStore: copies 16 bytes (the two pointers above). Cheap.

Passing *UserStore: copies 8 bytes (a pointer to the 16-byte container above).
  ┌──────────┐     ┌──────────────┬──────────────┐
  │ ptr (8B) │ ──→ │ type ptr     │ data ptr     │ ──→ actual data
  └──────────┘     └──────────────┴──────────────┘
  You saved 8 bytes of copying but added an extra dereference at EVERY method call.
  Net result: slower, harder to read, and breaks nil comparison semantics.
```

> **In plain English:** An interface is already the envelope with the recipient's address written inside. Putting that envelope inside another envelope doesn't help — it just makes the mailman open two envelopes instead of one.

### Rule 5: sync.Mutex Must Never Be Copied

Types containing `sync.Mutex` must use pointer receivers and never be passed by value. Copying a locked mutex gives you a second mutex with independent state.

**WHY (Section 4.1, Section 4.5):** From Section 4.1, passing by value copies every byte of the struct. A `sync.Mutex` is a struct with internal state fields (lock state, waiter count). Copying those bytes creates a second, independent mutex. From Section 4.5, only pointer passing ensures all callers operate on the same lock.

```go
package main

import (
    "fmt"
    "sync"
)

type SafeCache struct {
    mu sync.Mutex
    m  map[string]int
}

// WRONG: value receiver copies the mutex
func (s SafeCache) GetBroken(key string) int {
    s.mu.Lock()         // locks the COPY's mutex
    defer s.mu.Unlock()
    return s.m[key]     // reads without real protection
}

// RIGHT: pointer receiver — everyone shares one mutex
func (s *SafeCache) Get(key string) int {
    s.mu.Lock()
    defer s.mu.Unlock()
    return s.m[key]
}

func main() {
    cache := &SafeCache{m: map[string]int{"x": 1}}
    fmt.Println(cache.Get("x")) // 1 — safe
}
```

```
Value receiver (WRONG) — what happens in memory:

  original at 0xA0: [ mu: {state: locked, waiters: 2} | m: 0xB0 ]
                                                         │
  GetBroken() copies ALL bytes:                          │
  copy at 0xC0:     [ mu: {state: locked, waiters: 2} | m: 0xB0 ]
                              ↑                          ↑
                     INDEPENDENT lock state!    Points at same map data

  Result: Two goroutines both call GetBroken():
    goroutine 1: locks copy₁.mu → reads m
    goroutine 2: locks copy₂.mu → reads m    ← no contention because DIFFERENT mutexes!
    RACE CONDITION: both read/write the same map without real synchronization

Pointer receiver (RIGHT):

  cache at 0xA0: [ mu: {state: unlocked} | m: 0xB0 ]
  Get() receives pointer 0xA0 → everyone locks THE SAME mu
```

`go vet` detects this: `call of GetBroken copies lock value: SafeCache contains sync.Mutex`

> **In plain English:** Photocopying a padlock gives you a different lock entirely — it doesn't share a key with the original. Now you have two goroutines each holding their own lock, both thinking they have exclusive access, but neither is actually blocking the other.

---

## 6. Code Examples (Show, Don't Tell)

### Example 1: Basic Pointer Operations — Traced Through Memory

The foundation for everything else. This example traces `&`, `*`, and passing pointers step by step.

```go
package main

import "fmt"

func double(p *int) {
    *p = *p * 2
}

func main() {
    score := 50
    fmt.Println("before:", score)

    double(&score)
    fmt.Println("after:", score) // 100

    double(&score)
    fmt.Println("after 2x:", score) // 200
}
```

```
Step 1: score := 50
  main's stack:
    score at 0xA0: [ 50 ]

Step 2: double(&score)
  Go copies 8 bytes (the address 0xA0) into double's parameter p
  double's stack:
    p at 0xB0: [ 0xA0 ]    ← p holds score's address

Step 3: *p = *p * 2
  Read:  *p → follow 0xA0 → read 50
  Compute: 50 * 2 = 100
  Write: *p → follow 0xA0 → write 100
  main's stack:
    score at 0xA0: [ 100 ]  ← changed through the pointer!

Step 4: Back in main, score is 100

Step 5: double(&score) again
  same process → 100 * 2 = 200
  score at 0xA0: [ 200 ]
```

### Example 2: Mutating a Struct via Pointer — PATCH /users/:id Shape

What your handler does after binding a JSON request and calling the service layer.

```go
package main

import "fmt"

type User struct {
    Name  string
    Email string
    Role  string
}

func promote(u *User) {
    u.Role = "admin"
}

func updateEmail(u *User, newEmail string) {
    u.Email = newEmail
}

func main() {
    u := &User{Name: "rahul", Email: "old@test.com", Role: "viewer"}
    fmt.Printf("before: %+v\n", *u)

    promote(u)
    updateEmail(u, "new@test.com")
    fmt.Printf("after: %+v\n", *u)
    // after: {Name:rahul Email:new@test.com Role:admin}
}
```

```
Step 1: u := &User{...} — escape analysis moves User to heap (we return/share it)
  heap 0xC000014040: [ Name:"rahul" | Email:"old@test.com" | Role:"viewer" ]
  main's stack: u = 0xC000014040

Step 2: promote(u) — copies 8-byte pointer
  promote's stack: u = 0xC000014040
  u.Role = "admin" → writes at 0xC000014040 + offset(Role)
  heap: [ Name:"rahul" | Email:"old@test.com" | Role:"admin" ]

Step 3: updateEmail(u, "new@test.com") — copies pointer + string
  heap: [ Name:"rahul" | Email:"new@test.com" | Role:"admin" ]

Step 4: main reads *u → sees both changes (same heap address)
```

### Example 3: Returning a Pointer — Constructor Pattern

This is the standard Go constructor: create a struct, configure it, return a pointer.

```go
package main

import "fmt"

type DBPool struct {
    DSN     string
    MaxConn int
}

func NewDBPool(dsn string, maxConn int) *DBPool {
    pool := DBPool{DSN: dsn, MaxConn: maxConn}
    return &pool // pool escapes to heap — safe in Go
}

func main() {
    pool := NewDBPool("postgres://localhost/mydb", 25)
    fmt.Printf("pool at %p: %+v\n", pool, *pool)
}
```

```
Step 1: NewDBPool called
  Compiler detects: &pool is returned → pool must escape to heap

Step 2: pool := DBPool{...} — allocated directly on heap (compiler optimization)
  heap 0xC000010060: [ DSN:"postgres://localhost/mydb" | MaxConn: 25 ]

Step 3: return &pool
  Returns 0xC000010060 to main
  NewDBPool's stack frame is destroyed, but the data lives on the heap

Step 4: main's pool = 0xC000010060
  pool ──→ heap: [ DSN:"postgres://localhost/mydb" | MaxConn: 25 ]
  GC will free this when no live pointer references it anymore

Verify: go build -gcflags="-m"
  → "moved to heap: pool"
```

### Example 4: The Nil Interface Trap — Pointer Angle

The most subtle pointer-related bug in Go services. Your handler returns a typed nil pointer as `error`, but the nil check fails.

```go
package main

import "fmt"

type APIError struct{ Code int; Msg string }
func (e *APIError) Error() string { return fmt.Sprintf("%d: %s", e.Code, e.Msg) }

func validate(name string) error {
    var apiErr *APIError // nil pointer, but TYPED
    if name == "" {
        apiErr = &APIError{Code: 400, Msg: "name required"}
    }
    return apiErr // BUG: returns non-nil interface even when apiErr is nil!
}

func main() {
    err := validate("rahul") // name is fine, no error created
    if err != nil {
        fmt.Println("unexpected error:", err) // THIS RUNS
    }
}
```

```
Step 1: validate("rahul")
  var apiErr *APIError → stack: [ apiErr = nil (0x0) ]
  name != "" → skip the if block → apiErr stays nil

Step 2: return apiErr
  Go wraps apiErr into an interface{} (error is an interface):
    interface value: [ type: *APIError | data: nil ]
                            ↑                ↑
                      NOT nil!          nil pointer

Step 3: main checks: err != nil
  err is: [ type: *APIError | data: nil ]
  An interface is nil ONLY when BOTH type AND data are nil
  Here type = *APIError (not nil) → so err != nil is TRUE

  err ──→ [ type: *APIError | data: nil ]   ← non-nil interface!
  nil ──→ [ type: nil        | data: nil ]   ← this is what nil looks like

FIX: return nil explicitly
  func validate(name string) error {
      if name == "" {
          return &APIError{Code: 400, Msg: "name required"}
      }
      return nil  // ← returns [ type: nil | data: nil ] → truly nil
  }
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

```go
func modify(s *[]int) {
    *s = append(*s, 4)
    (*s)[0] = 99
}

func main() {
    nums := []int{1, 2, 3}
    modify(&nums)
    fmt.Println(nums)
}
```

What prints? Think about it before checking.

> [!success]- Answer
> `[99 2 3 4]` — The pointer lets us modify the original slice header (append updates len) AND the backing array (index 0 changed). The `*s = append(*s, 4)` dereferences the pointer, appends, and writes the new slice header back. `(*s)[0] = 99` dereferences and modifies the first element of the backing array.

### Tier 2: Fix the Bug (5 min)

```go
type DB struct {
    conn string
}

func (db DB) Connect(dsn string) {
    db.conn = dsn
}

func main() {
    db := DB{}
    db.Connect("postgres://localhost/mydb")
    fmt.Println(db.conn)  // prints empty string — why?
}
```

Fix the `Connect` method so it actually stores the connection string.

> [!success]- Answer
> Change the value receiver to a pointer receiver:
> ```go
> func (db *DB) Connect(dsn string) {
>     db.conn = dsn
> }
> ```
> The value receiver `(db DB)` gets a copy of the struct. Setting `db.conn` modifies the copy, not the original. With `(db *DB)`, the method receives the address and modifies the original struct.

### Tier 3: Build It (15 min)

Implement **`WalkMiddleware`**: a tiny stack of `func(http.Handler) http.Handler` that lets you `Use(logging)`, `Use(auth)`, then `Then` your handler. Internals should use pointer semantics where the chain must mutate shared state (e.g., a slice of middleware in a `*Chain` struct), and you should be able to explain why a value receiver on the builder would break updates.

> Full solutions with explanations → [[exercises/T07 Pointers & Pointer Semantics - Exercises]]

---

## 7. Edge Cases & Gotchas

| Gotcha | What Happens | Because (Section 4 link) | Fix |
|--------|-------------|-------------------|-----|
| Nil `*User` before `json.Encode` | Panic: nil pointer dereference | Section 4.4 — dereferencing nil reads address 0x0, which is unmapped memory. CPU triggers SIGSEGV, Go converts to panic | Guard with `if u == nil` before encoding; return 400 early if binding produced nil |
| Value receiver on mutex-backed cache | Two independent locks; race under load | Section 4.1 + Section 4.5 — value receiver copies every byte of the struct, including the mutex's internal state. Two goroutines each lock their own copy — no real synchronization | Pointer receivers on all methods; never pass the struct by value |
| Comparing `*User` with `==` | Compares addresses, not fields | Section 4.1 — a pointer IS an address (8 bytes). `==` on two pointers checks if both hold the same address, not whether the structs they point at have equal fields | Compare IDs explicitly, or use `reflect.DeepEqual`, or dereference and compare `*a == *b` (only works if all fields are comparable) |
| Returning typed nil `*APIError` as `error` | `if err != nil` is true even though data pointer is nil | Section 4.4 — the interface wraps `[type: *APIError, data: nil]`. The type slot is non-nil, so the interface is non-nil | Always `return nil` for the no-error path; never return a typed nil pointer through an interface |
| `&i` in `for` loop (pre-Go 1.22) | Every pointer aliases the same loop variable | Section 4.2 — `&i` gives the address of `i`. Pre-1.22, there's ONE `i` variable reused each iteration, so every `&i` is the same address | Upgrade to Go 1.22+, or copy: `v := i; ptrs = append(ptrs, &v)` |
| `&m["key"]` on a map value | Compile error: can't take address | Section 4.2 — `&` gives a stable address, but map values get relocated during growth/evacuation (runtime moves values between buckets). A pointer from `&` would become dangling after growth | Copy to local: `u := m["key"]`; edit; write back `m["key"] = u` |
| Writing to a nil map | `panic: assignment to entry in nil map` | Section 4.4 — a nil pointer has no backing structure. A nil map has no underlying `hmap` allocated — no buckets to write to. Dereferencing nil storage triggers the same class of crash as nil pointer | Initialize with `make(map[K]V)` or a literal `map[K]V{}` before first store |

### Gotcha Deep Dive: Map Value Addressability

This one deserves a memory trace because it trips up nearly everyone:

```go
m := map[string]User{"a": {Name: "rahul"}}
// m["a"].Name = "admin"  // COMPILE ERROR: cannot take address of m["a"]

u := m["a"]       // copy the value out
u.Name = "admin"  // modify the copy
m["a"] = u        // write it back
fmt.Println(m["a"].Name) // "admin"
```

```
WHY you can't write m["a"].Name directly — traced through memory:

  Step 1: stack 0xC000060000: m = ptr → hmap at 0xC000010000 → buckets at 0xC000080000
    hash("a", hash0) → 0xF3...7B
    bucket = 0xF3...7B & (2^0 - 1) = 0 → bucket #0
    tophash 0xF3 found at slot 0 → User{Name:"rahul"} at 0xC000080030

  Step 2: m["a"].Name = "admin" would need to:
    a) Find bucket #0, slot 0 (done above)
    b) Take pointer: ptr = 0xC000080030 (address of User inside bucket)
    c) Write "admin" to ptr.Name

  BUT: if another insert triggers growth BETWEEN step (b) and (c):
    New bucket array allocated at 0xC000090000
    "a" evacuated to new bucket → now at 0xC000090158
    ptr is still 0xC000080030 → old bucket → DANGLING POINTER
    Writing to ptr.Name corrupts freed memory

  Go prevents this at compile time by refusing to give you an address
  into a map's internal storage.

FIX: copy-edit-write pattern
  u := m["a"]    ← runtime copies User from 0xC000080030 onto stack (safe)
  u.Name = ...   ← modify the stack copy
  m["a"] = u     ← runtime handles insertion into correct bucket safely
```

> **In plain English:** You can't edit a document while it's still clipped inside a filing cabinet drawer — the drawer might get reorganized while you're writing. Pull the document out, make your changes, and slide it back in.

### Gotcha Deep Dive: Nil Pointer in Handler Chain

This is the most common production panic in Go HTTP services:

```go
func (h *Handler) GetUser(w http.ResponseWriter, r *http.Request) {
    user, err := h.repo.FindByID(r.Context(), id)
    if err != nil {
        http.Error(w, "not found", 404)
        return // CRITICAL: must return here
    }
    // if you forget the return above and user is nil...
    json.NewEncoder(w).Encode(user) // PANIC if user is nil
}
```

```
What happens when user is nil:

  Step 1: user = nil (FindByID returned nil, *User)
  Step 2: json.NewEncoder(w).Encode(user)
    Encode calls user's MarshalJSON or uses reflection
    Reflection tries to follow the pointer: *user
    user holds 0x0 (nil)
    CPU reads address 0x0 → SIGSEGV → panic

  The panic crashes this goroutine.
  If you have no recover() middleware, the HTTP server
  catches it and returns 500 — but your logs show a panic stack trace.

SAFE PATTERN:
  if err != nil {
      http.Error(w, "not found", 404)
      return    ← exit the handler entirely
  }
  // user is guaranteed non-nil here
  json.NewEncoder(w).Encode(user)
```

### Gotcha Deep Dive: Typed Nil Pointer Returned as `error`

```go
func validate(name string) error {
    var apiErr *APIError // nil pointer, but typed
    if name == "" {
        apiErr = &APIError{Code: 400, Msg: "name required"}
    }
    return apiErr // BUG when name is valid!
}
```

```
validate("rahul") — name is valid, apiErr stays nil:

  Step 1: var apiErr *APIError → stack: [ nil (0x0) ]
  Step 2: name != "" → skip if block → apiErr is still nil

  Step 3: return apiErr → Go wraps into error interface:
    interface: [ type: *APIError | data: nil ]
                       ↑               ↑
                  NOT nil!         nil pointer

  Step 4: caller checks err != nil
    [ type: *APIError | data: nil ]  ← type slot is non-nil
    [ type: nil        | data: nil ]  ← what nil error looks like
    Different → err != nil is TRUE → caller thinks there's an error!

FIX:
  if apiErr != nil { return apiErr }
  return nil  // → [ type: nil | data: nil ] → truly nil
```

---

## 8. Performance & Tradeoffs

Picture a typical HTTP stack: `ListenConfig` + middleware structs + a fat `AppContext` with clients. Whether you pass those by pointer or by value changes how much data gets copied at the handler boundary and whether the GC sees extra heap objects.

| Approach | Copy Cost | Heap Alloc? | GC Pressure | When to use in handlers/services |
|----------|-----------|-------------|-------------|----------------------------------|
| Pass value (small struct, think ≤64B) | Low — a few words | Usually stays on stack | Minimal | `type TraceID [16]byte`, tiny DTO fragments, immutable value objects |
| Pass pointer (large struct or shared mutable state) | Always 8 bytes | Maybe — escape analysis | Higher if everything escapes | `*sql.DB`, `*User`, request-scoped structs you mutate, anything with `sync.Mutex` |
| Return value | Size of struct | Often stack | Low | Small result structs (`bool, int` pairs, lightweight stats) |
| Return pointer | 8 bytes to caller | Yes when compiler moves value to heap | Higher | Constructors returning `*Repository`, `*ListenConfig`, anything big or nil-able |

**Concrete sizes (64-bit, rough mental anchors):**
- `time.Time` is 24 bytes — still fine by value when you're not mutating it.
- A minimal `User` with a few strings is already multiple words; by the time you add slices for roles/permissions you're often past the "tiny value" comfort zone — pointers keep handler signatures stable.
- Anything embedding `sync.Mutex` or `sync.RWMutex` — always pointer receivers and pointer fields; copying would duplicate locks.

**Rule of thumb for APIs you actually ship:**
- Handler receives `http.ResponseWriter` + `*http.Request` (stdlib already chose pointers for the request body you read).
- Service methods that mutate repository state or counters → pointer receivers.
- Pure helpers on small immutable types → values are fine and can reduce GC churn.

---

## 9. Common Misconceptions

| Misconception | Reality |
|--------------|---------|
| "I passed `*http.Request`, so Go used pass-by-reference" | Still pass-by-value — you copied an 8-byte pointer. Both caller and `ServeHTTP` share the same request struct because the addresses match. |
| "`new(ListenConfig)` always hits the heap" | `new` is sugar for zero value + pointer; escape analysis decides stack vs heap based on whether the pointer escapes your function. |
| "`&local` inside a handler always allocates" | If you only pass that pointer to callees that don't store it past the handler return, it often stays stack-fast. Profile before guessing. |
| "Pointers are free performance" | Indirection costs cache misses; heap pointers add GC work. A storm of tiny heap allocations from unnecessary `&T{}` in hot paths hurts more than copying a 24-byte struct. |
| "Nil pointer means the variable doesn't exist" | The pointer variable exists on the stack with value `nil`; there's simply no valid object at address 0. Check before dereferencing. |

---

## 10. Related Tooling & Debugging

| Tool | What It Does |
|------|--------------|
| `go build -gcflags="-m"` | Shows escape analysis decisions — which handler-local structs moved to heap |
| `go build -gcflags="-m -m"` | Verbose escape analysis — reasons each variable escaped |
| `go vet` | Detects copied mutexes, printf formatting, and other pointer-related bugs |
| `go vet -copylocks` | Specifically checks for copying types with sync.Mutex/RWMutex |
| `dlv` (Delve debugger) | Print pointer addresses while stepping through `ServeHTTP`, inspect what they reference |

---

## 11. Interview Gold Questions

### Q1: "When should you use a pointer receiver vs a value receiver?"

If someone asks that in an interview, I'd start from what we do in real services: pointer receivers when the method mutates state you care about (`Save`, `Increment`, anything touching a mutex), or when the struct is large enough that copying it at every call would be silly. Value receivers are great for small, immutable-ish things — think `time.Time` or a little value object.

Then I'd mention the sharp edge: method sets. If you need `*PostgresStore` to satisfy `UserStore` because `Save` has a pointer receiver, you can't pretend the plain value type implements the interface — `PostgresStore`'s method set doesn't include that method. Consistency matters: once a type mixes receivers, reviewers (and the compiler) get cranky.

### Q2: "Is Go pass-by-value or pass-by-reference?"

I'd say Go is strictly pass-by-value, full stop — even when the thing being copied is a pointer. You hand the function its own 8-byte sticky note with an address on it; you didn't teleport the struct. That's why sharing works: two notes, one apartment.

I'd also nod at slices and maps: the header or map descriptor is copied by value, but the header points at shared backing storage, which is why mutations show up — and why `append` still surprises people until they internalize that the length field lives in the header you might have copied unless you return the new slice or pass `*[]T`.

### Q3: "Explain the nil interface trap."

I'd describe the interface as a tiny struct with `{type, data}`. A totally nil `error` has both fields empty. But the moment you write `var e *APIError; return e`, the interface's type slot says `*APIError` even though the data pointer inside is nil — so `err != nil` is true and your JSON error writer fires even though there's no actual `APIError` value.

Fix is boring but important: `return nil` for the no-error path, or only assign to the `error` variable when you truly constructed a non-nil concrete error. I've seen this in handlers that tried to be clever with typed errors.

---

## 12. Final Verbal Answer

If someone asks me about pointers in Go at the end of a long loop, I'd probably say something like:

I treat pointers as shared sticky notes: Go always copies what you pass, but a copied address still lands you in the same struct. That's how I mutate users, swap in new emails, or update repository state without returning giant structs. Pointer receivers line up with that — they're how methods get a stable address to write through, and they interact with interfaces in a picky way, which is why `*PostgresStore` implements `UserStore` but the bare struct might not.

I'd mention escape analysis only at a high level: if I return a pointer to something I built locally, the compiler moves the value to the heap so the pointer stays valid — fine for constructors, something to watch in hot paths. Gotchas I actually watch for in production: nil dereferences, typed nil errors tricking `if err != nil`, copying mutexes, and taking addresses of loop variables. Day to day, I reach for pointers when the struct is big, mutable, or owns a lock; I stick to values when the type is small and semantically immutable.

---

## 13. Comprehensive Interview Questions

> Full interview question bank (12 questions) → [[questions/T07 Pointers & Pointer Semantics - Interview Questions]]

Preview:
1. "What's the difference between `new()` and `&T{}`?" [COMMON]
2. "Can you take the address of a map value? Why not?" [TRICKY]
3. "What happens when you copy a struct that contains a sync.Mutex?" [ADVANCED]

---

> See [[Glossary]] for term definitions.
