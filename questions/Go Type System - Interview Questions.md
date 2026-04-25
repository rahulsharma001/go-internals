# Go Type System & Value Semantics — Interview Questions

> Comprehensive interview Q&A bank for [[Go Type System & Value Semantics]].
> Sorted by frequency at top tech companies (Google, Amazon, Meta, Uber, Stripe, Cloudflare).
> Tags: `[COMMON]` = asked frequently, `[ADVANCED]` = deep understanding expected, `[TRICKY]` = gotcha/trap question

---

## Q1: Why can't a value type satisfy an interface with pointer receiver methods? [COMMON]

**Answer:**

**In one line:** The interface value holds a copy of your value, not the original, so pointer-receiver methods on that copy would mutate the wrong place and Go blocks that at compile time.

**Visualize it:**

```
Original variable:     val  (addressable, lives in caller)
                              │
   assign to interface  ▼
Interface value:  ┌─────────────────────────┐
                  │  type: T                │
                  │  data: COPY of val      │  ◀── not addressable; hidden copy
                  └─────────────────────────┘
   If *T method ran:  would mutate "data" copy ──▶  original `val` unchanged (silent data loss)

Correct pattern:  assign &val  ──▶  interface holds  (type: *T, data: *to original)  ──▶  mutations visible

Method call on value (non-interface):  val.M()  ─(if `M` is `*T` and val addressable)─▶  (&val).M()
Interface assign:  NO such sugar  ──  copy is already inside iface
```

**Key facts:**
- Storing a `T` in an interface packages a copy; pointer-receiver methods need a `*T` that points at the real variable, or writes would go to the copy.
- Direct calls like `x.Method()` can take the address of an addressable `x`, but that does not apply when the value is only reachable as the opaque payload inside an interface.
- If any interface method is declared with a pointer receiver, only `*T` (not `T`) implements that interface when you need the full method set.
- The fix is to put a pointer in the interface: `var i Iface = &val` so method calls go through a `*T` to the same object the caller has.

**Interview tip:** This is the #1 most asked Go type system question: say that the interface stores a copy, so pointer-receiver mutations would be lost, and name the method-call sugar for variables versus no promotion on interface assignment.

> [!example]- Full Story: Value in the box, pointer at the door
>
> **The problem:** You want a type to implement an interface whose methods are all `func (p *T) ...`, assign a bare `T` to that interface, and expect in-place changes to be visible: if the compiler allowed it, the runtime would call `p`-receiver methods on a `T` that only exists as the `data` word of the interface—an isolated copy—so side effects on the "real" `T` in the outer scope would be lost; interface satisfaction ties to method sets, and for `*T` with pointer methods the assignable value type is not `T` when the interface’s required set includes those pointer methods, because direct `t.M()` can rewrite to `(&t).M()` when legal but the interface case never sees your original lvalue, only the stored copy, so that rewrite does not help.
>
> **How it works:** An interface is its own two-word value (`tab`/`_type` and `data`) that already copied the bits at assignment time, not a view onto your local variable, so "interface" is the box story: pointer semantics through an interface are only trustworthy when `data` is a `*T` to shared storage, and the type system + interface mechanism use method sets so `*T` is required when the interface needs pointer-receiver methods.
>
> **What to watch out for:** Conflating everyday `t.M()` (which may promote to `(&t).M()`) with `var i Iface = t` (no promotion to a pointer into the box); test with interface holding value versus pointer and whether mutation must round-trip to the same memory.

---

## Q2: How does struct embedding differ from inheritance in OOP? Show a case where it surprises you. [COMMON]

**Answer:**

**In one line:** Embedding promotes names for composition, but the promoted method’s receiver is still the inner type, so you do not get Java-style `this` dispatch down an override chain.

**Visualize it:**

```
type Base struct { name string }
type Derived struct { Base }   // embedded

Derived has field path:  d.Base.name  and promoted:  d.name
Method Base.Greet() has receiver b *Base:  b's dynamic type is *Base, not *Derived

Base.Greet() { print(b.Name()) }  ──▶  always Base.Name, even if Derived defines Name() too

OOP (conceptual):
   greet()  ──virtual dispatch──▶  most-derived Name()
Go embedding:
   Greet on *Base  ──no virtual table──▶  Base's method set only; outer Name never selected from inside Base
```

**Key facts:**
- Struct embedding flattens field and method *names* for access; it does not install a vtable or retarget the receiver to the outer struct.
- A promoted `Base` method is still a method on `*Base` (or `Base`); `Base.Greet` calling `b.Name()` uses `Base`’s `Name`, not a hypothetical “overridden” `Name` on the wrapper.
- Compared to Java/PHP, there is no `this` that late-binds to the most-derived type from inside a base method.
- Template Method and classic inheritance-based polymorphism are not modeled the same way; you tend to use explicit interfaces, function fields, or small wrappers instead of deep type trees.

