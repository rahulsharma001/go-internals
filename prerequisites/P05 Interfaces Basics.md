# P05 Interfaces Basics

> **Prerequisite note** — complete this before starting [[T09 Error Handling Patterns]], [[T11 Interface Internals (iface & eface)]], or [[T19 Context Package Internals]].
> Estimated time: ~20 min

---

## 1. Concept

An **interface** is a **contract**: a named set of method signatures. Any type that has those methods **satisfies** the interface. Callers depend on the contract, not on a concrete struct name.

> **In plain English:** Think **power outlet standards**. You do not label a lamp "implements US 120V outlet." If the plug shape matches, it fits. The wall cares about the **shape of the plug**, not the brand of the device.

---

## 2. Core Insight (TL;DR)

Go ties behavior to **methods**, not to type names. **Implicit satisfaction** means you never declare `implements`; the compiler checks method sets for you. **Interface values are two-part boxes**: a **dynamic type** and a **dynamic value**. **Nil is treacherous** here: a `nil` pointer **inside** a non-nil interface is **not** the same as a `nil` interface value.

---

## 3. Mental Model (Lock this in)

The outlet analogy again: the **interface** is the **socket shape**. The **concrete value** is the **device**. You can carry a **boxed device**: the box remembers **which device model** this is **and** holds the device **or** holds "nothing" in a way that still has a model sticker.

Rough picture of what an interface value conceptually carries:

MEMORY TRACE:

Step 1: Zero interface local (illustrative — e.g. `var s Speaker` before assignment)
stack:
  `s` @ 0x7ffcc0a0        ◄── interface slot (two words: type descriptor / data)
heap:
  —

──→  type word:  nil  (no dynamic type)
──→  data word:  nil  (no dynamic value)

Step 2: After `s = Dog{name:"Rex"}` (same section later — pattern preview)
stack:
  `s` still @ 0x7ffcc0a0  ◄── now holds non-nil type + pointer to value (or inline word)
heap:
  Dog payload @ 0xc0000140a0   ◄── `name`, etc.

──→  type word:  *Dog / itab for `Speaker`  ◄── "which plug shape"
──→  data word:  points at (or holds) concrete Dog  ◄── "the gadget"

```
Aha moment: you always reason about the pair (dynamic type, dynamic value). Nil-interface confusion is always about whether the type word is still set.
```

**Error-driven trap preview.** This **compiles** and prints **`false`** for `e == nil`:

```go
type MyError struct{ msg string }

func (e *MyError) Error() string { return e.msg }

var p *MyError = nil
var e error = p

// println(e == nil) -> false
```

The full step-through lives in **Section 6**. The headline bug pattern is:

MEMORY TRACE:

Step 1: `var p *MyError = nil` — typed nil pointer only
stack:
  `p` @ 0x7ffcc0b0     ◄── pointer variable
heap:
  —

──→  `p` stores address 0x0  (nil *MyError)

Step 2: `var e error = p` — interface assignment packs (type, value)
stack:
  `e` @ 0x7ffcc0c0     ◄── `error` is an interface value
heap:
  —

──→  type word:  *MyError / error itab  ◄── TYPE IS SET (not "absent")
──→  data word:  0x0  ◄── same nil pointer bits as `p`

Step 3: `e == nil` compares the whole interface, not the pointer alone
stack:
  (comparison uses both words of `e`)
heap:
  —

```
Aha moment: typed nil — type set, value nil — is NOT a nil interface. `e == nil` is false because the type half is non-nil.
```

> **In plain English:** A **labeled empty box** is not the same as **no box at all**. `nil` interface means **no label and no payload**. A **typed** `nil` payload still has a **label**.

---

## 4. How It Works

### 4.1 Implicit satisfaction

There is no `implements` keyword. If the type has the right methods, it **already** satisfies the interface.

```go
type Speaker interface {
	Speak() string
}

type Dog struct{ name string }

func (d Dog) Speak() string { return "woof" }

func Announce(s Speaker) { println(s.Speak()) }

func main() {
	Announce(Dog{name: "Rex"})
}
```

MEMORY TRACE:

Step 1: Compile-time — method set for `Dog` (value receiver)
stack:
  (compile-time only — no runtime frame yet)
heap:
  —

──→  `Dog`'s method set includes `Speak() string`  ◄── matches `Speaker`

