# T07 Pointers & Pointer Semantics — Interview Questions

> Comprehensive interview Q&A bank for [[T07 Pointers & Pointer Semantics]].
> Sorted by frequency at top tech companies. Tags: [COMMON] [ADVANCED] [TRICKY]

---

## Q1: When should you use a pointer receiver vs a value receiver? [COMMON]

**Answer:**

**In one line:** Use pointer receivers when the method must mutate the receiver, when the type is large, when it holds a `sync.Mutex` (or other things that must not be copied), or when you need a consistent receiver identity across methods; use value receivers for small, immutable-ish types and when you explicitly want a copy.

**Visualize it:**
```
Value receiver:  (copy)  method(T)   →  original T unchanged unless returned
Pointer receiver:        method(*T)  →  same T in memory; can mutate; one mutex
```

**Key facts:**
- Pointer receiver: can modify fields; no large struct copy; same `*T` for all methods; required if any method needs `*T` and you want a cohesive API.
- Value receiver: copies `T` on every call; safe for tiny structs; `sync.Mutex` in `T` with value receivers = each copy has its own mutex (wrong).
- Consistency: mixed receivers on the same type confuse readers; pick one style per type when practical (often all pointers for non-tiny structs).
- Method sets: value-only methods live on `T`; pointer methods live on `*T`—this ties into interface satisfaction (see Q8).

**Interview tip:** Name the three classic reasons—mutation, size/copy cost, and mutex/sync state—then add “consistency and method set” to show you’ve thought about API and interfaces, not just memory.

> [!example]- Full Story: Pointer vs value receivers
> With `func (p *Point) Move()`, `p` is the same struct instance every time; `Move` can update coordinates without returning a new `Point`. With `func (p Point) WithX(x int) Point`, you get a copy, change `X` on the copy, and typically return it—fine for small immutable-style helpers.
> For a struct embedding `sync.Mutex`, a value receiver copies the mutex; two copies are two independent locks, so they no longer protect the same data (undefined behavior for locking the “wrong” copy). Large structs: value receivers copy the whole struct on the stack (or as an argument) each call—`O(n)` in struct size. Teams often use all pointer receivers for any struct that is not obviously tiny and copy-safe.
> Consistency: if `SetName` is `*User` but `Name()` is `User`, call sites mix value and pointer semantics; interfaces may only see part of the method set. Prefer a clear rule: e.g. “methods on `*User` for anything non-trivial.”

---

## Q2: Is Go pass-by-value or pass-by-reference? [COMMON]

**Answer:**

**In one line:** Go always passes by value: function parameters and assignments copy something—but that “something” may be a pointer (address) or a small header (slice, map, channel), so behavior can look like “reference” without pass-by-reference semantics.

**Visualize it:**
```
func f(x T)   →  f receives a *copy* of x
*int          →  copy of the address (two locals point to same int)
[]int         →  copy of struct { ptr, len, cap }  →  same backing array
map[K]V       →  copy of map header  →  same underlying map
```

**Key facts:**
- There is no C++-style pass-by-reference for parameters; you pass a copy of a pointer to mutate caller data through a pointer.
- Slices, maps, and channels are descriptors; copying the header does not copy the whole backing store.
- `map` and `slice` “sharing” is because two variables hold headers pointing at the same runtime object or array, not because Go passed by reference.

**Interview tip:** Say “pass by value” first, then immediately qualify: “values are passed, and those values are sometimes addresses or fat pointers”— interviewers want precision, not a slogan.

> [!example]- Full Story: Pass by value in Go
> In `func g(p *int) { *p = 1 }` and `var x int; g(&x)`, `g` receives a **copy** of the pointer `&x`. Both the caller and callee have a word-sized value; dereferencing mutates the same `int` because the **addresses** were copied, not the `int` twice.
> For `s := make([]int, 2); t := s; t[0] = 1`, `s` and `t` share the backing array because the slice value was **copied** (header only). Same idea for `m := make(map[string]int); n := m; n["a"]=1`—`m` and `n` are two map header values, one map. Saying “Go is pass by value” is correct; “everything is deep-copied” is false.

---

## Q3: What's the difference between new() and &T{}? [COMMON]

**Answer:**

