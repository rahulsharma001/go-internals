# P02 Methods & Receivers

> **Prerequisite note** — complete this before starting [[T07 Pointers & Pointer Semantics]] or [[T11 Interface Internals (iface & eface)]].
> Estimated time: ~25 min

---

## 1. Concept

A **method** in Go is a function with a special first parameter called a **receiver**. The receiver binds the function to a type so you can call it with dot syntax, as if the value "has" that behavior.

> **In plain English:** A method is like a label on a toolbox drawer. The drawer is your value or pointer. The label says what operation you can perform on what is inside. The operation is still just a function, but the syntax makes it read like "ask this thing to do something."

---

## 2. Core Insight (TL;DR)

**The receiver decides whether you work on a copy or on the original.** A **value receiver** copies the whole value for the call. A **pointer receiver** passes an address so the method can change fields that live in the caller's variable.

**Method sets are asymmetric.** The set of methods available on `T` is not the same as on `*T`. That asymmetry is exactly what breaks or fixes **interface satisfaction** when you mix value and pointer receivers.

---

## 3. Mental Model (Lock this in)

Picture a paper form and a photocopy. A value receiver is the clerk who fills out a photocopy and hands it back. Your original form on the desk never changes. A pointer receiver is the clerk who walks to your desk and writes directly on your original form.

```go
type Counter int

func (c Counter) BumpValue() { c++ }       // edits the photocopy
func (c *Counter) BumpPointer() { *c++ }   // edits the original
```

```
VALUE RECEIVER (copy)

  caller's c:  [ 5 ]
                    |
                    | copy made for method
                    v
  inside method: [ 6 ]   <-- only this copy changes
  caller still sees 5


POINTER RECEIVER (shared location)

  caller's c points to --> [ 5 ]
                              ^
                              |
                    method edits this box
                              |
                              v
                           now [ 6 ]
```

Here is the classic silent failure: you "bump" with a value receiver and nothing happens.

```go
var x Counter = 5
x.BumpValue()
fmt.Println(x) // still 5
```

> **In plain English:** You shouted at a photograph of your bank balance, not at the bank. The real account never heard you.

---

## 4. How It Works

### Defining methods

Any named type defined in your package can have methods, not only structs. The receiver appears in parentheses before the method name.

```go
type ID string

func (id ID) IsEmpty() bool {
	return id == ""
}
```

```
syntax pattern

  func (receiver Type) MethodName(args...) (results...) { ... }
        ^^^^^^^^
        binds name + type
```

> **In plain English:** You are teaching Go a new verb that only applies to values of this type, the same way you might add a custom button only on one kind of remote control.

### Value receiver versus pointer receiver

A value receiver gets a copy of `T`. A pointer receiver gets `*T` and can mutate fields reachable through that pointer.

```go
type User struct {
	Name string
}

func (u User) SetNameWrong(s string) {
	u.Name = s // mutates copy only
}

func (u *User) SetNameRight(s string) {
	u.Name = s // mutates caller's User
}
```

```
SetNameWrong(u User)

  caller: User{"alice"}
              |
              +--copy--> User{...}  Name field changed here only
              |
  caller still "alice"


SetNameRight(u *User)

  caller: *User --> User{"alice"}
                      |
                      method writes here
                      |
                      v
                   User{"bob"}
```

> **In plain English:** Value receiver is a stunt double. Pointer receiver is the actor on set.

### Method sets

For type `T`:

- The method set of `T` contains all methods declared with receiver `T`.
- The method set of `*T` contains methods with receiver `T` **and** methods with receiver `*T`.

The method set of `T` does **not** include methods whose receiver is `*T` only.

```
type T struct{}

func (T)  A() {}
func (*T) B() {}

method set of T:   { A }
method set of *T:  { A, B }
```

> **In plain English:** A plain value is a locked-down employee badge that only opens doors listed for "value badge." A pointer badge inherits every door the value badge opens, plus extra doors only pointer people may use.

### Interface satisfaction

A type satisfies an interface if the type's method set contains every method in the interface, with matching signatures.

If the interface needs a method that only exists on `*T` with a pointer receiver, a bare value `T` cannot satisfy it. A pointer `*T` can.

```go
type Stringer interface {
	String() string
}

type Point struct{ X, Y int }

func (p *Point) String() string {
	return fmt.Sprintf("(%d,%d)", p.X, p.Y)
}

var _ Stringer = (*Point)(nil) // ok: *Point has String
// var _ Stringer = Point{}    // compile error: Point lacks *Point methods
```

```
Interface needs:  String() string

Point value:   method set has no String (only *Point does)
*Point value:  method set has String

So only *Point implements Stringer here.
```

> **In plain English:** The interface is a job description. Your value type might be under-qualified if all the real work was attached to the pointer job title instead.

### Go helps you call pointer methods on addressable values

