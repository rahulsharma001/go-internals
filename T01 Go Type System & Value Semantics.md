
> **Reading Guide**: Sections 1-3 and 6 are essential first read (20 min).
> Sections 4-5 deepen understanding (15 min).
> Sections 7-12 are interview-specific — read closer to interview day.
> Section 13 is your comprehensive interview Q&A bank → [[questions/T01 Go Type System - Interview Questions]]
> Something not clicking? → [[simplified/T01 Go Type System & Value Semantics - Simplified]]

---

## 0. Prerequisites

This is a foundational topic. No prerequisites are required — T01 is designed to be the first topic you study. However, if you find structs or methods confusing, read these P-notes first:

- [[prerequisites/P01 Structs & Struct Memory Layout]] (optional — covers struct basics in more depth)
- [[prerequisites/P02 Methods & Receivers]] (optional — covers receiver types in more depth)

---

## 1. Concept

When we talk about **the type system**, we mean how you name types, how they connect, and the rules for identity, assignability, what methods a type has, and composition. Every other idea in this language stacks on that.

> **Scope note**: We stick to the type system here — defined types, aliases, underlying types, zero values, methods, embedding. Stack vs heap and pass-by-value live in [[T02 Go Memory Allocation & Value Semantics]].

---

## 2. Core Insight (TL;DR)

**Go decides all types at compile time.** There are no runtime type surprises.