**In one line:** Both give you a `*T` to heap-allocated zeroed memory; `new(T)` only zeroes, while `&T{...}` can set fields in one expression.

**Visualize it:**
```
new(Thing)     →  *Thing  (all fields zero)
&Thing{}       →  *Thing  (all fields zero)
&Thing{a:1}    →  *Thing  (a set, rest zero)   ←  only this style can initialize
```

**Key facts:**
- `new(T)` is rare in idiomatic code; `&T{}` or a constructor `NewThing()` is more common and readable.
- Both allocate; the compiler, not the spelling `new` vs `&`, is the main authority on where memory lives (see escape analysis).
- `var t T; p := &t` gives a `*T` to a *named* `t` (often stack if it doesn’t escape).

**Interview tip:** Mention that `new` cannot initialize fields, so `&T{Field: v}` (or a helper) is preferred when you need non-zero state.

> [!example]- Full Story: new() vs &T{}
> `p := new(int)` yields `*int` to a zero int. `p := new(MyStruct)` zeroes all fields. There is no `new` form that takes field initializers.
> `&MyStruct{Count: 1}` allocates a `MyStruct` with `Count: 1` and takes its address. Idiomatic Go rarely uses `new` for structs except when brevity matters (`return new(Thing)`). For `new([N]T)` you get a pointer to a zeroed array, which is sometimes handy.
> Stylistically, prefer composite literals and local helpers over `new` for clarity.

---

## Q4: What is escape analysis and how does it relate to pointers? [COMMON]

**Answer:**

**In one line:** Escape analysis is the compiler pass that decides whether a value’s memory can live on the stack (short-lived) or must move to the heap (escapes); taking or returning pointers often causes escapes because stack frames cannot outlive the function.

**Visualize it:**
```
Stack:  frame dies →  memory invalid  →  can't return &local  unless copied to heap
Heap:   survives   →  safe after return
```

**Key facts:**
- Pointers to stack variables cannot be returned to callers; if you return `*T` to local `T`, the compiler **escapes** `T` to the heap.
- Not every `&x` escapes—if `&x` only flows within the function and does not outlive the frame, it can stay stack-allocated.
- “Escape” ≈ “allocation may happen on the heap and be GC’d”—exact placement is up to the compiler and version.

**Interview tip:** Tie “returning pointers” to “outliving the stack” and name `-gcflags="-m"` as how you *verify* in code reviews or perf work.

> [!example]- Full Story: Escape analysis and pointers
> Local variables in a function normally live in that function’s stack frame. If you return `&x` where `x` is local, the address would dangle if `x` stayed on the stack—so the compiler allocates `x` on the heap instead (escape).
> Cycles, closures capturing variables, sending pointers on channels, storing pointers in global state, and interface boxing can all cause escapes. Escape analysis is **function-local** in spirit but the compiler may be conservative. Use `go build -gcflags="-m"` to see “moved to heap:” lines—useful for hot paths, not for micro-rules on every `&`.
> The relationship to pointers: pointers *expose* lifetimes. If a pointer’s referent must survive beyond the current frame, the referent can’t be stack-only; hence heap allocation and GC pressure when hot.

---

## Q5: Explain the nil interface trap with pointers. [COMMON]

**Answer:**

**In one line:** A non-nil `interface{}` (or other interface type) can still hold a **typed nil** pointer (`(*T)(nil)`), so `v == nil` is false even though `*T` is nil—compare the concrete value or use reflection/`errors.Is` patterns carefully.

**Visualize it:**
```
var p *T = nil
var i interface{} = p

i == nil  →  false  (interface has (type *T, data nil))
p == nil  →  true
```

**Key facts:**
- An interface value is a `(type, data)` pair; it is only `== nil` when both type and data are “absent” / untyped.
- Assigning `var p *T = nil` to an interface sets the **type** to `*T` and data to `nil`—**not** the same as an empty interface.
- Safe patterns: return plain `error` (not a concrete pointer type as error sometimes), or check `v == nil` for concrete `*T` before boxing, or use `reflect.ValueOf(i).IsNil()` when appropriate.

**Interview tip:** State clearly: “nil interface is not the same as interface containing a nil pointer”—then give the two-line `var p *T; var i any = p` example.

