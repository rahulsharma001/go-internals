# T02 Go Memory Allocation & Value Semantics — Revision Card

> Drill-down from [[Daily Revision]] | Full notes → [[T02 Go Memory Allocation & Value Semantics]]
> Q&A bank → [[questions/T02 Go Memory Allocation - Interview Questions]]

---

## Recall Grid (answer each, then check)

| # | Prompt | Check |
|---|--------|-------|
| 1 | Stack alloc vs heap alloc (ballpark) | Stack ~1–2ns; heap ~25–50ns+ (allocator path) |
| 2 | Escape to heap: typical triggers (4) | Return addr of local; grow slice/map; assign to `interface{}`/wide interface; value escapes to another goroutine or upvalues |
| 3 | How does Go pass arguments? | Always pass-by-value (copies, including struct/slice header) |
| 4 | Slice header size and fields (64-bit) | 24 bytes: `ptr` + `len` + `cap` |
| 5 | Initial goroutine stack | Small (e.g. 2–8KB range); grows on demand |
| 6 | `GOGC` default | 100 (heap growth vs live heap ratio) |
| 7 | `GOMEMLIMIT` | Soft cap on heap; GC works harder to stay under it |
| 8 | `sync.Pool` | Cleared on GC; use for reuse, not as a cache with lifetime guarantees |
| 9 | Latency: mark assist vs STW | App assists GC under allocation pressure; often bigger issue than short STW |
| 10 | `new(T)` and heap | Does not by itself “force” heap; escape analysis still applies |

---

## Core Visual

```
  Per goroutine                         Process-wide
  ┌──────────────┐                    ┌─────────────────────────┐
  │   STACK      │  escape?        │  HEAP (GC: mark/sweep)   │
  │  auto-free   │ ───────────►   │  shared, ~25-50ns alloc   │
  │  ~1-2ns      │  return &local   │  mark assist on hot path  │
  │  LIFO        │  interface box   │  sync.Pool evicted on GC  │
  └──────────────┘  closure/cross-g  └─────────────────────────┘
  Checklist: return pointer to local? to interface? grows? another goroutine?
```

---

## Top Interview Questions (quick-fire)

**Q: How does escape analysis work?**
The compiler asks whether a value’s address can outlive its lexical scope. If yes, the value is allocated on the heap. It is a static, compile-time decision.

**Q: Slices are passed by value—what does that mean in practice?**
The slice header (ptr, len, cap) is copied, but the backing array is shared. Mutating `s[i]` in a callee is visible to the caller; `append` may reassign only if the caller’s capacity allows sharing.

**Q: How do you reduce GC pressure?**
Profile (`pprof`, traces) first, then: fewer heap allocations, `sync.Pool` for reuse, value semantics to avoid indirection, pre-size slices, tune `GOMEMLIMIT`/`GOGC` for your SLOs.

---

## Verbal Answer (say this out loud)

> "Go is strictly pass-by-value. The compiler uses escape analysis to decide stack vs heap. Stack is ~1-2ns and auto-freed; heap is ~25-50ns and needs GC. Mark assist (not STW) is the real latency killer. Reduce GC pressure: profile first, then sync.Pool, value semantics, pre-allocation, GOMEMLIMIT."

---
