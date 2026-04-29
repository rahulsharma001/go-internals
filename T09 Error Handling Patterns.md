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

```
  ┌─────────────────────────────────────────────┐
  │  handler envelope: "get user: ..."          │
  │  ┌─────────────────────────────────────┐    │
  │  │  service envelope: "lookup: ..."    │    │
  │  │  ┌─────────────────────────────┐    │    │
  │  │  │  original letter:           │    │    │
  │  │  │  ErrNotFound (sentinel)     │    │    │
  │  │  └─────────────────────────────┘    │    │
  │  └─────────────────────────────────────┘    │
  └─────────────────────────────────────────────┘
       ↑                        ↑
   == sees ONLY this       errors.Is opens
   outer envelope          every layer inside
```

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

### 4.1 The `error` Interface — What Lives in Memory

Every Go error — sentinel, custom struct, wrapped chain — ends up stored in the same kind of container. Before looking at any specific pattern, you need to understand what that container looks like in memory. Once you see the two-slot layout, everything else in this topic (sentinel identity, wrapping chains, the typed nil trap) clicks into place.

`error` is an interface. Every interface value in Go is a **16-byte container** with two slots: a **type pointer** (what concrete type is inside?) and a **data pointer** (where does the actual value live?).

```go
package main

import (
	"errors"
	"fmt"
	"unsafe"
)

func main() {
	var err error = errors.New("something broke")
	fmt.Println("size of error interface:", unsafe.Sizeof(err))  // 16
	fmt.Println("err:", err)                                       // something broke
	fmt.Printf("type: %T\n", err)                                 // *errors.errorString
}
```

```
Step 1: errors.New("something broke") creates a *errorString on the heap
  heap 0xC000010040: errorString{ s: "something broke" }

Step 2: var err error = ... stores it in the interface container
  stack (err): [ type ptr → *errors.errorString | data ptr → 0xC000010040 ]
                       ↑                               ↑
                 "what type is inside"          "where the actual value lives"

Step 3: err.Error() → Go reads the type ptr → finds Error() method → calls it
  Returns "something broke"

KEY:
  err is NOT a string. err is a 16-byte interface box.
  The box says "I contain a *errors.errorString at address 0xC000010040."
  When err == nil, BOTH slots are nil: [ type: nil | data: nil ]
```

> **In plain English:** An `error` is a labeled box. The label says what type of error is inside (sentinel? custom struct?). The box holds a pointer to the actual error data. When you compare errors, you're comparing boxes — not the messages printed on them.

### 4.2 Sentinel Errors — Pointer Identity, Not String Equality

`errors.New` returns a `*errorString` — a private type with one field: the message string. The critical insight: **identity is by pointer address, not by message text.**

```go
package main

import (
	"errors"
	"fmt"
)

var ErrNotFound = errors.New("not found")  // sentinel at package level
var ErrAlsoNotFound = errors.New("not found")  // DIFFERENT sentinel, same text

func main() {
	fmt.Println(ErrNotFound == ErrAlsoNotFound)  // false!
	fmt.Printf("ErrNotFound addr:     %p\n", ErrNotFound)      // 0xC000010040
	fmt.Printf("ErrAlsoNotFound addr: %p\n", ErrAlsoNotFound)  // 0xC000010050
}
```

```
Step 1: var ErrNotFound = errors.New("not found")
  heap 0xC000010040: errorString{ s: "not found" }
  ErrNotFound interface: [ type: *errorString | data: 0xC000010040 ]

Step 2: var ErrAlsoNotFound = errors.New("not found")
  heap 0xC000010050: errorString{ s: "not found" }    ← DIFFERENT allocation!
  ErrAlsoNotFound interface: [ type: *errorString | data: 0xC000010050 ]

Step 3: ErrNotFound == ErrAlsoNotFound
  Same type? Yes (*errorString == *errorString)
  Same data pointer? 0xC000010040 != 0xC000010050 → FALSE

  Even though both say "not found", they are DIFFERENT pointers → not equal.

WHY this design:
  If equality were by string, any errors.New("not found") anywhere in your
  codebase would accidentally match YOUR ErrNotFound sentinel.
  Pointer identity means only YOUR specific sentinel matches.
```

Think of it like serial-numbered forms. Two forms can say the same thing, but they have different serial numbers (memory addresses). `errors.Is` checks the serial number — not the text.

### 4.3 Error Wrapping — `%w` Builds a Linked List

When you wrap with `fmt.Errorf("...: %w", err)`, Go creates a `wrapError` struct that holds the formatted message AND a pointer to the original error. This creates a **linked list** of errors.

```go
package main

import (
	"errors"
	"fmt"
)

var ErrDBTimeout = errors.New("database timeout")

func repoCall() error {
	return ErrDBTimeout
}

func serviceCall() error {
	err := repoCall()
	return fmt.Errorf("load user: %w", err)   // wrap layer 1
}

func handlerCall() error {
	err := serviceCall()
	return fmt.Errorf("GET /users/1: %w", err)  // wrap layer 2
}

func main() {
	err := handlerCall()
	fmt.Println(err)  // GET /users/1: load user: database timeout
	fmt.Println(errors.Is(err, ErrDBTimeout))  // true — walks the chain
}
```