> [!example]- Full Story: The nil interface trap
> Go interfaces are not “just a pointer.” For `i` to be `nil`, the interface must have no dynamic type. A `nil *bytes.Buffer` and `var b *bytes.Buffer; var err error = b`—here `err` is **not** `nil` in the `error` interface because the dynamic type is `*bytes.Buffer` even when the data word is `nil` pointer.
> This often bites when returning a concrete `*MyError` that is `nil`: `return err` where `err` is `*MyError` and nil still wraps a type in `error`. **Fix:** return `error` without a typed nil, e.g. `if err == nil { return nil }` or use a `var` with static type `error`.
> Pointers: `var t *T = nil; var v interface{} = t` then `v == nil` is **false**—a classic gotcha in tests and APIs.

---

## Q6: Can you take the address of a map value? Why not? [TRICKY]

**Answer:**

**In one line:** No: map values are not addressable, because moving entries (grow/rehash) would invalidate the address—so you must use a temp variable, index again, or store pointers to values in the map.

**Visualize it:**
```
&m[k]  →  compile error: cannot take address of m[k]
```

**Key facts:**
- Map buckets move; a stable `*V` to `m[k]` would become unsafe.
- Workaround: `v := m[k]; ...; m[k] = v` or `map[K]*V` and mutate `*V`.
- You may take the address of a struct literal in a `map` composite literal in some *initialization* forms, but not `&m[k]` in general for lookup.

**Interview tip:** Lead with “not addressable, because implementation moves values,” then the practical fix: `*V` in the map or copy-out/copy-back.

> [!example]- Full Story: Map values and addresses
> Go’s map implementation may relocate stored values as the map grows. A pointer into the map’s internal storage would dangle or require expensive pinning; the language disallows it.
> Pattern for counting: `c := m[k]; c.N++; m[k] = c` (copy back). For large structs, store `*BigStruct` in the map. Some confusion exists around `&struct{}{}` in map literals (address of a composite literal) vs `&m[k]`—in interview, be crisp: you cannot do `&m[k]` for a lookup.
> This is a language rule tied to the moving representation, not a “reference vs value” accident.

---

## Q7: What happens when you copy a struct containing sync.Mutex? [ADVANCED]

**Answer:**

**In one line:** The mutex is **copied** as a value, producing two **independent** locks that must not be used to guard the same shared state—copying a locked mutex is also invalid—so the protected data is no longer correctly synchronized; use a pointer to one shared `struct` (or `*sync.Mutex` field) instead.

**Visualize it:**
```
a := T{ ... mutex m ... }
b := a   →  b.m and a.m are *different* mutexes (undefined if a.m was locked)
```

**Key facts:**
- `sync.Mutex` must not be copied after first use; vet/linter flags `go vet` **copylock**.
- Value receivers on structs holding mutexes copy the whole struct, including the mutex—dangerous.
- Idiom: `type Safe struct { mu sync.Mutex; ... }` and **always** use `*Safe` as the API, or embed `*sync.Mutex` in rare cases.

**Interview tip:** Say “copylock / two mutexes / not the same lock” in one breath, then `*T` API.

> [!example]- Full Story: Copying sync.Mutex
> A mutex is a small struct of runtime state. Copying `T` duplicates that state, so the two parts of the program think they hold different locks while sharing memory—data races. If you copy a struct while one lock is held, the copy’s mutex state is not valid the same way.
> **Lint:** `go vet` reports copying locks. **Design:** unexported `type service struct{ mu sync.Mutex; data ... }` and all methods on `*service`; no returning `service` by value.
> `sync` package comment: do not copy `Mutex` or `RWMutex` after use.

---

## Q8: How does method set affect interface satisfaction with pointers? [COMMON]

**Answer:**

**In one line:** The method set of type `T` includes only value receivers; the method set of `*T` includes both value and pointer methods—so `*T` can implement interfaces with pointer-receiver methods, but plain `T` may not, and assigning `T` to a variable of interface type can fail when the interface needs `*T` methods.

**Visualize it:**
```
Methods defined as (t T)    →  on T and *T
Methods defined as (t *T)   →  only on *T

var _ Interface = T{}   //  may be illegal if Interface needs *T method
var _ Interface = &T{} //  often works
```

