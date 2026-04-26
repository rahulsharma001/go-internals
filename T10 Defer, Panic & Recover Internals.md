# T10 Defer, Panic & Recover Internals

> **Reading Guide**: Sections 1-3 and 6 are essential first read (20 min).
> Sections 4-5 deepen understanding (15 min).
> Sections 7-12 are interview-specific — read closer to interview day.
> Section 13 is your comprehensive interview Q&A bank → [[questions/T10 Defer, Panic & Recover Internals - Interview Questions]]
> Something not clicking? → [[simplified/T10 Defer, Panic & Recover Internals - Simplified]]

---

## 0. Prerequisites

Complete these before starting this topic:

- [[prerequisites/P06 Function Call Stack]]

---

## 1. Concept

A **`defer` statement** schedules a function to run when the **surrounding function** returns, on every `return` path, or when a **panic** starts unwinding that goroutine. The scheduled work is **not** the next line. It is "later, on the way out."

A **`panic`** stops normal control flow. It **unwinds** the stack, runs **deferred** functions in that **goroutine**, and if nothing **recovers**, the runtime prints a stack trace. An unrecovered panic in **any** goroutine tears down the **whole program** — not just that goroutine.

A **`recover`** is a **built-in** that **returns the panic value** and **stops the panic** if it is called **while a deferred function from that same goroutine is still running** on the way out. Otherwise it returns **`nil`**.

> **In plain English:** `defer` is a sticky note you put on the door on your way in: you promise to do one more chore when you leave. `panic` is a fire alarm: everyone stops their normal work and runs for the exit. `recover` is a fire extinguisher you mounted **on that same door** — it only works if you already put the mount there with `defer`.

---

## 2. Core Insight (TL;DR)

**Three rules lock most interview answers.** **First,** arguments to a deferred function are **fully evaluated and copied at the `defer` line**, not when the deferred work runs. **Second,** deferred work runs in **LIFO** order. The **last** `defer` you wrote in that function is the **first** to run on exit. **Third,** if the function has **named result parameters**, deferred functions can **read and write** those names on the way out, which is how the famous "double return" works.

**`recover` is goroutine-scoped and defer-scoped.** It does **not** cross goroutines. A parent function cannot "catch" a **panic in a child goroutine** the way you might catch an error from a function call. The child must run its own `defer` + `recover`, or signal the parent on a channel.

> **In plain English:** You schedule chores with `defer` when you can still read the **labels on the boxes** for arguments, even if the room changes before you do the chore. The cleanup line is **LIFO** because you pile sticky notes, then peel from the top. A panic in another **worker** is not your sticky pile — you never see that alarm unless you wired a separate signal path.

---

## 3. Mental Model (Lock this in)

### The Sticky-Note Stack

Each **`defer` in a function** adds one piece of work to a **per-function stack of deferred calls** for that activation. The stack is **LIFO**. The **newest** note is on top. On **any** return or panic, Go **peels from the top** first.

```
defer A   ── pushes  [ A ]           stack:  top → A
defer B   ── pushes  [ B ]           stack:  top → B, A
defer C   ── pushes  [ C ]           stack:  top → C, B, A

function ends (return or panic unwind):
  run C  (first)
  run B
  run A  (last)
```

**Panic as fire alarm, recover as mounted extinguisher:** A **panic** starts an **emergency walk toward the door**. The **door** is where you hung **deferred** work. A **`recover` call** only "puts out" the panic if you already placed it in the **deferred** path. If the panic is in another **goroutine** (another room), your extinguisher in **this** room does nothing.

> **In plain English:** Sticky notes stack on a desk. You add new notes on top. When you stand up to leave, you read from the top down. A panic in another room is not on your desk.

### Mistake That Teaches: `defer` in a Loop (DB Connections)

In real services you see the same bug with **`sql.DB`**, Redis clients, or gRPC conns — not just files. Here, each order was supposed to use its **own** connection, but every iteration schedules **another** `Close` for **one** moment: when the **outer** function returns.

