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

Go is **always pass-by-value**. Every function call copies the argument. Pointers let you share data efficiently by copying a small address (8 bytes on 64-bit) instead of copying an entire struct — think of handing someone a sticky note with your house address instead of moving the whole house onto their desk. Anyone with that note can visit the same place and change what’s inside.

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

On a 64-bit system, every pointer is exactly **8 bytes** regardless of what it points to. A `*User` with twenty fields is still the same 8 bytes as a `*int`. The sticky note is always the same size; whether it points at a tiny counter or a fat DTO, you’re still copying one address through your API boundary.

```
*int:      [ 8 bytes: memory address ]  ──→  [ 8 bytes: int value ]
*User:     [ 8 bytes: memory address ]  ──→  [ N bytes: User struct fields ]
```

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

If you promise the caller a pointer to data you created inside the function, Go can’t leave that data on a stack frame that disappears — it promotes the value to the heap so the pointer stays valid after you return. Same vibe as moving the book to a permanent shelf because you handed out its address.

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

A **value receiver** gets a copy. A **pointer receiver** gets the address and can modify the original — what you want when a service method bumps an in-memory counter or updates repository state.

```go
type RequestCount struct {
    n int
}

func (c RequestCount) ValueSeen() {
    c.n++  // increments the copy, original unchanged
}

func (c *RequestCount) PointerSeen() {
    c.n++  // increments the original
}
```

```
c := RequestCount{n: 0}

c.ValueSeen():
  copy: [ n: 0 ] → [ n: 1 ]  ← copy dies, c.n still 0

c.PointerSeen():
  &c: ──→ [ n: 0 ] → [ n: 1 ]  ← original modified, c.n is now 1
```

Value receiver: you get a photocopy of the form; filling it in doesn’t touch the original. Pointer receiver: you get the actual form the whole app shares.

### Rule 2: Method Sets Determine Interface Satisfaction

This is the biggest pointer trap in Go when you wire handlers to interfaces.

- Type `T` (value) has methods with **value receivers only**
- Type `*T` (pointer) has methods with **both** value and pointer receivers

```go
type UserStore interface {
    Save(*User) error
}

type PostgresStore struct {
    // pool, etc.
}

func (s *PostgresStore) Save(u *User) error {
    // INSERT ... ON CONFLICT, etc.
    return nil
}

var _ UserStore = PostgresStore{}   // COMPILE ERROR: PostgresStore does not implement UserStore
var _ UserStore = &PostgresStore{}  // OK: *PostgresStore has Save()
```

```
Method set of PostgresStore:   { }              ← no Save() on the value type
Method set of *PostgresStore:  { Save() }       ← pointer receiver methods live here

Interface UserStore requires: { Save(*User) error }

PostgresStore{}  → method set {} → missing Save() → COMPILE ERROR
&PostgresStore{} → method set { Save() } → satisfies UserStore → OK
```

**Why?** Go needs a stable address to call a pointer receiver method. A bare `PostgresStore{}` sitting in an interface might be a transient copy with no stable address. Go refuses to silently take its address because that would hide allocations and confuse everyone.

Think of it like venue security: `*PostgresStore` holds the real ID; `PostgresStore` is a photocopy. The bouncer won’t let the photocopy in even if the picture looks right.

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

Before Go 1.22, the `for` loop reused one locker for every iteration — every sticky note pointed at the same locker, so after the loop everyone read whatever was left last (usually the final value). Same bug class shows up when you batch-scan rows and stash `&row` without copying.

### Rule 4: Pointer to Interface Is Almost Always Wrong

You almost never need `*UserStore` (pointer to interface). The interface value is already a small two-word container holding a type pointer and a data pointer.

```go
type UserStore interface {
    Save(*User) error
}

// WRONG — extra indirection, confuses every reader
func RegisterRoutes(store *UserStore) { ... }

// RIGHT — pass the interface; it already carries a pointer to the concrete store
func RegisterRoutes(store UserStore) { ... }
```