**Interview tip:** Say "delegation, not inheritance" and give the `Greet()`/`Name()` example so the receiver behavior is clear.

> [!example]- Full Story: The promoted name is not a subclass
>
> **The problem:** In classical OOP, a superclass method that calls a helper can route to overridden behavior in a subclass, but teams new to Go expect embedded structs to allow that and are surprised when behavior does not "override" through the outer type, because the outer `Derived` is a new struct type that *contains* a `Base` value, and when you call a promoted `Greet` on `Derived` the receiver passed in is the embedded `Base` (or a pointer to it), so method lookup for code defined on `*Base` never considers methods attached only to `*Derived` when the receiver is `*Base`.
>
> **How it works:** Embedding is a syntactic and namespace convenience over composition, not a subtype relationship: inheritance mental models are misleading here, think field plus delegation, not is-a with dynamic dispatch; the inner `Base` does not see the outer type’s identity without explicit wiring (interface, callbacks, strategy structs).
>
> **What to watch out for:** Hiding a promoted field, subtle shadowing, and workflows where the inner type must see the outer type’s identity without you passing it explicitly (see embedding an interface, callbacks, or small strategy structs).

---

## Q3: What is the nil interface trap? How do you avoid it in production? [TRICKY]

**Answer:**

**In one line:** A nil concrete pointer still has a static type, so stored in an interface you get (type, nil) where the interface is not nil and `if err != nil` can be wrong for errors.

**Visualize it:**

```
interface value = two words (conceptually):

  truly nil:     ┌────────────┬────────────┐
                 │  type: nil │  data: nil  │  ◀──  (err == nil) is true
                 └────────────┴────────────┘

typed nil:       ┌─────────────────┬────────────┐
                 │  type: *MyError │  data: nil  │  ◀──  interface != nil, dynamic value is still nil
                 └─────────────────┴────────────┘
```

**Key facts:**
- The interface is empty only if both the `type` descriptor and the `data` word represent "no type / no value" together in the way the implementation defines for a zero interface (both nil in the public mental model for user code).
- Assigning a typed nil pointer like `var e *T = nil` into a `error` (or any interface) still installs the `*T` type into the first word; the second word is nil, but the overall interface value is non-nil, producing the classic footgun: `return err` with `err` a typed `*MyError` variable holding nil makes callers see a non-nil `error` interface.
- Prefer `return nil` for "no error," or `if err != nil { return err }; return nil`, and be careful when returning predeclared `var err *Concrete` when it is nil; nilness of the interface and nilness of the underlying pointer are two different questions—first is about the pair `(type, data)`, second about `data` alone once the type is fixed, and the comparison operator follows the spec: different dynamic types mean different things for nil comparison on interfaces.

**Interview tip:** Draw the two-field interface layout: `[type: *MyError | data: nil]` is not nil, while `[type: nil | data: nil]` is nil.

> [!example]- Full Story: The handoff that is not "empty"
>
> **The problem:** You write `if err := f(); err != nil` expecting only real failures, but a helper returned a typed nil error through an interface, so the check is always true, or you compare `e == nil` on an interface and misunderstand typed nil, leading to misclassified errors and broken control flow; the interface must carry which concrete type the dynamic value would have, even if that value’s pointer is nil, so the type half is not empty and the whole `error` (or `interface{}`) is not the zero interface—there is no bug in the comparison operator, it is doing what the spec says.
>
> **How it works:** The runtime representation keeps `(type, data)` consistent so that a typed nil still records `*T` in the first word, which is why "empty" at the language level and "nil pointer" at the concrete level diverge, and "nilness" of an interface and "nilness" of the underlying pointer are distinct questions.
>
> **What to watch out for:** Relying on `reflect.ValueOf(i).IsNil()` as routine policy (diagnostic, not a substitute for return patterns that never shuttle typed nils through interfaces) and generic APIs that return `error` with named `*customError` return slots.

---

## Q4: Explain Go's type system. What is structural typing? [COMMON]

**Answer:**

**In one line:** Go is statically typed, and for interfaces assignability is structural: if the methods match, the type implements the interface with no `implements` keyword.

**Visualize it:**