```go
// BUG: N connections stay open until the *outer* function returns
func ProcessBatch(ctx context.Context, db *sql.DB, orders []Order) error {
	for _, ord := range orders {
		conn, err := db.Conn(ctx)
		if err != nil {
			return err
		}
		defer conn.Close() // <- one defer per iteration; all fire at outer return
		if err := applyOrder(ctx, conn, ord); err != nil {
			return err
		}
	}
	return nil
}
```

```
Iteration 0:  defer: Close conn₀   [stack: Close₀]
Iteration 1:  defer: Close conn₁   [stack: Close₁, Close₀]
...
Iteration n:  conns 0..n-1 are ALL still open
              until the whole function returns

       └── every iteration pushed another "Close later" note
           but "later" is ONE moment: outer function end
       └── pool exhaustion / too many open conns  <-- OOPS
```

**Fix pattern:** one `defer` per **scope that ends before the next** iteration — usually an IIFE or a small helper.

```go
for _, ord := range orders {
	err := func() error {
		conn, err := db.Conn(ctx)
		if err != nil {
			return err
		}
		defer conn.Close()
		return applyOrder(ctx, conn, ord)
	}()
	if err != nil {
		return err
	}
}
```

> **In plain English:** A `defer` in a loop is like writing "I will close every connection at midnight" fifty times. You still have fifty live connections until midnight. Put each order in a **small** room, close on the way out of **that** room, then start the next.

---

## 4. How It Actually Works (Internals) [INTERMEDIATE → ADVANCED]

> **In plain English:** The runtime does not magically remember your wishes. It tracks what to run on the way out.

**What you need to know:** Go keeps a **linked list of defers per running function** (conceptually: a chain hanging off the current call). When the function **returns** or **panics**, the runtime **walks that list from newest to oldest** and runs each deferred call. That is **LIFO** in practice.

You do **not** need the struct field names from `runtime`, open-coded defer optimizations, or a frame-by-frame unwind narrative for interviews. If someone presses for "how does panic find defers?" — **same list, walked while unwinding that goroutine's stack** until something `recover`s or the program exits.

> **In plain English:** The runtime keeps a **clothesline of hooks** on **this worker** only. You clip the newest tag next to your hand. When you back out, you unclip from the hand side first.

**Tiny closure reminder (still "Key Rules" territory, but it lives next to internals in every codebase):**

```go
func f() {
	x := 1
	defer func() { println(x) }()
	x = 2
}
// prints 2: the closure reads x from the frame at run time, not a copy at defer time
```

---

## 5. Key Rules & Behaviors

### Rule 1: Defer arguments are evaluated at the `defer` line, not at exit time

```go
func main() {
	i := 0
	defer fmt.Println("defer prints:", i) // argument list evaluated NOW
	i++
	fmt.Println("after:", i) // 1
}
// prints: after: 1, then "defer prints: 0" (evaluated 0)
```

```
Step: hit `defer fmt.Println("defer prints:", i)`
  evaluate fmt.Println, string constant, and **current i**  → 0
  those values are **stored for the deferred call**

Step: i++  →  i is 1 in the frame

Step: on return
  run deferred call with **captured 0**
```

> **In plain English:** A **phone order** is taken the moment you say `defer` — the kitchen writes down **"no onions"** from **today's** list. You can change the whiteboard after that. The old ticket does not rewrite itself.

---

### Rule 2: LIFO — last `defer` registered runs first

```go
func main() {
	defer fmt.Print("1 ")
	defer fmt.Print("2 ")
	defer fmt.Print("3 ")
}
// prints: 3 2 1
```

```
registration order: 1, then 2, then 3
stack:   top   3
              2
              1
execution: 3 → 2 → 1
```

> **In plain English:** The last **Post-it** you stack on the pile is the first one you peel when you clean the desk. That is **LIFO** order.

---

