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

Go is **always pass-by-value**. Every function call copies the argument. Pointers let you share data efficiently by copying a small address (8 bytes) instead of copying the entire struct.

> **In plain English:** A pointer is like writing down someone's home address on a sticky note. You don't carry the whole house — you carry the address. Anyone with that sticky note can visit the same house and rearrange the furniture.

---

## 2. Core Insight (TL;DR)

**Go has no references — only values.** When you pass a pointer, you're passing a *copy of the address*, not a reference. Both the caller and function have their own copy of the sticky note, but both sticky notes point to the same house.

The two most important decisions:
1. **Pointer receiver vs value receiver** — determines whether a method can modify its struct
2. **Return pointer vs return value** — determines where the data lives (stack vs heap)

---

## 3. Mental Model (Lock this in)

### The Photocopy vs Sticky Note Model

When you pass a **value**, Go photocopies the entire document. The function gets its own copy.
When you pass a **pointer**, Go gives you a sticky note with the shelf location. Both you and the function look at the same document.

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

> **In plain English:** Passing by value is handing someone a photocopy — they can scribble on it all day, your original is safe. Passing a pointer is handing someone your home address — they show up and rearrange your furniture.

### The Mistake That Teaches You

```go
type User struct {
    Name string
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

On a 64-bit system, every pointer is exactly **8 bytes** regardless of what it points to. A `*User` with 20 fields is the same 8 bytes as a `*int`.

```
*int:      [ 8 bytes: memory address ]  ──→  [ 8 bytes: int value ]
*User:     [ 8 bytes: memory address ]  ──→  [ N bytes: User struct fields ]
```

> **In plain English:** The sticky note is always the same size. Whether it points to a shoebox or a warehouse, the note itself is just an address.

### 4.2 The & and * Operators Under the Hood

`&x` — the compiler generates a `LEA` (Load Effective Address) instruction that puts x's memory address into a register.

`*p` — the compiler generates a `MOV` through the pointer. It reads the address stored in p, then loads the value at that address.

```go
x := 42
p := &x      // p now holds x's address
fmt.Println(*p)  // dereference: follow the address, read 42
*p = 100     // dereference + write: follow the address, write 100
fmt.Println(x)   // 100 — x changed because p pointed at it
```

```
Step 1: x := 42
  stack: [ x = 42 ]  at address 0xA0

Step 2: p := &x
  stack: [ x = 42 ]  at 0xA0
         [ p = 0xA0 ] at 0xA8    ◄── p holds x's address

Step 3: *p = 100
  follow p (0xA0) ──→ write 100
  stack: [ x = 100 ]  at 0xA0   ◄── x changed
         [ p = 0xA0 ] at 0xA8   ◄── p unchanged
```

### 4.3 Escape Analysis and Pointers

The Go compiler decides whether a variable lives on the **stack** (fast, auto-freed) or **heap** (slower, GC-managed). The key rule:

**If a pointer to a local variable escapes the function, the variable is moved to the heap.**

```go
func newUser() *User {
    u := User{Name: "rahul"}  // looks local, but...
    return &u                  // pointer escapes! u moves to heap
}
```

```
Without escape:                 With escape (pointer returned):
┌──────────────────┐            ┌──────────────────┐
│ STACK             │            │ STACK             │
│ u = User{...}    │            │ (pointer to heap) │
│ auto-freed ✓     │            └──────────────────┘
└──────────────────┘                    │
                                        ▼
                                ┌──────────────────┐
                                │ HEAP              │
                                │ u = User{...}    │
                                │ GC-managed        │
                                └──────────────────┘
```

Check what escapes with:
```bash
go build -gcflags="-m" main.go
# output: ./main.go:5:2: moved to heap: u
```

> **In plain English:** If you promise to give someone a sticky note pointing to a book, Go makes sure the book is on a permanent shelf (heap), not your desk (stack) that gets cleared when you leave.

### 4.4 Nil Pointers

Every pointer's zero value is `nil`. Dereferencing a nil pointer causes a **panic** — Go's equivalent of a crash.

```go
var p *int       // nil — not pointing anywhere
fmt.Println(*p)  // PANIC: runtime error: invalid memory address or nil pointer dereference
```

```
  p ──→ nil (address 0x0)

  *p: "Go, please read what's at address 0x0"
  Go: "There's nothing there." → PANIC
```

The runtime catches this at the OS level. Address 0x0 is always unmapped memory, so the CPU triggers a segfault that Go converts to a panic.

---

## 5. Key Rules & Behaviors

### Rule 1: Pointer Receiver vs Value Receiver

A **value receiver** gets a copy. A **pointer receiver** gets the address and can modify the original.

```go
type Counter struct {
    n int
}