```
Step 1: repoCall() returns ErrDBTimeout
  ErrDBTimeout: [ type: *errorString | data: 0xA0 ]
  heap 0xA0: errorString{ s: "database timeout" }

Step 2: serviceCall() wraps with %w
  heap 0xB0: wrapError{
    msg:  "load user: database timeout"
    err:  → ErrDBTimeout (0xA0)     ← linked list pointer!
  }
  Returns: [ type: *wrapError | data: 0xB0 ]

Step 3: handlerCall() wraps again with %w
  heap 0xC0: wrapError{
    msg:  "GET /users/1: load user: database timeout"
    err:  → serviceCall's wrapError (0xB0)     ← another link!
  }
  Returns: [ type: *wrapError | data: 0xC0 ]

THE CHAIN IN MEMORY:

  err (from handler)
  ┌──────────────────────────────────────────────┐
  │ wrapError at 0xC0                            │
  │ msg: "GET /users/1: load user: db timeout"   │
  │ err: ─────────────────────────────────────┐   │
  └───────────────────────────────────────────│───┘
                                              ▼
  ┌──────────────────────────────────────────────┐
  │ wrapError at 0xB0                            │
  │ msg: "load user: database timeout"           │
  │ err: ─────────────────────────────────────┐   │
  └───────────────────────────────────────────│───┘
                                              ▼
  ┌──────────────────────────────────────────────┐
  │ *errorString at 0xA0                         │
  │ s: "database timeout"                        │
  │ (no Unwrap — this is the end of the chain)   │
  └──────────────────────────────────────────────┘

COMPARE with %v (NO link):
  fmt.Errorf("load user: %v", err) creates:
  heap 0xD0: errorString{ s: "load user: database timeout" }
  ← just a string, NO err pointer, NO Unwrap() method
  errors.Is(this, ErrDBTimeout) → false — chain is broken
```

> **In plain English:** `%w` is a window in the envelope — you can reach through it and grab what's inside. `%v` is a photocopy — it prints the same text on the outside, but there's nothing inside to grab. That's why `errors.Is` works with `%w` but fails with `%v`.

### 4.4 How `errors.Is` Walks the Chain — The Algorithm

`errors.Is(err, target)` is a simple loop: compare `err` to `target`, then call `err.Unwrap()` to get the next error, repeat until you find a match or hit the end.

```go
package main

import (
	"errors"
	"fmt"
)

var ErrAuth = errors.New("unauthorized")

func main() {
	layer1 := fmt.Errorf("validate token: %w", ErrAuth)
	layer2 := fmt.Errorf("middleware: %w", layer1)
	layer3 := fmt.Errorf("handler: %w", layer2)

	fmt.Println(errors.Is(layer3, ErrAuth))  // true
	fmt.Println(layer3 == ErrAuth)            // false
}
```

```
errors.Is(layer3, ErrAuth) — step by step:

  Iteration 1: compare layer3 with ErrAuth
    layer3 is wrapError{msg: "handler: ...", err: layer2}
    layer3 == ErrAuth? NO (different types, different pointers)
    layer3 has Unwrap() → call it → get layer2

  Iteration 2: compare layer2 with ErrAuth
    layer2 is wrapError{msg: "middleware: ...", err: layer1}
    layer2 == ErrAuth? NO
    layer2 has Unwrap() → call it → get layer1

  Iteration 3: compare layer1 with ErrAuth
    layer1 is wrapError{msg: "validate token: ...", err: ErrAuth}
    layer1 == ErrAuth? NO
    layer1 has Unwrap() → call it → get ErrAuth

  Iteration 4: compare ErrAuth with ErrAuth
    Same type (*errorString)? YES
    Same data pointer (0xA0 == 0xA0)? YES
    → MATCH! Return true.

  layer3 == ErrAuth only compares the OUTER box:
    layer3 is wrapError at 0xC0, ErrAuth is *errorString at 0xA0
    Different types → false immediately. No chain walking.
```

> **In plain English:** `errors.Is` is like a detective opening nested envelopes one by one, checking the serial number at each level. `==` is a lazy clerk who only looks at the outside label and gives up immediately.

### 4.5 How `errors.As` Works — Type Extraction From the Chain

`errors.As(err, &target)` walks the same chain but instead of comparing values, it tries a **type assertion** at each level. When it finds a match, it populates your pointer.

```go
package main

import (
	"errors"
	"fmt"
)

type ValidationError struct {
	Field  string
	Reason string
}

func (e *ValidationError) Error() string {
	return fmt.Sprintf("validation: %s: %s", e.Field, e.Reason)
}

func validate(email string) error {
	if email == "" {
		return &ValidationError{Field: "email", Reason: "required"}
	}
	return nil
}

func serviceCall() error {
	err := validate("")
	return fmt.Errorf("create user: %w", err)
}

func main() {
	err := serviceCall()

	var ve *ValidationError
	if errors.As(err, &ve) {
		fmt.Printf("field=%s reason=%s\n", ve.Field, ve.Reason)
		// field=email reason=required
	}
}
```

