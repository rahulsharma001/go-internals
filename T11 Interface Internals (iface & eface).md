# T11 Interface Internals (iface & eface)

> **Reading Guide**: Sections 1-3 and 6 are essential first read (20 min).
> Sections 4-5 deepen understanding (15 min).
> Sections 7-12 are interview-specific — read closer to interview day.
> Section 13 is your comprehensive interview Q&A bank → [[questions/T11 Interface Internals (iface & eface) - Interview Questions]]
> Something not clicking? → [[simplified/T11 Interface Internals (iface & eface) - Simplified]]

---

## 0. Prerequisites

Complete these before starting this topic:

- [[prerequisites/P01 Structs & Struct Memory Layout]]
- [[prerequisites/P02 Methods & Receivers]]
- [[prerequisites/P05 Interfaces Basics]]

---

## 1. Concept

When you assign a concrete type to an interface variable, Go does not “wrap” it in something you see in source code — but at **runtime** there **is** a small two-word bundle. Think of it as a **tiny envelope**: one slot says **what kind of thing this is**, the other says **where the actual value lives**.

That bundle is what people mean by an **interface value**. It is **always two machine words** (on normal 64-bit builds): not “a pointer,” but **type information + value slot**.

- If the interface **lists methods** (like `error`, `io.Reader`, or your own `Repository`), the runtime uses a layout called **`iface`**. The first word points at an **`itab`** — a **table** that remembers “for *this* interface and *this* concrete type, here are the real function entry points for each method.” The second word is the **data pointer** (or a word-sized value, depending on what the compiler did).
- If the interface is **empty** — written `any` or `interface{}` — the runtime uses **`eface`**. That is just **`_type` + `data`**: metadata about the concrete type, and a pointer to the stored value. There is **no** per-method table in the box itself, because an empty interface promises **no** methods.

You will read these names in **`runtime/iface.go`** in the public tree. **`eface`** is the real struct name for the empty pair. **`iface`** is the variant that must carry a **method table** pointer. **`itab`** is short for **interface table**: one **record** the runtime builds (and usually **caches**) for each **(interface type, concrete type)** pair.

> **In plain English:** A hotel gives you a **wristband** and a **key**. The band says *pool access* and *room type*. The key opens the right door. The empty desk only holds *some key* and a sticky note of *room type* — no “rules for how to swim.”

**This note** is where **iface / eface / itab** belong: learn them once, tie each to a **handler**, **`map[string]any`**, or **`Repository` + `*PostgresRepo`**.

---

## 2. Core Insight (TL;DR)

**Interfaces power polymorphism without inheritance.** A concrete type **satisfies** an interface when its **method set** matches — you never write `implements` in Go.

The interview-shaped picture:

- **`iface`** (non-empty interface) ≈ **`{ tab, data }`**. **`tab`** → **`itab`** (cached method dispatch + pairing). **`data`** → the dynamic value (often a pointer to a heap object).
- **`eface`** (`any`) ≈ **`{ _type, data }`**. Only type metadata + value — **no** `fun[]` in the pair itself.

The **`nil` interface** trap sticks because a Go interface is **`nil` only if both words are “empty”**: no dynamic type installed **and** no value slot. A **typed nil** — for example `(*NotFoundError)(nil)` stored in an `error` variable — still has a **known dynamic type**. The **type word is live**. So `err != nil` can be **true** even when the **pointer inside** is nil.

> **In plain English:** *Empty pocket* is not the same as a pocket with a **card that says “apple”** and a **moldy apple-shaped hole** where the fruit should be. The label makes it “something,” even when the fruit is missing.

---

## 3. Mental Model (Lock this in)

### Gift box with a label

Picture a **box** with two parts. **What kind of thing** you have is a **label**. The **thing itself** is the **content**.

- A **methoded** interface is a box whose label also carries **a short instruction card**: which buttons to press. That card is the **`itab`**’s function list.
- A **truly empty** interface value in the Go sense needs **no label and no object** to be nil. If a label exists, the box is not an empty *interface* — it may still hold a nil **concrete** pointer.

