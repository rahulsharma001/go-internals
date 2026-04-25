# T11: Interface Internals (iface & eface) — Interview Questions

> Deep-dive pack for [[T11 Interface Internals (iface & eface)]]. Each item uses: **C** = compact; **+D** = layered **accordion** (full story). All questions link the hub note.

**Hub:** [[T11 Interface Internals (iface & eface)]]

---

## 1. "What is the internal representation of a Go interface?" [COMMON]

**In one line (C):** A word pair: **dynamic type** + **dynamic data**; non-empty interfaces also go through an **`itab`** that carries **method dispatch** metadata.

**Visualize (ASCII):**

```text
  any/eface:  [ _type | data ]      iface:  [ itab* | data ]
```

**Key facts:** `eface` for empty iface; `iface` for methods; `data` is pointer or inline bits for small values.

**Interview tip:** Draw the two words, say **itab** only for **non-empty** interface—shows you know there are **two** representations.

<details>
<summary><strong>Full story (+D)</strong></summary>

The compiler represents `interface{...}` and `any` as **`runtime.eface`**: a pointer to the **concrete** type’s `runtime._type` and a data word. For an interface with **methods** (`io.Reader`, `fmt.Stringer`), the value is **`runtime.iface`**: a pointer to **`runtime.itab`** (linking the **interfacetype** to the **concrete** `_type` and providing **`fun` slots** for calls) and the same data word. The data word often points to the **heap-allocated** value, but small scalars can live **in-place** depending on size and version. Stating “interface is just a `void*`” is **wrong** for Go: there is **always** type information in the first word (for `eface` directly `_type`, for `iface` via `itab` that references types).

**Links:** [[T11 Interface Internals (iface & eface) - Visual Map]] · [[T11 Interface Internals (iface & eface) - Simplified]]

</details>

---

## 2. "What's the difference between iface and eface?" [COMMON]

**In one line (C):** **`eface`** = `any` (type + data only). **`iface`** = interface with methods ( **`itab`** + data ).

**Visualize (ASCII):**

```text
  eface:  type + data          iface:  (iface,concrete) itab  +  data
```

**Key facts:** Same **data** word idea; `iface` adds **method table** through **`tab`**.

**Interview tip:** Contrast in **one** sentence, then add **dispatch** = `itab.fun[i]`.

<details>
<summary><strong>Full story (+D)</strong></summary>

`eface` is the minimum needed to type-erase **any** single value: what type, where is the bit pattern. `iface` is required when the **compiler** must support **Interface method calls**: the `itab` encodes the **pair** (interface, concrete) and a **per-interface** function pointer array aligned to the **interface’s** method order (not the concrete type’s private method list order on the vtable in general). Storing a concrete value in `any` and later assigning to `io.Reader` can trigger building/finding the appropriate **`itab`**.

**Links:** [[T11 Interface Internals (iface & eface) - Revision]] · [[T11 Interface Internals (iface & eface)]]

</details>

---

## 3. "Explain the nil interface trap." [COMMON]

**In one line (C):** A **`nil` pointer of concrete type** placed in an **interface** still has a **non-nil** **type** **word**—so the **interface** is **not** `== nil`.

**Visualize (ASCII):**

```text
  var p *T = nil
  var i Iface = p     →   [ type = *T  |  data = nil word ]  ≠  [ nil | nil ]
```

**Key facts:** `== nil` on **interface** checks the **interface header**, not “logical nil” of the payload alone.

**Interview tip:** Name **“typed nil”**; fix with **`return nil`** (untyped) for `error` or set **var** to **untyped** `nil` in interface-typed return.

<details>
<summary><strong>Full story (+D)</strong></summary>

Interfaces are a **pair** of runtime words. A nil interface means **both** the **rtti/type slot** and **value** are nil **for the interface as a whole**. A `(*T)(nil)` has a **concrete** type *T* even when the pointer is zero; stored in `error` or `fmt.Stringer`, the **interface** is **non-nil** because **dynamic type** is set. This breaks `if err == nil` when functions return a **typed** nil variable. Fix: return **`nil` without a typed variable** of pointer type, or return **untyped** `nil` in interface-typed context.