Step 2: `main` calls `Announce(Dog{name: "Rex"})` — argument becomes `Speaker`
stack:
  `main` frame: literal `Dog{name: "Rex"}` @ 0x7ffcc0d0
  `Announce` param `s` @ 0x7ffcc120   ◄── interface `Speaker` (iface words)
heap:
  Dog value @ 0xc000016080   ◄── `name: "Rex"` (or equivalent)

──→  `s` type word:  itab for `(Dog, Speaker)`  (or *Dog pattern per implementation)
──→  `s` data word:  ◄── points at Dog payload

Step 3: Method dispatch — `s.Speak()`
stack:
  call resolves through itab → `Dog.Speak` (value receiver)
heap:
  same Dog @ 0xc000016080

```
Aha moment: implicit satisfaction is "can we build an iface with this concrete type for this interface?" — no separate implements table at runtime.
```

> **In plain English:** The compiler is a **bouncer checking dance moves**, not **checking your ID card against a list of approved names**.

### 4.2 The `error` interface

The standard library defines:

```go
type error interface {
	Error() string
}
```

MEMORY TRACE:

Step 1: `error` as a named interface type (prelude — no variable yet)
stack:
  —
heap:
  —

──→  required method: `Error() string`  ◄── one slot in the iface / itab template

Step 2: Any concrete type with that method can fill an `error` iface value
stack:
  future `var e error` will be (type word, data word)
heap:
  concrete value lives here once assigned

```
Aha moment: `error` is not special at runtime — it is still a two-word interface; the name is just the standard library's contract.
```

Anything with `Error() string` is an `error`. That is why you can `return fmt.Errorf(...)`, custom structs, or `errors.New("msg")` through the same return paths.

```go
type MyErr struct{ msg string }

func (e MyErr) Error() string { return e.msg }

func f() error {
	return MyErr{msg: "boom"}
}
```

MEMORY TRACE:

Step 1: `error` interface layout (conceptual — one method)
stack:
  (interface descriptor: needs `Error() string`)
heap:
  —

──→  iface identity:  method tuple `(Error)`  ◄── smallest useful contract

Step 2: `MyErr` value implements `error` (value receiver `Error`)
stack:
  `f` builds return value `err error` @ 0x7ffcc140
heap:
  MyErr struct @ 0xc0000160a0   ◄── `msg: "boom"`

──→  `err` type word:  itab for `(MyErr, error)`
──→  `err` data word:  ◄── points at MyErr value (not a pointer here)

Step 3: Caller sees `error` — dynamic type is `MyErr` until asserted
stack:
  caller's `err` iface copies the same pair
heap:
  same MyErr @ 0xc0000160a0

```
Aha moment: `error` is still a two-word iface; the only requirement is that the dynamic type's method table exposes `Error() string`.
```

> **In plain English:** **`error` is the smallest useful contract** in Go: "give me a string explanation."

### 4.3 Empty interface: `any` / `interface{}`

`any` is an alias for `interface{}`. It can hold **any value** because **every type** satisfies the **empty method set**.

```go
func Println(v any) {
	// fmt.Println eventually formats v; the parameter is "anything"
}

func main() {
	Println(42)
	Println("hi")
	Println(struct{ X int }{X: 1})
}
```

MEMORY TRACE:

Step 1: `Println(42)` — `any` holds a scalar (implementation may use special representation)
stack:
  `Println` param `v` @ 0x7ffcc160   ◄── `any` / empty interface (`eface`)
heap:
  —

──→  type word:  `int` descriptor
──→  data word:  holds `42` (or pointer to boxed int — implementation detail)

Step 2: `Println("hi")` — string is (ptr, len)
stack:
  `v` @ 0x7ffcc160
heap:
  string data @ 0xc0000160c0   ◄── backing bytes for `"hi"`

──→  type word:  `string`
──→  data word:  string header (ptr + len)

Step 3: `Println(struct{ X int }{X: 1})` — struct literal
stack:
  temporary struct @ 0x7ffcc180
heap:
  may be stack-only; iface still records concrete struct type

──→  type word:  anonymous struct type
──→  data word:  ◄── points at `{X:1}`

```
Aha moment: empty method set means every concrete type fits — you always pay the (type, value) tax on `any`.
```