```
errors.As(err, &ve) — step by step:

  err is: wrapError{msg: "create user: validation: email: required",
                     err: → *ValidationError{Field:"email", Reason:"required"}}

  Iteration 1: try type assertion on err
    err is *wrapError — can it be assigned to *ValidationError? NO
    err has Unwrap() → call it → get the inner error

  Iteration 2: try type assertion on inner error
    inner is *ValidationError — can it be assigned to *ValidationError? YES!
    Set ve = inner (*ValidationError)
    Return true

  Now ve points at the ValidationError:
    ve → heap: [ Field: "email" | Reason: "required" ]
    You can read ve.Field, ve.Reason — the structured data from the original error.

WHY this matters for HTTP handlers:
  Your handler doesn't unwrap manually. It calls:
    var ve *ValidationError
    if errors.As(err, &ve) {
        http.Error(w, ve.Error(), 400)   ← structured 400 with field info
        return
    }
  The wrapping from service/repo layers is transparent.
```

Think of it like searching through a stack of folders for a specific form — say, a validation report. You flip through each folder until you find one that matches the shape you need, then pull out the form and read its fields.

### 4.6 Backend Scenario: Repo → Service → Handler Error Flow

Here's a complete trace of how an error flows through a real service stack:

```go
package main

import (
	"errors"
	"fmt"
)

var ErrNotFound = errors.New("not found")

type User struct {
	ID   int
	Name string
}

func repoFindUser(id int) (*User, error) {
	if id == 0 {
		return nil, ErrNotFound  // sentinel from repo layer
	}
	return &User{ID: id, Name: "rahul"}, nil
}

func serviceGetUser(id int) (*User, error) {
	user, err := repoFindUser(id)
	if err != nil {
		return nil, fmt.Errorf("get user %d: %w", id, err)  // wrap with context
	}
	return user, nil
}

type ValidationError struct {
	Field, Reason string
}
func (e *ValidationError) Error() string {
	return e.Field + ": " + e.Reason
}

func handler(id int) {
	user, err := serviceGetUser(id)
	if err != nil {
		switch {
		case errors.Is(err, ErrNotFound):
			fmt.Println("404:", err)
		default:
			fmt.Println("500:", err)
		}
		return
	}
	fmt.Printf("200: %+v\n", *user)
}

func main() {
	handler(0)  // 404: get user 0: not found
	handler(1)  // 200: {ID:1 Name:rahul}
}
```

```
handler(0) — error path traced through memory:

  Step 1: repoFindUser(0)
    id == 0 → return nil, ErrNotFound
    ErrNotFound: [ type: *errorString | data: 0xA0 ]
    heap 0xA0: { s: "not found" }

  Step 2: serviceGetUser wraps: fmt.Errorf("get user 0: %w", err)
    heap 0xB0: wrapError{
      msg: "get user 0: not found",
      err: → 0xA0 (ErrNotFound)        ← chain link preserved
    }
    Returns: [ type: *wrapError | data: 0xB0 ]

  Step 3: handler checks errors.Is(err, ErrNotFound)
    Iteration 1: err at 0xB0 == ErrNotFound at 0xA0? NO
    Unwrap → get ErrNotFound at 0xA0
    Iteration 2: 0xA0 == 0xA0? YES → match!
    → prints "404: get user 0: not found"

  The error message is human-readable ("get user 0: not found")
  AND machine-parseable (errors.Is finds ErrNotFound through the chain).

handler(1) — success path:
  repoFindUser(1) → returns &User{...}, nil
  serviceGetUser → user is non-nil, err is nil
  handler prints user → "200: {ID:1 Name:rahul}"
```

> **In plain English:** The repo says "not found." The service puts that note in an envelope labeled "get user 0." The handler opens the envelope, checks the note's serial number, and says "yep, that's a 404." The wrapping adds human context without destroying machine-readable identity.

---

## 5. Key Rules & Behaviors

### Rule 1: Always Check `err != nil` Before Using the Result

**WHY (Section 4.1):** From Section 4.1, `error` is an interface. When a function returns `(result, error)`, the result is only valid if the error interface is nil (both type and data slots are nil). Using `result` when `err != nil` risks operating on zero values or stale data.

```go
f, err := os.Open("cfg.json")
if err != nil {
	return fmt.Errorf("open config: %w", err)
}
defer f.Close()
```

```
Step 1: os.Open("cfg.json") returns (f, err)
  Case A (success): f = *os.File{...}, err = [ type: nil | data: nil ] → nil
  Case B (failure):  f = nil,          err = [ type: *PathError | data: 0xB0 ] → non-nil

  If you skip the nil check and call f.Read() in Case B:
    f is nil → f.Read() dereferences nil → PANIC

  The check ensures you only use f when it's actually valid.
```

You don't start reading a book before checking someone actually handed you a book. The handle might be empty.

### Rule 2: Wrap Errors at Abstraction Boundaries with `%w`

**WHY (Section 4.3):** From Section 4.3, `%w` creates a linked list that preserves the original error's identity. Each layer adds context ("what was I doing when this failed?") while keeping the chain walkable by `errors.Is` and `errors.As`.

```go
var ErrUserNotFound = errors.New("user not found")

func repoGet(id int) error {
	return sql.ErrNoRows  // raw database error
}

func LoadUser(id int) error {
	err := repoGet(id)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return fmt.Errorf("load user %d: %w", id, ErrUserNotFound)  // translate + wrap
		}
		return fmt.Errorf("load user %d: %w", id, err)
	}
	return nil
}
```