**Key facts:**
- If all methods on the type are value receivers, both `T` and `*T` satisfy the same value-method interfaces in many cases, but addressable `*T` still matters for calling pointer methods.
- A `T` value in an interface is **not** addressable, so the compiler can’t call `*T` methods on it through the interface even if a pointer is “conceptually” there in some other API.
- Pointer receiver is common for “one big struct, many interface impls” for consistency and mutex reasons.

**Interview tip:** Draw the 2×2: receiver kind × value vs pointer concrete type, and when interface conversion works.

> [!example]- Full Story: Method sets and interfaces
> Spec: method set of `T` = all methods with receiver `T`; method set of `*T` = those with receiver `*T` **or** `T` (pointer receiver methods are not in `T`’s set, but `*T` gets both). So an interface that only has `Read() T` (value receiver) can be implemented by `T` without pointers; an interface with `Mutate() *T` only methods needs `*T` in the method set, so a bare `T` may not implement it.
> Gotcha: `var x S = S{}; var v fmt.Stringer = x` can fail if `String()` is on `*S` only, because the method set of `S` has no `String` when defined only on `*S`—`&S{}` works. Another: storing large structs as interface values; often people pass `&T` to get pointer stable identity and right method set.
> Consistency: if your type implements an interface, document whether `T` or `*T` is the intended type for assignment.

---

## Q9: What is a nil pointer dereference and how to prevent it? [COMMON]

**Answer:**

**In one line:** Reading or writing through a `*T` (or a method) when the pointer is `nil` **panics** at runtime—guard with `p != nil`, design APIs with constructors, and return `error` for missing state instead of silent nils when appropriate.

**Visualize it:**
```
var p *T
p.Field  →  panic: runtime error: invalid memory address or nil pointer dereference
```

**Key facts:**
- `panic` is not recoverable in normal “errors as values” code paths; prefer nil checks in hot paths, or invariants.
- `nil` map read is safe; `nil` slice is safe; `nil` pointer method call can call `*T` method with `nil` receiver (allowed if the method checks `t == nil`—e.g. `error` on `*PathError`).
- Defense: nil checks, constructors (`NewT()` that returns non-nil invariants), avoid returning bare pointers to optional fields when `error` fits.

**Interview tip:** Mention that **methods** can be defined on `*T` with a nil receiver if they handle it—`(*BigInt).String()`-style—so “nil pointer” is not always immediate panic, only *field access* or bad assumptions.

> [!example]- Full Story: Nil pointer dereference
> The CPU cannot load from address 0 (or a nil `*T` is not 0 in all cases, but the pointer value is not a valid object). Field access and many operations assume a real object. Hence panic.
> **Optional pointers:** use `*T` as “optional T” and check before use, or `if v, ok := opt.Unwrap()`. `sync/atomic` and unsafe aside, the safe pattern is check-then-use.
> **error pattern:** if a function can fail, return `(*Result, error)`; don’t document “nil means error” and then also dereference without a check. **Constructors** return `*Client` with internal state set so downstream code assumes non-nil, or return `error` for invalid config.
> `recover()` exists for real panics; business logic should not use panic for control flow. Nil receivers: `func (b *Buffer) Len() int { if b == nil { return 0 } ... }` is idiomatic in stdlib in limited cases.

---

## Q10: What's the difference between *[]int and []*int? [TRICKY]

**Answer:**

**In one line:** `*[]int` is a **pointer to a slice** (one `[]int` value you can reassign the whole thing through); `[]*int` is a **slice of pointers to ints** (each element is an `*int`, not contiguous `int` layout).

**Visualize it:**
```
*[]int:   s →  []int header → [a b c]    (rebind entire slice: *s = other)
[]*int:  [p0, p1, p2]  →  each points to a distinct int
```

**Key facts:**
- `*[]int` is occasional (JSON unmarshaling, optional slice field, in-place re-slice in helpers); you rarely need it for everyday code.
- `[]*int` is common for “slice of things allocated elsewhere,” nullable columns, or avoiding large struct copies; order is slice order, data is all over the heap.
- `[]int` vs `*[]int`: indirection to allow `nil` meaning “not present” vs empty slice `[]int{}` meaning present-but-empty (API design choice).

**Interview tip:** Contrast in one pass: indirection to the slice as a **whole** vs many **int pointers** as elements; mention JSON `omitempty` *pointer to slice* sometimes.