```
Interface value (2 words, 16 bytes):
┌──────────────┬──────────────┐
│ type pointer  │ data pointer  │  ← already contains a pointer to your PostgresStore
└──────────────┴──────────────┘

*UserStore would be a pointer TO this container — useless wrapping.
```

An interface is already the envelope with the recipient’s address written inside. Putting that envelope inside another envelope doesn’t help.

### Rule 5: sync.Mutex Must Never Be Copied

Types containing `sync.Mutex` must use pointer receivers and never be passed by value. Copying a locked mutex gives you a second mutex with independent state — your HTTP middleware thinks it serialized access; it didn’t.

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

Photocopying a padlock doesn’t give you a second key to the same lock — it gives you a different lock entirely, so nothing is actually guarded.

---

## 6. Code Examples (Show, Don't Tell)

### Example 1: Mutating through a pointer (real service shape)

```go
func UpdateUserEmail(u *User, newEmail string) {
    u.Email = newEmail
}

func main() {
    u := &User{Name: "rahul", Email: "old@example.com"}
    UpdateUserEmail(u, "new@example.com")
    fmt.Println(u.Email)  // new@example.com
}
```

```
Step 1: u points at heap or stack User
Step 2: UpdateUserEmail receives a copy of the pointer (still 8 bytes) → same struct
Step 3: u.Email = newEmail writes through that address
Step 4: caller sees updated email — same idea as swapping fields via pointers, but this is what you actually do after a PATCH /users/:id
```

### Example 2: Returning a pointer (escape to heap)

```go
type ListenConfig struct {
    Addr         string
    ReadTimeout  time.Duration
}

func newListenConfig() *ListenConfig {
    c := ListenConfig{Addr: ":8080", ReadTimeout: 30 * time.Second}
    return &c  // c escapes to heap — safe in Go
}

func main() {
    cfg := newListenConfig()
    fmt.Println(cfg.Addr)  // :8080
}
```

```
Step 1: newListenConfig() creates c on stack
Step 2: Compiler detects &c is returned → moves c to heap
Step 3: Returns pointer to heap-allocated ListenConfig
Step 4: main's cfg points to heap: [ Addr: ":8080", ... ]
         GC will clean this up when no pointers reference it
```

This pattern is what you reach for when a constructor hands fully populated server config to `http.ListenAndServe` or your DI container.

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

Same bug bites you when a JSON handler builds `var apiErr *APIError` and returns it as `error` — tests think failure happened because `err != nil` is true even though the pointer inside is nil.

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

| Gotcha | What Happens | Fix |
|--------|-------------|-----|
| Nil `*User` before `json.NewEncoder(w).Encode` | Panic: invalid memory address | Return `400` early if binding produced nil; guard with `if u == nil` |
| Value receiver on `SafeMap` or any mutex-backed cache | Two independent locks; race under load | Pointer receivers on methods; never pass the struct by value into goroutines |
| Comparing `*User` with `==` in a test | You compared addresses, not fields | Compare IDs or use `reflect.DeepEqual` / explicit field checks |
| Returning typed nil `*APIError` as `error` | `if err != nil` true even though data pointer is nil | `return nil` or var of interface type assigned only on real failure |
| `&i` inside `for _, row := range rows` (pre-1.22 / shared var bugs) | Every ptr aliases the same loop var | Copy `row := row`, or upgrade Go, or index with `&slice[i]` intentionally |
| `&m["session"]` on a map value | Compile error: map values aren’t addressable | Copy to local `u := m["session"]`, edit, write `m["session"] = u` |
| Writing to a nil map in a lazy-loaded cache | `panic: assignment to entry in nil map` | Initialize with `make` before first store |

**The addressability trap:**

```go
m := map[string]User{"a": {Name: "rahul"}}
m["a"].Name = "admin"  // COMPILE ERROR: cannot take address of map value

// Fix: copy, modify, write back
u := m["a"]
u.Name = "admin"
m["a"] = u
```

