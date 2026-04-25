# T11: Interface Internals (iface & eface) — Revision

> Spaced recall for [[T11 Interface Internals (iface & eface)]].

---

## 10-row recall grid

| # | Topic | You recall (row prompt) |
|---|--------|-------------------------|
| 1 | **eface fields** | `type` pointer + `data` word (concrete type + value pointer / scalar bits) — `any` / empty iface |
| 2 | **iface fields** | `itab` pointer + `data` — non-empty interface |
| 3 | **itab purpose** | Cache/link **(interface type, concrete type)** + **method fn slots** for dispatch + type info |
| 4 | **nil interface condition** | Interface value is nil only if **type word is nil** (and per runtime invariants, data is nil) — *typed nil breaks `== nil`* |
| 5 | **Method set `T` vs `*T`** | Value `T` gets methods with `T` receiver; `*T` gets both `*T` and `T` receivers (synthesized) — pointer receiver methods not on `T` value for satisfaction |
| 6 | **Type assertion: safe vs unsafe** | `v, ok := x.(T)` safe; `v := x.(T)` panics on failure |
| 7 | **itab caching** | Runtime reuses or builds `itab` for given **(interface, concrete)** so repeated conversions/dispatch are cheap |
| 8 | **Boxing / allocation (threshold)** | Small values may stay **in-place** in the data word; **larger** or **non**-scalar layouts often **heap**-allocate when placed in an interface (implementation-dependent size threshold) |
| 9 | **Structural typing (Go)** | **Implicit**: type satisfies interface if **method set** matches — no `implements` keyword |
|10 | **Interface comparison rule** | Two interface values are `==` if **identical dynamic types** and **comparable** dynamic values; **mismatched types** → `==` is false; **uncomparable** types inside (e.g. slice as dynamic value) **panic** at compare |

(Fill the middle column from memory, then open [[T11 Interface Internals (iface & eface) - Visual Map]] to verify.)

---

## Core visual: `iface` and `eface` side by side

```text
  eface (any / interface{})                iface (e.g. io.Reader)
  ┌───────────────────────┐                ┌───────────────────────┐
  │  _type  *runtime._type│                │  tab   *runtime.itab  │
  │  data   unsafe.Pointer│   (or word)   │  data  unsafe.Pointer│   (or word)
  └───────────────────────┘                └───────────────────────┘
         │    │                                    │    │
         │    └─→ concrete value                    │    └─→ concrete value
         └─→ concrete type descrip.                 └─→ itab: iface↔concrete, fn[]…
```

```text
  itab (conceptual)                fun[]  (per-interface function slots)
  ┌─────────────────────┐          ┌───┬───┬───┬───┐
  │ itab / type links   │   ────►  │f0 │f1 │f2 │...│
  │ cache next (impl.) │          └───┴───┴───┴───┘
  └─────────────────────┘
```

> Names (`_type`, `tab`, `itab` internals) follow runtime layout; exact struct fields are version-specific—**shape** is what matters for exams.

---

## Quick-fire (answer verbally — no notes)

1. **Why** is `var e error = (*MyError)(nil)` not equal to a bare `nil` `error`?
2. **In one breath:** what does the **itab** connect?
3. **When** does type assertion *without* `ok` crash?

**Verbal answer key (after you try):**

1. The `error` interface’s **type component** is `*MyError` (non-nil) even though the **data** pointer is `nil` — `err == nil` is false.
2. **Interface type** + **concrete type** (+ dispatch table) for a given **iface**-method call.
3. When the **dynamic type** is not the **asserted** type (or cannot be represented that way).

---

## Links

- Simplified: [[T11 Interface Internals (iface & eface) - Simplified]]
- Exercises: [[T11 Interface Internals (iface & eface) - Exercises]]
- Visual map: [[T11 Interface Internals (iface & eface) - Visual Map]]
- Interview: [[T11 Interface Internals (iface & eface) - Interview Questions]]