Every type has three properties: an **underlying type** (what it's made of), a **zero value** (its safe default), and a **list of methods** (what it can do).

Interfaces work **implicitly** — if your type has the right methods, it fits the interface. No signup form, no `implements` keyword.

If you prep for interviews, double down on **type identity vs assignability** and **value vs pointer receiver rules**. Section 4 takes you through each, one step at a time.

---

## 3. Mental Model (Lock this in)

### Types are blueprints, values are the thing built from them

- Every variable has a type, known at compile time
- Every type has a **zero value** — Go never has uninitialized memory
- Types don't inherit; they **compose** via embedding

### The Three Questions for Any Type

1. **What is its underlying type?** (determines behavior)
2. **What is its zero value?** (determines safety)
3. **What methods does it have?** (determines which interfaces it fits)

> **In plain English:** Every type in Go comes with three things baked in: what raw material it's made from, what its default empty state is, and what methods are attached to it. That's all the compiler needs to know about any type.

### The mistake that teaches you

```go
type UserID int
type OrderID int

func LookupOrder(id OrderID) { fmt.Println("looking up order", id) }

func main() {
    uid := UserID(42)
    LookupOrder(uid) // What happens?
}
```

**What you'd expect:** Maybe it works — both are `int` under the hood, right?

**What actually happens:** Compile error: `cannot use uid (variable of type UserID) as OrderID value in argument to LookupOrder`.

**Why:** `UserID` and `OrderID` are **defined types**. Even though both have the same underlying type (`int`), they are completely separate types. Go's type system prevents you from accidentally passing a user ID where an order ID is expected.

**The fix:** If you genuinely need to convert, you must be explicit: `LookupOrder(OrderID(uid))`. The type system forces you to think about whether that conversion makes sense.

```
Your Type
  ├── Underlying type  (what it's made of — int, struct, slice, etc.)
  ├── Zero value       (its safe default — 0, "", nil, false, etc.)
  └── Methods          (what you can call on it)

Method rules:
  Value T    → only value receiver methods
  Pointer *T → value receiver methods + pointer receiver methods

  *T gets everything. T only gets value receiver methods.
```

---

## 4. How It Actually Works (Internals) [INTERMEDIATE → ADVANCED]

### Defined Types vs Type Aliases

Go gives you two ways to name a type, and they work very differently. A **defined type** is like creating a new brand of coffee — it's still coffee inside, but you can't accidentally mix it with tea. You get your own label, your own methods, and the compiler treats it as a separate thing. A **type alias** is a nickname — same coffee, different label on the bag.

```go
type UserID int64       // DEFINED TYPE — new type, can attach methods
type LegacyID = int64   // TYPE ALIAS — same type, no own methods
```

**What Go does with each line:**

```
Defined type:  type UserID int64
  Creates a BRAND NEW type called UserID
  UserID and int64 are DIFFERENT types — can't assign between them
  BUT you can convert: UserID(42) or int64(uid)
  You CAN attach methods to UserID

Type alias:  type LegacyID = int64
  LegacyID IS int64 — another name for the same type
  No conversion needed: var id LegacyID = 42
  You CANNOT attach methods to LegacyID (they'd go on int64)
```

| Feature | Defined Type (`type X T`) | Type Alias (`type X = T`) |
|---|---|---|
| New type? | ✅ Yes, distinct from T | ❌ No, identical to T |
| Own methods? | ✅ Can attach methods | ❌ Cannot add methods |
| Assignable to T? | ❌ Requires explicit conversion | ✅ Directly assignable |
| Underlying type | T | T |
| Use case | Domain modeling (`UserID`, `Currency`) | Gradual refactoring, cross-package access |

```
Defined type:    UserID ──builds on──→ int64     (separate type, own methods)
Type alias:      LegacyID ══is══→ int64          (same type, no own methods)
```

### Underlying Types

Think of the underlying type as the raw material a type is made from. A `UserID` is made from `int64` the way a wooden chair is made from wood — the chair has its own identity, but you can always ask "what is it made of?"

For built-in types (`int`, `string`, `bool`), the underlying type is itself. For defined types, it's the type on the right side of the definition:

```go
type UserID int64                    // underlying: int64
type Config struct{ Port int }       // underlying: struct{ Port int }
type Permissions []string            // underlying: []string
```

**What Go sees for each line:**

```
Step 1: `type UserID int64` — a new defined type `UserID` whose underlying type is `int64`.
Step 2: `type Config struct{...}` — a new defined type `Config` whose underlying type is the struct `struct{ Port int }`.
Step 3: `type Permissions []string` — a new defined type `Permissions` whose underlying type is `[]string`.
```

**Why this matters:** Go only calls two types **identical** in those narrow cases: same name in the same package, or both unnamed with the same shape. From there, you read off which **conversions** the compiler will allow.

### Type Identity vs Assignability

Go is strict about which types can talk to each other. Even if two types are made from the same raw material, they're different types. Think of it like two different airlines using the same model of airplane — you can't use a Delta boarding pass on a United flight even though the plane is identical.

```go
type MyInt int
var a int = 42
var b MyInt = a        // COMPILE ERROR: different types
var c MyInt = MyInt(a) // OK: explicit conversion
```

```
Step 1: a is type int, value 42
Step 2: b is type MyInt — even though MyInt's underlying type is int,
        MyInt and int are DIFFERENT types.
        You can't assign int to MyInt directly.
Step 3: MyInt(a) — explicit conversion works because they share
        the same underlying type (int).
```

```
int ─────── MyInt
  │  same underlying type (int)  │
  │  but DIFFERENT named types   │
  ╰──── explicit conversion ─────╯
```

**Assignability rules** (when `x` can be assigned to type `T`):
1. `x`'s type is identical to `T`
2. `x`'s type and `T` have identical underlying types, and at least one is unnamed
3. `T` is an interface and `x` implements `T`
4. `x` is the untyped nil and `T` is a pointer, function, slice, map, channel, or interface
5. `x` is an untyped constant representable by type `T`

```go
var a [3]int
var b [4]int
a = b // COMPILE ERROR: [3]int and [4]int are different types
```

**What Go does:**

```
Step 1: `a` has type [3]int and `b` has type [4]int — the length is part of the type, so these are not the same type.
Step 2: For assignment, rule 1 requires `x`'s type to be identical to `T`; [3]int and [4]int are not identical.
Step 3: The compiler rejects `a = b` because there is no built-in conversion between different array types.
```

### Zero Values

Go guarantees every variable is initialized to its **zero value** — there is no uninitialized memory:

| Type Category | Zero Value |
|---|---|
| `bool` | `false` |
| Numeric (`int`, `float64`, etc.) | `0` |
| `string` | `""` (empty string) |
| Pointer, function, slice, map, channel, interface | `nil` |
| Array | All elements zeroed |
| Struct | All fields zeroed |

> Design types so their zero value is **useful**. `sync.Mutex{}` is ready to use. `bytes.Buffer{}` is an empty buffer. This is idiomatic Go.

> **In plain English:** In Go, there's no such thing as "uninitialized." Every variable starts with a sensible default — numbers start at 0, strings start empty, booleans start false. You never get garbage memory.

### Which Methods Does a Type Have?

The list of methods on a type determines which interfaces it fits:

| Receiver | Methods available on `T` | Methods available on `*T` |
|---|---|---|
| `func (t T) M()` | ✅ Yes | ✅ Yes |
| `func (t *T) M()` | ❌ No | ✅ Yes |

> **`*T` gets everything. `T` only gets value receiver methods.**

This is the most tested type system rule in Go interviews.

```
Why this asymmetry?

Value receiver: func (t T) M()
  Works on T:  Go copies the value → safe, no side effects
  Works on *T: Go auto-dereferences → (*p).M() copies the pointed-to value

Pointer receiver: func (t *T) M()
  Works on *T: pointer is passed → can modify original
  FAILS on T stored in interface: interface holds a COPY of T
    If Go auto-took &copy, mutations would hit the copy, not the original
    → silently wrong behavior → Go prevents this at compile time
```

### Struct Embedding (Composition, NOT Inheritance)

Embedding is like hiring a specialist. A Hospital doesn't become a Doctor — it has a Doctor on staff. When someone asks the Hospital to diagnose, the Doctor does the work. In Go, when you embed a type inside a struct, its fields and methods get "promoted" — you can call them directly on the outer struct.

```go
type AuditLog struct {
    Message string
}
func (a AuditLog) Summary() string { return "audit: " + a.Message }

type OrderService struct {
    AuditLog         // embedded — promotes fields + methods
    ServiceName string
}

svc := OrderService{AuditLog{"order created"}, "orders"}
svc.Message    // promoted from AuditLog
svc.Summary()  // promoted from AuditLog
```

```
What embedding looks like in memory:

  stack 0xC000060000: svc (OrderService struct, ~48 bytes)
    offset 0x00: AuditLog.Message = string{ ptr=0xC000080000, len=13 }  ← "order created"
    offset 0x10: ServiceName      = string{ ptr=0xC000080020, len=6 }   ← "orders"

  svc.Message → compiler rewrites to svc.AuditLog.Message → reads at offset 0x00
  svc.Summary() → compiler rewrites to svc.AuditLog.Summary()
    receiver is ALWAYS AuditLog (the embedded value at offset 0x00), not OrderService
```

> **In plain English:** Embedding promotes the embedded type's fields and methods so you can call them directly on the outer struct. But the embedded type is always the one doing the work — the outer struct just gets credit for having the capability.

---

## 5. Key Rules & Behaviors

### Rule 1: Defined types create new types

`type X int` makes `X` and `int` distinct types. You need an explicit conversion to go between them.

```go
type OrderID int64
var raw int64 = 42
var oid OrderID = raw           // COMPILE ERROR
var oid OrderID = OrderID(raw)  // OK — explicit conversion
```

```
int64 ─────── OrderID
  │  same underlying type (int64) │
  │  but DIFFERENT defined types   │
  ╰──── explicit conversion ───────╯
```

**Why (Section 4.1):** Defined types exist so the compiler can catch domain bugs. You don't want to pass a `UserID` where an `OrderID` is expected, even if both are `int64` underneath.

### Rule 2: Type aliases are the same type

`type X = int` is just another name for `int`. No conversion needed.

```go
type LegacyID = int64
var id LegacyID = 42  // fine — LegacyID IS int64
```

```
LegacyID ══is══→ int64   (same type, just a different name)
```

**Why (Section 4.1):** Aliases exist for gradual refactoring — when you're migrating a type from one package to another and don't want to break callers all at once.

### Rule 3: Underlying type determines convertibility

Two defined types can be explicitly converted if they share the same underlying type.

```go
type UserID int64
type OrderID int64
uid := UserID(1)
oid := OrderID(uid)  // OK — both have underlying type int64
```

```
UserID ──underlying──→ int64 ←──underlying── OrderID
                 ↑ same raw material → conversion allowed
```

**Why (Section 4.2):** The compiler checks that the raw material (underlying type) matches before allowing a conversion. Same raw material = safe to reinterpret the bits.

### Rule 4: Zero values are guaranteed

Every variable in Go is initialized to its zero value. You never read garbage memory.

```go
var s Session  // Session{UserID: 0, Token: "", Active: false}
```

```
var s Session declared:
  s.UserID = 0       ← numeric zero
  s.Token  = ""      ← empty string
  s.Active = false   ← boolean zero
  Every field is safe to read immediately.
```

**Why (Section 4.4):** Go allocates memory zeroed. This eliminates an entire class of bugs that languages like C have with uninitialized memory.

### Rule 5: *T has all methods, T only has value receiver methods

This is the most frequently tested Go rule in interviews. A pointer `*T` can call both value and pointer receiver methods. A value `T` can only call value receiver methods.

```go
type UserService struct{ db *sql.DB }
func (s UserService) Name() string     { return "users" }  // value receiver
func (s *UserService) Reload()         { /* ... */ }        // pointer receiver

// UserService  methods: { Name() }
// *UserService methods: { Name(), Reload() }
```

```
Value (UserService):
  ┌──────────────┐
  │  Name() ✅   │  ← only value receiver methods
  │  Reload() ❌  │
  └──────────────┘

Pointer (*UserService):
  ┌──────────────┐
  │  Name() ✅   │  ← both value and pointer receiver methods
  │  Reload() ✅  │
  └──────────────┘
```

**Why (Section 4.5):** When a value is stored in an interface, the interface holds a *copy*. If Go allowed pointer-receiver methods on that copy, mutations would silently hit the copy instead of your original. Go blocks this at compile time.

### Rule 6: Interface matching is implicit

If your type has all the methods an interface asks for, it fits. No `implements` keyword.

```go
type Handler interface { ServeHTTP(http.ResponseWriter, *http.Request) }
type UserHandler struct{}
func (h *UserHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) { /* ... */ }
// *UserHandler has ServeHTTP → it fits Handler. No registration needed.
```

```
Handler interface needs: ServeHTTP(ResponseWriter, *Request)
*UserHandler has:        ServeHTTP(ResponseWriter, *Request)  ✅ match
  → *UserHandler fits Handler automatically
```

**Why:** Go's design avoids the coupling that `implements` creates. You can write an interface in one package and have types in a completely different package match it without importing the interface package.

### Rule 7: Embedding promotes, doesn't inherit

The embedded type's methods are promoted to the outer struct. But the receiver is always the embedded type, not the outer struct.

```go
type AuditLog struct{ Message string }
func (a AuditLog) Print() { fmt.Println(a.Message) }

type OrderService struct{ AuditLog }
svc := OrderService{AuditLog{"order created"}}
svc.Print()  // calls AuditLog.Print() — receiver is AuditLog, not OrderService
```

```
svc.Print() → compiler rewrites → svc.AuditLog.Print()
  receiver = AuditLog (the embedded value), NOT OrderService
  This is delegation, not inheritance.
```

**Why (Section 4.6):** There's no virtual dispatch in Go. The embedded type doesn't know it's embedded. It always sees itself as the receiver.

### Rule 8: Ambiguous embedding is a compile error

If you embed two types that both have a method with the same name, Go won't guess which one you mean.

```go
type Logger struct{}
func (Logger) Start() { fmt.Println("log start") }

type Metrics struct{}
func (Metrics) Start() { fmt.Println("metric start") }

type Server struct{ Logger; Metrics }
s := Server{}
s.Start()          // COMPILE ERROR: ambiguous selector
s.Logger.Start()   // OK — disambiguate explicitly
```

```
Server embeds Logger AND Metrics → both have Start()
Go promotes BOTH → conflict at same depth → compile error
Fix: call s.Logger.Start() or s.Metrics.Start() explicitly
```

**Why:** Go won't make assumptions about which promoted method you want. Explicit is better than implicit when there's ambiguity.

### Rule 9: Untyped constants fit any compatible type

An untyped constant like `42` or `"hello"` can be assigned to any type with a compatible underlying type, without explicit conversion.

```go
type UserID int64
const defaultID = 0      // untyped constant
var uid UserID = defaultID  // OK — no conversion needed
```

```
defaultID is untyped → Go sees it can represent 0 as int64 → fits UserID
No explicit conversion required for untyped constants.
```

**Why:** Untyped constants are a convenience — they make the type system less painful for literal values while still being type-safe at runtime.

---

## 6. Code Examples (Show, Don't Tell)

### Defined type vs underlying type

```go
type UserID int64
type SessionID int64

var uid UserID = 42
var sid SessionID = uid           // COMPILE ERROR: different types!
var sid2 SessionID = SessionID(uid) // OK: same underlying type
```

```
Step 1: uid is type UserID, value 42
Step 2: sid = uid → FAILS because UserID and SessionID are different types
        Even though both have underlying type int64!
        This is the POINT of defined types — type safety.
Step 3: SessionID(uid) → explicit conversion works
        Compiler knows both underlying types are int64 → safe to convert
```

### Zero value usefulness

```go
var mu sync.Mutex   // ready to use, no initialization needed
mu.Lock()
defer mu.Unlock()

var buf bytes.Buffer // empty buffer, ready to write
buf.WriteString("hello")
```

```
In Go, the zero value IS the ready-to-use state — no extra setup step:
  sync.Mutex{}  → locked: false, ready to Lock()
  bytes.Buffer{} → empty buffer, ready to Write()
  
This is a design principle, not an accident.
```

### Value vs pointer and interface matching

```go
type Repository interface {
    FindByID(id int64) error
}

type UserRepo struct{ connStr string }

func (r *UserRepo) FindByID(id int64) error { return nil }

var repo Repository
repo = &UserRepo{"postgres://..."}  // ✅ *UserRepo has FindByID()
repo = UserRepo{"postgres://..."}   // ❌ COMPILE ERROR: UserRepo (value) lacks FindByID()
```

```
Step 1: Repository interface requires: FindByID(int64) error

Step 2: FindByID() is defined on *UserRepo (pointer receiver)
  *UserRepo methods: { FindByID() }   ← has it
  UserRepo methods:  { }              ← empty! No value receiver methods.

Step 3: repo = &UserRepo{"postgres://..."}  → *UserRepo has all methods Repository asks for → ✅
  What repo looks like in memory (interface = 16 bytes):
    stack 0xC000060000: repo = [ tab: *itab{Repository, *UserRepo} | data: 0xC000080000 ]
                                                                            │
                                                                            ▼
    heap 0xC000080000: UserRepo{ connStr: "postgres://..." }
  Calling repo.FindByID(1): tab → method table → find FindByID → call with data ptr 0xC000080000

Step 4: repo = UserRepo{"postgres://..."}  → UserRepo does NOT have FindByID() → ❌ COMPILE ERROR
  Why? The interface would store a COPY of UserRepo in the data slot.
  If Go allowed pointer-receiver methods on this copy, mutations would
  hit the copy (inside the interface), not your original UserRepo.
  Go prevents this silent bug at compile time.
```

### Embedding and method promotion

```go
type AuditLog struct{}
func (a AuditLog) Record(msg string) { fmt.Println(msg) }

type OrderService struct {
    AuditLog  // embedding
    Name string
}

svc := OrderService{Name: "orders"}
svc.Record("order placed") // promoted from AuditLog
```

```
Step 1: OrderService embeds AuditLog (not a field name, only the type)
Step 2: AuditLog has method Record()
Step 3: Go promotes Record() to OrderService — svc.Record() works
Step 4: Under the hood: svc.Record("order placed") → svc.AuditLog.Record("order placed")
        The receiver is AuditLog, NOT OrderService
```

### The embedding "inheritance" trap

```go
type NotificationService struct{}
func (n NotificationService) Channel() string { return "email" }
func (n NotificationService) Send() string    { return "sending via " + n.Channel() }

type OrderNotifier struct{ NotificationService }
func (o OrderNotifier) Channel() string { return "sms" }

notifier := OrderNotifier{}
fmt.Println(notifier.Send()) // "sending via email" — NOT "sending via sms"!
```

```
Step 1: notifier.Send() → Go looks for Send() on OrderNotifier
        OrderNotifier doesn't have Send() directly
        But embedded NotificationService does → promoted → calls NotificationService.Send()

Step 2: Inside NotificationService.Send(): "sending via " + n.Channel()
        n is type NotificationService (the receiver is ALWAYS the embedded type)
        n.Channel() calls NotificationService.Channel() → "email"

Step 3: Result: "sending via email"
                 <-- NOT "sending via sms"!

Inside `NotificationService.Send`, the receiver `n` is a `NotificationService`, 
not an `OrderNotifier`, so `n.Channel()` always calls `NotificationService.Channel()`.
The outer type's `Channel()` is never in play for that call. There is no dynamic dispatch.
This is delegation, not the outer struct replacing the embedded type's behavior mid-call.
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

Paste into [Go Playground](https://go.dev/play/) and predict output BEFORE running:

```go
package main

import "fmt"

type Config struct{ Env string }
func (c Config) Label() string { return c.Env }

type AppConfig struct {
    Config
    Env string
}

func main() {
    ac := AppConfig{Config{"staging"}, "production"}
    fmt.Println(ac.Env)
    fmt.Println(ac.Label())
}
```

> [!success]- Answer
> 
> `production` then `staging`. `ac.Env` accesses AppConfig's own `Env` field (shadows Config's). But `ac.Label()` calls `Config.Label()` which uses `c.Env` — Config's Env, which is "staging".

### Tier 2: Fix the Bug (5 min)

This code should implement the `Stringer` interface but doesn't compile:

```go
type User struct {
    Name string
    Age  int
}

func (u *User) String() string {
    return fmt.Sprintf("%s (age %d)", u.Name, u.Age)
}

func printUser(s fmt.Stringer) {
    fmt.Println(s.String())
}

func main() {
    u := User{"Alice", 30}
    printUser(u) // doesn't compile!
}
```

> [!success]- Hint
> 
> `String()` is defined on `*User` (pointer receiver), but `u` is a value. Values don't have pointer-receiver methods in their list of methods.

> [!success]- Fix
> 
> Either change to value receiver: `func (u User) String()` or pass a pointer: `printUser(&u)`.

### Tier 3: Build It (15 min)

1. Create a `Storage` interface with `Save(key string, value []byte) error`
2. Implement it for `MemoryStore` (value receiver) and `RedisStore` (pointer receiver — it holds a connection string)
3. Write a function `storeConfig(s Storage)` and call it with both types
4. Observe which requires `&` and which doesn't. Then verify with `var _ Storage = MemoryStore{}` and `var _ Storage = (*RedisStore)(nil)` compile-time checks.

> Full solutions with explanations → [[exercises/T01 Go Type System - Exercises]]

---

## 7. Edge Cases & Gotchas

### Value can't fit an interface with pointer-receiver methods

```go
type Writer interface { Write([]byte) }
type ResponseBuffer struct{}
func (w *ResponseBuffer) Write(b []byte) {}

var w Writer = ResponseBuffer{}  // ❌ COMPILE ERROR
var w Writer = &ResponseBuffer{} // ✅ OK
```

```
ResponseBuffer methods:  { }           ← no methods (Write is on *ResponseBuffer)
*ResponseBuffer methods: { Write() }   ← has it

Interface stores a COPY of the value.
If Go allowed pointer-receiver methods on a copy:
  mutations would hit the copy, not your original → silent data loss
Go prevents this at compile time.
```

**Why**: Go won't silently take the address of a value stored in an interface, because the interface holds a copy — mutations via pointer receiver would be lost.

> **In plain English:** When you put a value into an interface, Go stores a copy. If the method needs to modify the original, a copy won't do — so Go blocks it at compile time rather than letting you silently modify a copy that nobody else can see.

### Method call shorthand does NOT apply to interfaces

```go
v := ResponseBuffer{}
v.Write(data) // ✅ works: compiler rewrites to (&v).Write(data)

// BUT for interfaces, this shorthand does NOT apply:
var w Writer = v // ❌ still fails
```

```
Direct method call:
  v.Write(data) → compiler sees you can take the address of v with & → rewrites to (&v).Write(data)
  This is shorthand that Go lets you write — a convenience the compiler provides.

Interface assignment:
  var w Writer = v → compiler checks the methods on ResponseBuffer (not *ResponseBuffer)
  ResponseBuffer has no Write() → COMPILE ERROR
  
  The shorthand does NOT apply here because the interface would store a COPY,
  and taking &copy would be meaningless (not your original v).
```

> Direct method calls get automatic `&v` insertion. Interface assignment does not.

### Ambiguous embedding

```go
type Logger struct{}
func (Logger) Start() { fmt.Println("log start") }

type Metrics struct{}
func (Metrics) Start() { fmt.Println("metric start") }

type APIServer struct{ Logger; Metrics }

s := APIServer{}
s.Start()          // ❌ COMPILE ERROR: ambiguous selector
s.Logger.Start()   // ✅ disambiguate explicitly
```

```
APIServer embeds both Logger and Metrics.
Both Logger and Metrics have Start().
Go promotes BOTH → conflict at the same depth level.
s.Start() is ambiguous — which Start()?
Fix: call explicitly via s.Logger.Start() or s.Metrics.Start()
```

### You can't take the address of a map value with &

```go
type User struct{ Name string }
m := map[string]User{"alice": {"Alice"}}
m["alice"].Name = "Bob" // ❌ COMPILE ERROR: cannot assign to map value
```

```
Why? Map entries physically relocate during growth. Traced through memory:

  BEFORE growth (B=0, 1 bucket at 0xC000080000):
    stack 0xC000060000: m = ptr → hmap at 0xC000010000
    hmap.B=0, hmap.buckets → 0xC000080000
    hash("alice", hash0) → 0xD4...9E
    bucket = 0xD4...9E & (2^0 - 1) = 0 → bucket #0 at 0xC000080000
    tophash 0xD4 at slot 0 → key="alice", value=User{Name:"Alice"} at 0xC000080030

  Suppose Go let you do: ptr := &m["alice"]
    ptr = 0xC000080030

  Insert 7 more users → load factor exceeded → growth:
    New bucket array at 0xC000090000
    "alice" evacuated to new bucket1, slot 2 → now at 0xC000090158

  ptr is still 0xC000080030 → old bucket → DANGLING POINTER
  Go prevents this at compile time: map values are not something you can
  take the address of. You can't modify them in place for the same reason.
```

**Fix**: copy out, modify, assign back:

```go
u := m["alice"]
u.Name = "Bob"
m["alice"] = u
```

Or use `map[string]*User` for direct mutation.

### Nil interface vs typed nil (from [[T02 Go Memory Allocation & Value Semantics]])

```go
var p *MyStruct = nil
var i interface{} = p
i == nil // false — type info is non-nil
```

```
i = [ type: *MyStruct | data: nil ]
     type is NOT nil → interface is NOT nil

For true nil: var i interface{} = nil
i = [ type: nil | data: nil ] → i == nil is true
```

### Comparable types and map keys

Not all types can be map keys or compared with `==`:

| Comparable? | Types |
|---|---|
| ✅ Yes | bool, numeric, string, pointer, channel, interface, array (if element type is comparable), struct (if all fields comparable) |
| ❌ No | slice, map, function |

```go
m := map[[]int]string{} // ❌ COMPILE ERROR: slice not comparable
```

> **In plain English:** Slices, maps, and functions can't be compared with `==`. They're reference types whose contents can change independently, so a simple equality check would be misleading. Go refuses to do it rather than guess wrong.

---

## 8. Performance & Tradeoffs

Your `UserService` handles 5k RPM. It has a `User` struct (4 fields, ~80 bytes), methods with both value and pointer receivers, and you're passing these through interfaces for dependency injection. Where does the type system actually cost you something?

| Pattern | What it costs | You'd see this in... | Verdict |
|---|---|---|---|
| Value receiver on small struct (<128 bytes) | One copy per call (~80 bytes on stack) | `User.FullName()` returning a formatted string | Noise — the copy is stack-allocated, gone in nanoseconds |
| Pointer receiver on `UserService` with `*sql.DB` | 8-byte pointer, no copy | `(*UserService).FindByID()` every request | Use this — you don't want copies of your DB connection |
| Defined type `UserID int64` vs raw `int64` | Zero runtime cost — types are erased at compile time | Every function signature in your service | Free type safety — no reason not to use it |
| Type alias `LegacyID = int64` | Zero cost — compiler resolves at compile time | Migration: `pkg/v1.ID` aliased in `pkg/v2` | Use during refactoring, then remove the alias |
| Embedding `AuditLog` into `OrderService` | Promoted methods are normal calls — no indirection, no allocation | `svc.Record("order placed")` | Same cost as calling the method on the embedded type directly |
| Storing value in interface | One heap allocation for the data (if >pointer-sized) | `var repo Repository = &UserRepo{}` → pointer fits in interface, no extra alloc | Pointer-typed values fit without allocation. Value types may allocate. |

### What actually hurts

The type system itself costs you almost nothing at runtime — types are a compile-time concept. What bites you is the *indirect* cost of pointer receivers causing heap escapes. Your `UserService` has a `Reload()` method with a pointer receiver. That means `*UserService` is the concrete type everywhere. If you ever store it in an interface (for dependency injection), the compiler can't prove it doesn't escape, so the struct moves to the heap. At 5k RPM, that's 5k allocations/sec for a struct that could've lived on the stack if all methods were value receivers. For a small struct, that shows up in `alloc_objects` under `pprof`.

Bill Kennedy's rule: if *any* method on a type uses a pointer receiver, *all* methods should use pointer receiver for consistency. Mixing confuses the reader about mutation intent.

### What to measure

```bash
# See which values escape to the heap because of pointer receivers
go build -gcflags="-m" ./... 2>&1 | grep "escapes to heap"

# Benchmark value vs pointer receiver for your specific struct size
go test -bench=BenchmarkReceiver -benchmem ./...

# Profile allocations in a running service
go tool pprof -alloc_objects http://localhost:6060/debug/pprof/heap
```

In practice: if your struct is under 128 bytes and doesn't need mutation, value receivers keep it on the stack. If it holds a `*sql.DB`, a `*redis.Client`, or any connection — pointer receivers, no question.

---

## 9. Common Misconceptions

| Misconception | Reality |
|---|---|
| Embedding is inheritance | **WRONG** — it's delegation/composition; the receiver is always the embedded type |
| Value `T` has all the methods `*T` has | **WRONG** — `T` only has value receiver methods; `*T` has both |
| `type X int` and `int` are the same | **WRONG** — they're distinct types; explicit conversion required |
| `type X = int` creates a new type | **WRONG** — it's an alias; `X` IS `int` |
| Zero value means uninitialized | **WRONG** — zero value is a deliberate, defined, safe state |
| You need constructors in Go | **WRONG** — design for useful zero values instead; use `NewX()` only when needed |
| Struct embedding means the outer type IS-A inner type | **WRONG** — outer type HAS-A inner type with promoted access |

---

## 10. Related Tooling & Debugging

### Type inspection

```bash
go vet ./...                    # catches interface matching issues
go build -gcflags="-m"          # shows escape analysis (type-related escapes)
```

**What each command does:** `go vet ./...` runs the static analyzer on all packages in the tree (suspicious code, some API misuse, and related issues; use it to catch problems before they ship). `go build` compiles; `-gcflags` forwards flags to the compiler, and `"-m"` means print **escape analysis and optimization decisions** (which values escape to the heap, inlining, etc.).

### Compile-time interface checks

```go
var _ Handler = (*Server)(nil)
```

This is a zero-cost compile-time assertion pattern. Use it to catch interface matching bugs early. If `*Server` doesn't have all the methods `Handler` asks for, this line fails at compile time.

### Struct size and alignment

```bash
go tool objdump -s "main.MyStruct" ./binary  # check layout
```

```go
import "unsafe"
fmt.Println(unsafe.Sizeof(MyStruct{}))   // total size in bytes
fmt.Println(unsafe.Alignof(MyStruct{}))  // alignment requirement
```

---

## 11. Interview Gold Questions

### Q1: Why can't a value type fit an interface that has pointer receiver methods?

**Answer**: When you assign a value to an interface, the interface stores a **copy** of that value. If Go allowed pointer-receiver methods on that copy, any mutations would happen to the interface's internal copy, not the original — silently losing writes. Go prevents this at compile time. The fix: assign a pointer to the interface (`&val`), or switch to value receivers if mutation isn't needed.

### Q2: What's the difference between `type X int` and `type X = int`?

**Answer**: `type X int` creates a **new defined type** with `int` as its underlying type. `X` and `int` are distinct — you can't assign between them without explicit conversion, and you can attach methods to `X`. `type X = int` creates a **type alias** — `X` IS `int`, no conversion needed, but you can't add methods to `X`. Use defined types for domain modeling (`UserID`, `Currency`) where you want the compiler to catch mix-ups. Use aliases when you're migrating a type from one package to another and don't want to break callers.

### Q3: How does struct embedding work? Why isn't it inheritance?

**Answer**: Embedding promotes the embedded type's fields and methods to the outer type for convenience, but it's composition, not inheritance. The critical difference: when a promoted method runs, its receiver is always the **embedded type**, not the outer type. So if `NotificationService.Send()` calls `n.Channel()`, it calls `NotificationService.Channel()` even if the outer `OrderNotifier` type defines its own `Channel()`. There's no virtual dispatch. This means embedding can't be used for the Template Method pattern or polymorphism — it's pure delegation.

---

## 12. Final Verbal Answer

> "Go's type system is entirely compile-time — there are no runtime type surprises. Every type you create has three things: what it's made from (the underlying type), what its zero value is, and what methods it has.
> 
> The rule that comes up in every interview is the value vs pointer receiver asymmetry. If you define a method on `*T`, only pointers can use it — a plain value `T` can't. This matters when you store something in an interface, because the interface holds a copy. If Go allowed pointer-receiver methods on that copy, mutations would silently hit the copy instead of your original. So Go blocks it at compile time.
> 
> Go uses composition instead of inheritance. When you embed a type, its fields and methods get promoted to the outer struct, but it's delegation — the embedded type is always the receiver. If you come from Java or Python and expect the outer struct to override methods mid-call, it won't. There's no dynamic dispatch.
> 
> Defined types like `type UserID int64` give you compile-time safety — the compiler won't let you pass a `UserID` where a `SessionID` is expected, even though both are `int64` underneath. Type aliases are just nicknames for gradual refactoring. And every variable in Go starts at its zero value — no uninitialized memory, no constructors needed if you design your types well."

---

## 13. Comprehensive Interview Questions

> Full interview question bank (15 questions) → [[questions/T01 Go Type System - Interview Questions]]

Preview of most frequently asked:

1. **Why can't a value type fit an interface that has pointer receiver methods?** `[COMMON]`
2. **How does struct embedding work? Why isn't it inheritance? Show a case where it surprises you.** `[COMMON]`
3. **What's the nil interface trap and how do you avoid it in production?** `[TRICKY]`

---

## Quick Recall (test yourself)

> [!info]- 1. What are the three properties of every Go type?
> Every type has an **underlying type**, a well-defined **zero value**, and a **list of methods** (value `T` only has value receiver methods; `*T` has both value and pointer receiver methods).

> [!info]- 2. Can a value type fit an interface with pointer receiver methods?
> **Not as `T` alone** — a value only has value receiver methods, so it can't fit an interface that requires `*T` methods. You need to pass a `*T` instead.

> [!info]- 3. What does struct embedding promote?
> It **promotes** the embedded type's **field names and methods** onto the outer type for direct access, but the receiver of promoted methods remains the **embedded value**, not a subclass (delegation, not OO inheritance).

---

> See [[Glossary]] for term definitions.