You can’t edit a document while it’s still clipped inside the filing cabinet drawer — pull it out, change it, slide it back.

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
- `time.Time` is 24 bytes — still fine by value when you’re not mutating it.
- A minimal `User` with a few strings is already multiple words; by the time you add slices for roles/permissions you’re often past the “tiny value” comfort zone — pointers keep handler signatures stable.
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
| "`&local` inside a handler always allocates" | If you only pass that pointer to callees that don’t store it past the handler return, it often stays stack-fast. Profile before guessing. |
| "Pointers are free performance" | Indirection costs cache misses; heap pointers add GC work. A storm of tiny heap allocations from unnecessary `&T{}` in hot paths hurts more than copying a 24-byte struct. |
| "Nil pointer means the variable doesn’t exist" | The pointer variable exists on the stack with value `nil`; there’s simply no valid object at address 0. Check before dereferencing. |

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

If someone asks that in an interview, I’d start from what we do in real services: pointer receivers when the method mutates state you care about (`Save`, `Increment`, anything touching a mutex), or when the struct is large enough that copying it at every call would be silly. Value receivers are great for small, immutable-ish things — think `time.Time` or a little value object.

Then I’d mention the sharp edge: method sets. If you need `*PostgresStore` to satisfy `UserStore` because `Save` has a pointer receiver, you can’t pretend the plain value type implements the interface — `PostgresStore`’s method set doesn’t include that method. Consistency matters: once a type mixes receivers, reviewers (and the compiler) get cranky.

### Q2: "Is Go pass-by-value or pass-by-reference?"

I’d say Go is strictly pass-by-value, full stop — even when the thing being copied is a pointer. You hand the function its own 8-byte sticky note with an address on it; you didn’t teleport the struct. That’s why sharing works: two notes, one apartment.

I’d also nod at slices and maps: the header or map descriptor is copied by value, but the header points at shared backing storage, which is why mutations show up — and why `append` still surprises people until they internalize that the length field lives in the header you might have copied unless you return the new slice or pass `*[]T`.

### Q3: "Explain the nil interface trap."

I’d describe the interface as a tiny struct with `{type, data}`. A totally nil `error` has both fields empty. But the moment you write `var e *APIError; return e`, the interface’s type slot says `*APIError` even though the data pointer inside is nil — so `err != nil` is true and your JSON error writer fires even though there’s no actual `APIError` value.

Fix is boring but important: `return nil` for the no-error path, or only assign to the `error` variable when you truly constructed a non-nil concrete error. I’ve seen this in handlers that tried to be clever with typed errors.

---

## 12. Final Verbal Answer

If someone asks me about pointers in Go at the end of a long loop, I’d probably say something like:

I treat pointers as shared sticky notes: Go always copies what you pass, but a copied address still lands you in the same struct. That’s how I mutate users, swap in new emails, or update repository state without returning giant structs. Pointer receivers line up with that — they’re how methods get a stable address to write through, and they interact with interfaces in a picky way, which is why `*PostgresStore` implements `UserStore` but the bare struct might not.

I’d mention escape analysis only at a high level: if I return a pointer to something I built locally, the compiler moves the value to the heap so the pointer stays valid — fine for constructors, something to watch in hot paths. Gotchas I actually watch for in production: nil dereferences, typed nil errors tricking `if err != nil`, copying mutexes, and taking addresses of loop variables. Day to day, I reach for pointers when the struct is big, mutable, or owns a lock; I stick to values when the type is small and semantically immutable.

---

## 13. Comprehensive Interview Questions

> Full interview question bank (12 questions) → [[questions/T07 Pointers & Pointer Semantics - Interview Questions]]

Preview:
1. "What's the difference between `new()` and `&T{}`?" [COMMON]
2. "Can you take the address of a map value? Why not?" [TRICKY]
3. "What happens when you copy a struct that contains a sync.Mutex?" [ADVANCED]

---

> See [[Glossary]] for term definitions.