```
Nominal (Java):
   class Foo implements Reader { ... }  ◀──  must NAME the interface in source

Go structural:
   package consumer defines:  type Reader interface { Read([]byte) (int, error) }
   package other has type File { func (f *File) Read([]byte) (int, error) { ... } }
   *File satisfies Reader automatically  (method shapes line up)  ◀──  no import-time bond

Type identity (separate idea):
   type UserID int      ◀ defined type, distinct from int
   type OldName = int   ◀ alias, same type as int
```

**Key facts:**
- Core language uses static typing: every value has a known type (or, for interface dynamic values, a known *interface* and a concrete *dynamic type* at runtime).
- Interface satisfaction is implicit: a named type has a method set; if it is a superset of the interface’s method set with matching signatures, assignment is allowed.
- `type T U` (non-alias) creates a *defined* type with the same *underlying* type as `U` but a distinct *named* type; `type T = U` is an alias, no new type.
- Underlying type, zero value, method set, and convertibility all matter when explaining how the type system composes beyond a single "interfaces are structural" line, and "behavior is all that matters" for interfaces: names of concrete types and interface definitions meet only at assignment/check time.

**Interview tip:** Use "structural typing" or "implicit interface satisfaction" and connect the practical benefit: accept `io.Reader` and any type with `Read()` works, including types the interface author never knew about.

> [!example]- Full Story: Structural contracts decouple authors
>
> **The problem:** In nominal systems, library and application authors can get stuck in reference cycles when you add an import just to `implements` an interface from another package, and small changes ripple; Go wanted package-local, consumer-defined boundaries.
>
> **How it works:** The compiler only checks whether this named type *T* has the required exported and unexported-as-needed methods with legal signatures to implement interface `I`, and if yes, `var i I = valueOfT` type-checks without the implementing package knowing `I` at all, inverting the dependency arrow compared to many OOP stacks, while generics, embedding, and method promotion still interact with the same method-set rules so "structural" is not a license to ignore pointer versus value method sets, blank interfaces, and assignability in composite types.
>
> **What to watch out for:** Forgetting that structural satisfaction still respects method-set, blank-interface, and assignability details when you combine features.

---

## Q5: What's the difference between `type X int` and `type X = int`? When do you use each? [COMMON]

**Answer:**

**In one line:** A defined `type X int` is a new named type (explicit conversion to and from `int`, methods allowed) while `type X = int` is just another spelling of `int`.

**Visualize it:**

```
type UserID int64        UserID(1)  ─convert──▶  int64(1)   (explicit)
                         int64(1)   ─convert──▶  UserID(1)

type Count = int         Count(3)  and  int(3)  are the SAME type, interchangeable

defined type:   methods can be:  func (u UserID) String() string
alias:          cannot define new methods on Count (it *is* int)
```

**Key facts:**
- `type T U` (without `=`) gives you a *defined* type `T` with underlying type the underlying type of `U`; you cannot assign between `T` and `U` without conversion even when they share a numeric or struct underlying.
- `type T = U` is a *type alias*—`T` and `U` are identical, used for large refactors, compatibility shims, and re-exporting from another path without changing the core type.
- Method declarations attach to the defined type, not to the alias name (the alias is not a new type).
- In production, defined types model domain IDs, units, and state machines; aliases are for when you must not fork type identity (gradual renames, embedding external types); generic constraints treat aliases as whatever type they are an alias of, and re-aliasing `byte` and `uint8` when you wanted distinct wrapper types is a common mistake.

**Interview tip:** Use `type UserID int64` versus `type OrderID int64` to show the type checker enforces ID separation, not just syntax.

> [!example]- Full Story: New name vs new identity
>
> **The problem:** You want to stop mixing int-sized IDs in function arguments and database scans, and separately you need to move a public type to a new import path without breaking binary compatibility in every intermediate release.
>
> **How it works:** A defined type is a namespace for methods and a separate static type with convert rules to its base, while a type alias never introduces a new type, only a new identifier in the type universe for an existing one, so you use defined types to let the type checker be your "units" layer and aliases to change organization without forking the underlying representation or method sets.
>
> **What to watch out for:** Accidentally re-aliasing `byte` and `uint8` when you wanted distinct wrapper types, and how generic constraints see aliases as the aliased type.

---

## Q6: What are Go's method set rules? Why is there an asymmetry between T and *T? [COMMON]

**Answer:**

**In one line:** `T`’s set is value-only methods and `*T`’s set adds pointer receivers too, because you must never silently mutate a copy living inside an interface.

**Visualize it:**

```
         methods declared as     value set on T    also on *T?
  func (T) f()                      yes                 yes
  func (*T) g()                     no                  yes
                                     ▲
                                     └── T inside iface: copy, not addressable
                                         cannot attach *T g() in a sound way
```

