# T09 Error Handling Patterns

> **Reading Guide**: Sections 1-3 and 6 are essential first read (20 min).
> Sections 4-5 deepen understanding (15 min).
> Sections 7-12 are interview-specific — read closer to interview day.
> Section 13 is your comprehensive interview Q&A bank → [[questions/T09 Error Handling Patterns - Interview Questions]]
> Something not clicking? → [[simplified/T09 Error Handling Patterns - Simplified]]

---

## 0. Prerequisites

Complete these before starting this topic:

- [[prerequisites/P05 Interfaces Basics]]

---

## 1. Concept

In Go, **`error` is a built-in interface** with a single method: `Error() string`. Any concrete type that implements that method is an error. There is no `try` or `throw`. **Errors are values.** You return them. You test them. You do not "catch" them up the stack by default.

You handle failure by writing **`if err != nil`** and branching. The happy path keeps reading straight down. The failure path short-circuits with `return` or `continue`.

In some languages, errors are like air horns that go off in another room. In Go, errors are a slip of paper you hand to the next person. That person must read the slip. If they ignore it, the mistake stays.

---

## 2. Core Insight (TL;DR)

**Go treats errors as ordinary values that flow through your code.** The philosophy: be explicit, fail fast, and carry enough context to debug. **The interview gold** is the trio **sentinel errors**, **custom error types**, and **wrapping with `%w`**, then unwrapping with **`errors.Is`** and **`errors.As`**. If you can explain that chain clearly, you have shown senior-level Go.

You do not hope someone notices a flashing light. You pass a labeled note: what broke, and where, in order.

---

## 3. Mental Model (Lock this in)

### The Letter in Many Envelopes

Imagine a real letter. Each function that fails puts that letter into a new envelope. On the front of the envelope, someone writes what step failed: "read file", "parse JSON", and so on. The original letter is still inside.

- **`errors.Is`** keeps opening envelopes until it finds a letter that matches a specific stamp you care about, like `os.ErrNotExist`.
- **`errors.As`** keeps opening until it finds an envelope of a **specific shape** — for example, a red envelope with a form inside your custom type, so you can read extra fields.

Plain `==` only compares the **outer** envelope, not the letter hidden inside after wrapping. That is the trap.

`==` sees only the last envelope. `Is` and `As` are willing to open every layer to find the original note or the right kind of case file.

### Mistake That Teaches You: `==` After Wrapping

```go
package main

import (
	"errors"
	"fmt"
	"os"
)

func main() {
	var ErrNotFound = errors.New("not found")
	wrapped := fmt.Errorf("lookup user: %w", ErrNotFound)
	fmt.Println(wrapped == ErrNotFound)         // false — compares outer value only
	fmt.Println(errors.Is(wrapped, ErrNotFound)) // true — follows unwrap chain
	_ = os.ErrNotExist
}
```

**Why it breaks:** Wrapping builds a new error value. That value is not equal to the original sentinel. The chain of `Unwrap()` calls is what links them. `errors.Is` walks that chain. `==` does not.

---

## 4. How It Actually Works (Internals) [INTERMEDIATE → ADVANCED]

Small values, sometimes with an inner `error` linked by `Unwrap()`.

### 4.1 The `error` Interface (Just `Error() string`)

```go
// From the spec — roughly what you are matching against
type error interface {
	Error() string
}
```

`string` and `*MyError` are different types, but if both implement `Error() string`, both satisfy `error`.

"Error" here means "I can print a one-line message." The language does not care what struct you used to build that line.

### 4.2 Sentinel Errors — `errors.New` and `*errorString`

```go
var ErrNotFound = errors.New("not found")
```

`errors.New` allocates a private pointer type in the standard library, often shown in docs as **`errorString`**. The pointer identity matters: two `errors.New("same")` calls give two **different** sentinels.

Two calls to `errors.New("x")` yield **different pointers**, so **`==`** between them is **false**.

A sentinel is a pre-printed form with a unique serial number. Two forms can say the same words but still be two different papers.

### 4.3 Error Wrapping — `fmt.Errorf` with `%w` and `*fmt.wrapError`

```go
import "fmt"
wrapped := fmt.Errorf("load config: %w", err) // build link to `err`
```

The **`%w` verb** creates a value that usually implements **`Unwrap() error`**. The concrete type is often documented as **`wrapError`**. The **`%v` verb** only formats text. It does not attach an unwrap target.

`%w` is a window in the new envelope. Helpers can look through the window at the old letter. `%v` is a photocopy of the text on the new envelope only — the window is missing.

### 4.4 The Unwrap Chain — `errors.Is` and `errors.As` Walk the Chain