**Grounding — `iface`:** This is what Go creates when you do:

```go
var store Repository = &PostgresRepo{db: db}
```

When you assign a **`*PostgresRepo`** to a **`Repository`** interface variable, Go creates a **small wrapper** with two parts: a pointer to a **table of methods** (**`itab`**) and a pointer to **your actual repo**. The **`itab`** is built or looked up once per **(`Repository`, `*PostgresRepo`)** pair and reused.

**Grounding — `eface`:** This is what **`any`** or **`interface{}`** looks like internally — **just a type pointer and a data pointer**. No method table in the pair. That is why `json.Unmarshal` into `map[string]any` creates a **forest of `eface` values**: every value slot in the map is “type + pointer,” discovered at decode time.

> **In plain English:** A **sealed** empty gift box: no label, no gift. **Some** “empty” boxes still have a **printed** tag that says *book*; they are not the same as *nothing*.

### Mistake that teaches: production handler, typed nil `*NotFoundError`

Your `GetUser` service returns `*NotFoundError` when the user is missing. On the “found” path someone refactors poorly and returns a **typed nil**:

```go
type NotFoundError struct {
	UserID string
}

func (e *NotFoundError) Error() string {
	if e == nil {
		return "nil *NotFoundError"
	}
	return "user not found: " + e.UserID
}

// GetUser returns *NotFoundError on missing user; nil pointer on success.
func (s *UserService) GetUser(ctx context.Context, id string) *NotFoundError {
	if id == "" {
		return &NotFoundError{UserID: id}
	}
	// BUG: success path returns typed nil
	return (*NotFoundError)(nil)
}

func getUserHandler(w http.ResponseWriter, r *http.Request) {
	// svc := &UserService{} // ...
	err := error(svc.GetUser(r.Context(), r.PathValue("id")))
	if err != nil {
		// Caller thinks "any non-nil error is a real failure"
		http.Error(w, err.Error(), http.StatusInternalServerError) // 500
		return
	}
	w.WriteHeader(http.StatusOK) // never reached on the bug path
}
```

**What the handler expected:** “nil pointer from `GetUser` means no error → 200.”

**What Go actually did:** assigning `(*NotFoundError)(nil)` to `error` builds an **`iface`** whose **`tab`** points at the **`itab` for (`error`, `*NotFoundError`)**, and whose **`data`** word is nil. **`err != nil` is true** because the **interface** is not the zero interface — only the **data** word is nil.

```
Step 1:  GetUser returns (*NotFoundError)(nil)
        concrete side: nil pointer

Step 2:  handler does err := error(...)
        iface:
                +------+     +-----------------------------+
                | tab  | ──▶ | itab: error + *NotFoundError |
                +------+     +-----------------------------+
                | data | ──▶ (nil *NotFoundError)
                +------+

        type word: NOT nil  (tab/itab is live)
        data word: nil

        => err != nil   // interface is "something," even though pointer is nil
        => 500 instead of 200
```

**Fix pattern:** on success, return an **untyped** `nil` from a function typed as `error`, or return `error` from `GetUser` directly and use `return nil` on the happy path — never `return (*NotFoundError)(nil)` through an `error`-typed channel unless you **mean** “this is still an error value with a type.”

> **In plain English:** The cash register beeps **sold** as soon as the **SKU sticker** is on the bag, even if the bag is **empty** inside. The **SKU** is the dynamic type. The **bag** can be empty. The order is still a real line item.

```
iface:   [ tab  → itab+fun[]  ]  [ data → *concrete  ]
eface:   [ _type → *type     ]  [ data → value/addr  ]
```

---

## 4. How It Actually Works (Internals) [INTERMEDIATE → ADVANCED]

> **In plain English:** The runtime is a **shipping warehouse**. A **dolly** is two slots: *what is this* and *where is the crate*. The **itab** is a **sticker** that was printed once, listing which dock doors the crate must pass through for that *interface* contract.