### Rule 3: Named return values can be written by deferred functions (the "double return")

```go
func f() (n int) { // n is a **named** result; addressable on the way out
	defer func() { n++ }()
	return 42  // 1) n := 42  2) defers: n++  3) RET with n=43
}
```

```
sequence:
1) `return 42` assigns **n = 42**
2) defers: **n++**  →  n = 43
3) the **final** n is 43
```

> **In plain English:** A **name tag** is stuck on a box the whole office shares for **this** shipment. A cleanup crew on the way out can still **relabel** the box, because the label is a **shared** physical slot.

**Trap:** the trick needs **named** result parameters. Do not "clever" this in real APIs unless your team loves Easter eggs.

---

### Rule 4: `recover` must be called **inside a deferred function**; awkward placements return `nil`

**Broken pattern: `recover()` not in a deferred function**

```go
func bad() {
	recover() // not inside defer → always useless here
}
```

**Safe idiom:** a **`defer` function literal** that calls `recover` **inside** the literal.

```go
func good() (caught string) {
	defer func() {
		if v := recover(); v != nil {
			caught = fmt.Sprint(v)
		}
	}()
	panic("oops")
	return ""
}
```

> **In plain English:** The extinguisher's **bracket** is the **`func() { ... }`**. You do not balance the can on the floor and hope the inspector approves.

---

### Rule 5: Panics are **goroutine-isolated**; parent cannot "catch" child

```go
func main() {
	defer func() {
		if v := recover(); v != nil {
			fmt.Println("parent caught:", v)
		}
	}()
	go func() { panic("child") }()
	time.Sleep(100 * time.Millisecond)
	// Child's panic is NOT recovered here. Default: **whole process dies**.
}
```

> **In plain English:** A smoke alarm in **your** apartment does not silence a fire in **the neighbor's** unit. Each goroutine has its own defer chain; the parent does not subsume the child's panic.

**Worker pool pattern:** the **child** recovers (or never panics) and sends `error` / status on a channel. The parent selects on results and keeps serving.

---

## 6. Code Examples (Show, Don't Tell)

### The three defers you will actually type in backend Go

**1. `defer rows.Close()`** — arguably the single most common `defer` after you run `Query`.

```go
rows, err := db.QueryContext(ctx, `SELECT id, status FROM orders WHERE batch_id = $1`, batchID)
if err != nil {
	return fmt.Errorf("query orders: %w", err)
}
defer rows.Close()

for rows.Next() {
	var id int64
	var status string
	if err := rows.Scan(&id, &status); err != nil {
		return fmt.Errorf("scan: %w", err)
	}
	// ...
}
if err := rows.Err(); err != nil {
	return fmt.Errorf("rows: %w", err)
}
return nil
```

If you forget `rows.Close()`, you leak connections from the pool until the GC finalizer path runs — which is **not** something you want to rely on under load.

**2. Transactions: `defer tx.Rollback()` + happy-path `Commit()`**

This is the standard "always release the tx" pattern. If you return early with an error, **`Rollback`** runs. If you commit successfully, **`Rollback`** after **`Commit`** is a no-op on `database/sql` (safe).

```go
func DebitWallet(ctx context.Context, db *sql.DB, userID int64, cents int64) error {
	tx, err := db.BeginTx(ctx, &sql.TxOptions{Isolation: sql.LevelSerializable})
	if err != nil {
		return fmt.Errorf("begin: %w", err)
	}
	defer tx.Rollback() // safe if Commit succeeds; catches all early returns

	if _, err := tx.ExecContext(ctx, `UPDATE wallets SET balance = balance - $1 WHERE user_id = $2`, cents, userID); err != nil {
		return fmt.Errorf("debit: %w", err)
	}
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("commit: %w", err)
	}
	return nil
}
```

**3. Tracing / observability: `defer span.End()`**

```go
ctx, span := tracer.Start(ctx, "orders.ProcessBatch")
defer span.End()
// ... work; child spans can fork from ctx
```

