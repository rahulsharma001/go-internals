# T09 Error Handling Patterns — Revision Card

> Drill-down from [[Daily Revision]] | Full notes → [[T09 Error Handling Patterns]]  
> Q&A bank → [[T09 Error Handling Patterns - Interview Questions]]  
> Exercises → [[T09 Error Handling Patterns - Exercises]]

---

## Recall Grid (10 rows)

| # | Prompt | Check |
|---|--------|-------|
| 1 | What is `error` in Go? | **Interface** with `Error() string` — **any** type can satisfy it. |
| 2 | Sentinel pattern | **Package-level** `var ErrX = errors.New("…")` — compare with **`errors.Is`**, not raw `==` on wrapped values. |
| 3 | `%w` in `fmt.Errorf` | **Wraps** inner error — preserves **unwrap chain** for `Is` / `As`. |
| 4 | `%v` in `fmt.Errorf` | **Formats** inner error as text; **no** `Unwrap` link — not for semantic wrapping. |
| 5 | `errors.Is` | Walks **unwrap chain** — tests **identity** to a **target** error (incl. sentinels). |
| 6 | `errors.As` | Walks **unwrap chain** — finds first assignable value into **target pointer** (**custom** types / interfaces). |
| 7 | Custom error types | Struct + `Error()`; often **pointer receiver**; use with **`errors.As`**. |
| 8 | Typed nil trap | `var p *T = nil; return p` as **`error`** → **non-nil** `error` (interface box holds type `*T`, value `nil`). |
| 9 | When to wrap? | **Layer boundaries** — add **context**; do **not** wrap if only **duplicating** or **leaking** sensitive detail. |
| 10 | `errcheck` | Static / vet-style helper — **flags ignored return values** (`_ = f()`), not your wrapping policy. |

---

## Core Visual: error wrapping chain (ASCII)

```
caller sees:
  "save profile: open file: permission denied"
        │
        ▼
  fmt.Errorf("save profile: %w", errInner)
        │
        ├─ Unwrap() ──► fmt.Errorf("open file: %w", errInner2)
        │                    │
        │                    └─ Unwrap() ──► os.PathError (or syscall errno wrapper)
        │
        v
errors.Is / As start here and follow Unwrap() links until match or end.
```

- **`Is`:** compares against **target** at each step (with optional internal equality rules for certain types).  
- **`As`:** tries **type assertion** at each unwrapped value into `**T`.

---

## Top Interview Questions (quick-fire, 3)

**1. `errors.Is` vs `errors.As` in one breath?**  
`Is` checks **value identity** to a **specific error** in the **chain**; `As` extracts the **first** value assignable to a **target type** (usually a `**Custom`).

**2. `%w` vs `%v`?**  
`%w` **preserves** an **unwrap** link for the chain; `%v` is **string formatting** of the child — fine for **logs**, not for **sentinel** / **As** **semantics** on that link.

**3. When does `err != nil` lie?**  
When `err` is a **non-nil interface** whose **dynamic type** is `*T` but **dynamic value** is **nil** — classic **typed nil** return. **Fix:** return **`nil` as `error`**, or use **`var e error`**, or return **`error` variable** of interface type that is **truly** unset.

---

## Verbal answer (say this out loud)

Go **`error` is an interface** — usually **sentinels** (named vars), **custom** structs with `Error()`, and **wrapping** via **`fmt.Errorf`…`%w`** to build a **chain**. Use **`errors.Is`** for “**is this exact situation** in the chain?”, **`errors.As`** to **recover a concrete type** for **fields**. **`%v` formats**; **`%w` links**. Beware the **typed nil** (`*T` `nil` **into** `error`). For robust code, use **`errcheck`**, and **wrap at boundaries** with **useful** context, not **noise or secrets**.

---

## Related

- [[T09 Error Handling Patterns]]  
- [[T09 Error Handling Patterns - Visual Map]]  
- [[T09 Error Handling Patterns - Simplified]]