### 4.1 `eface` — the empty interface / `any`

**`eface`** is the runtime name for a struct of two fields. The first points at **`_type`** metadata (the concrete type’s description). The second is `unsafe.Pointer` to the value — or a word-sized representation, depending on compiler/version.

You see this whenever you use **`any`**, including at **API boundaries** where you deliberately erase static type information.

**Conceptual shape, read-the-runtime only:**

```go
// runtime/iface.go — conceptual, names vary slightly by version
// type eface struct {
//     _type *_type
//     data  unsafe.Pointer
// }
```

**Real boundary:** `encoding/json` decoding into **`map[string]any`**:

```go
var payload map[string]any
_ = json.Unmarshal(body, &payload)
// Every value in `payload` sits behind an eface: { _type, data }.
// The decoder picks a concrete type per JSON token (float64, string, []any, map[string]any, ...).
```

```
any holds int or string:  [ _type → concrete ] [ data → value or pointer — impl-dependent ]
```

### 4.2 `iface` — non-empty interface values

**`iface`** is the layout for interfaces that **require methods**. The first word is **`tab`** → **`itab`**. The second is **`data`**.

When you pass a **`*PostgresRepo`** where a **`Repository`** is expected, Go does **not** copy your whole repo into the interface. It installs **two pointers**: one to the **shared** **`itab`** for (`Repository`, `*PostgresRepo`), one to the **concrete** repo value (almost always on the heap).

**Conceptual shape:**

```go
// type iface struct {
//     tab  *itab
//     data unsafe.Pointer
// }
```

```go
type Repository interface {
	GetUser(ctx context.Context, id string) (*User, error)
}

type PostgresRepo struct { /* db *sql.DB, etc. */ }

func (r *PostgresRepo) GetUser(ctx context.Context, id string) (*User, error) {
	// ...
	return nil, nil
}

func main() {
	var store Repository = &PostgresRepo{}
	_ = store
}
```

```
iface for store (Repository holding *PostgresRepo):

  +------+        +--------------------------------------------+
  | tab  |   ──▶  | itab: Repository + *PostgresRepo, fun[...]   |
  +------+        +--------------------------------------------+
  | data |   ──▶  | *PostgresRepo value (heap object)            |
  +------+        +--------------------------------------------+
```

> **In plain English:** A **kiosk** screen shows **which app** and **one icon row**. The first word picks the **row of app icons** for this contract. The second word is the **app instance** you tapped.

### 4.3 `itab` — the interface table

**`itab`** is the struct that **pairs** an **interface type** and a **concrete type** and holds **function pointers** for the interface’s methods, plus a **type hash** used for type switches and fast paths.

The **`fun` “slice”** is a flexible array in memory: one **code pointer** per interface method, in **interface method order**.

**Conceptual fields:**

```go
// type itab struct {
//     inter *interfacetype
//     _type *_type
//     hash  uint32
//     _     [4]byte
//     fun   [1]uintptr // var-length in memory; one slot per iface method
// }
```

```
itab
  inter  ──▶  type descriptor for the **interface** type (Repository, error, io.Reader, ...)
  _type  ──▶  type descriptor for the **concrete** type (*PostgresRepo, *NotFoundError, ...)
  hash   →    32-bit hash of _type (fast switch paths)
  fun[i] →    i-th interface method, resolved for this (interface, concrete) pair
```

> **In plain English:** A **wedding seating chart** where each **guest** name is matched to a **real chair number**. The chart is only printed **once** per *guest list plus venue layout* pair, then you thumb the same printout every time that pair shows up.

### 4.4 `itab` caching and `itabTable`

The runtime does **not** rebuild a full **`itab`** from scratch on every assignment. There is a **table** (conceptually a hash table) — you will see **`itabTable`** in the source — that **caches** `(interface, concrete) → *itab`.

**Grounding:** Go builds the method lookup table **once** and reuses it. So the **second** time you assign a `*PostgresRepo` to a `Repository`, it is **cheap**: lookup or pointer copy, not a full metadata walk.

