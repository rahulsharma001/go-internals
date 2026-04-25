# Arrays & Slice Internals — Revision Card

> Drill-down from [[Daily Revision]] | Full notes → [[Arrays & Slice Internals]]
> Q&A bank → [[questions/Arrays & Slice Internals - Interview Questions]]

---

## Recall Grid (answer each, then check)

| # | Prompt | Check |
|---|--------|-------|
| 1 | Slice header fields and total size? | unsafe.Pointer + len + cap = 24 bytes |
| 2 | Array vs slice: value type or reference? | Array = value type (full copy). Slice = value type header sharing backing array |
| 3 | What happens when append exceeds capacity? | New backing array allocated, data copied, old array eligible for GC |
| 4 | Why doesn't caller see appended elements? | Slice header copied by value, function's header updated locally |
| 5 | Growth formula below 256 cap? | Double (2x) |
| 6 | Growth formula above 256 cap? | newcap += (newcap + 768) / 4, smooth transition to ~1.25x |
| 7 | Three-index slice a[low:high:max] does what? | Sets cap = max-low, prevents append from overwriting shared data |
| 8 | nil slice vs empty slice? | nil: ptr=nil. empty: ptr=valid. Both: len=0, cap=0. JSON differs: null vs [] |
| 9 | Sub-slice memory leak and fix? | Sub-slice keeps entire backing array alive. Fix: copy() or slices.Clone() |
| 10 | make([]T, 5) vs make([]T, 0, 5)? | First: 5 zero elements. Second: empty, cap 5, ready for append |

---

## Core Visual

```
SliceHeader (24 bytes)
┌──────────────────┬──────┬──────┐
│ ptr *array       │ len  │ cap  │
└──────┬───────────┴──────┴──────┘
       │
       ▼
  Backing Array: [0][1][2][3][4][_][_][_]
                  ▲           ▲        ▲
                  ptr      len=5    cap=8

Append within cap:  writes to [5], len→6, SAME array
Append beyond cap:  NEW array [0][1][2][3][4][5][_][_][_][_]..., cap doubles
```

---

## Top Interview Questions (quick-fire)

**Q: What is the append trap?**
Slice header is 24 bytes copied by value. Append inside a function updates the local header's len (and maybe ptr if reallocated), but the caller's header is stale. Fix: always return the new slice and reassign at the call site.

**Q: How does sub-slicing cause memory leaks?**
`s2 := s1[2:5]` creates a header pointing into the same backing array. Even if s1 goes out of scope, the entire backing array stays alive because s2's pointer references it. Fix: `copy()` into a new slice.

**Q: When would you use an array over a slice?**
Fixed-size data known at compile time (SHA-256 = [32]byte, IP address = [4]byte). Arrays are value types, stack-allocated, no indirection, and comparable (can be map keys). Slices cannot be map keys.

---

## Verbal Answer (say this out loud)

> "A Go slice is a 24-byte header — pointer, length, capacity — that describes a window into a backing array. Passing a slice copies this header, so both copies share the same array. Append within capacity writes to the shared array; append beyond capacity allocates a new, larger array and copies data over — the caller's header becomes stale. The growth formula doubles below 256 elements and smoothly transitions to ~1.25x for large slices. Common traps: append not visible to caller, sub-slice keeping large arrays alive, and forgetting to nil pointer elements on delete."

---
