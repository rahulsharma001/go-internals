# P07 Functions, Closures & Variable Capture

> **Prerequisite note** — complete this before starting [[T13 Goroutine Internals]].
> Estimated time: ~20 min

---

## 1. Concept

A **closure** is a function that remembers variables from where it was created.

You already use functions everywhere in backend code: handlers, middleware, retries, background jobs. When that function is defined **inside** another function (or block) and it reads names from outside its own parameter list, Go ties that inner function to those outer names. That bundle — the function plus the remembered variables — is what people mean by a closure.

You don't need a compiler course to use this. You need a clear picture of **what** gets remembered and **whether** it's one shared slot or a fresh copy per call.

---

## 2. Core Insight (TL;DR)

**Functions are values.** You can store them, pass them, return them. A handler is just a value whose type is `func(http.ResponseWriter, *http.Request)`.

**Closures remember outer variables by reference, not by snapshot.** If ten goroutines all close over the same loop variable, they all read the **same** storage. When the loop finishes, that storage often holds the **last** value. That's the famous loop trap.

**Middleware is closures all the way down.** `AuthMiddleware(secret)` returns a function. That returned function closes over `secret`. Each request runs your inner function; it still sees the same `secret` the factory saw when you wired the chain.

**Go 1.22** gave each `for` loop iteration fresh variables for the index and range value. That fixes a lot of accidental bugs. You should still know the classic model: **one variable reused per iteration** is how people reason about capture, and it's how older code and interviews still talk about it.

---

## 3. Mental Model (Lock this in)

Think **sticky note on a shared whiteboard**, not **a photo of the whiteboard**.

When a closure "remembers" `secret` or `job`, it remembers **where that name lives**. If the outer code changes what's in that slot, the closure sees the update. If five closures all point at the **same** slot (same loop variable), they all see the same final value.

**Error-driven picture — middleware:** You build `AuthMiddleware("hunter2")` once. The function you get back is not a copy of the string for each request. It's code that always reads the **same** `secret` binding until that middleware value is garbage-collected.

**Error-driven picture — loop:** You write `for _, job := range jobs { go func() { process(job) }() }`. Every goroutine's function closes over **one** `job` variable. The loop keeps reusing that name. By the time the goroutines run, that name usually holds the **last** job.

---

## 4. How It Works

### 4.1 First-class functions (nothing fancy)

In Go, a function type is a type like `func(context.Context) error`. You assign it to variables, pass it to helpers, return it from constructors.

Your HTTP server does this constantly: you pass `http.HandlerFunc(...)` to `mux.Handle`. That value might be a plain function with no captures, or it might close over `db`, `logger`, `featureFlags` — then it's a closure.

---

### 4.2 Middleware factory: closing over configuration

You want HMAC or JWT checks. The **secret** (or key id, or verifier) is fixed at startup. The thing that varies per request is the next handler in the chain.

```go
func AuthMiddleware(secret string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.Header.Get("X-Auth") != secret {
				http.Error(w, "unauthorized", http.StatusUnauthorized)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}
```

- The **outer** function takes `secret` once.
- The **middle** function takes `next` when you compose the chain.
- The **inner** `ServeHTTP` closes over both `secret` and `next`.

Every request hits that inner function. It reads the **same** `secret` every time. You did not pass `secret` on every `ServeHTTP` call; the closure remembers it.

Chaining looks like `AuthMiddleware(secret)(LoggingMiddleware(log)(mux))`: each layer returns an `http.Handler` that wraps `next`, so you get nested closures and one `ServeHTTP` path through the stack.

```
MEMORY TRACE — middleware captures secret:

Step 1: You call AuthMiddleware("hunter2").
  stack:
    factory frame: secret ──→ "hunter2"

Step 2: The returned func(http.Handler) http.Handler is a closure. It needs
        to keep using secret after AuthMiddleware returns. The compiler stores
        the live secret binding where the closure can reach it (typically heap).
  heap:
    captured_secret ──→ "hunter2"
    closure_A (the func(next http.Handler) http.Handler you got back)
      function code ──→ "build inner handler"
      remembers ──→ &captured_secret

Step 3: Later you do chain := AuthMiddleware("hunter2")(nextHandler).
        The innermost http.HandlerFunc is another closure: it remembers
        secret (same cell) and next (the handler you passed in).
  **Aha:** The inner handler is a function value plus links to outer variables.
          secret is not re-read from a global; it's the same binding the factory closed over.
```

---

### 4.3 Handler closing over `*sql.DB` and a logger

This is the same idea, without nested `return func` noise:

```go
func NewUserHandler(db *sql.DB, log *slog.Logger) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if err := db.PingContext(r.Context()); err != nil {
			log.Error("ping", "err", err)
			http.Error(w, "db down", http.StatusServiceUnavailable)
			return
		}
		w.Write([]byte("ok"))
	})
}
```

