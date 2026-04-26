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

An **interface value** in Go is always a **pair of words** at runtime. The first word is **“what is this, really”**. The second word is **“where is the value”**. Together they are the whole interface, not a single pointer. **Non-empty** interfaces, which are interfaces that list **one or more methods**, use a runtime shape called **iface** with a method dispatch table. **Empty** interfaces, written **`any`**, use **eface**, which is just **type** plus **data**, with no method table. In the **Go runtime** source, **eface** is the real struct name for the empty slot pair. The **iface** name flags the variant that must carry a **method table** pointer. That table is a struct called an **itab** from **interface** **table** in the runtime. It is the one **record** the runtime reuses to map an **interface** to a **concrete** type. You will read that name in **runtime/iface.go** in the public tree.

> **In plain English:** A hotel gives you a **wristband** and a **key**. The band says *pool access* and *room type*. The key opens the right door. The empty desk only holds *some key* and a sticky note of *room type* — no “rules for how to swim.”

---

## 2. Core Insight (TL;DR)

**Interfaces power polymorphism without inheritance.** A concrete type **satisfies** an interface when its **method set** matches, not when you write `implements` in source code. The interview-shaped picture: **iface** is two words, **`{ tab, data }`**, where **tab** points to an **itab** that caches the concrete type, the interface type, a hash, and the **function pointers** for the interface’s methods. **eface** is **`{ _type, data }`** — only type metadata and a data pointer, because there are **no** methods to dispatch. The **nil interface** trap sticks because a Go interface is **nil** only if **both** the **type word** and the **data word** are nil. A **typed** nil, such as a nil pointer in a still-known concrete type, is **not** a nil **interface** value.

> **In plain English:** *Empty pocket* is not the same as a pocket with a **card that says “apple”** and a **moldy apple-shaped hole** where the fruit should be. The label makes it “something,” even when the fruit is missing.

---

## 3. Mental Model (Lock this in)

### Gift box with a label

Picture a **box** with two parts. **What kind of thing** you have is a **label**. The **thing itself** is the **content**. A **methoded** interface is a box whose label also has **a short instruction card**: which buttons to press. That card is the **itab**’s function list. A **truly** empty **interface value** in the *Go sense* needs **no label and no object**. If a label exists, the box is not an empty *interface* — it may still hold a nil **concrete** pointer.

> **In plain English:** A **sealed** empty gift box: no label, no gift. **Some** “empty” boxes still have a **printed** tag that says *book*; they are not the same as *nothing*.

### Mistake that teaches: the nil `error` from a typed nil pointer

```go
type MyError struct{ msg string }

func (e *MyError) Error() string {
	if e == nil {
		return "nil *MyError"
	}
	return e.msg
}

func oops() *MyError { return nil }

func main() {
	var e1 error = oops() // *MyError is nil, but you assign to `error` (interface)
	if e1 != nil {
		fmt.Println("e1 is non-nil interface:", e1, "Error():", e1.Error())
	} else {
		fmt.Println("e1 is nil")
	}
}
```

```
Step 1:  oops() returns nil  →  *MyError value is a nil **pointer**
        pointer itself:  (nil *MyError)

Step 2:  assign to `error` (a non-empty interface)
        iface:  +------+     +--------+
                 | tab| ──▶  |  itab  |  (pairs *MyError with `error` interface)
                 +------+     +--------+
                 | data| ──▶  (nil *MyError)  ← **typed** nil pointer, still a "value slot"
                 +------+

        type word: NOT nil  (tab/itab is live)
        data word: nil      (nil pointer to *MyError)

        BOTH words are not nil/empty?  -> type is set  -> interface != nil  <-- aha
```

`e1 != nil` is **true** even though the **underlying** pointer is nil. Callers who thought “nil pointer means nil error” get **burned** here.

> **In plain English:** The cash register beeps **sold** as soon as the **SKU sticker** is on the bag, even if the bag is **empty** inside. The **SKU** is the dynamic type. The **bag** can be empty. The order is still a real line item.

```
iface:   [ tab  → itab+fun[]  ]  [ data → *concrete  ]
eface:   [ _type → *type     ]  [ data → value/addr  ]
```

---

## 4. How It Actually Works (Internals) [INTERMEDIATE → ADVANCED]