> **In plain English:** **`any` is a generic shipping crate**. You can ship **anything**, but you **lose specific tools** until you **open the crate** with assertions or reflection.

### 4.4 Interface values as `(type, value)` pairs

An interface value is **not** "just a pointer." Conceptually it stores **type information** plus **the data** or **nil data** for that type.

Assigning a **pointer** sets dynamic type to **`*T`**. The dynamic value is the **pointer itself**, which may be **`nil`**.

MEMORY TRACE:

Step 1: Assignment `var i I = concrete` — iface receives a pair
stack:
  `i` @ 0x7ffcc1a0
heap:
  concrete payload @ 0xc000016100  (if pointer target or large value)

──→  type word:  concrete dynamic type `T` or `*T`
──→  data word:  pointer bits OR inline value per ABI

Step 2: Pointer case `var i I = (*Dog)(nil)` (illustrative typed-nil pattern)
stack:
  `i` @ 0x7ffcc1a0
heap:
  —

──→  type word:  *Dog / itab  ◄── set
──→  data word:  nil pointer  ◄── still a non-nil interface value

```
Aha moment: "assigning a pointer" means the type word names `*T`; a nil `*T` is still a complete iface pair.
```

### 4.5 Type assertions

A **type assertion** extracts the concrete side **you believe** is there.

```go
var v any = 42

n := v.(int)       // panics if wrong
x, ok := v.(int)   // ok is false if wrong; no panic
```

MEMORY TRACE:

Step 1: `var v any = 42` — `v` is `eface` with dynamic type `int`
stack:
  `v` @ 0x7ffcc1c0
heap:
  —

──→  type word:  `int`
──→  data word:  `42`

Step 2: `v.(int)` — extract concrete type matching dynamic type
stack:
  result `n` @ 0x7ffcc1d0  ◄── receives unboxed `int`
heap:
  —

──→  runtime compares dynamic type to `int`  ◄── match
──→  copies value bits into `n`

Step 3: `x, ok := v.(int)` — same check, no panic on failure
stack:
  `ok` @ 0x7ffcc1e0
heap:
  —

──→  if types match: `ok == true`, `x` gets value
──→  if mismatch: `ok == false`, `x` is zero value of `int`

```
Aha moment: assertion reads the iface's type word first — it is "unwrap if this is exactly the dynamic type I expect" (or interface-assert variant for interface targets).
```

**Asserting to concrete type `T`:** succeeds when the dynamic type is **`T`**, not when it is `*T` unless that is what is stored.

**Asserting to interface type `I`:** succeeds if the dynamic type **implements** `I`.

> **In plain English:** A type assertion is **"open the crate and insist it contains a hammer."** Use the **two-return form** if you are not **100% sure**.

### 4.6 Type switches

A **type switch** branches on the **dynamic type** of an interface value.

```go
func Describe(v any) string {
	switch x := v.(type) {
	case int:
		return fmt.Sprintf("int %d", x)
	case string:
		return fmt.Sprintf("string %q", x)
	default:
		return fmt.Sprintf("something else %T", x)
	}
}
```

MEMORY TRACE:

Step 1: Enter `Describe(v)` — `v` is `any` / `eface`
stack:
  `v` @ 0x7ffcc200
heap:
  (depends on caller)

──→  type word:  dynamic concrete type
──→  data word:  payload

Step 2: `switch x := v.(type)` — bind `x` with concrete type per case
stack:
  discriminant reads `v`'s type word once  ◄── compare to `int`, `string`, ...
heap:
  same payload

──→  `case int:`    — `x` is `int`, stack slot width = int
──→  `case string:` — `x` is `string` (ptr+len)
──→  `default:`    — `x` has static type `interface{}` but holds same pair

Step 3: Method dispatch not involved — this is compile-time table + type equality
stack:
  jump to matching case body
heap:
  —

```
Aha moment: type switch is multi-way type assertion — each arm sees `x` as a concrete type, not as `any`.
```

> **In plain English:** It is a **sorting station**: each **bin** is a concrete type pattern.

---

## 5. Key Rules & Behaviors

### Interfaces are satisfied implicitly (no `implements`)

```go
type Reader interface {
	Read([]byte) (int, error)
}

type MyBuf struct{ /* ... */ }

func (m MyBuf) Read(b []byte) (int, error) { return 0, nil }

var _ Reader = MyBuf{} // compile-time assertion: MyBuf must satisfy Reader
```

