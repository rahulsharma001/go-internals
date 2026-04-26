# P06 Function Call Stack

> **Prerequisite note** — complete this before starting **T10 Defer, Panic & Recover Internals** or **T13 Goroutine Internals**.
> Estimated time: ~15 min

---

## 1. Concept

The **call stack** is a last-in, first-out pile of **stack frames**. Every time you call a function, Go puts a new block on the stack for that call. That block holds what this invocation needs: arguments, local variables, where to go back when the call finishes, and room for return values.

Picture a stack of plates at a buffet. You only ever touch the top plate. A new function call adds a plate. A return removes the top plate. The plate on top is always whoever is running *right now*.

For you as a backend engineer, this matters because **defers** attach cleanup to *your* frame and run in reverse order when you leave. **Named return values** are real variables in that frame — so a `defer` can still change what the caller gets. **Each goroutine** has its own stack. And if you recurse without stopping, frames keep piling up until the runtime hits **stack overflow**.

---

## 2. Core Insight (TL;DR)

**One active call ⇒ one frame.** Nesting depth equals how many frames are stacked. Calling pushes; returning pops. **Defer** is not a queue — it’s a stack of “do this before this function is done,” so the **last** `defer` you registered runs **first** at exit. **Named results** (`(err error)`) live in the outer function’s frame the whole time, so `defer` can wrap or rewrite `err` after the body runs. **Goroutines** don’t share stacks; two concurrent requests each grow their own pile.

---

## 3. Mental Model (Lock this in)

Think of a request walking through your server.

`ServeHTTP` is on the bottom — the entry from `net/http`. It calls `AuthMiddleware`, which calls your handler’s `GetUser`, which calls `db.Query`. While `db.Query` runs, you have **four frames** stacked: query on top, then user lookup, then middleware, then the server glue underneath.

Checkout flows work the same way: `HandleCheckout` → `ValidateCart` → `ChargePayment`. Same idea — each arrow is a call, each call adds a frame.

When the innermost function returns, its frame vanishes. Locals tied to that call go away with it (unless the compiler moved them to the heap — more on that below).

**Defer** is “chores pinned to your current plate.” You finish the function body first. Then you run those chores from the **top of the defer list** down. That’s why `defer rows.Close()` and `defer tx.Rollback()` pair naturally with “open, work, return” — order of registration controls cleanup order.

---

## 4. How It Works

### 4.1 What lives in a frame (the interview-safe version)

For one invocation, think in terms of:

- **Parameters** you passed in
- **Locals** declared in that function
- **Where to resume** in the caller when this call returns
- **Space for return values** the caller will read

You don’t need register names or exact memory layouts. You need **lifetime**: stuff that belongs to this call disappears when this call’s frame is popped — unless the compiler **escapes** it to the heap (e.g. you return a pointer to a local and that pointer must stay valid).

### 4.2 Push on call, pop on return

You call `ValidateCart` from `HandleCheckout`. `HandleCheckout`’s frame stays. `ValidateCart`’s frame goes on top. If `ValidateCart` calls `ChargePayment`, you get a third frame. Returns unwind in the opposite order: payment finishes, then cart, then checkout.

Same function text can run many times — each call gets a **fresh** frame. Two calls to `GetUser` in one request means two separate workspaces, not one reused block.

### 4.3 Defer runs after the body, still on your frame

When you hit the closing brace (or a `return`), Go runs your deferred calls **before** the function is fully done from the caller’s perspective. They still see your named results and can still call functions — but your body has already finished its normal work.

That’s why this pattern works:

```go
rows, err := db.QueryContext(ctx, `SELECT id FROM orders WHERE user_id = ?`, userID)
if err != nil {
    return nil, err
}
defer rows.Close()
// ... scan rows ...
```

`rows.Close()` runs when **this** function exits, in LIFO order with any other `defer`s you registered in the same function.

### 4.4 Named returns + defer = wrap errors with context

If you write `(cfg Config, err error)`, both `cfg` and `err` are variables in **this** function’s frame for the whole call. A `defer` can read and assign them. That’s how people add context to errors without repeating boilerplate on every `return`:

```go
func loadConfig(path string) (cfg Config, err error) {
    defer func() {
        if err != nil {
            err = fmt.Errorf("loadConfig %q: %w", path, err)
        }
    }()
    data, err := os.ReadFile(path)
    if err != nil {
        return cfg, err
    }
    err = json.Unmarshal(data, &cfg)
    return cfg, err
}
```

Assume `encoding/json` is imported. Every path that sets `err` is still visible to the `defer`, which runs after those assignments and can wrap `err` before the caller sees the final value.

### 4.5 Goroutine stacks

Each **goroutine** has its own stack. It starts small and **grows** when your call chain gets deep. Two goroutines handling two HTTP requests both run `ServeHTTP` with the same source code — but **different stacks**, different frames, different locals.

### 4.6 Stack overflow

If you never stop calling yourself, frames never pop. Eventually that goroutine’s stack hits its limit and you get a **stack overflow**.