> **In plain English:** The runtime is a **shipping warehouse**. A **dolly** is two slots: *what is this* and *where is the crate*. The **itab** is a **sticker** that was printed once, listing which dock doors the crate must pass through for that *interface* contract.

### 4.1 `eface` — the empty interface / `any`

**eface** is the runtime name for a **struct** of two fields. The **first** points to `_type` metadata. The **second** is `unsafe.Pointer` to the value, or a word-sized value depending on the compiler. You see this for **`any`**, the modern spelling of the empty interface.

**Conceptual shape, read-the-runtime only:**

```go
// runtime/iface.go — conceptual, names vary slightly by version
// type eface struct {
//     _type *_type
//     data  unsafe.Pointer
// }
```

```go
var x any = 42
var y any = "hello"
```

```
eface for x:   [ _type → int  ] [ data → 42 or *copy on heap, impl-dependent ]
eface for y:   [ _type → str  ] [ data → *string data                        ]
```

> **In plain English:** A **luggage** tag and a **handle**. No menu of “how to ride” on the tag — *anything* you can shove in counts.

### 4.2 `iface` — non-empty interface values

**iface** is the other layout. The **first** word is **`tab`**, a pointer to **itab**. The **second** is **`data`**, a pointer to the **dynamic** value as stored for this call. When you have methods, the runtime must know how to find **`Read`**, **`Write`**, and so on for that **dynamic** type through **that** interface. That is what **itab** stores.

**Conceptual shape:**

```go
// type iface struct {
//     tab  *itab
//     data unsafe.Pointer
// }
```

```go
var r io.Reader = strings.NewReader("x")
_ = r
```

```
iface for r (Reader):
  +------+        +-----------------------------+
  | tab  |   ──▶  | itab: io.Reader + *strings.Reader, fun[...]  |
  +------+        +-----------------------------+
  | data |   ──▶  the concrete reader value
  +------+
```

> **In plain English:** A **kiosk** screen shows **which app** and **one icon row**. The first word picks the **row of app icons** for this contract. The second word is the **app instance** you tapped.

### 4.3 `itab` — the interface table

**itab** is the struct that **pairs** an **interface type** and a **concrete type** and holds **function pointers** for the interface’s methods, plus a **type hash** used for type switches. The **`fun` slice** is a flexible array. Each slot is a **code pointer** for one interface method, in **interface** method order.

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
  inter  ──▶  type descriptor for the **interface** type (io.Reader, etc.)
  _type  ──▶  type descriptor for the **concrete** type
  hash   →    32-bit hash of _type (fast switch paths)
  fun[i] →    i-th interface method, resolved for this (interface,concrete) pair
```

> **In plain English:** A **wedding seating chart** where each **guest** name is matched to a **real chair number**. The chart is only printed **once** per *guest list plus venue layout* pair, then you thumb the same printout every time that pair shows up.

### 4.4 `itab` caching and `itabTable`

The runtime does **not** recompute a full **itab** on every interface assignment. There is a **global** or **per-runtime** table. The exact structure is a **hashtable** you will read as `itabTable` in the source. A given **interface** plus **concrete** pair gets a single **itab** built **once** and reused. That is your **"computed once, shared forever"** story for interviews.

**Checklist, not a mermaid flowchart — does a new (iface,concrete) pair get a new itab?**

1. Is there already an **itab** for that pair? → Reuse the pointer, done.
2. Not yet? → **Build** the **itab** once, place it in the table, return it.
3. **Later** uses only **look up** the same entry.

> **In plain English:** A **stencil** of your logo is cut **once** in metal. You **spray** through the stencil every T-shirt, not a new **metal shop** per shirt.

### 4.5 Type assertions and type switches

A **type assertion** asks: **does the dynamic** type match, and **give** me the value? The runtime compares the **dynamic** `*_type` in the **iface** or **eface** to what you ask for, or to each **case** in a **type switch**. For **eface** it is a **direct** type check. For **iface** the target must still be **assignable** and **compatible** with the **itab**’s view of the world.

**Assertion kinds:**

- **`v.(T)`** with **one** return — **panics** on failure.
- **`t, ok := v.(T)`** with **two** returns — **ok** is **false** on failure, **no** panic.
- **type switch** compiles to a small decision tree, often with **hash** and **itab** fast paths for interfaces.

```go
var i any = 3
j := i.(int)    // j == 3
// k := i.(int64) // would panic: dynamic is int, not int64
w, ok := i.(int64) // w == 0, ok == false
```

```
after i := 3  (eface, dynamic type int)
  assert int64:  _type is int, want int64  -> FAIL (panic or ok=false)
  assert int:     match -> OK, unwrap value