MEMORY TRACE:

Step 1: Compile-time only — `var _ Reader = MyBuf{}`
stack:
  (package init / unused var — compiler proves assignment legal)
heap:
  —

──→  compiler: `MyBuf` method set includes `Read([]byte)(int,error)`  ◄── satisfies `Reader`

Step 2: If you later pass `MyBuf` where `Reader` is expected (runtime pattern)
stack:
  caller passes iface `Reader` @ 0x7ffcc220
heap:
  `MyBuf` value @ 0xc000016140

──→  type word:  itab for `(MyBuf, Reader)`
──→  data word:  ◄── points at buf state

```
Aha moment: `_` assignment is a proof obligation at compile time; runtime iface layout is the same as any other interface pair.
```

> **In plain English:** **Behavior is the passport.** Names are not.

### An interface value is nil ONLY when both type and value are nil

```go
var e error
// e is nil: no dynamic type, no dynamic value
```

MEMORY TRACE:

Step 1: `var e error` — zero value of interface type
stack:
  `e` @ 0x7ffcc240   ◄── `error` is an iface (two words)
heap:
  —

──→  type word:  nil  ◄── no dynamic type
──→  data word:  nil  ◄── no dynamic value

Step 2: `e == nil` is true — both halves unset
stack:
  comparison sees (nil, nil)
heap:
  —

```
Aha moment: nil interface means BOTH fields nil — this is the only case `e == nil` for an interface variable.
```

> **In plain English:** **Totally empty box:** no sticker, no gadget.

### A nil concrete value inside an interface is NOT a nil interface (THE trap)

```go
type T struct{}
func (t *T) Error() string { return "t" }

var p *T = nil
var e error = p

println(e == nil) // false
```

MEMORY TRACE:

Step 1: `var p *T = nil`
stack:
  `p` @ 0x7ffcc260
heap:
  —

──→  `p` holds 0x0

Step 2: `var e error = p` — pack into `error` iface
stack:
  `e` @ 0x7ffcc270
heap:
  —

──→  type word:  *T + `error` itab  ◄── dynamic type PRESENT
──→  data word:  0x0  ◄── nil pointer payload

Step 3: `e == nil` is false — interface value is non-nil
stack:
  runtime compares iface to typed nil: type word ≠ nil
heap:
  —

```
Aha moment: typed-nil trap — type set, value nil — the interface is "labeled empty box," not "no box."
```

> **In plain English:** You still have a **sticker** that says **`*T`**. That is enough to make the **interface value** non-nil **even if the pointer is nil**.

### Type assertion panics if wrong type (use comma-ok pattern)

```go
var v any = "hi"
// n := v.(int) // panic

x, ok := v.(int)
// ok == false, x == zero value of int
```

MEMORY TRACE:

Step 1: `var v any = "hi"` — dynamic type is `string`
stack:
  `v` @ 0x7ffcc280
heap:
  bytes @ 0xc000016180

──→  type word:  `string`
──→  data word:  string header

Step 2: `n := v.(int)` would panic — dynamic type ≠ `int`
stack:
  panic unwinds before `n` assigned
heap:
  —

──→  single-result form: mismatch ──→ `panic: interface conversion`

Step 3: `x, ok := v.(int)` — safe path
stack:
  `x` @ 0x7ffcc290  ◄── zero `int`
  `ok` @ 0x7ffcc298  ◄── `false`
heap:
  —

```
Aha moment: comma-ok form never panics; it is the same type-word check without throwing.
```

> **In plain English:** **One-return assertion is a bet.** **Two-return assertion is a safe check.**

### Pointer receiver methods don't count for value's method set

```go
type I interface{ M() }

type T struct{}

func (t *T) M() {}

var i I = T{} // compile error: T lacks M in value method set
```

MEMORY TRACE:

Step 1: Method set for value `T` (no `M` on `T`)
stack:
  (compile-time symbol tables)
heap:
  —

──→  `T` method set:  ∅  (only `*T` has `M`)

Step 2: `var i I = T{}` — compiler must build iface from `T`
stack:
  (rejected — no `M` with value receiver)
heap:
  —

──→  cannot form itab: `T` does not implement `I`

Step 3: Contrast `var i I = new(T)` or `&T{}` (hypothetical OK)
stack:
  `i` would hold `*T` + pointer