```
WHY translate sql.ErrNoRows → ErrUserNotFound:

  Without translation:
    handler imports database/sql to check sql.ErrNoRows
    → your HTTP layer depends on your database driver. Bad coupling.

  With translation:
    handler checks errors.Is(err, ErrUserNotFound)
    → handler doesn't know or care that the repo uses SQL

  Chain in memory after translation:
    wrapError{ msg: "load user 42: user not found", err: → ErrUserNotFound }
    Handler checks: errors.Is(err, ErrUserNotFound) → true → 404
```

Picture a moving truck: you write your name on a new label, but the old sticker from the furniture shop is still visible through a plastic window. Delivery staff can read both.

### Rule 2b: Map Errors to HTTP at the Edge (Handler), Not in the Repo

**WHY (Section 4.5, Section 4.6):** From Section 4.5, `errors.As` can extract typed errors at any depth. The handler is the right place to decide HTTP status codes because it knows the HTTP contract. The repo should never import `net/http`.

- **`errors.Is(err, ErrUserNotFound)`** → **404**
- **`errors.As(err, &validationErr)`** → **400**
- **Everything else** → **500** (log the real chain; return a safe message)

```go
func (h *Handler) handleErr(w http.ResponseWriter, err error) {
	var ve *ValidationError
	switch {
	case errors.Is(err, ErrUserNotFound):
		http.Error(w, "not found", 404)
	case errors.As(err, &ve):
		http.Error(w, ve.Error(), 400)
	default:
		h.log.Error("request failed", "err", err)
		http.Error(w, "internal error", 500)
	}
}
```

```
Error flow through layers:

  repo layer:       sql.ErrNoRows
                         │
  service layer:    fmt.Errorf("get user: %w", ErrUserNotFound)
                         │
  handler layer:    errors.Is(err, ErrUserNotFound)? → 404
                    errors.As(err, &ve)?             → 400
                    else                             → 500

  The handler NEVER imports database/sql.
  The repo NEVER imports net/http.
  errors.Is / errors.As cross the boundary through the chain.
```

Same idea as a hospital: inside, doctors use medical terminology on the chart. At the reception desk, you translate that into "your test results are ready" — not "serum creatinine elevated 2.3 mg/dL." The repo never decides how to talk to the API consumer.

### Rule 2c: Middleware — Log Once, Attach Request Context, Then Wrap

A common pattern: generate a **request ID**, put it in **`context`**, and when something fails deep in the stack, wrap so operators can grep logs.

```go
type ctxKey string
const reqIDKey ctxKey = "request_id"

func wrapReq(ctx context.Context, msg string, err error) error {
	if err == nil {
		return nil
	}
	return fmt.Errorf("%s (req_id=%s): %w", msg, RequestIDFrom(ctx), err)
}
```

**WHY (Section 4.3):** The `%w` keeps the chain intact, so `errors.Is`/`errors.As` still work downstream. The request ID is baked into the message for log correlation, but the chain structure is preserved for programmatic checks.

```
Chain after wrapReq:

  wrapError{ msg: "load user (req_id=abc123): ...",
             err: → original error }
                    ↑ chain still intact — errors.Is/As can walk through
                    ↑ req_id is in the MESSAGE for logs, not blocking the chain
```

It's like stamping a tracking number on every envelope — anyone who opens it can still read the original letter. The stamp doesn't cover anything up.

### Rule 2d: Retryable vs Non-Retryable

Not every failure deserves a retry loop.

- **Retry:** transient network blips, deadline exceeded, 503 with Retry-After
- **Do not retry:** validation errors, 4xx, business rule violations, duplicate key

```go
var ErrRetryable = errors.New("retryable")

type TemporaryError struct{ Cause error }
func (e *TemporaryError) Error() string { return "temporary: " + e.Cause.Error() }
func (e *TemporaryError) Unwrap() error { return e.Cause }
```

**WHY (Section 4.4, Section 4.5):** Retry middleware uses `errors.Is(err, ErrRetryable)` or `errors.As(err, &temp)` to decide whether to retry. The chain walking from Section 4.4 means the retry marker can be at any depth — the middleware finds it regardless of how many wraps sit above it.

```
Retry decision via chain walk:

  err: wrapError{ "handler: service: temporary: context deadline exceeded"
       err: → wrapError{ "service: ..."
              err: → TemporaryError{ Cause: → context.DeadlineExceeded } } }

  errors.As(err, &temp):
    wrapError → no → Unwrap
    wrapError → no → Unwrap
    TemporaryError → YES → temp.Cause = DeadlineExceeded
    → retry middleware retries

  errors.As(err, &validationErr):
    walks entire chain → no ValidationError found → don't retry
```

A "temporary" sticker on an envelope means "try sending this again." A "validation failed" sticker means "fix the contents first — resending won't help."

### Rule 2e: Error Boundary — `*RepoError` Inside, `*APIError` at the Edge

