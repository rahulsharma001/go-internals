# T07 Pointers & Pointer Semantics — Revision Card

> Drill-down from [[Daily Revision]] | Full notes → [[T07 Pointers & Pointer Semantics]]
> Q&A bank → [[questions/T07 Pointers & Pointer Semantics - Interview Questions]]

---

## Recall Grid

| # | Prompt | Check |
|---|--------|-------|
| 1 | What is a pointer's size on 64-bit? | **8 bytes** always |
| 2 | What's the zero value of a pointer? | **nil** |
| 3 | What happens when you dereference nil? | **runtime panic** |
| 4 | Value receiver method set for `T`? | **value receiver methods only** |
| 5 | Method set for `*T`? | **both** value and pointer receiver methods |
| 6 | When does a pointer cause heap allocation? | when it **escapes** the function scope |
| 7 | Can you take address of map value? | **No** — map values are not addressable |
| 8 | What's the typed nil interface trap? | interface has **type field set** but **data is nil** — not a nil interface |
| 9 | Should you copy `sync.Mutex`? | **Never** — copied mutex has independent state |
| 10 | Go passes by value or reference? | **Always pass-by-value** |

---

## Core Visual

Pointer memory: `&x` yields an address; `*p` reads/writes through that address.

```
  stack                         (heap, if x escaped)
  ┌─────────────────┐            ┌──────────┐
  │  x  int  42     │            │  ...     │
  │  0x7fff_...     │            └──────────┘
  └────────┬────────┘
           │
  p := &x  │  p holds copy of address (8 bytes on 64-bit)
           ▼
  ┌─────────────────┐
  │  p  *int        │───*p───►  value at that address (42)
  │  0x7fff_...     │
  └─────────────────┘
```

- **`&x`**: address-of → pointer value (where `x` lives).  
- **`*p`**: dereference → the `int` (or type) that `p` points at.  
- A **nil** `p` still has a valid *type* (`*int`); **`*p` on nil** → panic.

---

## Top Interview Questions (quick-fire)

**1. When to use a pointer vs value receiver?**

Use a **pointer receiver** when the method must **mutate** the receiver, when the struct is **large** (avoid copying), or it holds a **mutex** or other **non-copyable** state. Use a **value receiver** for **small, immutable** types and when you explicitly want a copy per call.

**2. Is Go pass-by-reference?**

**No.** Go is always **pass-by-value**. Slices, maps, and channels are small descriptors passed by value; a **pointer** is passed by copying the **8-byte address**, which still lets callees mutate shared data through that address.

**3. What's the nil interface trap?**

A **typed nil** pointer stored in an interface has the interface’s **type field set** (e.g. `*MyType`) while the **data word is nil**. **`var i interface{} = (*T)(nil)`** is **not** equal to an **untyped nil** interface—`i == nil` is **false**. Code that only checks for nil on the interface value can be wrong.

---

## Verbal Answer (say this out loud)

Go uses pointers for indirect access — they're 8-byte addresses. Go is always pass-by-value; pointers share access by copying the address. Pointer receivers modify the struct and affect method sets: T has value-receiver methods, *T has both. Escape analysis moves data to the heap if a pointer outlives its function. Key traps: nil dereference panics, typed-nil interface, never copy mutex.

---