**Checklist — does a new (iface, concrete) pair get a new itab?**

1. Is there already an **`itab`** for that pair? → Reuse the pointer, done.
2. Not yet? → **Build** the **`itab`** once, store it in the table, return it.
3. **Later** uses only **look up** the same entry.

### 4.5 Type assertions and type switches

A **type assertion** asks: **does the dynamic type match**, and **give** me the value? The runtime compares the dynamic **`_type`** in **`eface`** or the concrete side recorded in **`itab`** for **`iface`**.

**Assertion kinds:**

- **`v.(T)`** with **one** return — **panics** on failure.
- **`t, ok := v.(T)`** with **two** returns — **`ok == false`** on failure, **no** panic.
- **type switch** compiles to a decision tree, often with **hash** / **`itab`** fast paths.

```go
var i any = 3
j := i.(int)       // j == 3
// k := i.(int64) // would panic: dynamic is int, not int64
w, ok := i.(int64) // w == 0, ok == false
```

```
after i := 3  (eface, dynamic type int)
  assert int64:  _type is int, want int64  -> FAIL (panic or ok=false)
  assert int:    match -> OK, unwrap value
```

### 4.6 Boxing: heap vs “inlined” data word

**Boxing** here means: **putting a concrete value inside an interface-shaped slot** so the runtime can treat it uniformly. The **`data` word** might point at a **heap copy**, or hold a **small scalar**, depending on type, size, and **escape analysis**.

**Grounding:** When you stuff a **small `int`** into an **`any`**, the compiler/runtime often ends up with a **heap allocation** anyway for the stored bits — and for **hot paths** (millions of iterations), that **adds up**. In contrast, **interface calls in HTTP handlers** — a few per request — are **not** where this shows up first.

**Large struct example — `AuditEvent`:**

```go
type AuditEvent struct {
	ID       [16]byte
	ActorID  string
	Action   string
	Metadata [256]byte // pushes struct size up — typical “big value” for escape demos
	IP       [16]byte
	TS       int64
}

func logAny(a any) { _ = a }

func emit() {
	var ev AuditEvent
	logAny(ev) // often: `data` → heap copy of AuditEvent (impl-dependent)
}
```

```
AuditEvent in interface:  data ──▶ (heap-allocated copy of large struct)  (often)
small int in any:         data ──▶ may still allocate / use word tricks (version-dependent)
```

**Advisor read:** escape analysis is **the compiler’s job**; **`any` at JSON boundaries** is normal overhead — **profile** inner loops if you box **`AuditEvent`-sized** values millions of times.

---

## 5. Key Rules & Behaviors

### Rule 1: A nil interface needs **both** words empty

```go
var err1 error // (nil, nil) — truly nil

var err2 error = (*NotFoundError)(nil)
fmt.Println(err1 == nil) // true
fmt.Println(err2 == nil) // false — classic typed-nil trap
```

```
err1:  [ tab:  nil  ]  [ data: nil  ]  -> interface == nil  ✅

err2:  [ tab:  itab* ]  [ data: nil *NotFoundError ]  -> interface != nil
       ^^ type word is live ^^
```

### Rule 2: **Method sets** decide satisfaction — `T` vs `*T`

A type **`T` satisfies** an interface if **`T`’s** method set is enough. A pointer **`*T` might add** methods when only `*T` has the receiver.

```go
type S struct{}
func (s S)  A() {}
func (s *S) B() {} // B only on pointer

type I interface{ A() }
type J interface{ A(); B() }

var _ I = S{}  // ok
// var _ J = S{}  // compile error: S lacks B
var _ J = &S{} // ok
```

```
Interface J needs A and B.
  S   method set: {A}      -> does not satisfy J
  *S  method set: {A, B}   -> satisfies J
```

### Rule 3: Comma-ok is safe, single result **panics** on mismatch

```go
var i any = "s"
// j := i.(int)     // panics: wrong dynamic type
k, ok := i.(int)    // k == 0, ok == false, no panic
```