`NewUserHandler` returns one function value. That value **remembers** `db` and `log`. Your mux does not pass them on every request — the handler closure carries them.

---

### 4.4 Retry wrapper: the work function closes over your request

```go
func WithRetry(maxAttempts int, fn func() error) error {
	var err error
	for attempt := 1; attempt <= maxAttempts; attempt++ {
		if err = fn(); err == nil {
			return nil
		}
		if attempt < maxAttempts {
			time.Sleep(time.Duration(attempt) * 100 * time.Millisecond)
		}
	}
	return fmt.Errorf("after %d attempts: %w", maxAttempts, err)
}
```

`fn` is often a **closure** built at the call site: it already captured `ctx`, row ids, or an HTTP client. `WithRetry` only calls `fn()`; it does not thread those through. If you instead **return** a function that mutates a single outer `attempt` across calls, that state is shared for every call to that returned func — fine for a limiter, surprising if you expected a fresh counter per caller.

---

### 4.5 Rate limiter factory per tenant

You want one limiter function per tenant id, each with its own window and count:

```go
func NewTenantLimiter(requestsPerMinute int) func() bool {
	var count int
	var windowStart time.Time
	return func() bool {
		now := time.Now()
		if now.Sub(windowStart) > time.Minute {
			windowStart = now
			count = 0
		}
		if count >= requestsPerMinute {
			return false
		}
		count++
		return true
	}
}

// usage: limiter := NewTenantLimiter(100); if !limiter() { return 429 }
```

Each call to `NewTenantLimiter` creates **new** `count`, **new** `windowStart`, and **new** closure. Different tenants get different factories — different remembered state.

---

## 5. Key Rules & Behaviors

### Capture is by reference

If the closure sees a variable `x` from outside and you assign `x = 2` before calling the closure, the closure prints `2`. It was never a frozen copy of `x` at the moment you defined the function.

```go
x := 1
f := func() { fmt.Println(x) }
x = 2
f() // 2
```

---

### The loop trap: goroutines and one shared variable

Classic bug — still worth knowing for old Go, interview questions, and **mental discipline**:

```go
for _, job := range jobs {
	go func() {
		process(job) // every goroutine reads the SAME job variable
	}()
}
```

The `job` name is reused each iteration. Every goroutine's function closes over **that one** `job`. When they run, they often all process the **last** job.

```
MEMORY TRACE — loop trap (jobs):

Step 1: for _, job := range jobs — one variable job; each iteration assigns the next element to the SAME name.
  stack (conceptually):
    job ──→ Job{ID: "a"}  then  Job{ID: "b"}  then  Job{ID: "c"}

Step 2: Each go func() { process(job) }() creates a closure. Each closure remembers
        the same job slot — not a snapshot of "a", "b", "c" at spawn time.
  heap (conceptual):
    shared_job ──→ (whatever job points at when goroutines actually read it)
    closure_g1, closure_g2, closure_g3 each "remembers" ──→ &shared_job

Step 3: The loop finishes; shared_job holds the last element. Goroutines run process(job).
  **Aha:** Three goroutines, one variable. You get triple work on the last job, not parallel work on a, b, c.
```

---

### Fix: give each goroutine its own copy

Pass the value as a parameter. Parameters are **new** slots per call:

```go
for _, job := range jobs {
	j := job
	go func() {
		process(j)
	}()
}

// or, equivalently:
for _, job := range jobs {
	go func(j Job) {
		process(j)
	}(job)
}
```

```
MEMORY TRACE — fix with parameter:

Step 1: go func(j Job) { process(j) }(job) — the current job is evaluated NOW and copied into j for THIS goroutine.

Step 2: Goroutine A's frame has j ──→ copy of job "a". Goroutine B has j ──→ "b".
        Each closure may still close over its own j (per-goroutine), not the loop's single job slot.

  **Aha:** Copy at spawn time breaks the sharing. Same pattern fixes for i, id, file path, etc.
```

---

### Defer in a loop: leaks and late cleanup

`defer` runs when the **function** returns, not when the **iteration** ends. A `defer f.Close()` inside `for _, path := range paths` queues one defer per file, but **all** of them run when the **outer** function exits — so you keep every file open until then.

Fix: give each iteration its own function frame — extract `processFile(path string) error` or use a small inline wrapper so `defer` runs after that iteration's body:

```go
for _, path := range paths {
	err := func() error {
		f, err := os.Open(path)
		if err != nil {
			return err
		}
		defer f.Close()
		// read f...
		return nil
	}()
	if err != nil {
		return err
	}
}
```

