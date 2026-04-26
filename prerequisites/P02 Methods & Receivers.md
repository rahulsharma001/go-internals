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
MEMORY TRACE:

Scenario A — value receiver: caller holds Counter(5), calls BumpValue()

Step 1: c := Counter(5)  (conceptually; Counter is int underneath)
  stack:
    c ──→ [ 5 ]  at addr 0xC000

Step 2: c.BumpValue() — full copy of c into the value receiver parameter; c++ runs on the copy only  ◄── aha: caller’s slot is never written
  stack:
    c ──→ [ 5 ]  at addr 0xC000   ◄── unchanged
    receiver in BumpValue ──→ [ 6 ]  at addr 0xC010   ◄── only this temporary copy increments

Step 3: BumpValue returns; receiver copy discarded
  stack:
    c ──→ [ 5 ]  at addr 0xC000


Scenario B — pointer receiver: cp := &c, then BumpPointer()

Step 1: c holds 5; cp holds c’s address
  stack:
    c  ──→ [ 5 ]  at addr 0xC000
    cp ──→ 0xC000   ◄── pointer value (8 bytes) names the same underlying int as c

Step 2: cp.BumpPointer() — receiver is a copy of the pointer bits, still pointing at 0xC000; *c++ mutates that int
  stack:
    c  ──→ [ 6 ]  at addr 0xC000   ◄── original storage updated
    cp ──→ 0xC000
    receiver *Counter in BumpPointer ──→ 0xC000   ◄── same address as cp; aliases caller’s value
```

Here is the classic silent failure: you "bump" with a value receiver and nothing happens.

```go
var x Counter = 5
x.BumpValue()
fmt.Println(x) // still 5
```

```
MEMORY TRACE:

Step 1: var x Counter = 5
  stack:
    x ──→ [ 5 ]  at addr 0xC000

Step 2: x.BumpValue() — entire Counter value copied into value receiver; only the copy is incremented  ◄── aha: silent no-op from caller’s perspective
  stack:
    x ──→ [ 5 ]  at addr 0xC000   ◄── never updated
    receiver copy ──→ [ 6 ]  at addr 0xC010   ◄── thrown away when the method returns

Step 3: fmt.Println(x) observes x ──→ [ 5 ]  at addr 0xC000
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
MEMORY TRACE:

Step 1: id := ID("")
  stack:
    id ──→ [ string header: ptr,len for empty string ]  at addr 0xC000

Step 2: id.IsEmpty() — value receiver copies the whole ID (the string header bytes) into the method’s `id` parameter
  stack:
    caller id ──→ …  at addr 0xC000
    receiver id in IsEmpty ──→ copy of same header  at addr 0xC010   ◄── separate stack slot; comparison does not mutate caller

Step 3: return id == ""  → true (reads only the receiver copy’s contents)

(The `func (id ID)` syntax binds that receiver name + type to every call site the compiler generates.)
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
MEMORY TRACE:

SetNameWrong — value receiver

Step 1: u := User{Name: "alice"} in caller
  stack:
    u ──→ [ Name: "alice" ]  at addr 0xC000

Step 2: SetNameWrong("bob") — entire User struct copied into value receiver; assignment writes Name on the copy only  ◄── aha: caller’s struct untouched
  stack:
    caller u ──→ [ Name: "alice" ]  at addr 0xC000
    receiver u ──→ [ Name: "bob" ]  at addr 0xC010

Step 3: after return, receiver discarded; caller u still "alice"


SetNameRight — pointer receiver

Step 1: u := User{Name: "alice"}
  stack:
    u ──→ [ Name: "alice" ]  at addr 0xC000

Step 2: SetNameRight("bob") — receiver parameter is a copy of &u (8-byte pointer), not a copy of the struct
  stack:
    u ──→ [ Name: "bob" ]  at addr 0xC000   ◄── same struct mutated in place
    receiver *User ──→ 0xC000   ◄── aliases caller’s User