```
single v.(T) on mismatch:  -> **panic** (runtime walk leaves your handler)

comma-ok:  if types disagree  ->  ok = false, value zero  -> you stay alive
```

### Rule 4: Empty interface and `any` take **any** value, give **no** methods

With **`any`**, you can store **any** value. The **trade** is: you cannot call **`GetUser`** on `any` until you **assert**, **reflect**, or **decode into a concrete type**.

```go
func inspect(a any) {
	// a.GetUser(...) // illegal: any has no methods
	_ = a
}
```

```
any/eface:  [ _type ] [ data ]   —  no  fun[ ]  list in the box itself
            you must  **learn**  the type  before  calling  methods
```

### Rule 5: **Comparable** interface values only if the **dynamic** type is **comparable**

`==` / `!=` on interfaces delegates to the **concrete** type’s rules. If the dynamic type is **not** comparable, you can **panic at runtime** — classic **`map` key** footgun.

```go
var a any = []int{1}
var b any = []int{1}
// _ = a == b  // run-time panic: slices are not comparable
```

**Checklist — will `x == y` for two `any` be legal at run time?**

1. If **either** dynamic type is not comparable, **`==`** is a bad idea.
2. If **both** are the **same** comparable type and values are legally comparable, you get a defined result.
3. If you need safety when types differ, **assert first** or use a **type switch**.

## 6. Code Examples (Show, Don't Tell)

### `iface` vs `eface` at the **value** level (`Notifier` vs `any`)

```go
package main

import (
	"fmt"
	"io"
	"strings"
)

type Notifier interface {
	Notify(msg string) error
}

type EmailNotifier struct{ SMTPHost string }
func (e EmailNotifier) Notify(msg string) error { /* send email */ return nil }

type SlackNotifier struct{ Webhook string }
func (s SlackNotifier) Notify(msg string) error { /* post */ return nil }

func main() {
	var n Notifier = EmailNotifier{SMTPHost: "smtp.example.com"}
	// iface: tab → itab(Notifier, EmailNotifier), data → EmailNotifier value

	var a any = SlackNotifier{Webhook: "https://hooks.slack.com/..."}
	// eface: _type → SlackNotifier, data → SlackNotifier value

	_ = n.Notify("deployed")
	fmt.Printf("any holds: %T\n", a)

	var r io.Reader = strings.NewReader("x")
	_ = r // iface: Reader has Read method → non-empty interface
}
```

```
Notifier:   iface — tab+data+itab+fun[...] for Notify
any:        eface — _type+data only
io.Reader:  iface — itab for Read, etc.
```

### Type assertion, safe and unsafe, side by side

```go
var i any = 10

n, ok := i.(int)     // 10, true
f, bad := i.(float64) // 0, false — no panic
// x := i.(string)   // WOULD panic
```

Minimal **typed-nil** trace (same mechanics as **§3**’s `getUserHandler`): `var err error = (*NotFoundError)(nil)` → `iface{ tab: live, data: nil }` → `err != nil` is **true**.

## 6.5. Practice Checkpoint

