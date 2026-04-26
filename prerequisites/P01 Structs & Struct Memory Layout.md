# P01 Structs & Struct Memory Layout

> **Prerequisite note** — complete this before starting [[T07 Pointers & Pointer Semantics]], [[T08 Map Internals]], or [[T11 Interface Internals (iface & eface)]].
> Estimated time: ~25 min

---

## 1. Concept

A **struct** is a named bundle of fields. Each field has a name and a type. The whole bundle is one value in the type system.

> **In plain English:** A struct is a labeled cardboard box with fixed compartments. You do not get a magic drawer that grows new compartments at runtime. You designed the box when you wrote the type. Go uses structs because the language has no classes. You build behavior with functions and methods *on types*, not with a single inheritance tree baked into the language.

---

## 2. Core Insight (TL;DR)

**Structs are value types.** Assignment and function calls copy the whole bundle unless you pass a **pointer**.

**Field order and types decide memory size** because the compiler inserts **padding** so each field lines up on valid alignment boundaries.

**Embedding flattens names into the outer struct** for convenient access, but it is **not** class inheritance.

---

## 3. Mental Model (Lock this in)

Picture a warehouse pallet. Each field is a crate placed in order. The compiler may slip **spacer blocks** between crates so every crate sits on a grid line the CPU likes. If you reorder crates, the total pallet width can shrink or grow even when the *logical* contents look the same.

**ASCII: logical vs physical layout**

```
type User struct {
    Age   uint8   // 1 byte
    Score int64   // 8 bytes
}

Logical fields in source order:
[ Age | Score ]

Physical memory (typical 64-bit; int64 wants 8-byte alignment):
offset:  0      1 2 3 4 5 6 7    8........15
        [Age][  padding 7 bytes ][   Score   ]
```

**Error-driven example: silent duplication**

```go
type Counter struct{ n int }

func bump(c Counter) {
	c.n++
}

func main() {
	c := Counter{n: 0}
	bump(c)
	fmt.Println(c.n) // still 0!
}
```

```
MEMORY TRACE:

Step 1: c := Counter{n: 0}
  main stack:
    c ──→ [ n: 0 ]  at addr 0xC000

Step 2: bump(c)  — Go copies the ENTIRE struct
  main stack:
    c ──→ [ n: 0 ]  at addr 0xC000        ◄── untouched
  bump stack:
    c ──→ [ n: 0 ]  at addr 0xD000        ◄── brand new copy at DIFFERENT address

Step 3: c.n++ inside bump()
  main stack:
    c ──→ [ n: 0 ]  at addr 0xC000        ◄── STILL 0, nobody touched this
  bump stack:
    c ──→ [ n: 1 ]  at addr 0xD000        ◄── only the copy changed

Step 4: bump() returns — copy at 0xD000 is gone
  main stack:
    c ──→ [ n: 0 ]  at addr 0xC000        ◄── still 0. the increment was lost.
```

> **In plain English:** You handed the function a photocopy of the form. They scribbled on the photocopy. Your original form never changed. Pass `&c` if you want one shared form everyone edits.

---

## 4. How It Works

### 4.1 Declaration forms

```go
type Person struct {
	Name string
	Age  int
}

v := struct {
	ID int
}{ID: 42}

p := Person{Name: "Ada", Age: 36}
q := Person{"Grace", 31} // positional; order must match type definition

pp := &Person{Name: "Lin", Age: 40}
fmt.Println(pp.Name) // compiler inserts * for field access
```

```
MEMORY TRACE:

Step 1: p := Person{Name: "Ada", Age: 36}
  stack:
    p ──→ [ Name: "Ada" | Age: 36 ]  at addr 0xC000
           (Name is a StringHeader: ptr to "Ada" bytes + len=3)
           (Age is an int: 8 bytes holding 36)

Step 2: q := Person{"Grace", 31}
  stack:
    q ──→ [ Name: "Grace" | Age: 31 ]  at addr 0xC028   ◄── separate copy

Step 3: pp := &Person{Name: "Lin", Age: 40}
  heap (or stack, escape analysis decides):
    Person ──→ [ Name: "Lin" | Age: 40 ]  at addr 0xE000
  stack:
    pp ──→ [ 0xE000 ]                                    ◄── pp is just an address (8 bytes)

Step 4: pp.Name
  Go reads: *pp → follow 0xE000 → find Name field → "Lin"
  The compiler inserts the dereference for you. pp.Name is sugar for (*pp).Name
```