**Key facts:**
- Value-receiver methods run on a copy and are in `T`’s method set; pointer-receiver methods are only in `*T`’s set, and for a plain `T` you may call a `*T` method when the `T` value is *addressable* (so the compiler can pass `&T`); a `T` stored inside an interface is not addressable, which is the core of the copy problem.
- `*T`’s method set is the union: all value-receiver methods on `T` and all pointer-receiver methods on `*T`.
- For interface implementation, a pointer requirement arises when the interface requires a method that only exists in pointer form for your named type, matching the `*T` set.
- The asymmetry’s root: if an interface’s dynamic value is a `T` copy, pointer methods would have to read or write a hidden copy, breaking expectations about mutation and identity, so the type system disallows that combination, and the restriction is the same "copy in a box" story as in Q1 from the method-set angle.

**Interview tip:** Give the full chain: method set, interface satisfaction, and why the asymmetry exists (mutation safety), not just the table.

> [!example]- Full Story: Method set as safety rail
>
> **The problem:** You want a uniform rule for "what can I call on this value," but pointer receivers carry identity and mutation obligations that value-receiver methods (which receive a copy) do not.
>
> **How it works:** The method set of `*T` is a superset when `T` is not a pointer type because a pointer can address storage for value- and pointer-receiver bodies, while the method set of `T` is only those declared with a value receiver because a bare `T` is always copyable but a pointer receiver needs a pointer in some static scenarios and interfaces holding concrete `T` values break that, so `T` with only value receivers lets both `T` and `*T` satisfy many interfaces, but adding a `*T`-only method means the value side stops implementing interfaces that need that method, and large structs often push you toward `*T` for efficiency, matching pointer-heavy interfaces.
>
> **What to watch out for:** Losing track of which side of a type implements which interfaces after you add a pointer-only method.

---

## Q7: What is a zero value in Go? Why does it matter for API design? [COMMON]

**Answer:**

**In one line:** Every variable starts life fully initialized and the zero of its type is a well-defined, safe default, and good APIs make that default a usable, ready object.

**Visualize it:**

```
var n int         ──▶ 0
var s string      ──▶ ""
var p *T          ──▶ nil
var sl []int      ──▶ (nil slice: len 0, usable)
var m map[K]V     ──▶ nil (read-only OK, write needs make)
struct{}          ──▶ all fields at *their* zeroes

"Useful zero" idiom:
  var mu sync.Mutex  ── valid to Lock immediately
  var buf bytes.Buffer  ── Write works out of the box
```

**Key facts:**
- There is no "indeterminate" memory for variables; the zero value is always defined for the type, and aggregate types (arrays, structs) zero element-wise and field-wise.
- Pointers, slices, maps, channels, functions, and interfaces are nil at zero, but slices are often still readable (length 0) while nil maps are not write-ready, and `sync.Mutex`, `bytes.Buffer`, and `http.Client` showcase "zero is ready" while semantics that require mandatory configuration call for `New` or builders.
- "Make zero useful" shrinks the invariants the caller must reason about in the default case, which is the common case, unlike constructor-heavy languages where partially constructed objects are dangerous.

**Interview tip:** Name `sync.Mutex` and `bytes.Buffer` and contrast with languages where uninitialized object fields can cause `NullPointerException`.

> [!example]- Full Story: The default is not chaos
>
> **The problem:** Constructor-heavy languages push you to always call a factory because partially constructed objects are dangerous, while Go makes defaults explicit in the spec so `var` declarations and composite literals have predictable, safe starting points.
>
> **How it works:** Library types exploit zero: mutex zero is an unlocked ready mutex, an empty `bytes.Buffer` can receive writes, many clients do `var c http.Client` and get sensible transport defaults, and the API surface stays small with fewer "must call Init" preconditions in normal paths, though zeros that *look* live but are not semantically (nil `map` versus empty map, nil channel `select` behavior) still need care, and fields that must be coordinated use constructors or unexported fields plus setters.
>
> **What to watch out for:** Zeros that look live but are not (nil map, nil channel), coordinated fields, and fields that need explicit initialization beyond zero.

---

## Q8: How does Go handle polymorphism without classes or inheritance? [COMMON]

**Answer:**

**In one line:** Polymorphic behavior uses small interfaces, dynamic dispatch on interface values, and explicit composition, while embedding is for reuse, not virtual methods.

**Visualize it:**

```
  func Process(r io.Reader)   ◀──  accepts *File, *bytes.Buffer, *Conn, etc.

  r.Read(...)  ──▶  runtime: iface word pair + itab
                      └──▶  concrete ( *File ).Read  (or whatever dynamic type is)

  struct embedding:
    Outer{ Inner }  ─▶  promotes methods, but  Inner.method  still has Inner as receiver
                      (no automatic override / virtual table)
```