func (c Counter) ValueIncrement() {
    c.n++  // increments the copy, original unchanged
}

func (c *Counter) PointerIncrement() {
    c.n++  // increments the original
}
```

```
c := Counter{n: 0}

c.ValueIncrement():
  copy: [ n: 0 ] → [ n: 1 ]  ← copy dies, c.n still 0

c.PointerIncrement():
  &c: ──→ [ n: 0 ] → [ n: 1 ]  ← original modified, c.n is now 1
```

> **In plain English:** Value receiver: you get a photocopy of the form and fill it in. The original stays blank. Pointer receiver: you get the actual form and fill it in.

### Rule 2: Method Sets Determine Interface Satisfaction

This is the biggest pointer trap in Go.

- Type `T` (value) has methods with **value receivers only**
- Type `*T` (pointer) has methods with **both** value and pointer receivers

```go
type Saver interface {
    Save()
}

type Doc struct{}

func (d *Doc) Save() {}  // pointer receiver

var _ Saver = Doc{}   // COMPILE ERROR: Doc does not implement Saver
var _ Saver = &Doc{}  // OK: *Doc has Save()
```

```
Method set of Doc:   { }           ← no Save() here
Method set of *Doc:  { Save() }    ← pointer receiver methods live here

Interface Saver requires: { Save() }

Doc{}  → method set {} → missing Save() → COMPILE ERROR
&Doc{} → method set { Save() } → satisfies Saver → OK
```

**Why?** Go needs a real address to call a pointer receiver method. A bare `Doc{}` value in an interface might be a copy with no stable address. Go refuses to silently take its address because that would be confusing.

> **In plain English:** Imagine a club that requires ID. `*Doc` has the ID card (address). `Doc` is a photocopy without ID. The bouncer won't let a photocopy in, even if it looks the same.

### Rule 3: Don't Return Pointers to Loop Variables

Before Go 1.22, the loop variable was reused across iterations. Taking its address gave you a pointer to the same slot every time.

```go
// Go < 1.22: BUG
var ptrs []*int
for i := 0; i < 3; i++ {
    ptrs = append(ptrs, &i)  // all point to same i!
}
// ptrs[0], ptrs[1], ptrs[2] all point to i = 3

// Go >= 1.22: FIXED — each iteration gets its own i
```

```
Go < 1.22:
  ptrs[0] ──→ [ i ]
  ptrs[1] ──→ [ i ]   ← all three point to THE SAME slot
  ptrs[2] ──→ [ i ]
  After loop: i = 3, so all dereferences give 3

Go >= 1.22:
  ptrs[0] ──→ [ i₀ = 0 ]
  ptrs[1] ──→ [ i₁ = 1 ]   ← each iteration has its own variable
  ptrs[2] ──→ [ i₂ = 2 ]
```

> **In plain English:** Before Go 1.22, the loop reused one locker for every iteration. Everyone's sticky note pointed to the same locker. At the end, whatever was in the locker last is what everyone sees.

### Rule 4: Pointer to Interface Is Almost Always Wrong

You almost never need `*Saver` (pointer to interface). The interface itself is already a two-word container holding a pointer to the data.

```go
type Saver interface { Save() }

// WRONG — pointer to interface
func process(s *Saver) { ... }

// RIGHT — interface already holds the pointer internally
func process(s Saver) { ... }
```

```
Interface value (2 words, 16 bytes):
┌──────────────┬──────────────┐
│ type pointer  │ data pointer  │  ← already contains a pointer!
└──────────────┴──────────────┘

*Saver would be a pointer TO this container — an extra level of indirection
that confuses everyone and gains nothing.
```

> **In plain English:** An interface is like an envelope that already contains the letter's address. Putting the envelope inside another envelope is pointless.

### Rule 5: sync.Mutex Must Never Be Copied

Types containing `sync.Mutex` must use pointer receivers and never be passed by value. Copying a locked mutex gives you a second locked mutex with independent state.

```go
type SafeMap struct {
    mu sync.Mutex
    m  map[string]int
}

// WRONG: value receiver copies the mutex
func (s SafeMap) Get(key string) int {
    s.mu.Lock()          // locks the COPY's mutex
    defer s.mu.Unlock()
    return s.m[key]      // reads the COPY's map — no real protection
}