> **In plain English:** You invented a dictionary word (`Person`), printed a one-time label (anonymous struct), filled out the form (literal), or kept the house address instead of cloning the house (pointer).

---

### 4.2 Zero values

Every field of a new struct starts at its **zero value** unless you initialize it.

```go
type Job struct {
	Title string
	Done  bool
	Ticks int
}

var j Job
// j.Title == ""  j.Done == false  j.Ticks == 0
```

```
MEMORY TRACE:

var j Job
  stack:
    j ──→ [ Title: "" (ptr=nil, len=0) | Done: false | Ticks: 0 ]

  Every byte is zeroed by Go. No garbage, no uninitialized memory.

  Title field breakdown:
    StringHeader [ Data: nil | Len: 0 ]  ──→ points nowhere (empty string)

  Done: 1 byte, value 0x00 = false
  Ticks: 8 bytes, all zeros = 0
```

> **In plain English:** The form is printed. No one wrote on it yet. Defaults: empty string, false, zero number, nil pointer, nil slice, nil map as appropriate.

---

### 4.3 Field access, nesting, embedding

```go
type Address struct{ City string }
type Employee struct {
	Name string
	Home Address
}

e := Employee{Name: "Sam", Home: Address{City: "Austin"}}
fmt.Println(e.Home.City)

type Meta struct{ ID int }
type Record struct {
	Meta // anonymous field: embedding
	Label string
}

r := Record{Meta: Meta{ID: 7}, Label: "x"}
fmt.Println(r.ID)       // promoted: r.Meta.ID
fmt.Println(r.Meta.ID)  // explicit
```

```
MEMORY TRACE:

Step 1: e := Employee{Name: "Sam", Home: Address{City: "Austin"}}
  stack:
    e ──→ [ Name: "Sam" | Home: [ City: "Austin" ] ]
           ↑ field 1      ↑ field 2 (nested struct, stored INLINE, not a pointer)

  e.Home.City → navigate: e → Home field → City field → "Austin"
  Total size: sizeof(string) + sizeof(Address) = 16 + 16 = 32 bytes

Step 2: r := Record{Meta: Meta{ID: 7}, Label: "x"}
  stack:
    r ──→ [ Meta: [ ID: 7 ] | Label: "x" ]
           ↑ embedded (no field name in source, but occupies real memory)

  r.ID → compiler rewrites to → r.Meta.ID → 7
  r.Meta.ID → same thing, explicit path → 7

  Memory layout:
  offset 0:  [ ID: 7 ]         ← Meta subobject (8 bytes)
  offset 8:  [ Label: "x" ]    ← string (16 bytes)
  total: 24 bytes
```

> **In plain English:** Nested is a folder inside a folder. Embedding slides a small card under a big card so the small headings line up at the outer edge; you can still lift the small card with `r.Meta`.

---

### 4.4 Struct tags

Tags are string metadata on fields. They do not change normal Go execution by themselves. Libraries read them with **reflection**.

```go
type User struct {
	Name string `json:"name" db:"full_name"`
	Age  int    `json:"age,omitempty" db:"age_years"`
}
```

```
Compiler ignores tags for normal reads/writes of fields.
`encoding/json` reads json tags; database scanners often read db tags
```

> **In plain English:** Sticky notes for tools. JSON uses them for wire names and omit rules. SQL helpers use them to map a struct field to a column name without renaming your Go field.

---

### 4.5 Memory layout, alignment, padding

The compiler lays struct fields **contiguously in memory** in declaration order, but inserts **padding** so each field begins at an address aligned to its **alignment requirement**.

```go
type Bad struct {
	A int8   // 1 byte
	B int64  // typically 8-byte alignment
}

type Good struct {
	B int64
	A int8
	// struct may still get tail padding for arrays of Good
}
```