```go
// internal/userrepo
type RepoError struct {
	Op  string
	Err error
}
func (e *RepoError) Error() string { return e.Op + ": " + e.Err.Error() }
func (e *RepoError) Unwrap() error { return e.Err }

// api layer
type APIError struct {
	Status int
	Public string
	Cause  error
}
func (e *APIError) Error() string { return e.Public }
func (e *APIError) Unwrap() error { return e.Cause }
```

**WHY (Section 4.5):** `errors.As` lets the handler extract `*RepoError` to understand what happened, then create an `*APIError` with a safe public message. The Cause field preserves the full chain for logs while Public protects the user from internal details.

```
Error boundary translation:

  INTERNAL (repo layer):
    RepoError{ Op: "findUser", Err: → sql.ErrNoRows }
              ↓ errors.As extracts RepoError
  API EDGE (handler):
    APIError{ Status: 404, Public: "not found", Cause: → RepoError{...} }
              ↑ Public: safe for JSON body
              ↑ Cause: full chain preserved for structured logs
```

Inside the hospital, doctors use medical terminology. At the reception desk, you translate that into "your test results are ready." Same principle: internal errors stay internal, the API boundary translates.

### Rule 3: Use `errors.Is` for Sentinels, `errors.As` for Type Extraction

**WHY (Section 4.4, Section 4.5):** `errors.Is` walks the chain comparing values (pointer identity for sentinels). `errors.As` walks the chain trying type assertions. Using `==` skips the chain entirely.

```go
if errors.Is(err, os.ErrNotExist) {
	// file missing — uses Section 4.4 chain walking
}

var v *ValidationError
if errors.As(err, &v) {
	_ = v.Field  // uses Section 4.5 type extraction
}
```

```
errors.Is vs errors.As — what each does at each chain level:

  err → wrapError → wrapError → *ValidationError → ErrNotFound(sentinel)

  errors.Is(err, ErrNotFound):
    level 1: wrapError == ErrNotFound? NO → Unwrap
    level 2: wrapError == ErrNotFound? NO → Unwrap
    level 3: *ValidationError == ErrNotFound? NO → Unwrap
    level 4: ErrNotFound == ErrNotFound? YES → return true

  errors.As(err, &v):
    level 1: wrapError assignable to *ValidationError? NO → Unwrap
    level 2: wrapError assignable to *ValidationError? NO → Unwrap
    level 3: *ValidationError assignable? YES → set v, return true
```

`Is` checks if the same serial-numbered form is inside any envelope. `As` checks if any layer uses a specific form template, and hands you the form so you can read its fields.

### Rule 4: Do Not Wrap Twice with the Same Context

**WHY (Section 4.3):** Each `%w` adds a new node to the linked list. Duplicate labels create a chain like `"service: service: service: db error"` — three identical envelopes with no new information, just noise in logs.

```go
// BAD — repeated label
return fmt.Errorf("service: %w", fmt.Errorf("service: %w", err))

// GOOD — one wrap per layer
return fmt.Errorf("service: %w", err)
```

```
BAD chain:
  wrapError{ "service: service: db error"
    err: → wrapError{ "service: db error"    ← redundant node, no new info
           err: → errorString{"db error"} } }

GOOD chain:
  wrapError{ "service: db error"
    err: → errorString{"db error"} }         ← one wrap, one new label
```

You don't put two identical address labels on the same box. One clear label is enough.

### Rule 5: Return `nil` for Success — Avoid the Typed Nil Interface Trap

**WHY (Section 4.1):** From Section 4.1, an error interface is nil only when BOTH type and data slots are nil. A `nil` pointer with a concrete type fills the type slot, making the interface non-nil.

```go
type AppError struct{ msg string }
func (e *AppError) Error() string { return e.msg }

func f() *AppError { return nil }

func g() error {
	return f()  // BUG: returns [ type: *AppError | data: nil ] — non-nil interface!
}
```

```
What happens in memory:

  f() returns nil *AppError
    stack: [ 0x0 ]   ← nil pointer of type *AppError

  g() assigns to error return:
    Go wraps: [ type: *AppError | data: nil ]
    Type slot is NOT nil → interface is NOT nil!

  Caller checks: err != nil → TRUE → thinks there's an error

FIX:
  func g() error {
      p := f()
      if p != nil {
          return p
      }
      return nil  // ← [ type: nil | data: nil ] → truly nil
  }
```

> **In plain English:** A labeled empty tray is not "no tray." The label `*AppError` is still there even though the tray is empty. A truly empty hand — no label — is what `nil` means for `error`.

### Rule 6: The `(*User, *NotFoundError)` Shape — Watch the Promotion

Some teams return data + typed error pointer so callers can branch without losing type information. The trap comes when promoting to `error`:

```go
func getUser(id string) (*User, *NotFoundError) {
	if id == "" {
		return nil, &NotFoundError{Resource: "user"}
	}
	return &User{Name: "Ada"}, nil  // nil *NotFoundError
}

func LoadForAPI(id string) (*User, error) {
	u, nf := getUser(id)
	return u, nf  // BUG: nil *NotFoundError → non-nil error interface!
}
```

**WHY (Section 4.1, Rule 5):** Same mechanism as Rule 5. The `nil *NotFoundError` fills the type slot when assigned to `error`.