**Links:** [[T11 Interface Internals (iface & eface) - Simplified]] · [[T11 Interface Internals (iface & eface) - Exercises]] (Tier 2)

</details>

---

## 4. "How does the itab work for method dispatch?" [ADVANCED]

**In one line (C):** `itab` links **(interface, concrete type)**; **`fun[i]`** is the **code pointer** for the **i-th interface method** at call sites.

**Visualize (ASCII):**

```text
  itab → fun[0], fun[1] ...   ;   call: iface.data as receiver + fun[k]
```

**Key facts:** Order follows **interface** method order; **not** a naive C++ vtable of the **concrete** type alone.

**Interview tip:** Say **“per-pair cache”** and **indirect** call through `fun` + **receiver** in `data`.

<details>
<summary><strong>Full story (+D)</strong></summary>

When the compiler compiles `var r io.Reader = f; r.Read(b)`, the **concrete** `Read` to invoke depends on `f`’s **dynamic** type. The **iface**’s `tab` points to an `itab` that has already matched **`io.Reader`** to that concrete’s **implementation** of `Read`, storing the **right** function pointer. Dispatch is: load **`itab`**, read **`fun[slot-for-Read-in-io.Reader]`**, pass **data** as the receiver. The runtime may **build** the `itab` on first use and **insert** it into a **cache** (hash/lookup by `(interfacetype, concrete _type)`) for reuse. **Wrapper** and **embed** cases have additional indirection, but the **image** of “slot in `itab`” remains the mental model.

**Links:** [[T11 Interface Internals (iface & eface) - Visual Map]] · [[T11 Interface Internals (iface & eface)]]

</details>

---

## 5. "How does structural typing differ from nominal typing?" [COMMON]

**In one line (C):** **Go:** types **satisfy** interfaces if **method sets** **match**—**no** `implements` clause. **Nominal:** you **declare** implementation by **name** (e.g. Java `implements`).

**Visualize (ASCII):**

```text
  structural:   methods?  ──yes──►  satisfies
  nominal:      named?    ──yes──►  implements
```

**Key facts:** Duck typing **at compile time**; **unrelated** packages can match.

**Interview tip:** One sentence each; mention **safety** is still **static** in Go (compiler checks).

<details>
<summary><strong>Full story (+D)</strong></summary>

Structural typing (Go’s **implicit** interface satisfaction) decouples **definition** of the interface from the **definition** of the implementing type. Any named type with a superset of **required** **methods** with **matching** **signatures** works. Contrast: Java/C# tie implementation with **declarations**; Go avoids **import cycles** and **skeleton** `implements` lists at the type definition site. The **itab** is then **runtime** evidence that a **concrete** type **at that moment** is known to work for a **given** interface in this program—built when you **assign** to the interface.

**Links:** [[T11 Interface Internals (iface & eface)]]

</details>

---

## 6. "What happens when you type-assert without comma-ok?" [COMMON]

**In one line (C):** If the **dynamic type** is **not** the asserted one (or the **assertion** is **invalid**), the program **panics** at that point.

**Visualize (ASCII):**

```text
  v := x.(T)   ──type mismatch──►  panic: interface conversion
```

**Key facts:** **Two-value** form is the **only** in-expression **non-panicking** check.

**Interview tip:** Say: same as an out-of-range index — single-form assertion panics on failure.

<details>
<summary><strong>Full story (+D)</strong></summary>

Type assertion reifies the **concrete** type inside an `interface` value. The single-result form is **intended** when the **invariant** is “this *must* be a `*bytes.Buffer` here.” The two-result `v, ok :=` form compiles the same test but **returns** `ok == false` instead of **unwinding** via panic, allowing **defensive** code at boundaries (parsers, `plugin` backends, `encoding/json` with `any`). **Type switch** is the **multi**-case form of the same test.

**Links:** [[T11 Interface Internals (iface & eface) - Simplified]] · [[T11 Interface Internals (iface & eface)]]