```
Bad:   [A][ pad 7 ][    B    ]
Good:  [    B    ][A][ tail pad? ]
```

> **In plain English:** Some crates only sit on every eighth floor tile. A tiny crate first wastes space before the big one lands. Put heavy crates first when you care about packing.

---

## 5. Key Rules & Behaviors

### Structs are value types (copy on assignment)

```go
type Point struct{ X, Y int }
p := Point{1, 2}
q := p
q.X = 99 // p.X still 1
```

```
MEMORY TRACE:

Step 1: p := Point{1, 2}
  stack:
    p ──→ [ X: 1 | Y: 2 ]  at addr 0xC000

Step 2: q := p    — FULL COPY of all bytes
  stack:
    p ──→ [ X: 1 | Y: 2 ]  at addr 0xC000
    q ──→ [ X: 1 | Y: 2 ]  at addr 0xC010   ◄── different address, same values

Step 3: q.X = 99
  stack:
    p ──→ [ X: 1 | Y: 2 ]  at addr 0xC000   ◄── unchanged
    q ──→ [ X: 99 | Y: 2 ] at addr 0xC010   ◄── only q changed
```

> **In plain English:** Duplicate sticky notes. Erasing one copy does not erase the other.

---

### Zero value is usable

```go
type Stats struct{ Sum, Count int }

func add(s Stats, v int) Stats {
	s.Sum += v
	s.Count++
	return s
}

var acc Stats
acc = add(acc, 10)
```

```
`var acc Stats` is a real value; safe to pass into add immediately
```

> **In plain English:** A tally sheet that starts at all zeros is still a valid tally sheet.

---

### Comparison rules

Structs work with `==` and `!=` **only if every field is comparable**. Slices, maps, and functions break comparability.

```go
type OK struct{ A int; B string }
type Bad struct{ S []int }

var a, b OK
_ = a == b
// var x, y Bad; _ = x == y // compile error
```

```
== compares fields in order when the type allows it
```

> **In plain English:** You may only ask if two binders match when every divider inside can be checked. A divider full of loose sheets has no single yes-or-no match.

---

### Field ordering affects memory size (padding)

```go
import "unsafe"

type Loose struct{ a int8; b int64; c int8 }
type Tight struct{ b int64; a, c int8 }

func main() {
	fmt.Println(unsafe.Sizeof(Loose{})) // 24
	fmt.Println(unsafe.Sizeof(Tight{})) // 16
}
```

```
MEMORY TRACE:

Loose layout (a int8, b int64, c int8):
  offset 0:   [a: 1 byte]
  offset 1-7: [padding 7 bytes]     ◄── wasted! b needs 8-byte alignment
  offset 8:   [b: 8 bytes]
  offset 16:  [c: 1 byte]
  offset 17-23: [tail padding 7 bytes]  ◄── struct alignment = max field = 8
  total: 24 bytes

Tight layout (b int64, a int8, c int8):
  offset 0:   [b: 8 bytes]          ◄── already aligned
  offset 8:   [a: 1 byte]
  offset 9:   [c: 1 byte]
  offset 10-15: [tail padding 6 bytes]
  total: 16 bytes

  Same fields, same data, 8 bytes SAVED just by reordering.
```

> **In plain English:** Suitcase order changes how much foam you waste in the trunk.

---

### Embedding is not inheritance

```go
type Base struct{ N int }
type Derived struct{ Base }

func (b Base) Show() int { return b.N }

func main() {
	d := Derived{Base: Base{N: 5}}
	fmt.Println(d.Show())      // 5 — promoted, calls d.Base.Show()
	fmt.Println(d.Base.Show()) // 5 — explicit
}
```

```
MEMORY TRACE:

Step 1: d := Derived{Base: Base{N: 5}}
  stack:
    d ──→ [ Base: [ N: 5 ] ]  at addr 0xC000
           ↑ Base is stored INLINE at the start of Derived

Step 2: d.Show()
  Go rewrites this to: d.Base.Show()
  The receiver is d.Base (type Base), NOT d (type Derived).
  So inside Show(): b.N reads from the Base subobject → 5

  IMPORTANT: if Base.Show() modifies b.N, it modifies a COPY of d.Base
  (because Show has a value receiver). The original d.Base.N stays the same.
```