```go
errors.Is(err, target)  // is `target` anywhere in the unwrap chain?
var ve *ValidationError
errors.As(err, &ve)     // find first error assignable to *ValidationError, set `ve`
```

**`errors.Is`** compares the chain with equality rules that understand sentinels and **Unwrap** steps.

**`errors.As`** tries type assertion at each level of the chain until one matches, then populates the pointer you passed.

`Is` asks "is this the same bad news, even through several retellings?" `As` asks "does any layer use our company's form?"

### 4.5 Custom Error Types — `Error()` and Optional `Unwrap()`

```go
type ValidationError struct {
	Field, Reason string
}

func (e *ValidationError) Error() string {
	return "validation: " + e.Field + ": " + e.Reason
}

// If this error wraps another:
func (e *ValidationError) Unwrap() error { return e.cause } // if you store one
```

If your type can wrap, implement **`Unwrap`**. Callers can then use **`errors.Is` / `errors.As` through your type.

A custom type is a company-branded case folder. It has extra fields. The folder can still enclose an older letter if you add an inner slot.

---

## 5. Key Rules & Behaviors

### Rule 1: Always Check `err != nil` Before Using the Result

```go
f, err := os.Open("cfg.json")
if err != nil { // do this FIRST
	return err
}
defer f.Close()
// only now safe to read from `f`
```

You do not start reading a book before checking someone actually handed you a book. The handle might be empty.

### Rule 2: Wrap Errors at Abstraction Boundaries with `%w`

This is the backbone pattern: low-level storage speaks `database/sql`, domain code speaks your sentinels and messages.

```go
var ErrUserNotFound = errors.New("user not found")

func dbGet(id int) error {
	// pretend: QueryRow.Scan fails with sql.ErrNoRows when missing
	return sql.ErrNoRows
}

func LoadUser(id int) error {
	_, err := dbGet(id)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return fmt.Errorf("load user %d: %w", id, ErrUserNotFound)
		}
		return fmt.Errorf("load user %d: %w", id, err)
	}
	return nil
}
```

The moving truck writes your name on a new label, but the old sticker from the furniture shop is still visible through a plastic window. Delivery staff can read both.

### Rule 2b: Map Errors to HTTP at the Edge (Handler), Not in the Repo

The **repository** should not import `net/http`. The **handler** (or a thin `api` package) decides status codes from error shape:

- **`sql.ErrNoRows`** or **`errors.Is(err, ErrUserNotFound)`** → **404 Not Found** (resource missing).
- **`ValidationError`** (or **`errors.As` into your validation type)** → **400 Bad Request** (client sent bad input).
- **Auth failures you classify** → **401 / 403** depending on your model.
- **Everything else** in a public API → **500 Internal Server Error** (log the real chain; return a safe message).

See **§6 — Handler sketch** for a concrete `switch` on **`errors.Is` / `errors.As`**. That keeps "what happened in the database" separate from "what the client is allowed to know."

### Rule 2c: Middleware — Log Once, Attach Request Context, Then Wrap

A common pattern: generate a **request ID**, put it in **`context`**, and when something fails deep in the stack, wrap so operators can grep logs.

```go
type ctxKey string

const reqIDKey ctxKey = "request_id"

func WithRequestID(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		id := r.Header.Get("X-Request-ID")
		if id == "" {
			id = "gen-" + shortID() // your UUID / snowflake / whatever
		}
		ctx := context.WithValue(r.Context(), reqIDKey, id)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func RequestIDFrom(ctx context.Context) string {
	id, _ := ctx.Value(reqIDKey).(string)
	return id
}

func wrapReq(ctx context.Context, msg string, err error) error {
	if err == nil {
		return nil
	}
	return fmt.Errorf("%s (req_id=%s): %w", msg, RequestIDFrom(ctx), err)
}
```

Deep code does `return wrapReq(ctx, "load user", err)` so the unwrap chain is still intact for `errors.Is` / `errors.As`, but logs and dashboards have a correlation handle.

### Rule 2d: Retryable vs Non-Retryable

Not every failure deserves a retry loop.

- **Retry:** transient network blips, **deadline exceeded** on an upstream you trust, **503** with **`Retry-After`**, optional **idempotency key** on writes.
- **Do not retry:** **validation errors**, **4xx** you caused, **business rule violations**, **duplicate key** you cannot fix by hammering the same payload.

One light pattern is a **marker interface or sentinel** the retry middleware understands:

```go
var ErrRetryable = errors.New("retryable")

type TemporaryError struct{ Cause error }

func (e *TemporaryError) Error() string { return "temporary: " + e.Cause.Error() }
func (e *TemporaryError) Unwrap() error { return e.Cause }

// Wrap: fmt.Errorf("call payments: %w", &TemporaryError{Cause: ctx.Err()})
```

The **retry policy** checks `errors.Is(err, ErrRetryable)` or **`errors.As` into `*TemporaryError`**; the **handler** still maps "gave up after retries" to **502/504** as appropriate.

### Rule 2e: Error Boundary — `*RepoError` Inside, `*APIError` at the Edge

Inside `internal/userrepo`, return errors that make sense for **your team**: operation name, maybe store-specific codes. At the **HTTP boundary**, convert to something safe for **users and frontends**.

```go
// internal/userrepo
type RepoError struct {
	Op   string
	Err  error
}

func (e *RepoError) Error() string { return e.Op + ": " + e.Err.Error() }
func (e *RepoError) Unwrap() error { return e.Err }

// api layer
type APIError struct {
	Status  int    // HTTP status
	Public  string // safe for JSON body
	Cause   error  // for logs only
}

func (e *APIError) Error() string { return e.Public }
func (e *APIError) Unwrap() error { return e.Cause }

func MapRepoToAPI(err error) *APIError {
	var re *RepoError
	if errors.As(err, &re) && errors.Is(re.Err, sql.ErrNoRows) {
		return &APIError{http.StatusNotFound, "not found", err}
	}
	return &APIError{http.StatusInternalServerError, "internal error", err}
}
```

The **public** string is boring on purpose; **Cause** still unwraps for structured logs.

### Rule 3: Use `errors.Is` for Sentinels, `errors.As` for Type Extraction

```go
if errors.Is(err, os.ErrNotExist) {
	// file missing
}
var v *ValidationError
if errors.As(err, &v) {
	_ = v.Field
}
```

`Is` checks for a known stamp. `As` looks for a specific folder shape and hands you the folder so you can open the extra tabs.

### Rule 4: Do Not Wrap Twice with the Same Context

**Bad — messy chain:**

```go
if err != nil {
	return fmt.Errorf("service: %w", fmt.Errorf("service: %w", err)) // repeated label
}
```

**Better — one wrap at this layer:**

```go
if err != nil {
	return fmt.Errorf("service: %w", err)
}
```

You do not put two identical address labels on the same box. One clear label is enough.

### Rule 5: Return `nil` for Success; Avoid the Typed Nil Interface Trap

```go
type AppError struct{ msg string }
func (e *AppError) Error() string { return e.msg }

// Returns typed nil: pointer value is nil, but type is *AppError
func f() *AppError { return nil }

func g() error {
	return f() // BUG: interface = (type *AppError, data nil) — not equal to untyped nil `error`
}
```

**Fix: convert through `error` the safe way, or return only `error` with an explicit `nil`:**

```go
func gOK() error {
	var p *AppError = f() // f returns nil *AppError
	if p != nil {
		return p
	}
	return nil // untyped nil → real nil `error` interface
}
```

Or avoid returning a **concrete** pointer-typed function into an **`error` result** without that guard. The underlying issue is: an `interface` value is a **pair** of dynamic type and data. A nil pointer with a named type is still a non-nil **interface** value.

A labeled empty tray is not "no tray." The label *AppError is still there. A truly empty hand — no type label — is what `nil` means for `error`.

### Rule 6: The `(*User, *NotFoundError)` Shape — `nil, nil` vs `error`

Some teams return **data + typed error pointer** so callers can branch without losing type information:

```go
type NotFoundError struct{ Resource string }

func (e *NotFoundError) Error() string {
	return e.Resource + " not found"
}

func getUser(id string) (*User, *NotFoundError) {
	if id == "" {
		return nil, &NotFoundError{Resource: "user"}
	}
	return &User{Name: "Ada"}, nil
}
```

When nothing is wrong, the second value is **`nil` of type `*NotFoundError`**. That is fine **until** someone promotes it to **`error`** without thinking:

```go
func LoadForAPI(id string) (*User, error) {
	u, nf := getUser(id)
	return u, nf // nf is nil *NotFoundError → non-nil `error` interface!
}

func main() {
	_, err := LoadForAPI("valid-id")
	fmt.Println(err != nil) // true — BUG: success looks like failure
}
```

**Fix:** only put a real `error` in the second position when it is non-nil, or change `getUser` to return `(*User, error)` and use **`var err error`** / **`return nil, nil`** through a single `error` typed return.

---

## 6. Code Examples (Show, Don't Tell)

### Sentinel Error Pattern