```

> **In plain English:** Value receiver is a stunt double. Pointer receiver is the actor on set.

### Method sets

For type `T`:

- The method set of `T` contains all methods declared with receiver `T`.
- The method set of `*T` contains methods with receiver `T` **and** methods with receiver `*T`.

The method set of `T` does **not** include methods whose receiver is `*T` only.

```
MEMORY TRACE:

Step 1: type T struct{}; var v T
  stack:
    v ──→ [ empty struct ]  at addr 0xC000

Step 2: method set of T (what you may call on a value of type T)
  dispatch: { A } only   ◄── B was declared with receiver *T, so it is not in T’s method set

Step 3: var p *T = &v
  stack:
    v ──→ [ ]  at addr 0xC000
    p ──→ 0xC000

Step 4: method set of *T (superset)
  dispatch: { A, B }   ◄── aha: *T gets value-receiver methods plus pointer-receiver-only methods; the converse is false for plain T
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
MEMORY TRACE:

Step 1: String is declared only on *Point
  method set of Point:   no String
  method set of *Point:  includes String

Step 2: var _ Stringer = (*Point)(nil) — interface value’s dynamic type is *Point; data word can be nil
  iface (conceptual):
    type ──→ *Point
    data ──→ 0x0   ◄── nil *Point is still typed; method table has String

Step 3: var _ Stringer = Point{} would require Point.String in Point’s method set — it is not there  ◄── aha: value Point cannot satisfy Stringer when only *Point carries the method
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
MEMORY TRACE:

Step 1: p := Point{X: 1, Y: 2}
  stack:
    p ──→ [ X: 1 | Y: 2 ]  at addr 0xC000

Step 2: s := p.String() — String’s receiver type is *Point; p is addressable, so compiler rewrites to (&p).String()  ◄── aha: no full struct copy; only the address (8 bytes) is passed into the method
  stack:
    p ──→ [ X: 1 | Y: 2 ]  at addr 0xC000
    receiver *Point inside String ──→ 0xC000   ◄── copy of pointer &p, aliases original p

Step 3: String reads p.X, p.Y through that pointer
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
MEMORY TRACE:

Step 1: b := Box{n: 1}
  stack:
    b ──→ [ n: 1 ]  at addr 0xC000

Step 2: b.Add(10) — full copy of Box into value receiver; b.n += 10 runs on the copy only  ◄── aha: caller’s Box never sees the +10
  stack:
    b ──→ [ n: 1 ]  at addr 0xC000   ◄── unchanged
    receiver in Add ──→ [ n: 11 ]  at addr 0xC010   ◄── discarded when Add returns

Step 3: fmt.Println(b.n) reads b ──→ [ n: 1 ]  at addr 0xC000
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
MEMORY TRACE:

Step 1: b := Box{n: 1}
  stack:
    b ──→ [ n: 1 ]  at addr 0xC000

Step 2: b.Add(10) — compiler passes address &b; receiver *Box is a copy of that pointer (8 bytes)
  stack:
    b ──→ [ n: 11 ]  at addr 0xC000   ◄── += applied through *Box on the live struct
    receiver *Box in Add ──→ 0xC000   ◄── aliases caller’s b

Step 3: fmt.Println(b.n) reads [ n: 11 ]  at addr 0xC000
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
MEMORY TRACE:

Step 1: var n N = 7
  stack:
    n ──→ [ N underlying int: 7 ]  at addr 0xC000

Step 2: method set attached by compiler to type N vs *N
  callable on n (value N):   { A }
  callable on &n (type *N): { A, B }   ◄── aha: *N includes value-receiver A plus pointer-only B; N never gets B without taking address

Step 3: calling B requires *N — e.g. (&n).B(); plain n.B() is invalid
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
MEMORY TRACE:

Step 1: var x V = 3
  stack:
    x ──→ [ 3 ]  at addr 0xC000

Step 2: x.Double() — x is addressable; compiler rewrites to (&x).Double(); receiver *V is copy of pointer &x (8 bytes), not a copy of the int  ◄── aha: same pattern as struct pointer receivers
  stack:
    x ──→ [ 6 ]  at addr 0xC000   ◄── after *v *= 2
    receiver *V in Double ──→ 0xC000

