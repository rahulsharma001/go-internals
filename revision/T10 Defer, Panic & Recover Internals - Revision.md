# T10 Defer, Panic & Recover Internals — Revision
#revision #go #defer #panic

Back to: [[T10 Defer, Panic & Recover Internals]]

---

## 10-row recall grid

| # | Topic | One-line hook |
|---|--------|----------------|
| 1 | **When are `defer` arguments evaluated?** | At the **`defer` statement**, not at run time of the deferred call. |
| 2 | **Order of many defers?** | **LIFO** — last registered runs first. |
| 3 | **Named return values** | Deferred closers can **write** to named `result` params; there is a **return / defer** interaction window. |
| 4 | **Where can `recover()` work?** | Only useful **while unwinding a panic** in the **current goroutine**, almost always from code executed **after** a **`defer`**. |
| 5 | **Goroutine isolation** | A panic in **G1** is not recoverable in **G2**; each goroutine **must** own its own `defer`/`recover`. |
| 6 | **`os.Exit` vs `defer`** | **`os.Exit`** **does not** run **deferred** functions — process stops; **returns** from `main` do. |
| 7 | **Open-coded defers** | Compiler inlines some defer setup **when possible** to avoid some heap defer records — **faster/leaner** hot paths. |
| 8 | **Panic “struct” (mental)** | Run-time records **value**, **link to next**, and stack/ABI glue while **unwinding** — think **chain of panic frames** while walking defers. |
| 9 | **Loop + single `defer` trap** | `defer` in a **loop** in one function = **N** deferred **calls** that **all** run at **function** exit — classic **leaks** and **late** work. |
| 10 | **What `recover()` returns** | The **`interface{}` value** passed to `panic`, or **`nil`** if not panicking (or if called outside valid unwind). |

**Full story for each row:** expand in [[T10 Defer, Panic & Recover Internals]].

---

## Core visual: defer stack + panic unwind

**Defer stack (LIFO, args already picked)**

```
defer C()   ─┐
defer B()    │  registration order A → B → C
defer A()   ─┘
  ... work ...
  return  →  run  C, then B, then A
```

**Panic unwind + recover point**

```
... normal ...
  panic(v)
      │
      ▼
 unwind stack, running defers (inner → outer)
      │
      ├─ defer: recover()  catches v  →  stop unwind, run rest of that defer, continue
      │
      └─ no recover → goroutine dies / fatal / program exit (unchained case)
```

**Where it lives in your vault:** same themes in [[T10 Defer, Panic & Recover Internals - Visual Map]] and [[T10 Defer, Panic & Recover Internals - Simplified]].

---

## 3 quick-fire questions (verbal only)

**Q1.** You `defer` three prints in order `1`, `2`, `3`. In what order do they execute at return?

**A1.** `3`, then `2`, then `1` (LIFO).

**Q2.** You call `recover()` in a helper that is **not** deferred, right after you imagine a child goroutine might panic. Does it work?

**A2.** No — **recover** only stops a **panic in the current goroutine** when called **during panic handling**, typically from a **deferred** function on that same unwinding stack.

**Q3.** Why is `defer os.Remove(tmp)` in a long handler sometimes paired with a warning about `os.Exit` in tests or `log.Fatal`?

**A3.** Any path that **exits the process** via **`os.Exit` / immediate fatal** **skips** defers, so **cleanup** might never run; normal **return** runs defers.

---

**Practice:** [[T10 Defer, Panic & Recover Internals - Exercises]] · **Interviews:** [[T10 Defer, Panic & Recover Internals - Interview Questions]]