Classic backend footgun: a recursive JSON decoder with no depth cap — nested `{` / `[` forever, one frame per level:

```go
func decodeValue(d *decoder) error {
    // missing: max depth check
    if d.peek() == '{' {
        return decodeObject(d) // each nested level = another frame
    }
    return nil
}
```

One hostile payload and you’re miles deep.

---

## 5. Key Rules & Behaviors

### Every call pushes a frame

Even if it’s the same function twice in a row — two calls, two frames.

### Returning pops the frame; stack locals are gone

After `GetUser` returns, its locals aren’t yours anymore. If you need a value to outlive the call, the compiler must place it somewhere that survives the pop (often the heap).

### Defer is LIFO

Last registered runs first at exit. Registration order matters for `Rollback` vs `Close`, or closing inner resources before outer ones.

### `defer f(args)` evaluates `args` when the `defer` line runs

Not when the deferred call runs. Closures `defer func() { ... }()` see variables later — interviewers love the difference.

### Named results are frame-long variables

Defer can change what the caller receives. Mixing bare `return` and `return expr` with defers that touch named results is easy to get wrong — draw one set of slots in your head.

---

## 6. Memory traces (three that matter)

These three traces are enough to carry the whole chapter.

### Trace 1 — Request flow: `ServeHTTP` → `AuthMiddleware` → `GetUser` → `db.Query`

Imagine `db.Query` is running (waiting on the driver / network). Your stack looks like:

```
MEMORY TRACE:

While db.QueryContext(...) is active:

  call stack (top = currently running):
    ┌─────────────────────────────────┐  ◄── top
    │ db.QueryContext frame           │  ← driver / DB layer
    │   "when I return, resume GetUser"
    ├─────────────────────────────────┤
    │ GetUser frame                   │  ← repo or service
    │   "when I return, resume handler"
    ├─────────────────────────────────┤
    │ AuthMiddleware frame            │  ← checks JWT / session
    │   "when I return, resume ServeHTTP"
    ├─────────────────────────────────┤
    │ ServeHTTP frame                 │  ← net/http entry
    │   "when I return, runtime resumes"
    └─────────────────────────────────┘

  **Aha:** The DB call isn’t lonely — the whole chain of who-called-whom is still underneath. Each layer is paused, waiting for the one above to return.
```

When `Query` returns, its frame pops. `GetUser` resumes. Then `GetUser` returns, and so on — always **one** pop per return.

### Trace 2 — Defer LIFO: transaction + file in a handler

You open a DB transaction, register `Rollback`, open a file, register `Close`. Happy path commits; defers still run in reverse registration order.

```go
func (h *Handler) ExportReport(w http.ResponseWriter, r *http.Request) error {
    tx, err := h.db.BeginTx(r.Context(), nil)
    if err != nil {
        return err
    }
    defer tx.Rollback() // no-op after Commit; safe pattern

    f, err := os.CreateTemp("", "report-*.csv")
    if err != nil {
        return err
    }
    defer os.Remove(f.Name())
    defer f.Close()

    if err := h.writeReport(tx, f); err != nil {
        return err
    }
    if err := tx.Commit(); err != nil {
        return err
    }
    return nil
}
```

At function exit (any path), deferred calls run **last registered first**:

```
MEMORY TRACE:

Defer stack inside ExportReport (bottom = first registered, top = last registered):

  Registration order:
    1. defer tx.Rollback()
    2. defer os.Remove(f.Name())
    3. defer f.Close()

  Defer stack (conceptual):
    bottom ──→ [ Rollback ][ Remove ][ Close ] ◄── top

  On exit, unwind order:
    1. f.Close()        ← closes the file handle
    2. os.Remove(...)   ← cleans temp file
    3. tx.Rollback()    ← rolls back if Commit never happened; no-op after Commit

  **Aha:** Last registered runs first — here `Close` then `Remove` then `Rollback`. Reorder your `defer` lines when you need a different teardown sequence.
```

### Trace 3 — Named return + defer wrapping `err`

```go
func loadConfig(path string) (cfg Config, err error) {
    defer func() {
        if err != nil {
            err = fmt.Errorf("loadConfig %q: %w", path, err)
        }
    }()

    data, err := os.ReadFile(path)
    if err != nil {
        return cfg, err // err is non-nil; defer will wrap it
    }
    err = json.Unmarshal(data, &cfg)
    return cfg, err
}
```

```
MEMORY TRACE:

Step 1: Enter loadConfig — named cfg and err exist in this frame (err starts as nil)

  call stack:
    ┌─────────────────────────────────┐  ◄── top
    │ loadConfig frame                │
    │   named: cfg (zero), err = nil  │  ◄── caller will read these slots
    │   defer: [ wrap err closure ]   │
    └─────────────────────────────────┘

Step 2: os.ReadFile fails — return assigns err; defer runs; defer wraps err

Step 3: Caller sees one error value with path context

  **Aha:** err isn’t invented at the return statement only. It’s a real slot in the frame. The defer runs after your return path sets it but before the caller takes delivery — so you can attach context once, centrally.
```

