# T01 Go Type System & Value Semantics — Revision Card

> Drill-down from [[Daily Revision]] | Full notes → [[T01 Go Type System & Value Semantics]]
> Q&A bank → [[questions/T01 Go Type System - Interview Questions]]

---

## Recall Grid (answer each, then check)

| # | Prompt | Check |
|---|--------|-------|
| 1 | Interface satisfaction | Structural (implicit): implement methods, no `implements` keyword |
| 2 | `type T int` vs `type T = int` | Defined type (new name, own method set) vs alias (same type) |
| 3 | Method set for `T` vs `*T` | `T`: value receivers; `*T`: value + pointer receivers (for that named type) |
| 4 | Zero value | Every type has a default; enables predictable initialization |
| 5 | “Nil interface” gotcha | `interface` value is `{type, data}`; typed nil `*T` in interface is non-nil |
| 6 | Embedding | Composition/delegation; promoted methods, not class inheritance |
| 7 | API shape | “Accept interfaces, return concrete structs” (common idiom) |
| 8 | `comparable` | Maps/slices/funcs are not comparable; most others are (with rules for structs) |
| 9 | Compile-time interface check | `var _ Iface = (*Concrete)(nil)` to assert *Concrete implements Iface |

---

## Core Visual

```
  nil interface                    typed-nil pointer in interface
  ┌──────────┬────────┐            ┌──────────┬────────┐
  │ type=nil │ data=? │  true nil  │ type=*T  │ data=nil (typed nil *T)
  └──────────┴────────┘            └──────────┴────────┘
       (interface value is nil)         (interface value is NOT nil)
```

---

## Top Interview Questions (quick-fire)

**Q: A concrete type T has value- and pointer-receivers. What implements an interface?**
Value `T` implements with methods whose receiver set is compatible; if only `*T` has the method, you need a `*T` in the interface slot. Pointers to T get both T and *T method sets (with usual rules).

**Q: When is a nil `error` or nil pointer still “non-nil” in an `interface{}`?**
The interface value holds a dynamic type and data. A `(*T)(nil)` assigned to an interface is typed-nil: `data` is nil but `type` is `*T`, so `i != nil` can be true.

**Q: What is structural typing?**
A type satisfies an interface if it has the required methods, by name and signature, without an explicit relationship declaration. That is how Go polymorphism works.

---

## Verbal Answer (say this out loud)

> "Go is statically typed with structural typing for interfaces. Types have an underlying type, zero value, and method set. Value T's method set only includes value receivers; *T gets both. Interfaces are two-field structs {type, data}. A typed nil pointer assigned to an interface is non-nil. Embedding is composition/delegation, not inheritance."

---