```

> **In plain English:** A **bouncer** checks your **photo ID**. The **one-result** form **throws** you out the door on mismatch. The **two-result** form **shrugs** and hands you a “no” slip instead of a **fight**.

### 4.6 Boxing: heap vs “inlined” data word

A concrete value in an **interface** is not always a separate heap allocation, but the **storable** part must fit the **model** the compiler uses. **Rule of thumb** for study: **very small** values that fit a **word** or are handled by a special fast path can avoid extra indirection. **Larger** structs, **strings** as **two-word** data, and many **nontrivial** things end up with **`data` pointing** at a **copy** on the **heap** or a stable **address** on the **stack** depending on escape analysis. **Do not** micro-optimize in production without a **benchmark**. **Do** know: **putting a value in an interface** can **allocate** for non-tiny cases.

```go
type Big [256]byte
var a any = Big{} // often escapes; interface holds pointer to copy, typically
var b any = byte(1)
```

```
Big  in interface:  data ──▶ (heap-allocated 256B copy, impl-dependent)  (often)
byte in interface:  data ──▶ may stay cheap / word tricks (version-dependent)
```

> **In plain English:** A **U-Haul** box for a **sofa** needs its **own** parking space. A **gum** wrapper can ride in your **shirt** pocket. **Moving** strategy depends on how big the thing is.

---

## 5. Key Rules & Behaviors

### Rule 1: A nil interface needs **both** words empty

```go
var i1 error                 // (nil, nil) — truly nil
var p *os.PathError = nil
var i2 error = p             // (tab set, data nil) — i2 is NOT nil
fmt.Println(i1 == nil)       // true
fmt.Println(i2 == nil)       // false
```

```
i1:  [ tab:  nil  ]  [ data: nil  ]  -> interface == nil  ✅

i2:  [ tab:  itab* ]  [ data: nil *os.PathError ]  -> interface != nil  ❌ for "nil error" checks
     ^^ type word is live ^^
```

> **In plain English:** An **envelope** is **truly** empty when there is **no** stamp and **no** paper. A **sealed** empty envelope with a **stamp** is still a **shipment**, not *nothing*.

---

### Rule 2: **Method sets** decide satisfaction — `T` vs `*T`

A type **`T` satisfies** an interface if **`T`’s** method set is enough. A pointer type **`*T` might add** methods, especially **when receivers are on the pointer** only. **Pass** the wrong **kind** to an interface-typed field and the compiler may refuse. A **value** in an interface of type **`*T` where methods need `*T` stores** a **pointer** in **`data`**.

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

> **In plain English:** A **jacket** with **pockets in the lining** is not the same as the same jacket **hung** without the lining turned out. The **hanger** you hand to the **coat check** is **your hand shape**: **value** vs **address** changes what the staff can **reach**.

---

### Rule 3: Comma-ok is safe, single result **panics** on mismatch

```go
var i any = "s"
j := i.(int)         // panics: wrong dynamic type
k, ok := i.(int)     // k == 0, ok == false, no panic
```

```
single v.(T) on mismatch:  -> **panic** (runtime walk leaves your handler)

comma-ok:  if types disagree  ->  ok = false, value zero  -> you stay alive
```

> **In plain English:** A **safety** chain on a **hazard** door **stops** the door at **two inches**; you feel the **click** and **stop**. **One** unguarded shove, you **nose-bleed**.

---

### Rule 4: Empty interface and `any` take **any** value, give **no** methods

With **`any`**, you can store **any** value. The **trade** is: you can only do **type assertion**, **reflection**, or **pass to generic** helpers. There is **no** `DoSomething` on `any` until you assert or constrain.

```go
func f(a any) {
	// a.Foo() // illegal: any has no methods
	_ = a
}
```

```
any/eface:  [ _type ] [ data ]   —  no  fun[ ]  list in the box itself
            you must  **learn**  the type  before  calling  methods