</details>

---

## 7. "Can you compare two interface values?" [TRICKY]

**In one line (C):** **Yes, with rules:** same **dynamic type** and `==`-defined for **values**; **mismatched** types → `false`; **uncomparable** **dynamic** value (e.g. **slice** map key style) → **panic**.

**Visualize (ASCII):**

```text
  a == b   →  type(a) == type(b)  ?  value(a) == value(b)  : false
            (or panic if not comparable)
```

**Key facts:** `interface` holding **uncomparable** inner value makes **`==` on interfaces** **panic** when that branch is **reached**—not a compile error.

**Interview tip:** Mention **NaN**-like cases for `float` inside interface, and **slice** in interface **panic**.

<details>
<summary><strong>Full story (+D)</strong></summary>

Interface comparison is **dynamic** twice: the **concrete** types must be **identical** (if not, result is `false` without panic), and then the **concrete** values are compared. If the **dynamic** type is **uncomparable** (slice, map, functions—mirroring map key rules in spirit), the comparison **panics** when evaluated. `nil` interface compares as usual only when both **headers** are nil. Mixed-interface assignment does not change: **concrete** type comes from the **value** in the right-hand **interface** at the time of comparison.

**Links:** [[T11 Interface Internals (iface & eface) - Revision]] · [[T11 Interface Internals (iface & eface)]]

</details>

---

## 8. "How does itab caching work?" [ADVANCED]

**In one line (C):** The runtime **reuses** or **creates** an `itab` the **first** time a **(interface, concrete)** pair is needed; **later** **assigns**/conversions **hit** the **cache**.

**Visualize (ASCII):**

```text
  (iface type, conc type)  ──lookup──►  existing itab?
                              │ no          │ yes
                              ▼ build        ▼ reuse
```

**Key facts:** **Amortized** `O(1)` for steady-state programs with fixed type combinations.

**Interview tip:** “Like *interning* a pair of types”—and avoid saying “vtable” without tying it to the interface + `itab`.

<details>
<summary><strong>Full story (+D)</strong></summary>

Constructing an `itab` requires the runtime to (1) **verify** the concrete’s **method set** is **a superset** of the interface, (2) **fill** `fun` with the **correct** **code** addresses in **interface** order, (3) **store** **hash/flags** for **quick** type checks. That work is **done once** per **pair** in a given binary’s execution, then **cached** in a **global** structure (implementation details: hash table / intrusive list, change between Go versions). **Generics** and **`interface` calling** in tight loops are **fast** in part because **itab** identity is **stable**.

**Links:** [[T11 Interface Internals (iface & eface) - Visual Map]] · [[T11 Interface Internals (iface & eface)]]

</details>

---

## 9. "What is the method set of T vs *T for interface satisfaction?" [COMMON]

**In one line (C):** Method set of **`T`** = all methods with **receiver** `T`; method set of **`*T`** = methods with receiver **`*T` or** **`T`**.

**Visualize (ASCII):**

```text
  (T)   foo()   on T?   yes.   (*T) bar()  on T value?  no.
  (*T)  foo+bar
```

**Key facts:** **Pointer** receiver methods **are not** in **`T`’s** set—so `var x T` may **not** satisfy if only `*T` has the method you need.

**Interview tip:** End with: pass `&x` (or a pointer variable) so the method set with pointer receivers actually satisfies the interface.

<details>
<summary><strong>Full story (+D)</strong></summary>

The spec defines method sets precisely. A value of type `T` cannot be used to call `*T`-receiver methods; those methods are not in `T`’s method set. So if only `*T` implements the interface, you need an `*T` (often `&x`). If the interface is covered by `T`’s value methods, a `T` value is enough. `T` and `*T` are different for satisfaction—compiler errors are not fixed by the runtime: no `itab` can save a type that does not match at compile time.

**Links:** [[T11 Interface Internals (iface & eface) - Revision]] · [[T11 Interface Internals (iface & eface)]]

</details>

---

## 10. "When does boxing an interface value cause heap allocation?" [ADVANCED]