```go
var ErrUserNotFound = errors.New("user not found")

func FindUser(id int) error {
	return ErrUserNotFound
}
```

**Trap — compare with `==` after wrap:**

```go
w := fmt.Errorf("repo: %w", ErrUserNotFound)
_ = w == ErrUserNotFound // false
```

### Custom Error Type With Extra Fields

```go
type ValidationError struct {
	Field, Msg string
}

func (e *ValidationError) Error() string {
	return e.Field + ": " + e.Msg
}

// usage
return &ValidationError{Field: "email", Msg: "invalid"}
```

### Error Wrapping Chain and Unwrapping

```go
root := os.ErrNotExist
layer1 := fmt.Errorf("open config: %w", root)
layer2 := fmt.Errorf("bootstrap: %w", layer1)

errors.Is(layer2, os.ErrNotExist) // true
```

### Handler Sketch: `svc.GetUser` → Status Code

```go
func (h *Handler) GetUser(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id") // 1.22+; or mux.Vars, etc.
	user, err := h.svc.GetUser(r.Context(), id)
	if err != nil {
		h.handleErr(w, err)
		return
	}
	json.NewEncoder(w).Encode(user)
}

func (h *Handler) handleErr(w http.ResponseWriter, err error) {
	var ve *ValidationError
	switch {
	case errors.Is(err, ErrUserNotFound) || errors.Is(err, sql.ErrNoRows):
		http.Error(w, "not found", http.StatusNotFound)
	case errors.As(err, &ve):
		http.Error(w, ve.Error(), http.StatusBadRequest)
	default:
		h.log.Error("request failed", "err", err)
		http.Error(w, "internal error", http.StatusInternalServerError)
	}
}
```

Your service should **`fmt.Errorf("get user: %w", err)`** and map **`sql.ErrNoRows` → `ErrUserNotFound`** so the handler can use **`errors.Is(err, ErrUserNotFound)`** only — then **`database/sql`** never lands in HTTP packages. The **`sql.ErrNoRows`** branch above is for small services where that tradeoff is acceptable.

---

## 6.5. Practice Checkpoint

