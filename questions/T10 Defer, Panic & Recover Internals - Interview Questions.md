# T10 Defer, Panic & Recover Internals — Interview Questions

#qa #go #interview

Back to: [[T10 Defer, Panic & Recover Internals]]

A compact bank of **defer, panic, and recover** questions in **Q1–Q12** order, tagged [COMMON], [ADVANCED], or [TRICKY].

**C + D (concise + deep):** each answer is layered — **In one line**, **Visualize it** (ASCII), **Key facts**, **Interview tip** — with a **collapsible Full Story** for the interview-length version.

---

## Q1: What are the three rules of defer? [COMMON]

**Answer:**

**In one line:** (1) Deferred call **arguments** are evaluated at the **`defer` statement**; (2) multiple defers in one function run in **LIFO** order; (3) defers run as part of **return/exit** from that function — **named** return values can still be read or **updated** in that window.

**Visualize it:**

```
defer f(a)  →  a evaluated NOW, f() not run yet
defer g()
defer h()   }  registration order: h, g, f from bottom to top; run order: f, g, h

return x    →  (if named) set results, then defers LIFO, then back to caller
```

**Key facts:**
- The spec says `defer` **schedules** a call; the **LIFO** order and the interaction with **returns** are defined by the language implementation you target.
- **Capture trap:** `defer f(x)` fixes `x` at defer time; `defer func() { use(x) }()` reads `x` when the deferred function **runs** (later).
- Defers on **inner** calls complete before **outer** frame finishes unwinding (stack order).

**Interview tip:** Memorize: **eager args, LIFO, named-return effect** — then draw LIFO. Mention the loop footgun (Q4) as a “related trap” if time allows.

> [!example]- Full Story: Three rules, no magic
>
> **The problem:** Candidates think deferred calls “run at the end with the **latest** value of every local” — only **closures** re-read variables; **argument** **lists** are **fixed** at `defer` time.
>
> **How it works:** The compiler **evaluates** the deferred call’s function value and **arguments** when `defer` executes, **enqueues** the invocation, and runs the queue in **LIFO** when the function **returns** (normally or while unwinding a panic in this goroutine). With **named** results, the compiler may spill into **named slots** and run defers in between — the famous `r =` overwrite pattern is a consequence, not a special rule about `int`.
>
> **What to watch out for:** Saying defers are “global reverse order for the **whole** program” — order is **per** **function invocation’s** **defer** chain; nested callees have their **own** lists that drain first on the way out.

---

## Q2: How does recover work and where must it be called? [COMMON]

**Answer:**

**In one line:** `recover()` only **stops a panic** when the goroutine is **unwinding** that panic and `recover` runs from **deferred** code (almost always) on **that same goroutine**; otherwise it returns `nil`.

**Visualize it:**

```
panic in G1  ──► unwind G1  ──►  defers on G1  ──►  r := recover() inside a defer  ✓

recover() in G2  X────  (cannot see G1's panic)
```

**Key facts:**
- If the goroutine is not panicking, `recover()` returns `nil`.
- The **innermost** defers run first during unwind; the **first** `recover` that is **allowed** sees the **active** panic and **absorbs** it.
- **Libraries:** prefer **`error` returns**; use `recover` in **safety** layers (HTTP middleware, per-goroutine wrappers, tests).

**Interview tip:** Say **same goroutine**, **during unwind**, **typically inside `defer`** — not “`recover` is Go’s `catch`” without those qualifiers.

> [!example]- Full Story: recover semantics and the unwinder
>
> **The problem:** `go f()` in `main` then `recover()` in `main` — the child’s `panic` is **not** visible to a `recover` in the parent; each stack is independent.
>
> **How it works:** The runtime records the **panic value** and walks this goroutine’s **deferred** calls. When a **deferred** function runs `recover()` **while** a panic is active on this `G`, `recover` returns that value and **stops** unwinding that panic; execution **continues** after that deferred function. Details are in the runtime’s panic handling and your tree’s `runtime` sources — in interviews, **G-locality** and **`defer`** are what matter. See [[T10 Defer, Panic & Recover Internals]].
>
> **What to watch out for:** Calling `recover()` in **non-deferred** code “right after a risky call” on the same goroutine but **not** in an unwind from **panic** — you get `nil` and a false sense of safety.

---

## Q3: What happens if a goroutine panics without recover? [COMMON]

**Answer:**

**In one line:** The panic **unwinds** that goroutine’s stack; if nothing **stops** it, that goroutine **dies**. Often the **whole process** exits (especially if the panic was in **`main`**, **`init`**, or is otherwise **fatal** to the program); a **server** that **recovers** per request may keep other goroutines **alive** depending on how it is built.