```
getUser("valid-id") returns: (*User, nil *NotFoundError)

LoadForAPI assigns nf to error return:
  nf is nil *NotFoundError
  error interface: [ type: *NotFoundError | data: nil ]   ← type slot filled!
  
  caller: err != nil → TRUE → thinks there's an error

FIX: if nf != nil { return u, nf }; return u, nil
  nil assigned to error: [ type: nil | data: nil ] → truly nil
```

Same trap, different disguise. A nil `*NotFoundError` is still a labeled tray. Guard before promoting: `if nf != nil { return u, nf }; return u, nil`.

---

## 6. Code Examples (Show, Don't Tell)

### Example 1: Sentinel Error — Identity Traced Through Memory

The foundation of Go error handling: create a sentinel, wrap it, and find it again.

```go
package main

import (
	"errors"
	"fmt"
)

var ErrDuplicate = errors.New("duplicate entry")

func insert(key string) error {
	return fmt.Errorf("insert %s: %w", key, ErrDuplicate)
}

func main() {
	err := insert("user-123")
	fmt.Println(err)                             // insert user-123: duplicate entry
	fmt.Println(errors.Is(err, ErrDuplicate))     // true
	fmt.Println(err == ErrDuplicate)               // false
}
```

```
Step 1: ErrDuplicate created at package init
  heap 0xA0: errorString{ s: "duplicate entry" }
  ErrDuplicate: [ type: *errorString | data: 0xA0 ]

Step 2: insert("user-123") wraps with %w
  heap 0xB0: wrapError{ msg: "insert user-123: duplicate entry", err: → 0xA0 }
  Returns: [ type: *wrapError | data: 0xB0 ]

Step 3: errors.Is(err, ErrDuplicate)
  err at 0xB0 → Unwrap() → ErrDuplicate at 0xA0
  0xA0 == 0xA0 → true!

Step 4: err == ErrDuplicate
  *wrapError != *errorString → false immediately (different types)
```

### Example 2: Custom Error Type — `errors.As` Extracts Fields

When you need structured error data (field names, error codes) for 400 responses.

```go
package main

import (
	"errors"
	"fmt"
)

type ValidationError struct {
	Field  string
	Reason string
}

func (e *ValidationError) Error() string {
	return fmt.Sprintf("%s: %s", e.Field, e.Reason)
}

func validateEmail(email string) error {
	if email == "" {
		return &ValidationError{Field: "email", Reason: "required"}
	}
	return nil
}

func createUser(email string) error {
	if err := validateEmail(email); err != nil {
		return fmt.Errorf("create user: %w", err)  // wrap preserves type
	}
	return nil
}

func main() {
	err := createUser("")

	var ve *ValidationError
	if errors.As(err, &ve) {
		fmt.Printf("Bad field: %s, reason: %s\n", ve.Field, ve.Reason)
		// Bad field: email, reason: required
	}
}
```

```
Step 1: validateEmail("") returns *ValidationError
  heap 0xA0: ValidationError{ Field: "email", Reason: "required" }

Step 2: createUser wraps: fmt.Errorf("create user: %w", err)
  heap 0xB0: wrapError{ msg: "create user: email: required", err: → 0xA0 }

Step 3: errors.As(err, &ve)
  err at 0xB0 is *wrapError — assignable to *ValidationError? NO
  Unwrap → get 0xA0 (*ValidationError)
  0xA0 is *ValidationError — assignable? YES
  Set ve = pointer to 0xA0
  ve.Field = "email", ve.Reason = "required" ✓
```

### Example 3: Wrapping Chain — Three Layers Deep

The full handler → service → repo pattern with both `errors.Is` and `errors.As`.

```go
package main

import (
	"errors"
	"fmt"
)

var ErrNotFound = errors.New("not found")

type DBError struct {
	Query string
	Err   error
}
func (e *DBError) Error() string  { return fmt.Sprintf("db(%s): %s", e.Query, e.Err) }
func (e *DBError) Unwrap() error  { return e.Err }

func repo() error {
	return &DBError{Query: "SELECT * FROM users WHERE id=$1", Err: ErrNotFound}
}

func service() error {
	return fmt.Errorf("get user: %w", repo())
}

func main() {
	err := service()

	fmt.Println(errors.Is(err, ErrNotFound))  // true — 3 levels deep

	var dbe *DBError
	fmt.Println(errors.As(err, &dbe))         // true
	fmt.Println("query:", dbe.Query)           // SELECT * FROM users WHERE id=$1
}
```

```
Chain in memory:

  err: wrapError{ msg: "get user: db(...): not found"
                  err: → DBError{ Query: "SELECT...", Err: → ErrNotFound } }

  errors.Is(err, ErrNotFound):
    wrapError → Unwrap → DBError → Unwrap → ErrNotFound → MATCH

  errors.As(err, &dbe):
    wrapError → not *DBError → Unwrap → DBError → MATCH → set dbe
```

### Example 4: The Typed Nil Trap — Production Bug

The subtle bug that makes success look like failure.