**Key facts:**
- Interfaces are the primary subtype-polymorphic abstraction: a single `interface` variable can hold many concrete types that share a method set, and dispatch uses efficient interface runtime structures (`itab` and friends) to reach the right function after the first use for a type pair.
- Struct embedding reuses code and data layout, but is not a substitute for a class hierarchy with dynamic `this`, so cross-cutting behavior usually uses function values, small interfaces, or hand-wired calls, and OOP "template method" style hierarchies are usually modeled with strategies plus interfaces or composition of named behaviors.
- "Polymorphism" is programmed at the site of use (interface definition by consumer) and implemented per concrete type without a central object model, which avoids inheritance-based coupling and fragile base classes.

**Interview tip:** State Go’s intentional choice: small interfaces and composition create less coupling than deep inheritance hierarchies.

> [!example]- Full Story: Contracts at the boundary
>
> **The problem:** Inheritance-based polymorphism bakes whole families of types and fragile base classes into a single hierarchy and diamond-shaped designs, which Go’s authors wanted to avoid.
>
> **How it works:** A consumer states the behavior it needs in an interface, implementations in unrelated packages satisfy it without a shared base class, interface calls are indirect through the vtable-like structure for the concrete+interface pair, and for shared implementation in structs you nest values and get promoted selectors, not automatically polymorphic "super" calls, so the host depends on a minimal interface surface, optional cross-cutting pieces use extra small interfaces, and you avoid over-using empty interfaces or building inheritance in disguise.
>
> **What to watch out for:** Over-using empty interfaces, trying to build inheritance, or embedding when an explicit `Strategy` field would be clearer (see Q2 and Q9).

---

## Q9: What's the "accept interfaces, return structs" principle? [COMMON]

**Answer:**

**In one line:** Take abstractions (interfaces) as inputs so anything can plug in, and return concrete data types so callers get full fields and clear evolution without an extra indirection of abstraction.

**Visualize it:**

```
CALLER
   │
   │  passes io.Reader, io.Writer, small domain interfaces
   ▼
┌────────────────────┐
│  func F(r io.Reader) *Result   │
│         │            │           │
│         │            └── returns *Result  (concrete) ──▶  caller can use all fields, methods, future additions w/o iface churn
└────────────────────┘

If F returned  Result  as interface, caller often needs assertions; producer-owned huge interfaces bloat all consumers.
```

**Key facts:**
- Input parameters of interface type maximize flexibility, testing (mocks), and reduce coupling because many concretes satisfy `io.Reader` and similar, while return values that are specific structs (or other named concretes) make APIs self-documenting.
- Defining the interface in the *consumer* package (where you need the behavior) keeps interfaces small and semantically right-sized, and a typical shape is `func Work(r io.Reader) (*Output, error)` with reader as file, buffer, or network body and `*Output` carrying everything specific.
- The consumer of behavior owns the `interface` that covers that slice of behavior, and the producer of data owns the shape of the return struct, so who owns the contract is explicit, though sometimes returning a minimal interface (e.g. `io.ReadCloser` from a constructor) is still appropriate to hide implementation.

**Interview tip:** Say interfaces should be defined where they are consumed, not where they are implemented.

> [!example]- Full Story: Flexibility in, facts out
>
> **The problem:** If a package returns only big interfaces, every caller re-learns the concrete type through assertions or the interface accretes every possible operation, while if it takes only concretes it is hard to test and reuse across IO sources.
>
> **How it works:** The producer constrains the input side to what it truly needs (read bytes, log events, time) and exposes the output as a concrete, rich result the caller is expected to work with, so tests swap readers while production uses real `*os.File` or `*http.Response.Body`, keeping the host minimal on dependencies and the result explicit.
>
> **What to watch out for:** The principle is a guideline, not a law, when you intentionally return a small interface to hide implementation.

---

## Q10: Can you embed an interface in a struct? What happens? [TRICKY]

**Answer:**

**In one line:** Yes, you can embed an interface, methods promote and the struct can satisfy the interface in principle, but a nil interface field means promoted calls nil-deref at runtime.

**Visualize it:**

```
type S struct { io.ReadCloser }  // embedded interface field
var s S

s.Read(...)  ──▶  promoted to s.ReadCloser.Read(...)
                  but ReadCloser is nil
                  ▼
             RUNTIME PANIC: nil interface method value

To be safe, assign real impl:
  s.ReadCloser = &bytes.Buffer{...}   // or an os.File, etc.
```

