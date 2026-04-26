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

```
Interface value (conceptual)
+------------------+------------------+
| dynamic type     | dynamic value    |
| (type metadata)  | (pointer/data)   |
+------------------+------------------+
        |                    |
        v                    v
   "what plug shape?"   "the actual gadget"
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

```
You put a nil POINTER of concrete type *T into interface I.
The interface's TYPE half says "*T".
The interface's VALUE half is nil — but the INTERFACE VALUE ITSELF is non-nil.
So `i == nil` is false.
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

```
Compiler checklist (simplified)
-----------------------------
Dog has method: Speak() string  ---> matches Speaker.Speak
=> Dog satisfies Speaker
=> Announce(Dog{...}) is allowed
```

> **In plain English:** The compiler is a **bouncer checking dance moves**, not **checking your ID card against a list of approved names**.

### 4.2 The `error` interface

The standard library defines:

```go
type error interface {
	Error() string
}
```

Anything with `Error() string` is an `error`. That is why you can `return fmt.Errorf(...)`, custom structs, or `errors.New("msg")` through the same return paths.

```go
type MyErr struct{ msg string }

func (e MyErr) Error() string { return e.msg }

func f() error {
	return MyErr{msg: "boom"}
}
```

```
error interface
+-------------+
| Error()     |
+-------------+
        ^
        |
   MyErr has Error() string  =>  MyErr values satisfy error
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

```
any / interface{}
+------------------+
| (no methods      |
|  required)       |
+------------------+
        ^
        |
  all types satisfy this (including structs, ints, pointers...)
```

> **In plain English:** **`any` is a generic shipping crate**. You can ship **anything**, but you **lose specific tools** until you **open the crate** with assertions or reflection.

### 4.4 Interface values as `(type, value)` pairs

An interface value is **not** "just a pointer." Conceptually it stores **type information** plus **the data** or **nil data** for that type.

```
Conceptual layout after assignment:
+------------------+---------------------------+
| dynamic type     | dynamic value             |
| concrete T or *T | data or pointer bits      |
+------------------+---------------------------+
```

Assigning a **pointer** sets dynamic type to **`*T`**. The dynamic value is the **pointer itself**, which may be **`nil`**.

### 4.5 Type assertions

A **type assertion** extracts the concrete side **you believe** is there.

```go
var v any = 42

n := v.(int)       // panics if wrong
x, ok := v.(int)   // ok is false if wrong; no panic
```

```
v.(T)

  v holds (dynamic_type, dynamic_value)
           |
           +--> assertion succeeds if dynamic_type is T (exact rules below)
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

```
switch v.(type)
       |
       +--> compare dynamic type against each case
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

```
No Java-style:
  class MyBuf implements Reader { ... }

Go-style:
  type has methods -> automatically usable as Reader
```

> **In plain English:** **Behavior is the passport.** Names are not.

### An interface value is nil ONLY when both type and value are nil

```go
var e error
// e is nil: no dynamic type, no dynamic value
```

```
nil interface value
+------------------+------------------+
| nil type         | nil value        |
+------------------+------------------+
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

```
e after assignment
+------------------+------------------+
| dynamic type *T  | dynamic value    |
|                  | nil *T pointer   |
+------------------+------------------+
        |
        +--> interface value is NON-nil
             because TYPE half is *T, not "absent"
```

> **In plain English:** You still have a **sticker** that says **`*T`**. That is enough to make the **interface value** non-nil **even if the pointer is nil**.

### Type assertion panics if wrong type (use comma-ok pattern)

```go
var v any = "hi"
// n := v.(int) // panic

x, ok := v.(int)
// ok == false, x == zero value of int
```

```
v.(T)            ---> panic on mismatch
v.(T), ok        ---> ok false on mismatch
```

> **In plain English:** **One-return assertion is a bet.** **Two-return assertion is a safe check.**

### Pointer receiver methods don't count for value's method set

```go
type I interface{ M() }

type T struct{}

func (t *T) M() {}

var i I = T{} // compile error: T lacks M in value method set
```

```
Value T method set:     (empty here)
Pointer *T method set: { M }

Interface needs M on the value you assign:
  T value  -> needs M on T   -> missing
  &T value -> needs M on *T  -> ok
```

> **In plain English:** **The receiver is part of the method identity.** A value **does not** automatically gain **pointer-only** methods.

### Keep interfaces small (1–3 methods)

```go
type Reader interface {
	Read([]byte) (int, error)
}
```

```
io.Reader
+--------+
| Read   |  <-- one method, enormous ecosystem
+--------+
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

```
Speaker
+--------+
| Speak  |
+--------+
    ^
    |
 Cat implements Speak on value receiver
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

```
ValidationError.Error() string  =>  value satisfies error  =>  can return as error
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

```
When fail == false:

p is a nil *MyError

return p  wraps p in error interface:

+------------------+------------------+
| dynamic type *MyError | nil *MyError |
+------------------+------------------+

err == nil checks the whole interface value:
  type half is non-nil (*MyError metadata exists)
  => err is NOT a nil interface
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

```
return nil  =>  (nil type, nil value)  =>  err == nil is true
```

### Type assertion with comma-ok

```go
var v any = 7
if n, ok := v.(int); ok {
	println("twice:", n*2)
}
```

```
v.(int), ok  ->  dynamic int  ->  ok true, n == 7
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

```
v.(type)  ->  dispatch by dynamic type: int / string / default
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