If you have an addressable `T` and the method is on `*T`, Go takes the address for you.

```go
p := Point{X: 1, Y: 2}
s := p.String() // same as (&p).String()
```

This is **syntactic sugar**. It does not change method sets. It only affects **call** sites.

```
p.String()

compiler rewrites to (&p).String() when method is on *Point and p is addressable
```

> **In plain English:** The language hands you a pointer behind the counter so you do not have to say "address of" out loud every time, but the job opening still said "pointer skills required."

---

## 5. Key Rules & Behaviors

### Value receiver gets a copy

```go
type Box struct{ n int }
func (b Box) Add(x int) { b.n += x }

func main() {
	b := Box{n: 1}
	b.Add(10)
	fmt.Println(b.n) // 1
}
```

```
b before: Box{n:1}
          |
Add copies --> Box{n:1} --+10--> Box{n:11}  (discarded)
          |
b after:  Box{n:1}
```

> **In plain English:** You inflated a balloon that was not tied to your wrist. It floated away.

### Pointer receiver can modify the original

```go
func (b *Box) Add(x int) { b.n += x }

func main() {
	b := Box{n: 1}
	b.Add(10)
	fmt.Println(b.n) // 11
}
```

```
b.n starts at 1
*b points at that field
method does b.n += 10 on the live struct
```

> **In plain English:** You edited the document saved on the shared drive. Everyone sees the update.

### Method set of `*T` includes `T` methods; method set of `T` does not include `*T`-only methods

```go
type N int
func (N) A() {}
func (*N) B() {}

// N  has {A}
// *N has {A,B}
```

```
   T ----A---->
  / \
 *T --A--+
        \--B-->
```

> **In plain English:** Promotion goes up, not sideways. The pointer world is a superset for methods, not the other way around.

### Go auto-dereferences: you can call pointer receiver methods on a value if addressable

```go
type V int
func (v *V) Double() { *v *= 2 }

func main() {
	var x V = 3
	x.Double()   // ok: &x.Double()
	fmt.Println(x)
}
```

```
x lives in a variable (addressable)
x.Double() --> (&x).Double()
```

> **In plain English:** The compiler quietly passes your home address when the method needs to ring your doorbell.

### Nil pointer receiver is valid (no panic unless you dereference a field)

```go
type Node struct{ value int; next *Node }

type List struct{ head *Node }

func (l *List) Len() int {
	if l == nil {
		return 0
	}
	// walk l.head ...
	return 0
}

func main() {
	var l *List
	fmt.Println(l.Len()) // prints 0, no panic
}
```

```
l is nil --+
           |
 l.Len() --+--> receiver is nil *List
           |
           +--> method body may still run
```

> **In plain English:** A nil pointer is an empty folder. You can still ask "how many papers?" and get zero, as long as you do not blindly open a drawer inside that folder.

### Consistency rule: if one method needs pointer receiver, use pointer receiver for all

Mixed styles on the same type confuse readers and break expectations about mutability.

```go
// Prefer this style when any method mutates:
type Wallet struct{ cents int }

func (w *Wallet) Deposit(c int) { w.cents += c }
func (w *Wallet) Balance() int { return w.cents }
```

```
all methods on *Wallet

readers assume: shared mutable state behind the pointer
```

> **In plain English:** If one door in the house needs a key, give every roommate the same keychain. Mixed locks invite accidents.

### The Decision Checklist

Use a **pointer receiver** when:

1. The method must mutate the receiver's fields.
2. The struct is large and copying it on every call is wasteful.
3. You want one consistent story for the type, especially if any method mutates.

Use a **value receiver** when:

1. The type is small and acts like an immutable value, such as a simple coordinate or identifier object.
2. You want each call to work on an isolated copy for safety, including easier reasoning in concurrent code when combined with immutable data.

If you are unsure and the type holds mutable fields, default to **pointer receiver** and keep the set consistent.

---

## 6. Code Examples (Show, Don't Tell)

### Value receiver method — modification is lost

```go
type Bank struct{ balance int }

func (b Bank) DepositWrong(amount int) { b.balance += amount }

func main() {
	b := Bank{balance: 100}
	b.DepositWrong(50)
	fmt.Println(b.balance) // still 100
}
```

```
b --> Bank{100}     DepositWrong copies --> Bank{150} discarded
b --> Bank{100}     caller unchanged
```

### Pointer receiver method — modification sticks

```go
func (b *Bank) DepositRight(amount int) { b.balance += amount }

func main() {
	b := Bank{balance: 100}
	b.DepositRight(50)
	fmt.Println(b.balance) // 150
}
```

```
b --> Bank{100} == *b edited in place --> Bank{150}
```

### Interface satisfaction: value versus pointer