Same idea as `Close`: pair acquisition with release on **every** exit path without spelling `End()` five times.

---

### LIFO ordering and the "value changes" surprise

**A: plain LIFO** — same three-defers example as **Rule 2** (`3 2 1`).

**B: closure sees live variable vs stamped argument**

```go
package main

import "fmt"

func main() {
	i := 0
	defer func() { fmt.Println("defer:", i) }() // closure reads **i** at exit
	i = 1
	fmt.Println("before return:", i)
}
// before return: 1, then "defer: 1"
```

> **In plain English:** A closure **follows** the person; `defer fmt.Println(i)` would have **photocopied** the number at breakfast.

**C: loop + closure — use `i := i` when you mean per-iteration capture**

```go
for i := 0; i < 3; i++ {
	i := i
	defer func() { fmt.Print(i) }()
}
// Go 1.22+ also gives a fresh `i` per iteration in `for` loops, but the copy pattern still shows up in older codebases
```

---

### Named return modification (double return)

```go
func readTwice() (n int, err error) {
	defer func() {
		if err != nil {
			return
		}
		n = n * 2
	}()
	return 21, nil
}
// caller sees n=42, err=nil
```

---

### HTTP middleware: request ID, structured panic log, JSON error body

```go
package main

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"log/slog"
	"net/http"
)

type ctxKey string

const requestIDKey ctxKey = "request_id"

func randomRequestID() string {
	b := make([]byte, 8)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}

type errPayload struct {
	Error     string `json:"error"`
	RequestID string `json:"request_id"`
}

func withRequestID(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		rid := r.Header.Get("X-Request-ID")
		if rid == "" {
			rid = randomRequestID()
		}
		ctx := context.WithValue(r.Context(), requestIDKey, rid)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func withRecover(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if v := recover(); v != nil {
				rid, _ := r.Context().Value(requestIDKey).(string)
				slog.Error("handler panic", "panic", v, "path", r.URL.Path, "request_id", rid)
				w.Header().Set("Content-Type", "application/json")
				w.WriteHeader(http.StatusInternalServerError)
				_ = json.NewEncoder(w).Encode(errPayload{
					Error:     "internal_error",
					RequestID: rid,
				})
			}
		}()
		next.ServeHTTP(w, r)
	})
}

// Wire: http.Handle("/api/", withRequestID(withRecover(apiHandler)))
// withRequestID must run *outside* recover so r.Context() in the defer still carries requestIDKey.
```

> **In plain English:** A **reception** desk puts a **net** at the **door** to your suite. A tantrum in the **hall** still hits the **net** in **this** suite. In production you also emit metrics, tie the request ID to traces, and never log sensitive fields. Wrap **`withRequestID` outside `withRecover`** so the `*http.Request` the recover closure sees already has the ID in `Context()`.

---

### Worker pool: unhandled panic in a child goroutine kills the **whole program**

There is no "just this worker died." Unless that worker **`recover`s**, the runtime aborts the process after printing stacks.

```go
// BUG: panic inside the loop takes down the whole process.
func worker(ctx context.Context, jobs <-chan Job, results chan<- Result) {
	defer close(results)
	for j := range jobs {
		processOne(ctx, j)
	}
}

// Safer: per-job scope with recover → surface as Result.Err on the channel.
func workerSafe(ctx context.Context, jobs <-chan Job, results chan<- Result) {
	defer close(results)
	for j := range jobs {
		res := Result{JobID: j.ID}
		func() {
			defer func() {
				if v := recover(); v != nil {
					res.Err = fmt.Errorf("panic: %v", v)
				}
			}()
			res.Payload = processOne(ctx, j)
		}()
		select {
		case <-ctx.Done():
			return
		case results <- res:
		}
	}
}
```

The parent **cannot** `recover` across goroutine boundaries — the child must **`recover` or not panic**.

---

## 6.5. Practice Checkpoint

All runnable in the Go Playground: https://go.dev/play/