Step 3: fmt.Println(x) observes updated x on the stack
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
MEMORY TRACE:

Step 1: var l *List — zero value
  stack:
    l ──→ nil (0x0)   ◄── no List struct allocated

Step 2: l.Len() — receiver parameter is a copy of l’s pointer bits (still nil)
  stack:
    caller l ──→ 0x0
    receiver *List in Len ──→ 0x0   ◄── nil receiver is legal; method runs

Step 3: if l == nil { return 0 } — compares pointer only; no field access on *List → no panic
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
MEMORY TRACE:

Step 1: w := &Wallet{cents: 100}
  heap:
    struct ──→ [ cents: 100 ]  at addr 0xH100
  stack:
    w ──→ 0xH100

Step 2: w.Deposit(50) — receiver *Wallet is copy of 0xH100; mutates same struct
  heap:
    struct ──→ [ cents: 150 ]  at addr 0xH100   ◄── one shared mutable backing store

Step 3: w.Balance() — again receiver ──→ 0xH100; read returns 150  ◄── consistent story: every method uses pointer receiver + same address
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
MEMORY TRACE:

Step 1: b := Bank{balance: 100}
  stack:
    b ──→ [ balance: 100 ]  at addr 0xC000

Step 2: b.DepositWrong(50) — full Bank struct copied into value receiver; += runs on copy only  ◄── aha: same failure mode as Box.Add with value receiver
  stack:
    b ──→ [ balance: 100 ]  at addr 0xC000
    receiver in DepositWrong ──→ [ balance: 150 ]  at addr 0xC010   ◄── discarded on return

Step 3: fmt.Println(b.balance) reads b ──→ [ balance: 100 ]  at addr 0xC000
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
MEMORY TRACE:

Step 1: b := Bank{balance: 100}
  stack:
    b ──→ [ balance: 100 ]  at addr 0xC000

Step 2: b.DepositRight(50) — receiver *Bank is copy of &b (8 bytes)
  stack:
    b ──→ [ balance: 150 ]  at addr 0xC000   ◄── mutation through pointer
    receiver *Bank ──→ 0xC000

Step 3: fmt.Println(b.balance) reads [ balance: 150 ]  at addr 0xC000
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
MEMORY TRACE:

Step 1: *Tag declares Format; Tag (value) has no Format in its method set
  *Tag satisfies Formatter; Tag does not

Step 2: var f Formatter = (*Tag)(nil)
  iface (conceptual):
    type/word ──→ *Tag
    data word ──→ 0x0   ◄── dynamic value is nil *Tag; interface value itself is non-nil

Step 3: f.Format() — dispatch to (*Tag).Format; receiver *Tag parameter ──→ 0x0
  method checks t == nil → "<nil tag>" without reading *t  ◄── aha: nil receiver safe until you dereference fields of the pointed-to Tag
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
MEMORY TRACE (Sum with nil check — safe):

Step 1: var t *Tree = nil
  stack:
    t ──→ 0x0

Step 2: t.Sum() — receiver *Tree ──→ 0x0 (copy of nil pointer)
  stack:
    receiver in Sum ──→ 0x0   ◄── nil is a legal pointer value in the receiver slot

Step 3: if t == nil { return 0 } — no load through nil → no panic


MEMORY TRACE (broken order — panic):

Step 1: var t *Tree = nil
  stack:
    t ──→ 0x0

Step 2: t.Sum() enters with receiver ──→ 0x0
Step 3: return t.v + ... — CPU tries to read field v through address 0x0  ◄── aha: nil receiver was fine to enter the method; dereferencing nil to reach fields panics
```

### Methods on non-struct types

```go
type Celsius float64

func (c Celsius) String() string {
	return fmt.Sprintf("%.1f C", c)
}
```

```
MEMORY TRACE:

Step 1: var c Celsius = 36.5
  stack:
    c ──→ [ float64: 36.5 ]  at addr 0xC000   ◄── named type Celsius, same size/layout as float64