// RIGHT: pointer receiver
func (s *SafeMap) Get(key string) int {
    s.mu.Lock()
    defer s.mu.Unlock()
    return s.m[key]
}
```

```
Value receiver (WRONG):
  original:  [ mu: locked   | m: {...} ]
  copy:      [ mu: locked   | m: {...} ]  ← TWO independent mutexes!
  Unlocking the copy doesn't unlock the original.

Pointer receiver (RIGHT):
  &original: ──→ [ mu: locked | m: {...} ]  ← only ONE mutex, shared
```

Use `go vet` — it detects copied mutexes.

> **In plain English:** Photocopying a padlock doesn't give you a second key to the same lock. It gives you a completely different lock. Now nothing is properly guarded.

---

## 6. Code Examples (Show, Don't Tell)

### Example 1: Swapping Values with Pointers

```go
func swap(a, b *int) {
    *a, *b = *b, *a
}

func main() {
    x, y := 10, 20
    swap(&x, &y)
    fmt.Println(x, y)  // 20 10
}
```

```
Step 1: x = 10 at 0xA0, y = 20 at 0xA8
Step 2: swap receives: a = 0xA0, b = 0xA8  (copies of the addresses)
Step 3: *a, *b = *b, *a
         read *b (20), read *a (10)
         write 20 to 0xA0, write 10 to 0xA8
Step 4: x = 20, y = 10  ◄── swapped via pointers
```

### Example 2: Returning a Pointer (Escape to Heap)

```go
func newConfig() *Config {
    c := Config{Port: 8080}
    return &c  // c escapes to heap — safe in Go
}

func main() {
    cfg := newConfig()
    fmt.Println(cfg.Port)  // 8080
}
```

```
Step 1: newConfig() creates c on stack
Step 2: Compiler detects &c is returned → moves c to heap
Step 3: Returns pointer to heap-allocated Config
Step 4: main's cfg points to heap: [ Port: 8080 ]
         GC will clean this up when no pointers reference it
```

### Example 3: The nil Interface Trap (Review from T01, Pointer Angle)

```go
type MyError struct{ msg string }
func (e *MyError) Error() string { return e.msg }

func mayFail() error {
    var err *MyError  // nil pointer, but typed
    return err        // returns non-nil interface!
}

func main() {
    if err := mayFail(); err != nil {
        fmt.Println("got error:", err)  // THIS RUNS — even though err is a nil pointer
    }
}
```

```
mayFail() returns:
  interface { type: *MyError | data: nil }  ← type field is NOT nil

  err != nil checks the INTERFACE, not the pointer inside.
  Interface has a type → it's not nil.

Fix: return nil explicitly, or use error interface directly:
  return nil  ← returns interface { type: nil | data: nil }
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

Build a `LinkedList` with `Push`, `Pop`, and `Print` methods. The list should use pointer semantics correctly — `Push` and `Pop` must modify the list, `Print` can use a value receiver. Use `*Node` pointers to chain elements.

> Full solutions with explanations → [[exercises/T07 Pointers & Pointer Semantics - Exercises]]

---

## 7. Edge Cases & Gotchas

| Gotcha | What Happens | Fix |
|--------|-------------|-----|
| Dereferencing nil pointer | `runtime panic: invalid memory address` | Check `!= nil` before access |
| Value receiver on mutex-containing type | Copies the mutex — two independent locks | Use pointer receiver |
| Comparing pointers with `==` | Compares addresses, not values | Dereference first: `*a == *b` |
| Returning `*T` nil through interface | Non-nil interface (typed nil trap) | Return `nil` explicitly |
| Pointer to loop variable (pre-1.22) | All pointers share one variable | Copy inside loop or use Go 1.22+ |
| Storing pointer to map value | Compile error: map values are not addressable | Copy to local, take address of local |
| nil map write | `panic: assignment to entry in nil map` | Initialize with `make()` |

**The addressability trap:**

```go
m := map[string]User{"a": {Name: "rahul"}}
m["a"].Name = "admin"  // COMPILE ERROR: cannot take address of map value

// Fix: copy, modify, write back
u := m["a"]
u.Name = "admin"
m["a"] = u
```

> **In plain English:** You can't reach into a filing cabinet and edit a document in place — you have to pull it out, change it, and put it back.

---

## 8. Performance & Tradeoffs

| Approach | Copy Cost | Heap Alloc? | GC Pressure | When to Use |
|----------|-----------|-------------|-------------|-------------|
| Pass value (small struct ≤64B) | Low | No (stays on stack) | None | Small immutable types: Point, Color, Time |
| Pass pointer (large struct) | 8 bytes always | Maybe (escape analysis) | Higher if escapes | Large structs, types with mutexes |
| Return value | Size of struct | No | None | Small structs, results |
| Return pointer | 8 bytes | Yes (escapes) | Higher | Large structs, nil-means-not-found |