### Tier 1: Predict the output (2 min)

```go
package main
import "fmt"
func f() (x int) {
	defer func() { x += 1 }()
	return 10
}
func main() { fmt.Println(f()) }
```

**Before you run:** what prints?

> [!success]- Answer
> Prints `11`. Here's why:
> 1. `return 10` sets the named return value `x = 10`
> 2. Before the function actually returns, the deferred closure runs
> 3. The closure does `x += 1`, changing `x` from 10 to 11
> 4. The function returns the current value of `x`, which is now 11
>
> This works because `x` is a **named return value** — it lives in the stack frame and defer can modify it after `return` sets it but before the function exits.

### Tier 2: Fix the bug (5 min)

You have a `defer` **inside a `for` loop** over database connections (like `ProcessBatch` above). The service **runs out of pool connections**. Rewrite so each connection is **closed** before the next iteration opens another, without changing the outer function's contract more than necessary.

> **Hint:** a **function literal** per iteration, or a **named** helper, gives a small **room** you return from each time so **defers** run **per** room.

> [!success]- Answer
> Wrap the body of the loop in an immediately-invoked function literal so defer runs per iteration:
> ```go
> for _, ord := range orders {
>     err := func() error {
>         conn, err := db.Conn(ctx)
>         if err != nil { return err }
>         defer conn.Close()
>         return applyOrder(ctx, conn, ord)
>     }()
>     if err != nil { return err }
> }
> ```
> Or extract `func processOneOrder(ctx context.Context, db *sql.DB, ord Order) error` and call it from the loop.

### Tier 3: Build it (15 min)

Build a small **`StartWorker(fn func())` helper** that **starts `fn` in a new goroutine** and **converts a panic in that child** into a **return** on a **result channel** or **err** to the **caller** — the **parent** must **not** **crash** or **leak** the panic. **You may not** **recover** in the **parent** from the child's work **directly** — design the child so **it** **recovers** and **sends** a value.

> Full solutions with explanations → [[exercises/T10 Defer, Panic & Recover Internals - Exercises]]

---

## 7. Edge Cases & Gotchas

**The loop full of defers.** You open resources in a `for` loop and write `defer res.Close()`. Every iteration adds another cleanup that runs only when the **outer** function ends. Under real traffic you exhaust file descriptors, DB pool slots, or ephemeral ports. The story is always: **narrow the scope** so each iteration returns from its **own** function.

**`recover` sitting in ordinary code.** Someone calls `recover()` in the middle of a function, not inside a `defer`ed closure. It returns `nil` and creates false confidence. The fix is boring: **`defer func() { if v := recover(); v != nil { ... } }()`**.

**Assuming the parent catches a worker panic.** A goroutine is not a `try` block. If a handler spawns work and that goroutine panics without `recover`, your process exits — your middleware `recover` never runs for that stack. Wrap **inside** the worker, or use `errgroup` / explicit error returns.

**`os.Exit` bypasses defers.** You call `os.Exit(0)` during shutdown. Every `defer` still pending in `main` is skipped — the process just stops. Tear down explicitly before exiting, or return from `main` and let defers run.

**`defer` in `init`.** `init` functions can use `defer`, but those defers run when **`init` ends**, not at program shutdown. Do not pretend `init` defers are global cleanup for the whole process.

**Mini step-through: `os.Exit` vs `return`**

```go
import "os"

func main() {
	defer println("deferred in main")
	os.Exit(0) // **no** "deferred in main"
}
```

> **In plain English:** A **main breaker** does not wait for you to close each window; the building goes dark.

---

## 8. Performance & Tradeoffs

**Defer costs almost nothing in handlers.** In typical HTTP / RPC code — parse JSON, hit Postgres, return — a handful of `defer`s (`rows.Close`, `tx.Rollback`, `span.End`, mutex unlocks) is not what shows up in `pprof`. The readability and pairing guarantee is worth it.