**Key facts:**
- Embedding a named `interface` type in a `struct` is legal, and the struct can implement that same `interface` if the promoted methods of the field cover the set (often used with partial forwarders), but a zero-initialized `struct` has the embedded field at its interface zero, so dynamic dispatch to methods has nothing concrete to call, compilation succeeds, and the bad path is a runtime panic like calling a method on a nil `interface` stored in a field you forgot to assign.
- Legitimate use decorates or partially overrides methods while delegating the rest to a wrapped implementation you must wire before use (tests, middleware-like wrappers), and "satisfies interface at compile time" and "all dynamic calls are safe" are different: promotion is name lookup, not proof that a runtime value is present.

**Interview tip:** Emphasize it compiles but can panic at runtime, the boundary between compile-time safety and runtime behavior.

> [!example]- Full Story: Promotion without possession
>
> **The problem:** You want a struct to "be" an `io.ReadCloser` with a few custom methods, embed the interface field, and implement overrides, but the embedded field starts at nil like an uninitialized pointer while the compiler still believes the *type* has the methods via promotion, so the struct can look done when it is not.
>
> **How it works:** You embed `io.ReadCloser`, forward unimplemented parts to a concrete you assign to that field, and override (for example) `Close` on the outer `struct` by defining a new method *on* the struct, which can shadow or combine with the embedded field, so initialization discipline is the whole game and partial mocks are easy to return as structures that *implement* the interface in static terms while still being unusable until fields are set.
>
> **What to watch out for:** Returning structs that *implement* the interface in static terms while still being unusable in practice until fields are set.

---

## Q11: How do type assertions and type switches work? What's the performance cost? [ADVANCED]

**Answer:**

**In one line:** Assertions unpack the interface’s dynamic value for a type (panic or comma-ok), type switches are multi-way assertions, and the runtime caches successful interface–type relations so repeat checks are very cheap.

**Visualize it:**

```
i := (interface{})(myptr)

v := i.(*Concrete)          // fails fast with panic if wrong
v, ok := i.(*Concrete)      // ok == false, no panic

switch t := i.(type) {
case *Concrete:  // t is *Concrete
case int:         // t is int
}

Under the hood (conceptual):
  iface + wanted type  ──▶  cache / itab  ──▶  "same pair seen before" path ≈ a few ns
  cold path: still typically pretty cheap, then cached
```

**Key facts:**
- A plain assertion is an unchecked dynamic cast: wrong type is a run-time panic, and `v, ok` turns it into a boolean outcome; `switch x := e.(type)` is syntactic sugar for a series of type tests with a binding in each arm.
- The runtime reuses and caches the relation between a concrete type and a particular interface, so re-asserting the same running pair in hot loops is near constant-time, low-constant work after warm-up in typical implementations, and caching the compatibility between `(I, T)` is what makes the feature usable in real servers without making every dispatch look like slow reflection.
- If you find yourself type-asserting everywhere, model behavior with interfaces; assertions are for extensions and genuine sum-type style branching, and you should watch panics when wrapping errors or asserting impossible combinations, including to `nil`.

**Interview tip:** Name `itab` caching for the performance question and comma-ok for safety.

> [!example]- Full Story: From opaque iface to a concrete you can touch
>
> **The problem:** You have an `interface{}` (or a narrow `interface`) but need a pointer to your concrete to access unexported data paths or a method not in the small interface, so you must recover static knowledge at the cost of a dynamic check, comparing the concrete type in the `iface` (with caching) to the type you name in the assertion *or* the cases in a type switch, then (conceptually) reinterpreting the `data` word, with wrong type becoming panic or `ok = false` depending on form.
>
> **How it works:** Type assertions and switches perform those dynamic checks and bindings with runtime support that caches `itab` or related structures so repeated work on the same interface–concrete pair stays cheap, which keeps servers practical without reflection on every use.
>
> **What to watch out for:** Chaining assertions on a wide union where a sum-type ADT in another language would be clearer, and interface equality or reflection edge cases when you mix assertions with other dynamic behavior.

---

## Q12: What are comparable types in Go? Why does it matter? [COMMON]

**Answer:**

**In one line:** Comparable means `==` and `!=` is defined and you may use the type as a `map` key, while slices, maps, and functions are not comparable and `interface` equality can still panic on bad dynamic values.

**Visualize it:**

```
comparable:   bool, numbers, string, pointer, channel,
              array of comparable T, struct of all comparable fields

NOT comparable:  []T, map[K]V, func(...)

map[K]V   requires  K comparable  at compile time

interface values:
  a == b  checks dynamic type and value, but
  if dynamic values hold non-comparable (e.g. []int)  ──▶  run-time panic

generics:  constraint  comparable
  *interface types are trickier: compile-time OK, possible runtime failure*
```