All runnable in [Go Playground](https://go.dev/play/).

### Tier 1: Handler wiring (3 min)

Your handler calls `user, err := svc.GetUser(ctx, id)`. `GetUser` wraps repo errors with `%w`. The repo returns **`sql.ErrNoRows`** when the row is missing.

Write the `if err != nil` block that sets **404** for missing users, **400** if `errors.As` finds your **`ValidationError`**, and **500** otherwise — without importing `database/sql` in the handler package (you may use **`errors.Is(err, ErrUserNotFound)`** if the service maps `ErrNoRows` to **`ErrUserNotFound`** before returning).

> [!success]- Answer
> Map **`sql.ErrNoRows`** to **`ErrUserNotFound`** in the **service** so the handler never imports **`database/sql`**. Then: **`errors.Is` → 404**, **`errors.As` into `ValidationError` → 400**, **else → 500** (after logging).

### Tier 2: Predict the Output (2 min)

```go
package main

import (
	"errors"
	"fmt"
)

var S = errors.New("S")

func main() {
	e := fmt.Errorf("a: %w", fmt.Errorf("b: %w", S))
	fmt.Println(e == S)
}
```

**Predict before run:** prints `true` or `false`?

> [!success]- Answer
> Prints **`false`**. The `==` operator compares the outer value. `e` is a wrapped error, not the sentinel `S`. Use **`errors.Is(e, S)`** → **`true`**.

### Tier 3: Fix the Bug (5 min)

```go
type RepoError struct{ s string }
func (e *RepoError) Error() string { return e.s }

func maybeFail(ok bool) *RepoError {
	if !ok { return &RepoError{"fail"} }
	return nil
}

func API() error {
	return maybeFail(true) // should be success, but is it?
}
```

**Goal:** `API()` should return a nil `error` on success. Fix the typed-nil interface issue.

> [!success]- Answer
> Typed **`nil` `*RepoError`** in an **`error`** slot is still a **non-nil interface**. Guard with **`if err != nil { return err }; return nil`**, or return **`error`** from **`maybeFail`**.

### Tier 4: Build It (15 min)

Package with a **validation** type (`Error()` + **`errors.As`**), a **`%w`** wrap from an inner failure, and a handler that returns **400** vs **500**.

> Full solutions with explanations → [[exercises/T09 Error Handling Patterns - Exercises]]

---

## 7. Edge Cases & Gotchas

**The wrapped sentinel you compare with `==`.** You promoted a note into a new envelope, then you hold the envelope up to the light and wonder why it does not look identical to the original stamp. **`errors.Is`** opens the stack; **`==`** does not.

**The handler that swears `err == nil` but logging still fires.** Somewhere below, a function returned **`nil` `*MyError`** into an **`error` return**. The interface is non-nil even though the pointer inside is. Fix by returning **`var err error`** and assigning only real failures, or by guarding before you **`return err`**.

**The `%v` wrap that breaks the chain.** You printed the inner text on the outside label and threw away the window. **`errors.Is`** cannot see through **`%v`**. If consumers need to unwrap, use **`%w`**.

**The `_ = f()` line in a hot path review.** That is not "clean code." That is dropping a slip on the floor. If you truly ignore an error, leave a comment that names the human who accepted the risk and why — better, handle it.

---

## 8. Performance & Tradeoffs

Wrapping with **`%w`** allocates a small wrapper and adds one more pointer hop when you walk the chain. In normal HTTP and service code, that cost is **noise next to I/O**: one database round trip or TLS handshake dominates your latency budget thousands of times over.

What **does** hurt is **logging every unwrap layer on every request**, serializing huge stacks to Splunk, or building giant `fmt.Errorf` strings with expensive `Sprintf` work in a tight loop. Keep wraps **short and structured**; log **once** at the boundary with the **request ID**; let metrics aggregate error codes instead of printing novels.

Sentinels stay cheap — one pointer compare after `Is` walks a short chain. Custom types cost a little more but buy you **`As`** and fields for **400** responses. If a boundary already exposes a stable, meaningful error and another sentence adds nothing, returning as-is is fine.

---

## 9. Common Misconceptions

**"Every `errors.New("foo")` is its own Go named type."** Nope — you get another pointer to the same **`errorString` idea**. Identity is **pointer equality**, not string equality. Two different calls with the same text are still two different errors.

**"`panic` is how production Go signals 'file not found'."** **`panic`** is for **programmer mistakes** and **unrecoverable** states — or truly rare init failures — not for "user typed bad JSON." Normal control flow returns **`error`**.

**"Always wrap, no matter what."** Wrap when you add **location** or **domain meaning**, or when callers need **`Is`/`As`**. Repeating the word **"service"** five times in the chain is just clutter.

**"`==` is fine; I control the whole repo."** The day someone adds **`fmt.Errorf("...: %w", err)`** above you, **`==`** goes quiet. Default to **`errors.Is`** for sentinels unless you have a **very** local, unexported helper.

---

## 10. Related Tooling & Debugging

`errcheck` is the friend who taps your shoulder when you ignore a return value. **`go vet`** catches a few suspicious patterns; teams usually add **staticcheck** for deeper linting. None of that replaces thinking — it catches the obvious foot-guns so code review can focus on **mapping** and **messages**.

Run **`go vet ./...`** in CI. Treat ignored errors like failing tests: either handle them or document the rare exceptions.

---

## 11. Interview Gold Questions

If someone asks **`Is` vs `As`**, say: **`Is`** hunts for a **value** (often a sentinel) anywhere in the unwrap stack; **`As`** finds the first **typed** shape and fills your pointer so you can read **fields**. Mention **`%w`** or you look like you memorized flash cards.

If they ask **`%w` vs `v`**, say **`%w`** keeps the **link** so **`Unwrap` / `Is` / `As`** still work; **`%v`** is a **pretty print** that **cuts** the chain.

If they ask the **typed nil** question, draw the **(type, data)** pair in the air: **`nil` `*T` inside `error`** still has type **`T`**, so the interface is **non-nil**. The fix is **explicit `return nil`** as **`error`**, or **`return err` only when `err != nil`**.

---

## 12. Final Verbal Answer

Go's **`error`** is just **`Error() string`**. You **`return`** failures; you **`if err != nil`**; you do not route normal cases through **`panic`**. In real services you **wrap** with **`%w`**, map to **HTTP** at the edge, **log once** with a **request ID**, and use **`Is`/`As`** so **404 / 400 / 500** stay honest. Avoid **`==`** after wraps, avoid **typed nil** surprises when you promote pointers to **`error`**, and treat **retries** as policy — not every error deserves another POST.

---

## 13. Comprehensive Interview Questions

> Full interview question bank (comprehensive Q&A) → [[questions/T09 Error Handling Patterns - Interview Questions]]

**Preview questions:**

1. How does `errors.Is` differ from a plain value comparison, and when does the difference matter in real code?
2. How would you design error types for a public library vs an internal service?
3. What happens if a function returns `*MyError` with value `nil` in a `error` return position?

---

> See [[Glossary]] for term definitions.