> **In plain English:** Taping notebooks together does not rewrite the author name on the cover. The promoted method still runs in the notebook's own context.

---

### Unexported fields cannot be accessed outside the package

```go
package a

type Secret struct {
	Public  int
	private int
}

func NewSecret() Secret { return Secret{1, 2} }
```

```go
package main

import "example.com/a"

func main() {
	s := a.NewSecret()
	_ = s.Public
	// _ = s.private // compile error
}
```

```
Uppercase name: exported. Lowercase: visible only inside same package.
```

> **In plain English:** Public section vs locked drawer. Other offices only see the public section.

---

## 6. Code Examples (Show, Don't Tell)

### Basic struct creation and field access

```go
type Car struct{ Make string; Miles int }

c := Car{Make: "Nova", Miles: 12000}
c.Miles += 500
pc := &c
pc.Make = "Nova Sport"
fmt.Println(c.Make) // "Nova Sport" — same underlying value
```

```
MEMORY TRACE:

Step 1: c := Car{Make: "Nova", Miles: 12000}
  stack:
    c ──→ [ Make: "Nova" | Miles: 12000 ]  at addr 0xC000

Step 2: c.Miles += 500
  stack:
    c ──→ [ Make: "Nova" | Miles: 12500 ]  at addr 0xC000
           direct field write: addr 0xC000 + offset(Miles) = 0xC010 → write 12500

Step 3: pc := &c
  stack:
    c  ──→ [ Make: "Nova" | Miles: 12500 ]  at addr 0xC000
    pc ──→ [ 0xC000 ]                        ◄── pc holds c's address

Step 4: pc.Make = "Nova Sport"
  Go rewrites to: (*pc).Make = "Nova Sport"
  Follow 0xC000 → find Make field → overwrite
  stack:
    c  ──→ [ Make: "Nova Sport" | Miles: 12500 ]  ◄── c changed via pointer!
    pc ──→ [ 0xC000 ]
```

---

### Struct copy vs pointer to struct

```go
type Wallet struct{ Balance int }

func addByValue(w Wallet, x int) Wallet {
	w.Balance += x
	return w
}

func addByPointer(w *Wallet, x int) { w.Balance += x }

func main() {
	var w Wallet
	w = addByValue(w, 10)

	w2 := Wallet{}
	addByPointer(&w2, 10)
}
```

```
MEMORY TRACE — value path:

Step 1: var w Wallet
  main stack:    w ──→ [ Balance: 0 ]  at 0xA000

Step 2: addByValue(w, 10)  — copies w into function's parameter
  main stack:    w ──→ [ Balance: 0 ]  at 0xA000     ◄── untouched
  func stack:    w ──→ [ Balance: 0 ]  at 0xB000     ◄── copy
  w.Balance += 10:
  func stack:    w ──→ [ Balance: 10 ] at 0xB000
  return w → copies 10 back to main's w

Step 3: w = addByValue(w, 10)
  main stack:    w ──→ [ Balance: 10 ] at 0xA000     ◄── updated by return


MEMORY TRACE — pointer path:

Step 1: w2 := Wallet{}
  main stack:    w2 ──→ [ Balance: 0 ]  at 0xA020

Step 2: addByPointer(&w2, 10)  — copies ADDRESS, not struct
  main stack:    w2 ──→ [ Balance: 0 ]  at 0xA020
  func stack:    w  ──→ [ 0xA020 ]                    ◄── pointer (8 bytes)
  w.Balance += 10 → follow 0xA020 → modify in place
  main stack:    w2 ──→ [ Balance: 10 ] at 0xA020     ◄── changed directly!
```

---

### Embedding and promoted fields

```go
type Audit struct{ CreatedBy string }
type Document struct {
	Audit
	Title string
}

d := Document{Audit: Audit{CreatedBy: "lee"}, Title: "memo"}
fmt.Println(d.CreatedBy, d.Audit.CreatedBy) // "lee lee"
```