**In one line (C):** **Often** when the **concrete** value is **too large** to **fit** the **data** **word** **inline** or is **not** a **trivial** **scalar** layout the compiler can **squelch** into the interface (implementation limits).

**Visualize (ASCII):**

```text
  small int ── maybe inline  │  big struct, string, slice, iface-in-iface  ── often heap
```

**Key facts:** Escape analysis still rules; not every `interface` conversion allocates on every run. A ~**16 byte** in-register threshold is a common *rule of thumb*—confirm with your Go version and `-gcflags=-m` escape output.

**Interview tip:** Say: large or escaping values end up *behind* the `data` word as a pointer; for hot paths, read escape reports and disassembly, not blog numbers.

<details>
<summary><strong>Full story (+D)</strong></summary>

The interface header is small; large values are not fully inlined in the `data` word, so the compiler may heap-allocate the concrete and store a pointer in `data`. Small values (e.g. `int`, a pointer) may use the word without an extra box. `string` and `slice` in an interface are header-shaped, not full backing arrays. For production, validate with `pprof` and escape analysis, not copy-pasted “always N bytes” from older posts.

**Links:** [[T11 Interface Internals (iface & eface) - Revision]] · [[T11 Interface Internals (iface & eface)]]

</details>

---

## 11. "Why should you avoid pointer to interface (*io.Reader)?" [TRICKY]

**In one line (C):** An interface is already a small *fat pointer* (type + data); `*io.Reader` adds a useless extra indirection and muddies `nil` and API clarity.

**Visualize (ASCII):**

```text
  f(io.Reader)     ✓  clear        f(*io.Reader)  ✗  almost never what you want
```

**Key facts:** You rarely need a pointer to an interface value; pass `io.Reader` or a concrete `*T` (or `any`) instead.

**Interview tip:** Accept `io.Reader` (or a concrete `*bytes.Buffer`), not `*io.Reader`.

<details>
<summary><strong>Full story (+D)</strong></summary>

`*io.Reader` points at an interface *value* (type + data), not the concrete reader. Call sites want `io.Reader` or a concrete `*T` that *implements* it. Pointers to `interface{}` only show up in rare reflection/encoding code paths; for normal libraries, they confuse reviewers and do not add expressiveness.

**Links:** [[T11 Interface Internals (iface & eface)]] · [[T11 Interface Internals (iface & eface) - Visual Map]] (cheat #12)

</details>

---

## 12. "How do type switches work internally?" [ADVANCED]

**In one line (C):** The compiler lowers each **case** to a **type** **guard** of the **interface**’s **dynamic** **type** (often as **a chain** of **comparisons** and **asserted** **extracts**).

**Visualize (ASCII):**

```text
  switch v := x.(type)  →  if dyn == T1 { ... } else if dyn == T2 { ... } ...
```

**Key facts:** **No** **OO** **v-table** **dispatch**—**it’s** a **cascade** of **type** **match**; **`v`** **in** each **case** is **statically** the **concrete** **type** there.

**Interview tip:** Relate to **repeated** **comma-ok** in spirit; **order** of **cases** **matters** for **nils** in **interfaces**.

<details>
<summary><strong>Full story (+D)</strong></summary>

`switch x.(type)` is syntactic sugar for a series of type tests on the same dynamic value. Each arm binds a name to the unwrapped value at the concrete type without writing `v, ok := x.(T)` manually every time (but under the hood it is still a runtime type check per case). In Go 1.18+ you may see similar patterns on type parameters; for classic “iface internals” interviews, describe the interface type-switch and dynamic-type checks, not the generic lowering.

**Links:** [[T11 Interface Internals (iface & eface) - Simplified]] · [[T11 Interface Internals (iface & eface)]]

</details>

---

## Index

| # | Tag |
|---|-----|
| 1—3, 5, 6, 9 | [COMMON] |
| 4, 8, 10, 12 | [ADVANCED] |
| 7, 11 | [TRICKY] |

**Hub (again):** [[T11 Interface Internals (iface & eface)]]