**Key facts:**
- A `map` key type must be comparable, and a slice as a key is a compile error; struct comparability is "all fields comparable" and arrays are comparable if their element type is, with matching length.
- Two interface values are equal if they have the same *dynamic* type and equal dynamic values, or if both are a suitable kind of `nil` per spec rules, but holding different concrete types is unequal, and the dangerous case is holding non-comparable concretes and running `==`.
- Go 1.18+ `comparable` in generics means `interface` may satisfy the constraint, but instantiations can still run into runtime issues when a type parameter is instantiated with a non-comparable *dynamic* set of cases, so "comparable at compile time" and "comparable in every concrete instantiation at runtime" diverge for interface-shaped type parameters, and you think about the actual dynamic *instances*; `reflect.DeepEqual` is a different tool with different cost and meaning than `==`.

**Interview tip:** Cover the runtime panic with non-comparable values inside `interface{}` and that `interface{}` `==` can panic when the underlying type is not comparable, such as a slice.

> [!example]- Full Story: The map and the == that bites
>
> **The problem:** You build `map[Key]T` and choose a key type, or you compare two `any` or `error` or custom interfaces generically, and a panic erupts only on certain data paths, not in shallow `go test` examples.
>
> **How it works:** The compiler enforces *static* knowledge for maps and the generic constraint, but `interface` values delay some knowledge until you actually compare the dynamic pair: a slice, map, or function is never allowed as a `map` key, and two interfaces of slice dynamic type cannot be `==` without a panic because slices are not comparable, while "comparable" for generics still needs you to think about dynamic instances that might be slice-backed in practice.
>
> **What to watch out for:** Comparing `interface` values in generic `comparable` code paths that might bind to slice-backed dynamics, and using `==` when you need `DeepEqual` semantics.

---

## Q13: How would you design a plugin system in Go without inheritance? [ADVANCED]

**Answer:**

**In one line:** Expose a tiny interface contract, load implementations that satisfy it, and compose optional cross-cutting behavior with more interfaces, options, and type-asserted capabilities instead of base classes.

**Visualize it:**

```
Host package defines:
  type Plugin interface { Name() string; Run(ctx) error }
  (maybe separate  io.Closer, Initializer, etc.)

Registration / discovery:
  plugin value  (concrete)  satisfies Plugin  via implicit method set

Optional capabilities:
  if c, ok := p.(io.Closer); ok { c.Close() }
```

**Key facts:**
- A single focused contract (`Handle`, `Run`, `Process`) is enough; metrics, health, and config reload can be separate, smaller interfaces to probe, `interface{}` + assertion, or `//go:embed`+registration patterns beyond a short answer, and the host only depends on the minimal surface, with each plugin as another package (or a `plugin` .so) exporting a global `func New(...) Plugin` or a registry the host walks.
- Composition over "extend `AbstractPlugin`" means you wrap a core with decorators that also satisfy `Plugin` by forwarding, using embedding carefully (see Q10), and `http.Handler` is the stdlib’s proof that one method—`ServeHTTP`—spawns a composable web ecosystem like an in-process plugin model.
- "Open for extension" is *interface satisfaction* + registration + dependency injection, not a framework superclass, but plugin isolation, security when loading code, and version skew between host and plugin remain (without `extends` as the source).

**Interview tip:** Cite `http.Handler` as the canonical example of interface-based extensibility.

> [!example]- Full Story: Plugins as behavior, not lineages
>
> **The problem:** Inheritance-laden plugin APIs force every plugin to inherit baggage from a `Base` class, understand template hooks, and fight visibility rules across packages, often creating dependency cycles and upgrade pain.
>
> **How it works:** A plugin is a value that implements a small interface, registered into a `map` or table keyed by name or version, with the host only talking through that interface plus optional init-time config, `context.Context` for cancellation, and extra interfaces discovered via `ok` type assertions, no subclassing, only substitutability of behavior, mirroring the `http.Handler` pattern at a different grain.
>
> **What to watch out for:** Plugin isolation (process versus in-process fakes), security when loading code, and version skew between host interface and plugin expectations, which are still hard problems, not `extends` problems.

---

## Q14: What happens when you assign a struct with unexported fields to an interface? [TRICKY]

**Answer:**

**In one line:** Unexported fields do not change method set or satisfaction, but you still copy the whole struct, including unexported and mutex fields, when you pass by value, which is how subtle duplication bugs appear.

**Visualize it:**