**Worry about defer in tight loops over millions of rows.** If the hot path is a tiny inner loop executing millions of times per request, **measure**. Sometimes explicit `cleanup()` after the loop, or restructuring so defers live in an outer function, is clearer **and** faster. Data beats faith: one benchmark or CPU profile answers the argument.

**Panic vs error:** Panic unwind is expensive and meant for **bugs** or **truly exceptional** breakage — not for "file not found." Normal control flow returns `error`.

---

## 9. Common Misconceptions

People say **`defer` runs when the inner function I called returns** — but `defer` binds to the **function you wrote it in**. Only a **new** function scope (literal, method, nested func) gets its own defer stack.

People say **I'll recover the worker from main** — you won't. The child must **`recover` or not panic**, and usually **signals** the parent.

People say **`recover` anywhere saves me** — the spec and runtime expect the **`defer func() { v := recover(); ... }`** shape. Random `recover()` calls are `nil` factories.

People confuse **stamped defer args** with **closures**. `defer fmt.Println(i)` copies `i` at the `defer` line. `defer func() { fmt.Println(i) }()` reads `i` when the closure runs.

People think **panic is a fast error path** — it is slower than returning an `error` and makes control flow hard to reason about in public APIs.

---

## 10. Related Tooling & Debugging

**`go test -race`** — catches races where defers and concurrent writes interact badly.

**`GOTRACEBACK=single|all`** — controls how much stack you see when something does panic during dev.

**`runtime/debug.Stack`** — paste stack bytes into logs inside middleware when you recover; pair with request ID.

**`pprof` (CPU, alloc)** — if someone swears defer is killing a hot loop, prove or disprove it with data.

---

## 11. Interview Gold Questions

**Q1: In what order do deferred calls run, and when are the arguments fixed?**

They run **last-in, first-out**. Arguments are evaluated **at the `defer` statement** — copies happen then, not at function exit. If they want extra color: the runtime keeps defers on a **per-function chain** and walks it **backwards** on return or panic.

**Q2: What happens with a named result and a defer that mutates it?**

The named result is **one live variable**. The `return expr` step assigns into it, then defers run, then the function returns the **final** value. That is the "double return" trick — clever in puzzles, use sparingly in production.

**Q3: Why `recover` in HTTP middleware, and what does it *not* cover?**

Middleware wraps **one request's** call stack. A `defer` + `recover` there can log a panic, return a **500**, and keep the process alive **for panics in that stack**. It does **not** catch panics in goroutines the handler fired **without** their own guard rails — those can still **crash the program**. You fix that with **worker-local** `recover` or structured error returns.

---

## 12. Final Verbal Answer

`defer` schedules cleanup when **this function** exits — on normal return or while unwinding a panic on **this goroutine**. Arguments are fixed at the **`defer` line**; order is **LIFO**. **`recover` only works inside a deferred function on the panicking goroutine** — parents do not catch children. In servers, middleware **`recover` is a safety net for the request stack**, not a substitute for disciplined goroutines. **`defer rows.Close`**, **`defer tx.Rollback`**, and **`defer span.End`** are the bread and butter patterns. Performance-wise, defer is **free enough** in handlers; second-guess it only in **tight inner loops** at huge scale, with profiling.

---

## 13. Comprehensive Interview Questions

> Full interview question bank (see companion file) → [[questions/T10 Defer, Panic & Recover Internals - Interview Questions]]

**Preview questions (answer in the bank):**
- When are **`defer` arguments** evaluated, and how is that different from a **closure** that captures a **loop** variable on **older** **Go** code?
- **Walk** a **LIFO** **order** of **three** defers, then add a **return** in the **middle** of the **function** — which **deferred** **calls** run?
- **Design** a **HTTP** **server** that **logs** a **request** **id** and **converts** **handler** **panics** to **500** while **leaving** a **separate** **goroutine** **pool** **safe** from **unhandled** **child** **panics**.

---

> See [[Glossary]] for term definitions.