> [!example]- Full Story: *[]int vs []*int
> `*[]int p`: `len(*p)`, `(*p)[i]`, and `*p = append(*p, x)`-style (careful: remember to write back in some patterns). The pointer is useful when a function reslices from the “outside in” and must replace the whole header (less common; often return `[]int` instead).
> `[]*int`: each `*int` may be different allocation; good when sharing elements across structures or representing sparse/pointer-rich graphs; bad for cache locality of raw ints.
> Confusion: `*[]int` is not “slice of pointers” at all. Read right-to-left: “pointer to slice of int” vs “slice of pointer to int”.

---

## Q11: When does returning a pointer from a function cause a heap allocation? [ADVANCED]

**Answer:**

**In one line:** When escape analysis determines the referent must **outlive** the function (or is shared in a way the stack can’t represent), the compiler **allocates on the heap**; returning `*T` to local `T` is the textbook escape.

**Visualize it:**
```
func f() *T { var x T; return &x }  //  x escapes → heap
func g() T  { var x T; return x  }  //  x return by value, typically stack
```

**Key facts:**
- `return &local` after `var local T` → `local` escapes (see Q4).
- Not every return of `*T` from `new` is “extra cost” in an obvious way; the key is *whether the compiler can place it on the stack*.
- `go build -gcflags="-m -m"` shows escape details; benchmark before assuming a problem.

**Interview tip:** Distinguish “**escape** to heap” from “`new` always means heap`”—both `new` and `&T{}` are subject to the same analysis in principle for locals.

> [!example]- Full Story: Heap allocation and returning pointers
> Stack allocation is cheap and cache-friendly, but stack slots die with the function. Any pointer to a local that’s returned, stored in a global, put on the heap-escaping channel send, or captured by a loop closure may force heap.
> Small `T` return by value: no pointer, no indirection, sometimes faster than pointer return for tiny structs; **pointers to huge structs** avoid copying the struct as a return value (but add indirection and GC). Micro-optimization: profile.
> The compiler can sometimes stack-allocate and pass interior pointers in limited cases, but for interview purposes: “returning pointer to local = escape” is the canonical line.
> `runtime` metrics and `GODEBUG` / `pprof` can show allocation counts in production tuning.

---

## Q12: Why should you avoid pointer to interface (*Saver)? [TRICKY]

**Answer:**

**In one line:** An interface value already **carries a pointer to concrete data**; `*io.Writer` adds confusing double indirection, rarely helps, and makes nil/type semantics even harder to reason about.

**Visualize it:**
```
w io.Writer  →  (itab, data)   //  data is often already a *concrete
var p *io.Writer  →  points to *that*  //  extra layer, no real win
```

**Key facts:**
- If you need “optional or mutable interface,” use `io.Writer` + zero value `nil`, or a struct field, not `*io.Writer` in public APIs.
- `[]interface{}` is already a recipe for reflection pain; `*interface{}` is rarer and worse.
- **Pointer to interface** is almost never the right public signature; accept `T` (interface type) or use generics, not `*T` when `T` is an interface.

**Interview tip:** Say: “interface is two words; it’s a fat pointer; `*` doesn’t add clarity”—cite “accept interfaces, return structs” and avoid `*error`/`*io.Reader` in signatures.

> [!example]- Full Story: Pointer to interface
> The FAQ-style guidance: do not use `*ReadWriter` as a type parameter or parameter type. If the caller has no concrete, pass `nil` `io.Reader`; if you need to swap implementation, use a struct holding `r io.Reader` and replace the field.
> `*io.Writer` could theoretically mean “pointer to a slot where an interface is stored” (e.g. mutating a field through reflection-like patterns), but in normal app code, it signals misunderstanding of the interface representation.
> **Generics** (`func F[T any](t T)`) and concrete types replace many abuses of `interface{}` and pointer-to-interface. For unit tests, pass `&fakeT{}` as `io.Writer`, not a pointer to an interface variable.
> `var w io.Writer; var pw *io.Writer = &w` is legal but `pw`’s use is contrived; **don’t** design APIs that require users to juggle that.

---

_End of T07 Pointers & Pointer Semantics Q&A bank._