**Visualize it:**

```
go child()  →  panic  →  no recover on this G
       →  goroutine’s defers run; if still unhandled → G dies
       →  if main/init / fatal path → process abort + stack dump
       →  if only a worker G in a well-designed server → request fails, process may run on
```

**Key facts:**
- Distinguish **one goroutine ending** from **entire process exit**.
- **net/http**-style: wrap **handler** in **middleware** `recover` on **that** request goroutine so one **panic** does not kill the process (if nothing else re-panics).
- Panic values print via **`String`/`Error`** on **interfaces** — know the **nil pointer in interface** case.

**Interview tip:** Name **G death** vs **process death** in two sentences, then point to Q12 for servers.

> [!example]- Full Story: From panic to process exit
>
> **The problem:** Treating any `go` **panic** as “the whole app always dies” — sometimes yes, sometimes no; the **unhandled** panic **in `main`/`init`** case is the clearest full-process story.
>
> **How it works:** Each `go` has its **own** stack. Unwind runs **defers** on that stack only. If the panic is never **recovered**, the runtime **aborts** that goroutine’s panic handling path; in common setups an **unhandled** panic in **`main`/`init`** **terminates the program** with a dump. A **pool** of workers that each do `defer`+`recover` at the top can keep the process alive while one worker fails.
>
> **What to watch out for:** `sync.WaitGroup` + **unhandled** child panic: **Wait** can complete while a **sibling** **dies**—prefer **errgroup**, explicit **error** channels, or **recover** in each **long-lived** `go`.

---

## Q4: Explain the problem with defer inside loops. [COMMON]

**Answer:**

**In one line:** A `defer` in a **loop** in **one** function appends to **that function’s** defer list **N** times, so all **N** cleanups run only when the **function** returns (not each iteration) — causing **leaks** and **wrong** **timing**; fix with a **per-iteration** function scope or **explicit** `Close` in the loop.

**Visualize it:**

```
for i := 0; i < N; i++ {
    f, _ := os.Open(path)
    defer f.Close()   // registered N times; all run at ReadMany return
    // N files can stay open until the whole loop + rest of function finish
}
```

**Key facts:**
- Grows the **defer** chain with **N** entries; for **files/locks/DB rows**, resource lifetime becomes **O(scope of whole function)**.
- **Fix:** `func() { f, _ := open(); defer f.Close(); ... }()` per iteration, or `Close()` + error handling without `defer` in the loop.

**Interview tip:** One image — **N sticky notes on one door** that all fire when you **leave the house** (function), not when you **finish each errand** (iteration).

> [!example]- Full Story: Why the compiler does not do “per loop body”
>
> **The problem:** “I **meant** defer per **turn**” — but `defer` is tied to the **enclosing** function, not the loop, unless you add an **inner** `func`.
>
> **How it works:** Each `defer` **pushes** onto the current function’s **defer** stack. The stack **drains** on **return** (or when unwinding from panic) for **that** function. **N** iterations ⇒ **N** pending defers, **LIFO** order on exit (last opened **closes first** on function exit) — not “close after each file use.”
>
> **What to watch out for:** Same with **`defer m.Unlock()`** in a hot loop: you may hold the **lock** for the **entire** outer function, not the **iteration**.

---

## Q5: Can a parent goroutine catch a child goroutine's panic? [TRICKY]

**Answer:**

**In one line:** **No** — you cannot `recover` a **panic** that occurred on **another** goroutine’s stack; the **child** must use **`defer`+`recover`**, or you surface failure via **channels** / **errgroup** / **return values** / logging.

**Visualize it:**

```
parent (G1)                   child (G2: go f())
  recover()  X------------------ panic
  only sees G1’s panics            only G2’s defers+recover can stop G2’s panic
```

**Key facts:**
- **Model:** panic **unwind** is **G-local**; there is no “propagate to parent G” in the spec.
- **Practical:** the [[T10 Defer, Panic & Recover Internals - Exercises]] `SafeGo` pattern, or `chan error`, or `errgroup.Group.Wait`.

**Interview tip:** One phrase: **G-local unwinding** — then how you **design** fault containment (per-goroutine `recover`, not parent `recover`).

> [!example]- Full Story: Why the runtime does not “teleport” panics
>
> **The problem:** “We’ll `recover` in `main` for background workers” — **no**: those panics are not `main`’s stack.
>
> **How it works:** The panic and unwind machinery is **per goroutine**; there is no parent pointer in the **panic** model for **cross-G recovery**. Asynchronous **failures** are usually reported as **values** (errors) for **control**; **synchronous** stack unwinding stays **local** to avoid racy, ambiguous ownership of which handler runs.
>
> **What to watch out for:** Tests that do not fail when a **child** **panics** because **the test’s** `recover` never runs in that **G**.