Step 2: s := c.String() — value receiver copies the full 8-byte Celsius value into the method’s receiver slot
  stack:
    caller c ──→ 36.5  at addr 0xC000
    receiver c in String ──→ 36.5  at addr 0xC010   ◄── full value copy (not a pointer), like a tiny struct with one scalar field

Step 3: fmt.Sprintf runs on the copy; caller’s c unchanged (method does not mutate)
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
MEMORY TRACE:

Step 1: var c Counter; c is 0
  stack:
    c ──→ [ 0 ]  at addr 0xC000

Step 2: f := (*Counter).Inc — method expression, type is func(*Counter); no receiver bound yet
  stack:
    c ──→ [ 0 ]  at addr 0xC000
    f ──→ function value (*Counter).Inc   ◄── not tied to a particular Counter yet

Step 3: f(&c) — you pass the pointer explicitly each call; receiver *Counter ──→ 0xC000; *c++ → c is 1
  stack:
    c ──→ [ 1 ]  at addr 0xC000

Step 4: g := c.Inc — method value: compiler builds a function value closed over receiver *Counter ──→ 0xC000  ◄── aha: no argument at call time; “who to mutate” is fixed
  stack:
    c ──→ [ 1 ]  at addr 0xC000
    g ──→ func bound to receiver ──→ 0xC000

Step 5: g() — same as another Inc on that fixed address; c becomes 2
  stack:
    c ──→ [ 2 ]  at addr 0xC000
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

```
MEMORY TRACE:

Step 1: initial state
  stack:
    v ──→ [ x: 1 ]  at addr 0xC000
    p ──→ 0xC100   ◄── pointer value (8 bytes)
  heap:
    object at 0xC100 ──→ [ x: 1 ]

Step 2: v.A() — value receiver copies v to a temp; temp.x++; v’s slot unchanged → v.x still 1
  stack:
    v ──→ [ x: 1 ]  at addr 0xC000
    receiver copy in A ──→ [ x: 2 ]  at addr 0xC020   ◄── discarded on return

Step 3: v.B() — rewrite (&v).B(); receiver *S ──→ 0xC000; mutates v.x → v.x = 2
  stack:
    v ──→ [ x: 2 ]  at addr 0xC000

Step 4: p.A() — value receiver copies the struct *p points at into a temp; only temp.x++; heap object unchanged  ◄── aha: looked like a “pointer call” but A still used a full struct copy
  stack:
    v ──→ [ x: 2 ]  at addr 0xC000
    p ──→ 0xC100
    receiver copy in A ──→ [ x: 2 ]  at addr 0xC030   ◄── temp only
  heap:
    0xC100 ──→ [ x: 1 ]   ◄── untouched

Step 5: p.B() — receiver *S ──→ 0xC100; *s++ mutates heap struct
  heap:
    0xC100 ──→ [ x: 2 ]

Step 6: fmt.Println(v.x, p.x) → 2 2
  stack:
    v ──→ [ x: 2 ]
    p ──→ 0xC100
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

```
MEMORY TRACE (bug — value receiver):

Step 1: var buf Buffer — zero value
  stack:
    buf ──→ [ data: slice header ptr=0 len=0 cap=0 ]  at addr 0xC000

Step 2: buf.Write("hello") — entire Buffer (the slice header) copied into value receiver
  stack:
    caller buf ──→ slice header at 0xC000
    receiver copy ──→ slice header at 0xC010   ◄── append may allocate and update ptr/len only on this copy

Step 3: method returns; caller’s buf.data still len 0  ◄── aha: mutation of backing array / header never propagated back

MEMORY TRACE (fix — pointer receiver):

Step 1: var buf Buffer; buf.Write with (b *Buffer) receiver
  stack:
    buf ──→ [ data: slice header ]  at addr 0xC000
    receiver *Buffer ──→ 0xC000   ◄── aliases caller’s Buffer; append updates this header in place → len(buf.data) reflects growth
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