heap:
  `T` @ 0xc0000161c0

──→  type word:  *T
──→  data word:  pointer to `T`  ◄── dispatch uses `(*T).M`

```
Aha moment: method dispatch uses the dynamic type's method table — value vs pointer receiver changes which type can sit in the iface.
```

> **In plain English:** **The receiver is part of the method identity.** A value **does not** automatically gain **pointer-only** methods.

### Keep interfaces small (1–3 methods)

```go
type Reader interface {
	Read([]byte) (int, error)
}
```

MEMORY TRACE:

Step 1: `io.Reader` — iface with single `Read` method slot
stack:
  (interface descriptor at compile time)
heap:
  —

──→  itab layout:  one function pointer slot for `Read`  ◄── minimal surface

Step 2: Concrete type `MyBuf` assigned to `Reader`
stack:
  `r` Reader @ 0x7ffcc2a0
heap:
  `MyBuf` @ 0xc000016200

──→  type word:  `(MyBuf, io.Reader)` itab
──→  data word:  ◄── `MyBuf` pointer or value

Step 3: Call `r.Read(b)` — dispatch through itab
stack:
  `b` slice header @ 0x7ffcc2b0
heap:
  backing array @ 0xc000016220

──→  indirect call: itab.Read → `MyBuf.Read`  ◄── dynamic dispatch

```
Aha moment: one method in the iface means one slot in the itab — tiny interface, huge fan-in of implementers.
```

> **In plain English:** **Small sockets** mean **many devices** can fit. **Giant sockets** mean **almost nobody** matches.

---

## 6. Code Examples (Show, Don't Tell)

### Defining and satisfying an interface

```go
type Speaker interface{ Speak() string }

type Cat struct{ name string }

func (c Cat) Speak() string { return "meow, " + c.name }

func Announce(s Speaker) { println(s.Speak()) } // Cat is fine: it has Speak() string
```

MEMORY TRACE:

Step 1: `Cat` value receiver `Speak` — satisfies `Speaker`
stack:
  (compile-time method set check)
heap:
  —

──→  `Cat` method set includes `Speak() string`

Step 2: Caller passes `Cat{name:"Felix"}` into `Announce` (pattern same as `Dog`)
stack:
  `s` Speaker @ 0x7ffcc300
heap:
  Cat @ 0xc000016280

──→  type word:  itab for `(Cat, Speaker)`
──→  data word:  ◄── points at Cat (value or ptr per ABI)

Step 3: `s.Speak()` — dispatch to `Cat.Speak`
stack:
  return `"meow, " + name` via value receiver
heap:
  same Cat

```
Aha moment: same iface `Speaker`; dynamic type is now `Cat`, not `Dog` — the itab is keyed by concrete type.
```

### The `error` interface in practice

```go
type ValidationError struct{ Field string }

func (e ValidationError) Error() string { return "invalid field: " + e.Field }

func validate(field string) error {
	if field == "" {
		return ValidationError{Field: "name"}
	}
	return nil
}
```

MEMORY TRACE:

Step 1: `return ValidationError{Field: "name"}` — concrete value becomes `error`
stack:
  `validate` return slot `error` @ 0x7ffcc320
heap:
  ValidationError @ 0xc0000162a0   ◄── `Field: "name"`

──→  type word:  itab for `(ValidationError, error)`
──→  data word:  ◄── points at struct value (`ValidationError` uses value receiver `Error`)

Step 2: `return nil` on success path — nil interface
stack:
  return slot cleared to (nil, nil)
heap:
  —

──→  type word:  nil
──→  data word:  nil

Step 3: Caller `err := validate("")` — holds non-nil iface with dynamic type `ValidationError`
stack:
  caller `err` @ 0x7ffcc340
heap:
  same ValidationError @ 0xc0000162a0

```
Aha moment: same function return type `error`; success vs failure differs only by whether both iface words are nil.
```

### The nil interface trap (step-through)

```go
package main

type MyError struct{ msg string }

func (e *MyError) Error() string { return e.msg }

func maybeErr(fail bool) error {
	var p *MyError = nil
	if fail {
		p = &MyError{msg: "oops"}
	}
	return p // interface value is (*MyError, nil) when fail==false
}

func main() {
	err := maybeErr(false)
	println(err == nil) // false
}
```