---

## Q6: How can deferred functions modify return values? [COMMON]

**Answer:**

**In one line:** If results are **named** (e.g. `(r int)`), a deferred function can **assign** to `r` after the `return` **expression** has been evaluated; that assignment can be what the **caller** **observes** — classic `defer func() { r = 10 }()` with `return 5` yielding **10** to the caller.

**Visualize it:**

```
func f() (r int) {
    defer func() { r = 10 }()
    return 5     // "return" sets r=5, then defer overwrites: caller sees 10
}
```

**Key facts:**
- Tied to **named** return **slots** and **closures** that **mutate** them; surprising for readers — **rare in public** APIs.
- The exact lowering is **compiler** detail; the **user-visible** pattern is the interview target. Full story in [[T10 Defer, Panic & Recover Internals]].

**Interview tip:** Show the three-line **gotcha**, then say: **I avoid named returns + defers in exported APIs** unless the team’s style document likes them.

> [!example]- Full Story: Result slots and the return sequence
>
> **The problem:** “Why did `f()` return 10 when I `return` 5?” — the **name** `r` is the **out** param **slot**; the deferred closure **overwrites** it.
>
> **How it works:** The compiler may emit **spill** to named **out** **parameters**, then run **deferred** functions that **see** the **address** of `r` (or equivalent) and can **write** it again. That is not “time travel” — it is **ordered** by the **return**+**defer** sequence.
>
> **What to watch out for:** **Many** defers and **bare** `return` in large functions with **named** results — readability and **lint** nags; prefer explicit returns in **small** **helpers** or avoid **named** results when you use **tricky** defers.

---

## Q7: What is open-coded defer and how does it improve performance? [ADVANCED]

**Answer:**

**In one line:** The compiler can **simplify** certain **static** `defer` patterns (e.g. a single `defer` paired with a **lock** in a small function) by **inlining** the **deferred** work at **return** / **unwind** edges **instead of** always building a full **heap** **defer** **record** — **reducing** overhead on **hot** paths. Exact rules **vary by Go version**; **profile** when it matters.

**Visualize it:**

```
general defer  →  defer record, runtime, maybe heap
open-coded     →  (simplified) direct unlock calls at return edges the compiler can prove
```

**Key facts:**
- **Not** “every `defer` is free” — **optimization** is **case-by-case** (SSA / defer passes in the compiler).
- See **release notes** and `cmd/compile` / SSA discussions for the **current** **story**; your **version** of Go is the source of truth.
- In **doubt**, **microbenchmark**; sometimes **manual** `unlock` in **all** **branches** is clearer than relying on inlining.

**Interview tip:** Say **“compiler may open-code elidable defers to avoid defer setup cost”** — avoid claiming a **number** you did not **measure** on **their** version.

> [!example]- Full Story: From defer records to direct calls
>
> **The problem:** Old guidance was “never `defer` in a hot `Lock`” because **older** `defer` had more fixed cost; **newer** compilers **elide** some patterns.
>
> **How it works:** The compiler’s **defer** and **SSA** passes can recognize **simple** patterns: one mutex, one `defer` **Unlock**, no **complex** control flow, **etc.**, and **lower** the unlock to direct calls on all **exit** **edges** (and maintain **panic** **correctness** along paths that need it). **Dynamic** or ** many** defers may still use the **general** path.
>
> **What to watch out for:** Treating this as a **portable** spec — it is an **implementation** **optimization**; `pprof` and **readability** still drive **local** **locks**.

---

## Q8: What happens to defers when `os.Exit` is called? [TRICKY]

**Answer:**

**In one line:** `os.Exit` **ends the process** immediately; **deferred** functions **do not** run. Returning from `main` (or falling off `main`) **does** run **defers** on that return path.

**Visualize it:**

```
return from main  →  defers in main  →  runtime teardown  →  exit

os.Exit(code)  ------------>  process terminates (defers SKIPPED)
```

**Key facts:**
- `log.Fatal` = **log** + `os.Exit(1)` — same **bypass** of **defers** after the log.
- **Tests** and **CLIs** that `os.Exit` **early** can **leak** **temp** files or **mocks** if cleanup was **defer**-only.
- If you must run work before exit, **restructure** to **`return`** + exit code, or a single **atexit**-style **helper** your team owns (not a Go keyword).

**Interview tip:** **Contrast in one line:** return **drains** defers, **`os.Exit` does** **not**.