```

> **In plain English:** A **mystery** box at a **flea** market. You can shove in **any** trinket. The box does not **buzz**, **glow**, or **brew coffee** on its own. You **open** the lid, **identify** the item, then use the right **tool**.

---

### Rule 5: **Comparable** interface values only if the **dynamic** type is **comparable**

`==` and `!=` for interface values compare the **type** and the **value** for **concrete** `==`. If the **dynamic** type is **not** comparable, **at runtime** a **panic** can occur when the comparison is **reached** — a classic **map key** and **==** footgun.

```go
var a any = []int{1}
var b any = []int{1}
// _ = a == b  // run-time: panic, slices are not comparable
type C struct{ x int }
// two empty interfaces holding comparable structs: possible
// two holding func() or map or slice: danger on ==
```

**Checklist, “will `x == y` for two `any` be legal at run time?”**

1. If **either** **dynamic** type is not comparable, **==** is **not** a safe idea.
2. If **both** are the **same** comparable type and the **values** use **legal** `==` for that type, you get a **defined** result.
3. If you need **safety** when types differ, assert first or use a **type switch** before comparing.

> **In plain English:** You **weigh** two **rocks** of the **same** mineral. You **do not** weigh **bubbles** — they **pop** when the scale **tries**.

---

## 6. Code Examples (Show, Don't Tell)

### iface vs eface at the **value** level

```go
package main

import (
	"fmt"
	"io"
	"strings"
)

type Greeter interface{ Greet() string }

type hi struct{ name string }
func (h hi) Greet() string { return "hi, " + h.name }

func main() {
	var g Greeter = hi{"Ann"} // iface: tab+data, interface has a method
	var a any = hi{"Bob"}     // eface: _type+data, no per-method itab
	fmt.Println("iface Greet:", g.Greet())
	fmt.Printf("any: %v\n", a)
	var r io.Reader = strings.NewReader("x")
	_ = r // iface, io.Reader has Read
}
```

```
Greeter:   iface, tab+data+itab+fun[...] for Greet
any:       eface, _type+data
io.Reader: iface, itab for Read, etc.
```

> **In plain English:** A **greeting** line at the bank needs a **script**. A **plain** “stuff goes here” bin needs **no** script, only **size** and **shape** labels.

### Type assertion, safe and unsafe, side by side

```go
var i any = 10

n, ok := i.(int)    // 10, true
f, bad := i.(float64) // 0, false — no panic
// x := i.(string)  // WOULD panic
```

### Nil interface trap — memory trace, **detailed**

```go
type E struct{ s string }
func (e *E) Error() string {
	if e == nil {
		return "nil *E" // never reached when e is a typed nil through interface field
	}
	return e.s
}
func g() *E { return nil }
func f() error { return g() } // *E nil -> into error (iface) -> **non-nil** error

func main() {
	err := f()
	if err != nil { // true!
		println("handler runs — surprise")
	} else {
		println("nil")
	}
}
```

```
f returns *E nil
  g():   data word for *E is a nil **pointer** value

f():   converts to `error` — iface
  [ tab: itab( error, *E )  ]  [ data: (nil *E) ]

err != nil  checks **interface** nilness, not *nil pointer inside*
  type word: **set**
  => err is **not** a nil `error`  <-- aha