---

## 7. Code Examples (Show, Don’t Tell)

`HandleCheckout` → `ValidateCart` → `ChargePayment`: three frames when the innermost body runs; returns peel from the inside out.

### Rows + defer (the pattern you’ll actually ship)

```go
func (r *UserRepo) GetUser(ctx context.Context, id int64) (*User, error) {
    rows, err := r.db.QueryContext(ctx, `SELECT id, email FROM users WHERE id = ?`, id)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    if !rows.Next() {
        return nil, sql.ErrNoRows
    }
    var u User
    if err := rows.Scan(&u.ID, &u.Email); err != nil {
        return nil, err
    }
    return &u, nil
}
```

`rows.Close()` always runs on the way out — success, early return, or error after `Query` succeeded.

---

## 8. Practice Checkpoint

### Tier 1: Predict the outcome (middleware-style)

`handle` registers `defer A` then `defer B`, then `panic("boom")`. Middleware wraps `next` with `recover` in a defer. What prints first, and who catches the panic?

```go
func withRecover(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if rec := recover(); rec != nil {
                http.Error(w, "internal error", http.StatusInternalServerError)
            }
        }()
        next.ServeHTTP(w, r)
    })
}

func handle(w http.ResponseWriter, r *http.Request) {
    defer fmt.Println("defer A")
    defer fmt.Println("defer B")
    panic("boom")
}
```

> [!success]- Answer
> Prints **`defer B`** then **`defer A`** (LIFO in `handle` as the panic unwinds). The middleware’s defer runs `recover` **after** control leaves `handle`; the panic is caught there, not inside `handle`. To recover inside `handle`, you’d defer `recover` in `handle` itself.

### Tier 2: Fix the bug (named return + defer)

This handler should log `err` **including** context if `decodeJSON` fails, but the log always shows `<nil>`. Why?

```go
func (h *Handler) PostWidget(w http.ResponseWriter, r *http.Request) (err error) {
    defer func() {
        if err != nil {
            h.log.Printf("PostWidget: %v", err)
        }
    }()

    var body widgetRequest
    if err := decodeJSON(r.Body, &body); err != nil {
        return err
    }
    return h.saveWidget(r.Context(), body)
}
```

> [!success]- Answer
> **Shadowing:** Inside the function, `if err := decodeJSON(...)` declares a **new** `err` scoped to the `if`. The deferred closure closes over the **outer** named return `err`. The inner assignment never updates that outer slot, so when the defer runs, the outer `err` is still `nil`.
>
> Fix: use `=` with a predeclared err, or name the inner error something else:
>
> ```go
> var body widgetRequest
> if err = decodeJSON(r.Body, &body); err != nil {
>     return err
> }
> ```
>
> or `if decErr := decodeJSON(...); decErr != nil { return decErr }`.

---

## 9. Gotchas & Interview Traps

| Trap | What bites you | What to say |
|------|----------------|-------------|
| Defer + loop | `defer` in a `for` registers many cleanups; all run when the **function** returns, not each iteration | “Defer binds to the enclosing function. Use a local closure or inline func per iteration if you need per-iteration cleanup.” |
| `defer f(i)` vs `defer func() { f(i) }()` | Arguments to `f` are evaluated at registration time | “Captured value vs live variable — know which one you need.” |
| Infinite recursion | JSON, AST, directory walk without depth cap | “Each call adds a frame; unbounded depth overflows the goroutine stack.” |
| Assuming stacks are shared | Two requests, one goroutine each | “Each goroutine has its own stack; same code, different frames.” |

**Stack vs heap (one sentence for interviews):** The compiler puts locals on the stack when they can die with the frame; if a pointer escapes, the value may live on the heap. You write locals; the compiler decides storage.

---

## 10. Interview Gold Questions (Top 3)

**Q1: What is a stack frame, and what happens on call vs return?**

A frame is this invocation’s workspace: arguments, locals, return path to the caller, and return value slots. Calling pushes a frame; returning pops it. Order is strictly LIFO.

**Q2: Why do defers run in reverse order, and when are deferred arguments evaluated?**

Defers are stacked on the current frame. Last registered runs first at exit. For `defer f(x)`, `x` is evaluated when the `defer` statement runs. A closure `defer func() { ... }()` observes variables at defer **execution** time (unless it copies them itself).

**Q3: How can a defer change what the caller receives?**

With **named return values**, the result slots are variables in the callee’s frame for the whole function. The body and the defer both can assign to them; the caller reads the final values after defers run.

---

## 11. 30-Second Verbal Answer

Every function call adds a stack frame — arguments, locals, where to resume, and return value space. Return pops the frame. You care because **defer** runs cleanup in reverse registration order as the function exits, still on that frame. **Named returns** are real variables in that frame, so defer can wrap errors or tweak results. Each **goroutine** has its own growing stack. Recursion or insane depth blows that stack — stack overflow.

---

> See [[Glossary]] for term definitions.