MEMORY TRACE:

Step 1: `maybeErr(false)` — `p` stays typed nil
stack:
  `maybeErr` frame: `p` @ 0x7ffcc360  ◄── `*MyError` = nil
heap:
  —

──→  `p` stores 0x0

Step 2: `return p` — compiler wraps in `error` iface (exit path)
stack:
  result `error` @ 0x7ffcc380
heap:
  —

──→  type word:  *MyError / error itab  ◄── non-nil
──→  data word:  0x0  ◄── nil *MyError

Step 3: `main`: `err := maybeErr(false)` then `err == nil`
stack:
  `err` @ 0x7ffcc3a0  ◄── copy of iface from return
heap:
  —

──→  comparison: type word ≠ nil  ◄── **`false`**

```
Aha moment: returning a bare `*MyError` variable that is nil still installs the *MyError descriptor — callers must get `(nil,nil)` via `return nil` on success.
```

**Fix:** return **`nil` in the success path** instead of returning a **typed nil pointer** through `error`:

```go
func maybeErrFixed(fail bool) error {
	if fail {
		return &MyError{msg: "oops"}
	}
	return nil // untyped nil interface: err == nil is true
}
```

MEMORY TRACE:

Step 1: Success path `return nil` — untyped nil becomes nil `error`
stack:
  `maybeErrFixed` return slot @ 0x7ffcc3c0
heap:
  —

──→  type word:  nil
──→  data word:  nil

Step 2: Caller `err := maybeErrFixed(false)`
stack:
  `err` @ 0x7ffcc3e0  ◄── (nil, nil)
heap:
  —

──→  `err == nil`  ◄── **`true`**

Step 3: Failure path still returns `&MyError{...}` — non-nil iface
stack:
  return slot holds (*MyError, ptr to struct)
heap:
  MyError @ 0xc0000162c0

```
Aha moment: `nil` in a return typed as `error` is the true empty interface — no dynamic type is installed.
```

### Type assertion with comma-ok

```go
var v any = 7
if n, ok := v.(int); ok {
	println("twice:", n*2)
}
```

MEMORY TRACE:

Step 1: `var v any = 7` — `eface` with dynamic `int`
stack:
  `v` @ 0x7ffcc400
heap:
  —

──→  type word:  `int`
──→  data word:  `7`

Step 2: `n, ok := v.(int)` — type word matches
stack:
  `n` @ 0x7ffcc410  ◄── `7`
  `ok` @ 0x7ffcc418  ◄── `true`
heap:
  —

──→  extract concrete `int` into `n`

Step 3: Branch runs — `n*2` uses unboxed int
stack:
  temporary `14` for `println`
heap:
  —

```
Aha moment: comma-ok assertion is a cheap type-word compare plus a copy of the data word when shapes match.
```

### Type switch

```go
import "fmt"

func Format(v any) string {
	switch t := v.(type) {
	case int:
		return fmt.Sprintf("int:%d", t)
	case string:
		return fmt.Sprintf("str:%s", t)
	default:
		return fmt.Sprintf("other:%T", t)
	}
}
```

MEMORY TRACE:

Step 1: `Format(v)` — `v` is `any`
stack:
  `v` @ 0x7ffcc420
heap:
  (caller-dependent)

──→  type word / data word of argument

Step 2: `switch t := v.(type)` — each case binds `t` with concrete static type
stack:
  `case int:`    — `t` is `int` @ 0x7ffcc430
  `case string:` — `t` is `string` (wider slot)
heap:
  payload for string case @ 0xc0000162e0

──→  compare dynamic type to case types top-to-bottom

Step 3: `default` — `t` is still `interface{}` / `any` with same pair
stack:
  `%T` formatting reads type from type word
heap:
  —

```
Aha moment: type switch is the safe multi-way form of assertion — one dynamic lookup, many arms.
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

What does this print?

```go
package main

import "fmt"

type I interface{ M() }

type T struct{}

func (t *T) M() {}