Three hands-on levels. All runnable in the Go Playground: [https://go.dev/play/](https://go.dev/play/)

### Tier 1: Predict the output (2 min)

```go
var i1 fmt.Stringer
var i2 fmt.Stringer = (*strings.Builder)(nil)
fmt.Println("i1==nil", i1 == nil, "i2==nil", i2 == nil)
```

Predict before you run. Name **each** word in **`iface`** for `i1` and `i2`.

> [!success]- Answer
> Prints: `i1==nil true i2==nil false`
>
> - `i1` is a zero-value interface: `iface{ tab: nil, data: nil }` — both fields nil, so `i1 == nil` is true.
> - `i2` has a typed nil assigned: `iface{ tab: *itab(Stringer, *strings.Builder), data: nil }` — the tab field is set (it knows the type), so `i2 == nil` is false even though the concrete pointer is nil.
>
> This is the classic **typed nil interface trap**.

### Tier 2: Fix the bug (5 min)

A `GetUser`-style function returns `*NotFoundError`. On success it incorrectly returns `(*NotFoundError)(nil)`, which is then assigned to an `error` in the handler. **`err != nil` is always true** on the happy path. **Fix** it so a true success path yields a **nil** `error` for `(error)` interface checks.

> Hint: the **name** and **concrete** nil pointer in an **`error`**-typed return are not your friend.

> [!success]- Answer
> Typed nil through `error` → `iface{ tab: itab(error, *NotFoundError), data: nil }` — **non-nil** `error`. Fix: return `(*User, error)` with `return user, nil`, or check `*NotFoundError` **before** assigning to `error`, or `return nil` (untyped) on success — never `return (*NotFoundError)(nil)` as the success path into `error`.

### Tier 3: Build it (15 min)

Build a small **plugin** registry: `Register(name string, p Plugin)` and `Get(name) (Plugin, bool)` where `Plugin` is an interface. **Prohibit** name collisions, allow **introspection** of the **dynamic** type, and write a **mock test** that stores a **nil** `*fakePlugin` in a map **without** confusing “missing plugin” vs “present but broken nil.”

> Full solutions with explanations → `[[exercises/T11 Interface Internals (iface & eface) - Exercises]]`

---

## 7. Edge Cases & Gotchas

| Gotcha | Code sketch | What bites you | Fix |
|--------|-------------|----------------|-----|
| Nil interface | `var e error = (*NotFoundError)(nil)` | `e != nil` is **true** | Return **untyped** `nil` for `error`, or compare **concrete** before lifting to `error` |
| `==` on interfaces with bad dynamics | `any` with slices | **panic** on `==` | Assert to comparable, or `reflect.DeepEqual` with eyes open |
| **Pointer to interface** | `var r *io.Reader` | Almost never what you want | `io.Reader` value, or **generics** |
| **Embedding** and methods | `type T struct { io.Reader }` | Method **promotion** can satisfy interfaces **unexpectedly** | Be explicit, read method **sets** |
| Unordered map keys of interface | `map[any]T` with func keys | run-time **panic** | Constrain to comparable, or string keys |

**Pointer to `io.Reader` sketch:**

```go
// var pr *io.Reader  // a pointer to an interface box — very rare, confusing
// var r  io.Reader   // normal: holds iface {tab, data}
```

## 8. Performance & Tradeoffs

**Where interface cost actually shows up**

- **HTTP handlers, gRPC methods, DB repository calls:** an indirect call through an **`itab`** is **noise** next to I/O. **Interface calls here basically do not matter** for throughput in the way people fear.
- **Tight loops** — log ingestion parsing **10M rows/s**, hot codecs, SIMD-adjacent inner kernels — **might**: devirtualization fails, **`any` boxing** allocates, **branchy** type switches miss prediction.

| Topic | What to know | When it matters |
|------|----------------|-----------------|
| **Indirect call** | Through **`itab.fun`** slots — one more hop than a **static** call | Inner loops with **tight** per-op budgets, not typical handlers |
| **Ballpark** | On modern `amd64` CPUs, measured interface overhead is **small** but **not zero** | When the **inner loop** is the whole product |
| **Allocation / boxing** | Large structs like **`AuditEvent`** assigned to **`any`** often **escape** | High-rate **encoding** paths, **analytics** pipelines |
| **Monomorphization** | **Generics** can avoid an interface at **some** call sites, at **code size** cost | Libraries where **inlining** and **devirtualization** are critical |

**Bottom line:** **Interface calls in handlers** rarely dominate; **interface + `any` boxing in a tight loop** processing **10M rows/s** might — **measure** that path.

## 9. Common Misconceptions

| Misconception | Reality |
|--------------|---------|
| A nil `*T` stored in an interface is a nil interface | The **`itab`** or **`_type`** is **set**; only **`data`** is nil — the interface is often **non-nil** |
| **Interfaces** are "just pointers" | They are **two** words, **type** plus **value slot**, not a single pointer in general |
| `any` is "free" | Still **erases** static types; decoding into **`map[string]any`** builds **efaces** for every value |
| **Small** values in `any` never allocate | **Compiler** and **version** matter — **benchmark** if you care |
| I need `interface{ io.Reader; io.Writer }` at once | Prefer **`io.ReadWriter`**-style **named** interfaces, **embedding**, or a **struct** of two — **unions of methods** need **composition** in the type system |

---

## 10. Related Tooling & Debugging

| Tool / knob | When to use it |
|-------------|-----------------|
| `go build -gcflags=-m=2` (per-package escape) | See **escapes to heap** for values ending in `any` or interfaces |
| `go tool objdump` / `pprof` | Prove **inlining** and **devirtualization** in **hot** paths |
| `GODEBUG=...` (version-specific) | Only when a **Go release note** or **expert** points you there |
| **Staticcheck** and friends | Catches some **suspicious** nil patterns |

## 11. Interview Gold Questions

### Q1: When is an `error` `nil`?

**What they want:** the **two-word** model and a **real** bug: handler returns 500 because `GetUser` handed up `(*NotFoundError)(nil)` and `err != nil` stayed true.

**How I'd say it in the room:** “An `error` is only nil when it’s the **zero interface** — both the type side and the data side are empty. If you put a **typed nil pointer** into `error`, Go still knows the **dynamic type**, so the interface isn’t nil even though the pointer inside is. That’s the production footgun: you think you returned ‘no error,’ but you returned a **non-nil `error` value**.”

### Q2: What lives in an **`itab`?

**What they probe:** the **(interface, concrete)** pairing, **`fun`** entry points, **`hash`**, and **caching** via **`itabTable`**.

**How I'd say it in the room:** “It’s the cached row for one interface and one concrete type: **which actual functions implement the interface methods**, plus a **hash** for fast switches. The runtime **builds it once** per pair and **reuses** the pointer — so the expensive part isn’t every call, it’s **first contact** between that interface and that concrete type.”

### Q3: Why can `==` on two `any` values **panic**?

**What they test:** interface compare **delegates** to the dynamic type; **slices**, **maps**, and **functions** blow up.

**How I'd say it in the room:** “`==` on interfaces asks the **concrete** type whether equality is even defined. If the dynamic type **isn’t comparable**, you don’t get `false` — you get a **panic**. That’s why slice-backed `any` values are scary in maps or blind compares.”

---

## 12. Final Verbal Answer (≈ 30 s)

**If someone says “explain interfaces at runtime” without wanting a speech:**

“I’d start with **two words**. Non-empty interface is **`iface`**: pointer to **`itab`** plus **data**. The **`itab`** is the cached **vtable-ish** thing for that **interface + concrete type** pair — method pointers, hash, reused from a table. **`any` is `eface`**: **type + data**, no method table in the pair — that’s your **`map[string]any`** after JSON. **Polymorphism** is structural: method sets, **`T` vs `*T`**. The bug to name is **typed nil**: `(*NotFoundError)(nil)` in an `error` is **not** a nil error. Assertions: **comma-ok** good, single form **panics**. Performance: **fine** at HTTP boundaries; worry when you’re in a **tight loop** or stuffing **big values** into **`any` without measuring.”

---

## 13. Comprehensive Interview Questions

> Full interview question bank (12–15 items, frequency-sorted) → [[questions/T11 Interface Internals (iface & eface) - Interview Questions]]

**Preview — questions you should already own:**

1. **Draw** `iface` and `eface` on a whiteboard and label the words. Where do the **function pointers** live?
2. **Walk** the **nil `error` from `(*NotFoundError)(nil)`** in four **steps** of memory — include the **500 vs 200** handler story.
3. **Why** does a **type switch** on an interface sometimes get **O(1) fast** paths, and when does it **fall** back to a **chain** of checks?

> See [[Glossary]] for term definitions.