```

> **In plain English:** A **lawsuit** folder with the **plaintiff** line **filled in** and **no** attached papers is not an **empty** drawer. The **folder tab** *exists*.

---

## 6.5. Practice Checkpoint

Three hands-on levels. All runnable in the Go Playground: [https://go.dev/play/](https://go.dev/play/)

### Tier 1: Predict the output (2 min)

```go
var i1 fmt.Stringer
var i2 fmt.Stringer = (*strings.Builder)(nil)
fmt.Println("i1==nil", i1 == nil, "i2==nil", i2 == nil)
```

Predict before you run. Name **each** word in **iface** for `i1` and `i2`.

> [!success]- Answer
> Prints: `i1==nil true i2==nil false`
>
> - `i1` is a zero-value interface: `iface{ tab: nil, data: nil }` -- both fields nil, so `i1 == nil` is true.
> - `i2` has a typed nil assigned: `iface{ tab: *itab(Stringer, *strings.Builder), data: nil }` -- the tab field is set (it knows the type), so `i2 == nil` is false even though the concrete pointer is nil.
>
> This is the classic **typed nil interface trap**.

### Tier 2: Fix the bug (5 min)

A function is supposed to return “no error” on success, but **always** returns a non-nil `error` to callers. The body ends with `return someTypedNil` where `someTypedNil` is a `*MyError` that is `nil`, assigned to the named result `err error`. **Fix** it so a **true** success path yields a **nil** `error` for `(error)` interface checks.

> Hint: the **name** and **concrete** nil pointer in an **error**-typed return are not your friend.

> [!success]- Answer
> The function returns `*MyError(nil)` through an `error` interface. The interface gets `iface{ tab: itab(error, *MyError), data: nil }` -- non-nil because tab is set.
>
> Fix: return untyped nil explicitly on the success path:
> ```go
> func doWork() error {
>     var myErr *MyError // nil
>     // ... logic that might set myErr ...
>     if myErr != nil {
>         return myErr
>     }
>     return nil  // untyped nil — both iface fields will be nil
> }
> ```
> Never return a typed nil pointer directly through an interface return.

### Tier 3: Build it (15 min)

Build a small **plugin** registry: `Register(name string, p Plugin)` and `Get(name) (Plugin, bool)` where `Plugin` is an interface. **Prohibit** name collisions, allow **introspection** of the **dynamic** type, and test that **storing a nil** concrete pointer does **not** look like a **missing** plugin when you are careless with the **return** `error` pattern from a helper.

> Full solutions with explanations → `[[exercises/T11 Interface Internals (iface & eface) - Exercises]]`

---

## 7. Edge Cases & Gotchas

| Gotcha | Code sketch | What bites you | Fix |
|--------|-------------|----------------|-----|
| Nil interface | `var e error = (*E)(nil)` | `e != nil` is **true** | Return **untyped** `nil` for `error`, or compare **concrete** after assert |
| `==` on interfaces with bad dynamics | `any` with slices | **panic** on `==` | Assert to comparable, or `reflect.DeepEqual` with eyes open |
| **Pointer to interface** | `var r *io.Reader` | Almost never what you want | `io.Reader` value, or **generic** |
| **Embedding** and methods | `type T struct { io.Reader }` | Method **promotion** can satisfy interfaces **unexpectedly** | Be explicit, read method **sets** |
| Unordered map keys of interface | `map[any]T` with func keys | run-time **panic** | Constrain to comparable, or string keys |

**Pointer to `io.Reader` sketch:**

```go
// var pr *io.Reader  // a pointer to an interface box — very rare, confusing
// var r  io.Reader   // normal: holds iface {tab, data}
```

> **In plain English:** A **magnifying glass** pointed at a **magnifying glass** does not make **reading** any clearer. A **thing you read** is a **book**. A **thing that points to the idea of books** is a **librarian’s memo about shelf layout**, not the book.

---

## 8. Performance & Tradeoffs

| Topic | What to know | When it matters |
|------|----------------|-----------------|
| **Indirect** call | Through **itab** `fun` slots, one more hop than a **devirtualized** static call | Hot loops with **tight** per-op budgets |
| **Ballpark** | On modern `amd64` class CPUs, a **deferred** devirtualized call is often a **handful of nanoseconds**; **measured** interface overhead is small but **not** free | Microservices where **p99** lives in a **tight** inner loop |
| **Allocation** | Assigning a **large** value to `any` or an interface-typed value can **escape** the value | High-allocation **RPC** or **encoding** |
| **Monomorphization** | **Generics** can avoid an interface in **some** call sites, at **code size** cost | Libraries where **inlining** and **devirt** are critical |

> **In plain English:** A **toll** booth adds **seconds** on a long road trip, **nothing** on a day’s drive. You **count** the tolls only on the **repeated** daily **commute**.

---

## 9. Common Misconceptions

| Misconception | Reality |
|--------------|---------|
| A nil `*T` stored in an interface is a nil interface | The **itab** or **`_type`** is **set**; only **data** is nil, so the **interface** is often **non-nil** |
| **Interfaces** are "just pointers" | They are **two** words, **type** plus **value slot**, not a single pointer in general |
| `any` is "free" | Still **erases** static types; **assert** or **generics** to recover **operations** |
| **Small** `interface{}` never allocates | The **runtime** and **escapes** are **compiler-** and **version-**sensitive. **Profile** if it matters |
| I need `interface{ io.Reader; io.Writer }` at once | In Go, use **`io.ReadWriter`**-style **named** interfaces, or **embed**, or a **struct** of two - **unions of methods** on one name need **composition** in the type system mind |

---

## 10. Related Tooling & Debugging

| Tool / knob | When to use it |
|-------------|-----------------|
| `go build -gcflags=-m=2` (per-package escape) | See **escapes to heap** for values ending in `any` or interfaces |
| `go tool objdump` / `pprof` | Prove **inlining** and **devirtualization** in **hot** paths |
| `GODEBUG=...` (version-specific) | Only when a **Go release note** or **expert** points you there — **defaults** are usually what you test against |
| **Staticcheck** and friends | Catches a few **impossible** comparisons and **suspicious** nil patterns |

> **In plain English:** A **wrench** you **rarely** use lives in the **trunk** under the **jumper** cables, not the **glove** box. Open the trunk on **nights** the **rattle** is **loud** enough to **bother** you.

---

## 11. Interview Gold Questions

### Q1: When is an `error` `nil`?

**Answer in depth:** A variable of **interface** type `error` is `nil` only if **both** the **type** word and the **value** word are the **empty** / **nil** state that represents “no type” and “no value.” A **concrete-typed** nil, such as a `nil` **pointer** to a type that **implements** `Error()`, still has a **known** **dynamic** type, so the **error** is **not** `nil` as an interface.

**What interviewers want:** The **pair-of-words** model and a **concrete** **typed-nil** return bug story.

> **Verbal 15-second:** *An error is nil only if it’s the zero interface, both words empty. A nil pointer in a known concrete type is still a non-nil error interface. Return plain `nil` for success, not a typed nil variable.*

### Q2: What lives in an **itab**?

**What they probe:** The **(interface, concrete)** **pairing**, the **function pointer** array, **caching** in a **global** table, and the **`hash`** for **faster** type switches. Bonus: **itab** is not recomputed for every call.

> **Verbal 15-second:** *Itab matches an interface to a concrete type. It has method function pointers, a type hash, and the runtime reuses a cached itab for each unique pair. That’s the iface first word.

### Q3: Why can two `==`ing interface values be **illegal** for some `any` values?

**What they test:** `==` for interfaces uses the **concrete** **equality** rules. If the **dynamic** type is **uncomparable**, **==** **panics** at **run** time, even when the **shapes** “look the same” to a human for **slices** and **maps**.

> **Verbal 15-second:** *Interface compare delegates to the dynamic type. If that type can’t be compared, you get a panic, not a false. That’s why you can’t use a slice as a map key.*

---

## 12. Final Verbal Answer (≈ 30 s)

*An interface value is two words. For non-empty interfaces, **iface** stores an **itab** pointer and a data pointer. **itab** is the **cached** table that pairs a concrete type with a given interface, holds **method** entry points, and a **hash** for type switches. For **`any`**, **eface** is only **type** metadata and **data** — no method table. Polymorphism is **structural**: your type satisfies the interface if its **method set** is enough, with the usual `T` vs `*T` **receiver** rules. The famous **bug** is the **non-nil** `error` from a **nil** `*T`, because the **type** word is set. Type assertions with **comma-ok** are **safe**; a bare assertion **panics** on mismatch. Know **comparability** for `==` on interface values, and that **indirect** calls have **small** but real cost — profile before you "optimize" away from interfaces everywhere.*

---

## 13. Comprehensive Interview Questions

> Full interview question bank (12–15 items, frequency-sorted) → [[questions/T11 Interface Internals (iface & eface) - Interview Questions]]

**Preview — questions you should already own:**

1. **Draw** `iface` and `eface` on a whiteboard and label the words. Where do the **function pointers** live?
2. **Walk** the **nil `error` from nil `*MyError` Return** in four **steps** of memory.
3. **Why** does a **type switch** on an interface sometimes get **O(1) fast** paths, and when does it **fall** back to a **chain** of checks?

> See [[Glossary]] for term definitions.