```
type t struct { mu sync.Mutex; secret int }  // in package p

// Another package can only:
  v := p.NewT()  // not struct literal
  var i SomeIface = v   // copies ENTIRE `t` including unexported + mutex

go vet:
  "copy of lock" if you return by value, assign by value, range over slice of `t`...
```

**Key facts:**
- Whether fields are unexported is irrelevant to *interface implementation*, which is decided solely by the required *methods* (exported and unexported as needed) with correct names and signatures in package scope.
- Callers in other packages cannot use composite literals to fabricate the struct, but the author can; exported constructors are the public construction path.
- Assigning a struct `T` to an `interface` with static type `T` (value interface) *copies* the struct into the `iface`’s `data` word, duplicating *all* fields, including a `sync.Mutex` or other "must not copy" types, which `go vet` / `copylocks` can flag.
- `reflect` can read unexported fields in many cases, but you cannot *set* them from another package; the copy-whole-value issue is a separate, practical bug class.
- Method export and field export are orthogonal: "private" governs *who can name* fields, not bit duplication, so use pointers, avoid blind value copies to interfaces, or `Clone` when copies are valid, and mind slices in structs (shared backing) and reflection-based serializers.

**Interview tip:** Lead with the mutex-copy angle, `go vet`, and the danger of copying types that contain `sync.Mutex`.

> [!example]- Full Story: Hidden bytes move with the value
>
> **The problem:** A team wraps sensitive state in a struct and passes it to APIs as `interface{}` or a domain interface, thinking private fields are the whole story, but a mutex inside the value exists in two copies with broken invariants, or a large internal buffer is duplicated unexpectedly.
>
> **How it works:** The language still lets the assignment happen because method export and field export are separate: privacy governs naming in source, not bit duplication on copy, and copy happens when a value-typed `T` is stored in an interface or passed by value, which is the same `iface` "box" copy story as elsewhere.
>
> **What to watch out for:** Slices in structs still share backing arrays on shallow copy, mutexes on deep structural copies, and reflection-based serializers that appear to duplicate state across packages without using constructors.

---

## Q15: How do you enforce that a type implements an interface at compile time? [COMMON]

**Answer:**

**In one line:** Add a no-op `var` assignment of your pointer type to the interface, `var _ I = (*T)(nil)`—if methods drift, the compiler errors at package init time, not in production.

**Visualize it:**

```
var _ io.Writer = (*myWriter)(nil)
      │   │         └── *myWriter may be nil pointer value; no runtime effect
      │   └────────── must be assignable: *myWriter has Writer methods
      └────────── blank identifier: package-level, discarded name

if method missing:  cannot convert (*myWriter)(nil) to io.Writer
                      ▼
                 compile error listing missing method(s)
```

**Key facts:**
- The `var` form uses only assignment compatibility: no allocation, and a typed nil `*T` is enough to stand in for a value of `*T` in the static check; the blank id discards the name while keeping the *check* (often beside the type or in `doc.go`).
- The compiler must prove the type is assignable to `I` using only method signatures, like any other assignment, and for `*T` a nil value still carries the type for method lookup with zero runtime cost for the idiom.
- The pattern is most valuable when the interface is defined elsewhere (`io.Reader` or a company port) and refactors could silently drop a method; `nil` is not special to type checking beyond assignability, so you get a pure compile-time proof without needing a nontrivial `func init` for this check.
- You can use `var _ I = T{}` when the interface is satisfied by a value (no pointer-only methods), but many APIs use `*T` when pointer receivers dominate; wrong `T` versus `*T` in the `var` can "pass" while real assignment paths still cannot use `T`.
- This enforces *assignability*, not full behavioral correctness: match pointer versus value to the real method set you use in production.

**Interview tip:** Show you use this pattern in real code for compile-time contract checks.

> [!example]- Full Story: The assignment that should never run
>
> **The problem:** A large refactor renames a method on `*UserRepository` and every call site in the same package updates, but you forget a cross-package `Database` `interface` you used to implement in tests only, nothing references it via normal code anymore, and `go test` in some packages does not re-touch that file, so the drift is silent.
>
> **How it works:** The idiom is `var _ Storage = (*UserRepository)(nil)`-style: the compiler *must* prove `*UserRepository` can be used wherever `Storage` is expected, just like any assignment, without needing a real `UserRepository` value because `nil` of type `*UserRepository` still enables method lookup, so you get a pure compile-time proof of assignability, not deep semantics, and you must pick `*T` versus `T` to match the interface’s method set.
>
> **What to watch out for:** Assignability is not full behavioral testing, and wrong `T` versus `*T` in the `var` line can "pass" while real assignments still fail elsewhere.

---

> Back to main note → [[Go Type System & Value Semantics]]