> [!example]- Full Story: Why exit is a hard cut
>
> **The problem:** `defer cleanup()` at **start of `main`**, then `os.Exit(0)` in a **branch** — `cleanup` **never** runs.
>
> **How it works:** `os.Exit` **calls** into the process **exit** path without **walking** the **Go** **stack** for defers. The runtime **does** not get a “normal” **return** from each frame.
>
> **What to watch out for:** **Cgo** and **C** `exit` — same class of **bypass**; **init** **order** and **globals** with **`log.Fatal`**.

---

## Q9: When should you use panic vs returning an error? [COMMON]

**Answer:**

**In one line:** Return **`error`** for **expected** and **operational** **failures**; use **`panic`** for **truly** **unrecoverable** **bugs** or **invariants** that should **not** be **false** in **correct** code (and **sparingly** in **library** **public** **APIs** — many **teams** return **`error`** even for “**shouldn’t** happen**” at **module** boundaries**).

**Visualize it:**

```
open file, bad JSON, ctx cancelled   →  error

invariant: map never nil here, index always in range in internal code
   →  panic in dev or tests, or return error in defensive library style (team policy)
```

**Key facts:**
- **Idiom:** `errors` are part of the **function** **contract**; `panic` **breaks** **normal** **control** **flow** on **this** **goroutine** until `recover` or process exit.
- **stdlib** mixes styles (e.g. some `Must*` **helpers** **panic** on bad input) — **read** the **package** **docs** you **use**.
- In **long-running** **servers**, **turn** most failures into **HTTP** **4xx/5xx**; reserve **unhandled** **panics** for **bugs** and rely on **middleware** `recover` as a **safety** **net**.

**Interview tip:** “**Errors** are **values**; **panic** is **abnormal** **stack** **unwind** on **this** **G**” + one real example (`json.Unmarshal` **returns** **error** vs `MustCompile` **panics** on bad **pattern**).

> [!example]- Full Story: Public API and the panic line
>
> **The problem:** Using **panic** for **“**file not** found**” in an **HTTP** handler — should be **4xx/5xx** and **`error`**. Using **panic** for **invariant** **violation** in **internal** **code** that should **never** **ship** — more **debatable**; some teams still **`return` `err`** for **defensive** code paths.
>
> **How it works:** **Ecosystem** **expectation** is **`error`** for **most** **recoverable** **and** many **“**unexpected** but** not **assert**”** cases** at **public** **boundaries**. **`panic`** **in** **tests** is sometimes replaced by `t.Fatalf` for **clarity**; in **net/http** **handlers** **,** top-level **middleware** **`recover`** **logs** and **replies** **500** for **stray** **panics** without **killing** the **process** if **set** **up** **(Q12)**.
>
> **What to watch out for:** **Libraries** that **panic** on **user** **input** (validation) — **usually** return **`error`**; **reserving** `panic` for **programmer** **errors** in **`Must*`**-style **names** is the **convention**.

---

## Q10: How does the `runtime._panic` struct work? [ADVANCED]

**Answer:**

**In one line:** The runtime keeps a **per-goroutine** **linked** list (conceptually) of **active** **panic** **nodes** — each has the **value** `panic` received, a **link** to a **previous** **panic** (for **nested** / **re-panics**), and **internal** **state** to **unwind** the **stack** and **interact** with `recover` — **not** a public **“exception** **object**” you allocate in **user** **code`.

**Visualize it:**

```
G:  p_oldest  →  ...  →  p_newest
             recover() targets the current (newest) active panic
```

**Key facts:**
- **Exact** **fields** and **names** are **in** **`runtime`**, versioned; read **`type _panic`** in **`panic.go`** in **your** **tree** if asked for **literals**.
- `recover()` returns the **interface{}** value passed to `panic`, not a **`*_panic`**.

**Interview tip:** **Describe** **node**+**G**+**unwind** **without** **memorizing** **field** **offsets** unless they **opened** **the** **source** **with** you.

> [!example]- Full Story: _panic, recover, and nested panics
>
> **The problem:** “Is **panic** just **any** `interface{}` on the **heap** you **catch** like **Java**?” — **no**: **runtime**-managed **state** on **unwind** **path**.
>
> **How it works:** **`gopanic`** **installs** a **panic** **record** and **unwinds**; **`recover`**, when **valid**, **pops** / **clears** the **current** **panic** **and** **stops** **further** **unwind** for it. **Nesting** and **re-panics** (panic during handling) **use** the **list**; **rare** in **app** code, **covered** in **runtime** **tests** **.
>
> **What to watch out for:** **`runtime.Goexit`** and **`os.Exit` — **different** from **`panic`/`recover`**; **`Goexit`** has **its** own **conventions** in **`runtime`**.

---

## Q11: What's the difference between `recover()` in a direct `defer` vs a nested function? [TRICKY]

**Answer:**

**In one line:** `recover` **only** **works** when **called** **while** a **panic** is **unwinding** **this** **goroutine** and **in** a **valid** **context** the **runtime** **associates** with **deferred** **unwind** — a **“nested** **function**” is **fine** if it is **invoked** from **that** `defer` (same **G**, **synchronous** **during** **unwind**); `recover` in a **helper** that is **not** on **that** **unwind** **path** **returns** **`nil`**.

**Visualize it:**

```
defer func() { recover() }()                    // valid — recover inside deferred func

