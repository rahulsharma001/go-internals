> This note has been superseded by [[Select in Go]].

# T17 Select Statement Internals — Revision Card

> Drill-down from [[Daily Revision]] | Full notes → [[T17 Select Statement Internals]]
> Q&A bank → [[questions/T17 Select Statement Internals - Interview Questions]]

---

## Recall Grid (answer each, then check)

| # | Prompt | Check |
|---|--------|-------|
| 1 | What implements `select` at runtime? | `runtime.selectgo` |
| 2 | Two scratch slices — roles? | `pollorder` shuffle (fairness), `lockorder` address sort (locks) |
| 3 | Multiple ready cases — who wins? | First ready along **shuffled** `pollorder` |
| 4 | Why lock channels by sorted address? | Total order prevents AB/BA deadlock |
| 5 | What does `default` set logically? | `block=false` — return without `gopark` |
| 6 | Nil channel case effect? | Omitted — never ready |
| 7 | Pass 2 vs pass 3 one-liner? | Pass2 enqueue sudogs + park; pass3 dequeue losers after wake |
| 8 | Empty `select {}`? | Blocks forever (`block`) |
| 9 | Perf pitfall? | `O(n)` sort/lock with huge case count |
| 10 | Balanced consumption guaranteed? | No — readiness drives winners |

---

## Core Visual

```
        cheaprandn shuffle
src cases ───────────────► pollorder (random inspection order)
                    │
                    ▼
              heap sort by &hchan
                    │
                    ▼
              lockorder + sellock
                    │
                    ▼
pass1 scan pollorder → first success? → done
                    │ no
                    ▼
          block? ─no──► unlock + default (-1)
            │
           yes
            ▼
         sudogs + gopark → wake → pass3 cleanup
```

---

## Top Interview Questions (quick-fire)

**Q: Multiple channels ready — determinism?**

Randomized `pollorder` — first ready in that order wins; **not** source priority.

**Q: Deadlock avoidance detail?**

Lock **`hchan`** mutexes in increasing pointer order via **`lockorder`**.

**Q: Try-send without blocking?**

`select { case ch<-v: ... default: ... }` — **`default`** path avoids parking.

---

## Verbal Answer (say this out loud)

> `select` lowers to **`selectgo`**, which builds **`scase` rows**, **shuffles** case indices for fairness, **sorts channels by address** to lock safely, then **pass 1** looks for immediate progress. If blocked and no **`default`**, **pass 2** attaches **`sudog`** waiters to **all** channels and parks once; **pass 3** cleans up after wakeup. **`default`** means **non-blocking** return. **Nil** cases vanish from consideration.

---