Here the inner `func` closes over `path` for that iteration, but the point is **defer scope**, not sharing mutable loop state across goroutines.

---

### Go 1.22 loop variables

Since **Go 1.22**, each iteration of a `for` loop creates **new** variables for the loop index and the range value. Many `go func() { use(i) }()` bugs go away without `i := i`.

You still need the mental model when:

- You touch code written for older Go.
- Someone asks **why** the old pattern was broken.
- You mutate a **single** outer struct or slice header and share it across goroutines — the language didn't fix that for you.

---

## 6. Code Examples (Show, Don't Tell)

The backend-shaped examples live in Section 4: `AuthMiddleware(secret)`, `NewUserHandler` (handler closes over `*sql.DB` and logger), `WithRetry` with a caller-built `fn`, `NewTenantLimiter`, plus the job loop and defer pattern in Section 5. No extra toy `apply`/`twice` snippets — same spirit as the rest of this series.

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the behavior (2 min)

You register this handler. Will every request see the same `secret`? Why?

```go
func mount(mux *http.ServeMux, secret string) {
	mux.HandleFunc("/ping", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Query().Get("key") != secret {
			http.Error(w, "nope", http.StatusUnauthorized)
			return
		}
		w.Write([]byte("pong"))
	})
}
```

> [!success]- Answer
> Yes. The `func(w, r)` closes over `secret` from `mount`'s parameter. All requests to `/ping` hit the same handler value, which reads the **same** `secret` binding you passed when you called `mount`. If you needed a different secret per route, you'd call `mount` again with a different argument or pass secret through a different factory.

---

### Tier 2: Fix the bug (5 min)

Workers should each process their own job id. Today they all process the last id on Go 1.21-style semantics. Fix it without relying on Go 1.22 loop changes.

```go
func spawnWorkers(jobs []string, process func(string)) {
	var wg sync.WaitGroup
	for _, jobID := range jobs {
		wg.Add(1)
		go func() {
			defer wg.Done()
			process(jobID)
		}()
	}
	wg.Wait()
}
```

> [!success]- Answer
> Pass `jobID` into the goroutine (or assign `jid := jobID` inside the loop body and capture `jid`):
>
> ```go
> for _, jobID := range jobs {
> 	wg.Add(1)
> 	go func(id string) {
> 		defer wg.Done()
> 		process(id)
> 	}(jobID)
> }
> ```
>
> Every goroutine gets its **own** `id` parameter — a copy at launch time — instead of sharing the loop variable's single slot.

---

## 7. Gotchas & Interview Traps

| Trap | What happens | What to say |
|------|--------------|-------------|
| `go func() { use(i) }()` in a loop | All goroutines see final `i` (classic) | "They share one variable. Pass `i` as a param or copy per iteration." |
| `defer` inside a plain `for` | Defers run when the **outer** function returns | "Wrap the body in a function or extract a helper so defer runs per iteration." |
| Assuming closure = snapshot | You expected the value at **define** time | "Closures see live outer bindings. Copy into a local or parameter if you need a snapshot." |
| Storing handlers with shared mutable outer state | Race or wrong tenant data | "If outer state mutates, guard it or pass values explicitly. Don't share maps without sync." |
| "Go 1.22 fixed closures" | Oversimplified | "Loop vars are per-iteration now, but capture and shared state still need thinking." |

---

## 8. Interview Gold Questions (Top 3)

**Q1: What is a closure in Go?**

A function value that remembers variables from the enclosing scope — for example, a handler that closes over `*sql.DB` and a logger, or middleware that closes over a signing secret. Those names are live bindings, not automatic snapshots.

**Q2: Why do goroutines in a loop sometimes all use the last index or element?**

The loop reuses one variable. Every goroutine's function closes over **that** variable's storage. When the goroutines run, they read whatever value it has after the loop advances — usually the last one. Fix: pass the value as an argument or introduce a per-iteration copy.

**Q3: How does middleware relate to closures?**

A factory like `AuthMiddleware(secret)` returns a function that returns a handler. The inner `ServeHTTP` closes over `secret` and `next`. You compose chains by nesting those function values — each layer wraps the next.

---

## 9. 30-Second Verbal Answer

Functions in Go are first-class values. A **closure** is a function that **remembers** variables from where it was created — middleware remembering a secret, a handler remembering `db` and a logger. Those variables are **shared bindings**, not frozen copies, unless you copy into parameters or locals. That's why **`go func()` in a loop** without passing the loop variable makes every goroutine see the **last** value. Fix by passing the current value into the goroutine or copying per iteration. **`defer` in a loop** without a per-iteration function can defer cleanup until the outer function returns. Go 1.22 made new loop variables each iteration, but you still reason about capture whenever you share outer state.

---

> See [[Glossary]] for term definitions.