func helper() { recover() }  // if called from normal code, not during panic unwind: nil
```

**Key facts:**
- The **interview** **trick** is not **nesting** **depth**; it is **valid** **unwind** **context** + **same** **G** as the **panic** (see Q2, Q5).
- A **pattern:** `defer func() { if r := recover(); r != nil { ... } }()` as the **outer** `defer` on the **G** that may **panic**.

**Interview tip:** If the question is **tangled** with **nesting** **,** refocus: **`recover` in** the **`defer`’s** **goroutine** **during** **panic** **unwind**; **nesting** **is** **OK** if **the** **call** **chain** **stays** **valid**.

> [!example]- Full Story: Valid recover contexts
>
> **The problem:** “I **called** **helper()** with **`recover`** from **`defer`”** **vs** from **normal** **code** **—** the **first** can **work**, the **second** **not** (unless **by** **coincidence** you are **in** a **panic** **unwind** from **higher** on **the** **stack**—usually **not** what they **meant**).
>
> **How it works:** The runtime checks whether `recover` is allowed in the current frame during panic handling; it is tied to deferred functions and the goroutine’s panic list, not to “nesting” by name alone.
>
> **What to watch out for:** Confusing this with Q5 — “wrong G” (cross-goroutine) vs “wrong place on the right G” (not in a valid `defer` unwind path).

---

## Q12: How would you implement a panic-safe HTTP middleware? [COMMON]

**Answer:**

**In one line:** **Wrap** the **next** `http.Handler` in a function that uses **`defer func() { if r := recover(); r != nil { log; http.Error(..., 500) } }()`** (or your **logger** / **observability**), then **call** `next.ServeHTTP` **synchronously** **on the same** **goroutine** the **server** used for **that** **request** — so **a** **handler** **panic** **does** **not** **kill** the **process** and **is** **turned** into a **5xx** **(or** your **policy** **)**.

**Visualize it:**

```
Client →  RecoveryMiddleware  →  Handler.ServeHTTP
              |
              +-- defer+recover: log panic, 500, no re-panic
```

**Key facts:**
- **net/http** **serves** each request on **a** **goroutine**; **this** `defer` is **on** **that** **G** **—** the **one** that **can** `recover` the **handler**’s **panic** **(Q2, Q3)**.
- If the **handler** spawns `go` work, that goroutine must own its own `defer`+`recover` (Q5); the middleware only sees **synchronous** panics in the handler chain.
- **Re-panic** **policy:** sometimes **rethrow** for **an** **outer** **logger**; **usually** **log**+**5xx** and **return** to **avoid** **double** **write** to **`ResponseWriter`**.

**Interview tip:** **Mention** **per-request** `recover`, **`ResponseWriter` ** state** if **headers** / **body** **already** **sent** **(hard** to **build** a **clean** 500) **,** and **httptest** for **regression** **.

> [!example]- Full Story: Middleware placement and re-panics
>
> **The problem:** `recover` **only in** `main` — **fails** for **`net/http`** because **request** **goroutines** are **not** `main` **(Q2)**.
>
> **How it works:** A wrapper that defers+recovers around `next` (same G as the `net/http` dispatch to the handler) sees panics in the handler and in dependencies it **called synchronously**. You log the value and stack (`debug.Stack` in production servers), optionally emit metrics, and send a safe 500 if the body is not already committed.
>
> **What to watch out for:** Streaming and `Hijack`; after some bytes are written to the client, a clean 500 may be impossible—log and end the stream per your framework. Test with `httptest` and a handler that panics on demand.

---

**Wikis:** All questions tie back to **[[T10 Defer, Panic & Recover Internals]]**; practice **[[T10 Defer, Panic & Recover Internals - Exercises]]** and the recall grid in **[[T10 Defer, Panic & Recover Internals - Revision]]**.