```go
package main

import "fmt"

type APIError struct {
	Code int
	Msg  string
}

func (e *APIError) Error() string { return fmt.Sprintf("%d: %s", e.Code, e.Msg) }

func validate(name string) *APIError {
	if name == "" {
		return &APIError{Code: 400, Msg: "name required"}
	}
	return nil
}

func process(name string) error {
	return validate(name)  // BUG when name is valid!
}

func main() {
	err := process("rahul")
	fmt.Println(err == nil)  // false! success looks like failure
	fmt.Printf("type=%T, value=%v\n", err, err)
	// type=*main.APIError, value=<nil>
}
```

```
Step 1: validate("rahul") → returns nil *APIError
  stack: [ nil ]  (a nil pointer of type *APIError)

Step 2: process returns this as error
  Go wraps into interface:
    [ type: *APIError | data: nil ]
         ↑                  ↑
    NOT nil!            nil pointer

Step 3: err == nil checks the interface
  [ type: *APIError | data: nil ] vs [ type: nil | data: nil ]
  Type slot differs → NOT equal → false!

  Your handler thinks there's an error even though validation passed.

FIX:
  func process(name string) error {
      if apiErr := validate(name); apiErr != nil {
          return apiErr
      }
      return nil  // → [ type: nil | data: nil ] → truly nil
  }
```

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
> Typed **`nil` `*RepoError`** in an **`error`** slot is still a **non-nil interface**. Guard with **`if err := maybeFail(true); err != nil { return err }; return nil`**, or return **`error`** from **`maybeFail`**.

### Tier 4: Build It (15 min)

Package with a **validation** type (`Error()` + **`errors.As`**), a **`%w`** wrap from an inner failure, and a handler that returns **400** vs **500**.

> Full solutions with explanations → [[exercises/T09 Error Handling Patterns - Exercises]]

---

## 7. Edge Cases & Gotchas

| Gotcha | What Happens | Because (Section 4 link) | Fix |
|--------|-------------|-------------------|-----|
| `==` after wrapping | `wrapped == ErrNotFound` is false even though the sentinel is inside | Section 4.3 — `%w` creates a new `wrapError` struct. `==` compares the outer struct, not the chain inside. The sentinel is at a deeper level | Use `errors.Is(err, ErrNotFound)` — it walks the chain (Section 4.4) |
| `%v` instead of `%w` | `errors.Is` and `errors.As` can't find the original error | Section 4.3 — `%v` creates a plain `errorString` with no Unwrap method. The chain link is severed — no linked list pointer | Always use `%w` when callers need to unwrap. Use `%v` only when you deliberately want to hide the inner error |
| Typed nil `*MyError` returned as `error` | `err != nil` is true even when no error occurred | Section 4.1 — interface stores `[type: *MyError, data: nil]`. Type slot is non-nil, so the interface is non-nil | Guard: `if p != nil { return p }; return nil`. Or return `error` directly, not `*MyError` |
| Two `errors.New("not found")` compared with `==` | Always false, even though messages match | Section 4.2 — each `errors.New` allocates a new `*errorString` on the heap. Identity is pointer address, not message content | Define sentinels once at package level: `var ErrNotFound = errors.New("not found")` |
| Ignoring error with `_ = f()` | Silent data loss, corrupt state, stale cache | Section 4.1 — the error interface value (16 bytes: type + data) is created and returned, but discarded by `_`. The chain from Section 4.3 exists but is never walked — the failure is invisible | Handle every error. If truly ignorable, document why with a comment naming who accepted the risk |
| Wrapping the same label twice | `"service: service: db error"` — duplicate context in logs | Section 4.3 — each `%w` adds a new linked list node. Two identical labels create two nodes with no new information | Wrap once per abstraction boundary. Each layer should add unique context |

### Gotcha Deep Dive: `%v` Breaks the Chain

This is the most silent bug — your wrapping looks correct but `errors.Is` silently fails:

```go
package main

import (
	"errors"
	"fmt"
)

var ErrAuth = errors.New("unauthorized")

func main() {
	withW := fmt.Errorf("middleware: %w", ErrAuth)   // %w — linked
	withV := fmt.Errorf("middleware: %v", ErrAuth)   // %v — broken

	fmt.Println(errors.Is(withW, ErrAuth))  // true  ← chain intact
	fmt.Println(errors.Is(withV, ErrAuth))  // false ← chain broken!
	fmt.Println(withV)                       // middleware: unauthorized (looks fine!)
}
```

```
%w wrapping:
  heap 0xB0: wrapError{
    msg: "middleware: unauthorized",
    err: → ErrAuth (0xA0)            ← Unwrap() returns ErrAuth
  }
  errors.Is walks: 0xB0 → Unwrap → 0xA0 → MATCH

%v wrapping:
  heap 0xC0: errorString{
    s: "middleware: unauthorized"     ← just a string, NO err field
  }
  errors.Is: 0xC0 has no Unwrap() → chain ends → no match → false

  The printed message looks identical!
  But the internal structure is completely different.
```

Remember: `%w` is the window in the envelope — you can reach through it. `%v` is a photocopy on a new envelope — looks the same from outside, but there's nothing inside to reach.

### Gotcha Deep Dive: Two Sentinels With Same Text