func main() {
	var pt *T = nil
	var i I = pt
	fmt.Println(i == nil)
}
```

MEMORY TRACE:

Step 1: `var pt *T = nil`
stack:
  `pt` @ 0x7ffcc440
heap:
  —

──→  `pt` = 0x0

Step 2: `var i I = pt` — iface gets dynamic type `*T`
stack:
  `i` @ 0x7ffcc450
heap:
  —

──→  type word:  *T / itab for `I`  ◄── set
──→  data word:  0x0  ◄── nil pointer

Step 3: `i == nil` — must be nil iface (both words nil)
stack:
  comparison fails: type word non-nil
heap:
  —

```
Aha moment: `pt` and `i` "look" nil at the pointer level, but `i` carries type metadata — prints `false`.
```

> [!success]- Answer
> It prints **`false`**.
>
> `i` holds dynamic type **`*T`** and dynamic value **a nil pointer**. The type half is present, so **`i` is not a nil interface value**, even though **`pt` is nil**.

### Tier 2: Fix the Bug (5 min)

This function should return "no error" when `enabled` is false, but callers see a non-nil `error`. Fix it.

```go
type AppError struct{ Code int }

func (e *AppError) Error() string { return fmt.Sprintf("code=%d", e.Code) }

func Do(enabled bool) error {
	var err *AppError
	if enabled {
		err = &AppError{Code: 1}
	}
	return err
}
```

MEMORY TRACE:

Step 1: `Do(false)` — `err` stays nil `*AppError`
stack:
  `Do` frame: `err` @ 0x7ffcc460  ◄── typed nil pointer
heap:
  —

──→  `err` = (*AppError)(nil)

Step 2: `return err` — wrap in `error` iface
stack:
  return slot `error` @ 0x7ffcc470
heap:
  —

──→  type word:  *AppError / error itab  ◄── non-nil
──→  data word:  0x0

Step 3: Caller sees non-nil `error` even though "no failure"
stack:
  caller's `err` compares `!= nil`  ◄── **bug**
heap:
  —

```
Aha moment: same typed-nil-through-`error` pattern — the fix is `return nil` when there is no real `*AppError` to return.
```

> [!success]- Answer
> **Problem:** When `enabled` is false, `err` is a nil `*AppError`, but returning it wraps **`*AppError` with a nil pointer** in the `error` interface. The interface value is **non-nil**.
>
> **Fix:** Return an **untyped nil `error`** in the success path:
>
> ```go
> func Do(enabled bool) error {
> 	if enabled {
> 		return &AppError{Code: 1}
> 	}
> 	return nil
> }
> ```
>
> Alternative pattern if you need a temporary `*AppError` variable: **before `return err`, check** `if err == nil { return nil }` so you do not return a typed nil through the `error` interface unintentionally.

---

## 7. Gotchas & Interview Traps

**Nil interface versus typed nil inside interface.** This is the **number one** debugging surprise in real services. Tests that do `if err != nil` **after** a helper returned a bare `*MyError` variable frequently get it wrong.

**Type assertion panic.** In hot paths and JSON decoding, wrong assumptions about `any` lead to **panic**. Prefer **`v.(T), ok`** or **type switches**.

**Pointer versus value method sets.** A value `T` does not pick up `*T` methods for interface satisfaction. Generics did not erase this rule.

**Over-wide interfaces.** An interface with **ten methods** forces **every mock** in tests to implement **ten methods**. **Shrink the surface**.

---

## 8. Interview Gold Questions (Top 3)

1. **Why does a nil pointer of concrete type `*T` become a non-nil `error` when returned as `error`?**  
   Walk through **dynamic type** and **dynamic value**. Contrast with **`return nil`**.

2. **What is the difference between `v.(Concrete)` and type switching on `v.(type)`?**  
   One **targets a single type** and can **panic**; the other **dispatches** across **many cases** safely.

3. **Why does Go use implicit interface satisfaction?**  
   Discuss **decoupling**, **package dependencies**, **testing with fakes**, and **post-hoc abstraction** without editing the concrete type's source.

---

## 9. 30-Second Verbal Answer

An interface is a **method contract**. Types satisfy it **implicitly** by having the right methods. An interface value is a **pair**: **what concrete type** and **what value**. It is **nil only if both are unset**. Putting a **nil pointer** into an interface still sets the **type half**, so **`== nil` fails**. Extract concrete types with **type assertions** or **type switches**, always using the **comma-ok** form when unsure. **`error`** and **`any`** are the two interfaces you will touch **daily**: **`error`** for failures, **`any`** for generic containers before you constrain types.

---

> See [[Glossary]] for term definitions.