```
MEMORY TRACE:

d ──→ [ Audit: [ CreatedBy: "lee" ] | Title: "memo" ]
       offset 0: Audit subobject (16 bytes — one string)
       offset 16: Title (16 bytes — one string)

d.CreatedBy  → compiler rewrites → d.Audit.CreatedBy → "lee"
d.Audit.CreatedBy → explicit path → same memory location → "lee"

Both paths read the SAME bytes at offset 0 inside d.
```

---

### Anonymous struct for test table

```go
func TestSquare(t *testing.T) {
	for _, tc := range []struct{ in, want int }{{2, 4}, {3, 9}} {
		if got := tc.in * tc.in; got != tc.want {
			t.Fatalf("square(%d)=%d want %d", tc.in, got, tc.want)
		}
	}
}
```

```
MEMORY TRACE:

The slice of anonymous structs in memory:
  [ {in: 2, want: 4} | {in: 3, want: 9} ]
    element 0 (16 bytes)  element 1 (16 bytes)

Each tc in the range loop is a COPY of the element.
Mutating tc would not change the slice.
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

```go
package main

import "fmt"

type S struct{ a, b int }

func f(x S) { x.a = 10 }

func main() {
	v := S{a: 1, b: 2}
	f(v)
	fmt.Println(v.a, v.b)
}
```

> [!success]- Answer
> `1 2`
>
> `f` receives a copy of `v`. Mutating `x.a` does not change `v`.

---

### Tier 2: Fix the Bug (5 min)

```go
package main

import "fmt"

type Buffer struct{ data []byte }

func grow(b Buffer) {
	b.data = append(b.data, 'x')
}

func main() {
	var b Buffer
	grow(b)
	fmt.Println(len(b.data))
}
```

> [!success]- Answer
> `grow` updates only its copy of `Buffer`. The caller never sees a new slice header. Pass `*Buffer`:
>
> ```go
> func grow(b *Buffer) { b.data = append(b.data, 'x') }
> func main() {
> 	var b Buffer
> 	grow(&b)
> 	fmt.Println(len(b.data)) // 1
> }
> ```
>
> **Interview line:** When a function must persist updated slice headers on the caller's struct, pass a pointer to that struct.

---

## 7. Gotchas & Interview Traps

| Trap | Why it bites | Fast fix / mental rule |
|------|--------------|------------------------|
| Huge struct by value in a hot loop | Full copy every call | Pass `*T` when copies show up in profiles |
| Expecting `d.Method()` from embedded type | Method sets do not auto-lift like some OO languages | Call through embedded value or add a wrapper method on outer type |
| `==` on structs with slice fields | Slices are not comparable | Compare with `slices.Equal` or hand-rolled logic |
| Tags "not working" for JSON | Unexported fields or wrong tag spelling | Export with uppercase; verify tag syntax |
| Padding shock after reordering fields | Alignment and tail padding | Measure `unsafe.Sizeof` on the target |

**Step-through: slice field blocks `==`**

```go
type Box struct{ Items []int }
// var p, q Box; _ = p == q // compile error
```

```
If any field forbids ==, the whole struct forbids ==
```

---

## 8. Interview Gold Questions (Top 3)

**1) Are Go structs classes?** No. You define types and attach methods. Composition is explicit. Embedding helps ergonomics but is not inheritance. Visibility is by capitalization at package scope.

**2) What happens when you pass a struct to a function?** The struct is copied unless you pass a pointer. `p.X` on `*T` still works. Mutations on a value parameter stay inside the function unless you return the updated value.

**3) Why can two structs with the "same fields" have different sizes?** Field order changes padding and trailing alignment for array stride. Always measure on the architecture you ship.

---

## 9. 30-Second Verbal Answer

A struct is a fixed-shape **value type**: named fields laid out contiguously with alignment and padding. Go uses structs instead of classes; behavior comes from functions and methods plus composition. Assignment copies the whole value, so pointers mean shared mutation and fewer large copies. `==` works only when every field type is comparable. Tags are reflection metadata for encoders. Embedding promotes selectors but is not inheritance.

---

> See [[Glossary]] for term definitions.