```go
package main

import (
	"errors"
	"fmt"
)

func main() {
	err1 := errors.New("timeout")
	err2 := errors.New("timeout")

	fmt.Println(err1 == err2)              // false
	fmt.Printf("err1 at %p\n", err1)       // 0xC000010040
	fmt.Printf("err2 at %p\n", err2)       // 0xC000010050

	fmt.Println(errors.Is(err1, err2))      // false — different pointers
}
```

```
err1: heap 0xC000010040: errorString{ s: "timeout" }
err2: heap 0xC000010050: errorString{ s: "timeout" }

== compares: same type? YES. Same pointer? 0x40 != 0x50 → NO.
errors.Is: err1 has no Unwrap → chain is just err1 → err1 != err2 → false.

This is BY DESIGN: if string equality worked, any package that
errors.New("timeout") would accidentally match YOUR sentinel.
```

---

## 8. Performance & Tradeoffs

### Where this hits you in production

Your order service handles 3k RPM. A failed Stripe charge returns an error that gets wrapped three times — `repo` adds context, `service` adds the order ID, `handler` adds the request ID. Three `fmt.Errorf("...: %w", err)` calls. Each one allocates a small struct on the heap (~64 bytes). At 3k RPM with a 2% error rate, that's 60 errors/sec times 3 wraps = 180 tiny allocations per second. Your Stripe round trip is 80ms. Those 180 allocations are invisible in pprof — you'd never find them unless you went looking.

Now compare that to what your structured logger does when it calls `err.Error()` on a 4-layer wrapped error. It walks the full chain, builds the concatenated string with every `: ` separator, and your logging middleware feeds that string into `json.Marshal` for Datadog. At 60 errors/sec, that's 60 string builds + 60 JSON encodes your handler didn't need. **That** shows up in `alloc_objects`.

| Pattern | What it costs | You'd see this in... | Verdict |
|---------|--------------|---------------------|---------|
| `fmt.Errorf("...: %w", err)` | ~64B heap alloc per wrap | Repo wrapping a DB error, service adding order ID | Noise next to any I/O call. Use freely. |
| `errors.Is(err, ErrNotFound)` | One pointer compare per chain link | Handler checking if repo returned "not found" for a 404 | Essentially free — a short chain means 2-4 pointer hops. |
| `errors.As(err, &target)` | Pointer compare + type check per link | Middleware extracting `*APIError` to set HTTP status | Slightly more work than `Is` but still trivial for typical 3-layer chains. |
| `%v` instead of `%w` | Zero — but **breaks the chain** | Accidentally cutting off `Is`/`As` for upstream callers | Free in CPU but costs you debuggability. A false economy. |
| Logging `err.Error()` every layer | String build at each layer, then the caller builds again | Each middleware layer logging the error before passing it up | Real cost. Log **once** at the boundary. Use request ID to correlate. |
| `fmt.Errorf` in a tight loop | `Sprintf` parsing + heap alloc per iteration | Validating 10k rows in a CSV import, wrapping per-row errors | Measurable. Pre-allocate an error slice, or use a `ValidationErrors` collector. |

### What actually hurts

The anti-pattern that burns real CPU: your error middleware calls `err.Error()` to log the error, then your response writer calls `err.Error()` again to build the JSON body, then your metrics middleware calls `err.Error()` a third time to extract a label. Each call walks the full chain and allocates a new string. At 2k errors/min on a high-traffic endpoint, that's 6k string builds per minute — and each one does `fmt.Sprintf` work under the hood.

The fix is boring: call `err.Error()` once at the handler boundary, stash the string, and reuse it for logging, response, and metrics. Or better — log the **structured fields** (order ID, error code, layer) instead of the concatenated message.

### What to measure

```bash
# Benchmark sentinel vs wrapped error check
go test -bench=BenchmarkErrorIs -benchmem ./pkg/errors/

# Find error-related allocations in a load test
go tool pprof -alloc_objects http://localhost:6060/debug/pprof/heap
# Then: top 20 -cum | grep "fmt\|errors\|Errorf"

# Quick check: how many allocs does your error path make?
go test -run=TestOrderPaymentFailure -benchmem -count=1 ./service/
```

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

Go errors are just values — any type that has an `Error() string` method counts as an `error`. You return errors explicitly and check them with `if err != nil`; you don't use `panic` for normal failure paths.

In a real backend service, you wrap errors with `%w` as they move up the call stack so each layer adds context — repo says what query failed, service says which user, handler adds a request ID. At the API boundary you map internal errors to HTTP status codes using `errors.Is` and `errors.As`, and you log the full chain once with the request ID so you can trace it in Datadog.

Two traps to watch for: first, never use `==` to compare errors after wrapping — the wrapper is a new value, so `==` fails. Use `errors.Is` instead. Second, the typed nil trap — if a function returns a concrete pointer type like `*AppError` with value `nil`, assigning it to an `error` return gives you a non-nil interface (the type slot is set). Always return bare `nil` for the success case.

---

## 13. Comprehensive Interview Questions

> Full interview question bank (comprehensive Q&A) → [[questions/T09 Error Handling Patterns - Interview Questions]]

**Preview questions:**

1. How does `errors.Is` differ from a plain value comparison, and when does the difference matter in real code?
2. How would you design error types for a public library vs an internal service?
3. What happens if a function returns `*MyError` with value `nil` in a `error` return position?

---

> See [[Glossary]] for term definitions.