**Rule of thumb:**
- Struct ≤ 64 bytes and no mutation needed? **Value.**
- Struct > 64 bytes or mutation needed? **Pointer.**
- Contains sync.Mutex? **Always pointer.**

---

## 9. Common Misconceptions

| Misconception | Reality |
|--------------|---------|
| "Go has pass-by-reference" | Go is always pass-by-value. Passing a pointer copies the address, not the data. |
| "new() allocates on the heap" | `new()` is just sugar for zero-value + pointer. Escape analysis decides stack vs heap. |
| "&x always escapes to heap" | Only if the pointer outlives the function scope. Local-only pointers stay on stack. |
| "Pointers are faster than values" | Not always. Small values on stack avoid GC overhead. Pointers add indirection + possible heap allocation. |
| "nil pointer means the variable doesn't exist" | The pointer variable exists; it just holds address 0x0 (nil). The thing it points to doesn't exist. |

---

## 10. Related Tooling & Debugging

| Tool | What It Does |
|------|-------------|
| `go build -gcflags="-m"` | Shows escape analysis decisions — which variables escape to heap |
| `go build -gcflags="-m -m"` | Verbose escape analysis — shows the reason for each decision |
| `go vet` | Detects copied mutexes, printf formatting, and other pointer-related bugs |
| `go vet -copylocks` | Specifically checks for copying types with sync.Mutex/RWMutex |
| `dlv` (Delve debugger) | Print pointer addresses, inspect what they point to at runtime |

---

## 11. Interview Gold Questions

### Q1: "When should you use a pointer receiver vs a value receiver?"

**Nuanced answer:** Use a pointer receiver when the method needs to mutate the struct, the struct is large (>64 bytes), or the struct contains synchronization primitives like mutex. Use a value receiver for small immutable types. The critical detail: if *any* method on a type uses a pointer receiver, *all* should for consistency, because it affects interface satisfaction — `T` only has value-receiver methods in its method set, but `*T` has both.

**Verbal summary:** "Pointer receivers for mutation, large structs, and types with mutexes. Value receivers for small immutable types. Keep it consistent per type because method sets affect interface satisfaction."

### Q2: "Is Go pass-by-value or pass-by-reference?"

**Nuanced answer:** Always pass-by-value. Every assignment and function call copies the value. When you pass a pointer, you're copying the 8-byte address — but both copies point to the same data. Slices and maps look like they're pass-by-reference because their headers contain pointers, but the header itself is still copied. The key insight: a function that appends to a slice won't update the caller's length unless you pass `*[]T` or return the new slice.

**Verbal summary:** "Go is strictly pass-by-value. Pointers give you shared access by copying the address. Slices and maps pass a header by value — the header contains a pointer to the data, which is why modifications to existing elements are visible, but append can silently diverge."

### Q3: "Explain the nil interface trap."

**Nuanced answer:** An interface in Go is a two-word struct: {type, data}. A nil interface has both fields nil. But when you store a typed nil pointer inside an interface (like `var err *MyError; return err` as `error`), the type field is set. The interface is non-nil even though the data is nil. This commonly causes `if err != nil` to be true when you expect false. Fix: return `nil` directly instead of returning a typed nil pointer through an interface.

**Verbal summary:** "An interface wraps a type pointer and a data pointer. A typed nil pointer inside an interface makes the interface non-nil because the type field is set. Always return bare nil for error interfaces, never a typed nil pointer."

---

## 12. Final Verbal Answer

> "Go uses pointers for indirect access to values. Every assignment is a value copy — when you pass a pointer, you copy the 8-byte address. Pointer receivers let methods modify their struct and affect interface satisfaction: T's method set only includes value-receiver methods, while *T includes both. The compiler's escape analysis decides whether pointed-to data lives on the stack or heap — returning a pointer forces the data to the heap. Key gotchas: nil pointer dereference panics, the typed-nil interface trap, and never copying sync.Mutex. Rule of thumb: use pointers for large structs, mutation, and sync primitives; use values for small immutable types."

---

## 13. Comprehensive Interview Questions

> Full interview question bank (12 questions) → [[questions/T07 Pointers & Pointer Semantics - Interview Questions]]

Preview:
1. "What's the difference between `new()` and `&T{}`?" [COMMON]
2. "Can you take the address of a map value? Why not?" [TRICKY]
3. "What happens when you copy a struct that contains a sync.Mutex?" [ADVANCED]

---

> See [[Glossary]] for term definitions.