```go
type Formatter interface {
	Format() string
}

type Tag string

func (t *Tag) Format() string {
	if t == nil {
		return "<nil tag>"
	}
	return string(*t)
}

func demo() {
	var f Formatter = (*Tag)(nil) // interface value non-nil, data nil
	fmt.Println(f.Format())       // "<nil tag>"
}
```

```
*Tag has Format; Tag does not. Interface holds *Tag with nil pointer; method handles nil.
```

### Nil receiver behavior

```go
type Tree struct {
	v    int
	left *Tree
	right *Tree
}

func (t *Tree) Sum() int {
	if t == nil {
		return 0
	}
	return t.v + t.left.Sum() + t.right.Sum()
}
```

If you forget the nil check and do `t.v` first, you panic. The nil receiver is allowed; **field access on nil** is not.

```
t == nil --> early return 0   (safe)

t == nil --> read t.v        (panic)
```

### Methods on non-struct types

```go
type Celsius float64

func (c Celsius) String() string {
	return fmt.Sprintf("%.1f C", c)
}
```

The defined type `Celsius` is not a struct, but methods attach to the named type the same way.

### Method expressions versus method values

```go
type Counter int

func (c *Counter) Inc() { *c++ }

func main() {
	var c Counter

	f := (*Counter).Inc // method expression: func(*Counter), pass receiver each call
	f(&c)

	g := c.Inc // method value: bound to &c, call with g()
	g()
}
```

```
method expression

  (*Counter).Inc  --> func(*Counter)

  call: f(&c)


method value

  c.Inc --> func() bound to receiver already (closure-like)
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

```go
package main

import "fmt"

type S struct{ x int }

func (s S) A() { s.x++ }
func (s *S) B() { s.x++ }

func main() {
	v := S{x: 1}
	p := &S{x: 1}

	v.A()
	v.B()
	p.A()
	p.B()

	fmt.Println(v.x, p.x)
}
```

> [!success]- Answer
> `2 2`
>
> `v.A` copies `v`, so `v.x` stays 1. `v.B` promotes to `(&v).B`, so `v.x` becomes 2. `p.A` copies the struct pointed to by `p` and increments only that copy, so `p.x` stays 1. `p.B` increments through the pointer, so `p.x` becomes 2. Final line prints `v.x` then `p.x`: 2 and 2.

### Tier 2: Fix the Bug (5 min)

```go
package main

import "fmt"

type Buffer struct{ data []byte }

func (b Buffer) Write(p []byte) {
	b.data = append(b.data, p...)
}

func main() {
	var buf Buffer
	buf.Write([]byte("hello"))
	fmt.Println(len(buf.data))
}
```

> [!success]- Answer
> Change the receiver to a pointer:
>
> ```go
> func (b *Buffer) Write(p []byte) {
> 	b.data = append(b.data, p...)
> }
> ```
>
> With a value receiver, `append` may write to a new backing array stored only in the copy's `data` field. The caller's slice header never updates, so the length stays 0.

---

## 7. Gotchas & Interview Traps

| Trap | Why it bites | Fast fix |
|------|--------------|----------|
| Value receiver "mutation" | Only the copy changes | Use pointer receiver when mutating fields |
| Interface not implemented by value | Method set on `T` missing `*T` methods | Pass `*T` or change receiver to value for tiny types |
| Assuming `p.M()` always copies | Compiler may pass `&p` for pointer methods | Learn method sets, not just call syntax |
| Nil receiver safe everywhere | Field access on nil pointer panics | Guard with `if v == nil` before touching fields |
| Mixed receiver styles | Mental overhead, surprises | Pick pointer receivers for mutable types, stay consistent |
| Method value captures state | Easy to misunderstand what is fixed | Picture a closure bound to a specific receiver value |

---

## 8. Interview Gold Questions (Top 3)

**1. What is the difference between a value receiver and a pointer receiver?**

Value receiver copies the receiver; field writes do not escape. Pointer receiver shares the live value; writes persist. Prefer pointers for mutating or large types; small immutable values may stay as values.

**2. Explain method sets and why `T` and `*T` differ.**

Method set is what a value of that type can dispatch. `T` gets only value-receiver methods. `*T` gets value-receiver and pointer-receiver methods. Pointer-only methods therefore require `*T` for interface implementation.

**3. When is a nil receiver allowed, and when does it panic?**

Calling `(*T).M` with a nil `*T` is legal if `M` checks `nil` before touching fields. Reading `t.field` when `t` is nil panics. Common in recursive structures where nil means empty.

---

## 9. 30-Second Verbal Answer

Methods are functions with receivers. Value receivers copy; pointer receivers alias the real data and can mutate. `*T`'s method set includes pointer-receiver methods that `T` lacks, so interface satisfaction differs for values versus pointers. Default to pointer receivers when anything mutates, and keep the style consistent on a type.

---

> See [[Glossary]] for term definitions.
