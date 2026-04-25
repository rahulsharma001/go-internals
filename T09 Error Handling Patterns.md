# T09 Error Handling Patterns

> **Reading Guide**: Sections 1-3 and 6 are essential first read (20 min).
> Sections 4-5 deepen understanding (15 min).
> Sections 7-12 are interview-specific — read closer to interview day.
> Section 13 is your comprehensive interview Q&A bank → [[questions/T09 Error Handling Patterns - Interview Questions]]
> Something not clicking? → [[simplified/T09 Error Handling Patterns - Simplified]]

---

## 1. Concept

In Go, **`error` is a built-in interface** with a single method: `Error() string`. Any concrete type that implements that method is an error. There is no `try` or `throw`. **Errors are values.** You return them. You test them. You do not "catch" them up the stack by default.

You handle failure by writing **`if err != nil`** and branching. The happy path keeps reading straight down. The failure path short-circuits with `return` or `continue`.

> **In plain English:** In some languages, errors are like air horns that go off in another room. In Go, errors are a slip of paper you hand to the next person. That person must read the slip. If they ignore it, the mistake stays.

---

## 2. Core Insight (TL;DR)

**Go treats errors as ordinary values that flow through your code.** The philosophy: be explicit, fail fast, and carry enough context to debug. **The interview gold** is the trio **sentinel errors**, **custom error types**, and **wrapping with `%w`**, then unwrapping with **`errors.Is`** and **`errors.As`**. If you can explain that chain clearly, you have shown senior-level Go.

> **In plain English:** You do not hope someone notices a flashing light. You pass a labeled note: what broke, and where, in order.

---

## 3. Mental Model (Lock this in)

### The Letter in Many Envelopes

Imagine a real letter. Each function that fails puts that letter into a new envelope. On the front of the envelope, someone writes what step failed: "read file", "parse JSON", and so on. The original letter is still inside.

- **`errors.Is`** keeps opening envelopes until it finds a letter that matches a specific stamp you care about, like `os.ErrNotExist`.
- **`errors.As`** keeps opening until it finds an envelope of a **specific shape** — for example, a red envelope with a form inside your custom type, so you can read extra fields.

Plain `==` only compares the **outer** envelope, not the letter hidden inside after wrapping. That is the trap.

> **In plain English:** `==` sees only the last envelope. `Is` and `As` are willing to open every layer to find the original note or the right kind of case file.

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
	fmt.Println(wrapped == ErrNotFound)        // false — compares outer value only
	fmt.Println(errors.Is(wrapped, ErrNotFound)) // true — follows unwrap chain
	_ = os.ErrNotExist
}
```

```
UNWRAP CHAIN (conceptual):

  ErrNotFound  (inner letter)
        ▲
        │  Unwrap()
        │
  *fmt.wrapError{ msg: "lookup user: ...", err: → ErrNotFound }

  wrapped == ErrNotFound
  └── compares pointer/value identity of the OUTER box → false  <-- wrong check

  errors.Is(wrapped, ErrNotFound)
  └── open outer → compare inner to ErrNotFound → true
```

**Why it breaks:** Wrapping builds a new error value. That value is not equal to the original sentinel. The chain of `Unwrap()` calls is what links them. `errors.Is` walks that chain. `==` does not.

---

## 4. How It Actually Works (Internals) [INTERMEDIATE → ADVANCED]

> **In plain English:** The standard library stores errors as small objects. Some are simple strings. Some are boxes that hold another error inside. Helpers know how to open the boxes in order.

### 4.1 The `error` Interface (Just `Error() string`)

```go
// From the spec — roughly what you are matching against
type error interface {
	Error() string
}
```

```
ANY VALUE THAT HAS Error() string  →  can live in a variable of type `error`
```

`string` and `*MyError` are different types, but if both implement `Error() string`, both satisfy `error`.

> **In plain English:** "Error" here means "I can print a one-line message." The language does not care what struct you used to build that line.

### 4.2 Sentinel Errors — `errors.New` and `*errorString`

```go
var ErrNotFound = errors.New("not found")
```

`errors.New` allocates a private pointer type in the standard library, often shown in docs as **`errorString`**. The pointer identity matters: two `errors.New("same")` calls give two **different** sentinels.

```
errors.New("not found")
  →  pointer to small struct  *errorString{ s: "not found" }

  ErrNotFoundA := errors.New("x")
  ErrNotFoundB := errors.New("x")
  ErrNotFoundA == ErrNotFoundB  →  false  (different pointers)
```

> **In plain English:** A sentinel is a pre-printed form with a unique serial number. Two forms can say the same words but still be two different papers.

### 4.3 Error Wrapping — `fmt.Errorf` with `%w` and `*fmt.wrapError`

```go
import "fmt"
wrapped := fmt.Errorf("load config: %w", err) // build link to `err`
```

The **`%w` verb** creates a value that usually implements **`Unwrap() error`**. The concrete type is often documented as **`wrapError`**. The **`%v` verb** only formats text. It does not attach an unwrap target.

```
fmt.Errorf("ctx: %w", inner)
  →  *wrapError { msg: "ctx: ...", err: → inner }
       └── Unwrap() returns inner
```

> **In plain English:** `%w` is a window in the new envelope. Helpers can look through the window at the old letter. `%v` is a photocopy of the text on the new envelope only — the window is missing.

### 4.4 The Unwrap Chain — `errors.Is` and `errors.As` Walk the Chain

```go
errors.Is(err, target)  // is `target` anywhere in the unwrap chain?
var ve *ValidationError
errors.As(err, &ve)     // find first error assignable to *ValidationError, set `ve`
```

**`errors.Is`** compares the chain with equality rules that understand sentinels and **Unwrap** steps.

**`errors.As`** tries type assertion at each level of the chain until one matches, then populates the pointer you passed.

```
err chain:  A wraps B wraps C

errors.Is(err, C):
  A → Unwrap → B → Unwrap → C  →  match  ✓

errors.As(&ptr, T):
  try A, try B, try C  →  first *T  →  ptr = that value
```

> **In plain English:** `Is` asks "is this the same bad news, even through several retellings?" `As` asks "does any layer use our company's form?"

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

> **In plain English:** A custom type is a company-branded case folder. It has extra fields. The folder can still enclose an older letter if you add an inner slot.

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

```
order of operations:

1) call os.Open
2) err != nil?  ──yes──▶ return (never touch f)
   │
   └──no──▶ use f
```

> **In plain English:** You do not start reading a book before checking someone actually handed you a book. The handle might be empty.

### Rule 2: Wrap Errors at Abstraction Boundaries with `%w`

```go
func LoadUser(id int) error {
	_, err := dbGet(id) // low-level: sql.ErrNoRows maybe
	if err != nil {
		return fmt.Errorf("load user %d: %w", id, err) // domain context + link
	}
	return nil
}
```

```
[ domain layer ]  "load user 42" + window to inner
        │
        ▼
[ storage layer ]  sql.ErrNoRows
```

> **In plain English:** The moving truck writes your name on a new label, but the old sticker from the furniture shop is still visible through a plastic window. Delivery staff can read both.

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

```
Is:     "any layer == this sentinel?"

As:     "any layer is this type?"
        └── fill pointer so you can read .Field
```

> **In plain English:** `Is` checks for a known stamp. `As` looks for a specific folder shape and hands you the folder so you can open the extra tabs.

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

```
BAD:
  "service:" → "service:" → real problem     (noisy, redundant)

GOOD:
  "service:" → real problem
```

> **In plain English:** You do not put two identical address labels on the same box. One clear label is enough.

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

```
typed *AppError with value nil  →  interface value ( *AppError , nil )  —  not nil
untyped nil assigned to `error`  →  interface value ( nil , nil )     —  nil
```

> **In plain English:** A labeled empty tray is not "no tray." The label *AppError is still there. A truly empty hand — no type label — is what `nil` means for `error`.

---

## 6. Code Examples (Show, Don't Tell)

### Sentinel Error Pattern

```go
var ErrUserNotFound = errors.New("user not found")

func FindUser(id int) error {
		return ErrUserNotFound
}
```

```
ErrUserNotFound  →  *errorString{ "user not found" }

Compare with:  errors.Is(err, ErrUserNotFound)  // after any wrap
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

```
stack:
  err  ──▶  *ValidationError{ Field: "email", ... }
                      │
errors.As(err, &ve)  ─┘  fills ve
```

### Error Wrapping Chain and Unwrapping

```go
root := os.ErrNotExist
layer1 := fmt.Errorf("open config: %w", root)
layer2 := fmt.Errorf("bootstrap: %w", layer1)

errors.Is(layer2, os.ErrNotExist) // true
```

```
layer2  ──Unwrap──▶  layer1  ──Unwrap──▶  root  (os.ErrNotExist)
```

**Step through:**

```
Step 1: root = os.ErrNotExist
  root is sentinel pointer

Step 2: layer1 = fmt.Errorf(..., %w, root)
  *wrapError → Unwrap() → root

Step 3: layer2 = fmt.Errorf(..., %w, layer1)
  *wrapError → Unwrap() → layer1

Step 4: errors.Is(layer2, os.ErrNotExist)
  walk Unwrap until match → true
```

---

## 6.5. Practice Checkpoint

All runnable in [Go Playground](https://go.dev/play/).

### Tier 1: Predict the Output (2 min)

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

### Tier 2: Fix the Bug (5 min)

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

### Tier 3: Build It (15 min)

Build a tiny **validation** package.

- One **custom type** for field errors. Implement `Error()`.
- A function that returns errors **wrapped** with `fmt.Errorf` and `%w` from an inner failure.
- A caller that uses **`errors.As`** to pull out your type and read the field name.

> Full solutions with explanations → [[exercises/T09 Error Handling Patterns - Exercises]]

---

## 7. Edge Cases & Gotchas

| Symptom | Why | Fix |
|--------|-----|-----|
| `err == target` is false, but the inner cause is `target` | Wrapping **replaces** the outer value | Use **`errors.Is(err, target)`** |
| `if err == nil` after `return` from helper, but error is not "really" nil | **Typed nil** in an interface | Return **`nil` without** a typed nil in the interface, or return **`error` interface** and set `var err error` then `return err` |
| `fmt.Errorf("x: %v", e)` and `errors.Is` fails | `%v` does not implement unwrap link | Use **`%w`** when the caller must unwrap |
| `_ = f()` | Error dropped on the floor | Always handle or return; use **`_`** only with a comment when truly intentional |

> **In plain English:** Hiding a note in a new envelope is not the same as throwing the note away. The `%v` printout is the thrown-away copy. The `%w` keeps the chain. Ignoring a return with `_` is signing for a package and leaving it in the rain.

---

## 8. Performance & Tradeoffs

| Topic | What to know |
|--------|----------------|
| **Creating errors** | `errors.New` and `fmt.Errorf` allocate. Hot paths may reuse sentinels or pre-built errors instead of `fmt` per call. |
| **Wrapping** | One `%w` layer adds a small object and a pointer hop. Chains a few levels deep are normal. Very deep custom chains are a smell. |
| **Sentinel vs custom** | Sentinel: tiny, good for "this exact condition" flags. Custom: when you need fields for APIs or UIs. |
| **When not to wrap** | If the next layer is already a clear public error and more text adds noise, returning as-is is fine at **stable boundaries** you own. |

---

## 9. Common Misconceptions

| Misconception | Reality |
|---------------|--------|
| "Every `errors.New` string is a unique *type* in the type system" | You get a pointer to **`errorString`**-like values. The **string** is not a distinct Go **named type** per call. **Identity** is by pointer, not by text. |
| "`panic` is how Go handles expected errors" | **`panic` is for truly exceptional states** and often **bugs** or unrecoverable situations. **Normal failures** are **`error` returns**. |
| "You should always wrap" | **Wrap to add context** or preserve **`Is`/`As`**. **Duplicating** the same line or **wrapping without added meaning** is noise. |
| "Comparing with `==` is fine for sentinels" | **Only** if you are sure nothing wrapped the value. In layered code, prefer **`errors.Is`**. |

---

## 10. Related Tooling & Debugging

- **`errcheck`**: find functions whose errors are not handled.
- **`go vet`**: some checks around suspicious prints and format; combine with `staticcheck` in real projects.
- **IDE linters** with rules like **errcheck**, **unparam**, and **ineffassign** to catch shadowed or ignored `err` variables.

You run **`go vet ./...`** in CI. You add **staticcheck** for deeper patterns on larger teams.

---

## 11. Interview Gold Questions

### Q1: When do you use `errors.Is` vs `errors.As`?

**Short answer:** **`Is`** matches a **value** in the chain, often a **sentinel** or a comparable target. **`As`** recovers a **concrete type** and fills a **pointer** so you read extra fields. Always mention **unwrapping** and **`%w`**.

**Tradeoff:** If you overuse `As` with a deep hierarchy of types, your API can become brittle. `Is` keeps packages decoupled around **known sentinels**.

### Q2: What does `fmt.Errorf` with `%w` do that `%v` does not?

**Short answer:** **`%w`** records **unwrap** behavior so **`errors.Is` / `errors.As` / `Unwrap` work. **`%v`** embeds text only for the outer error. You should mention an inner linked error such as `wrapError` in spirit — not a plain one-shot string.

### Q3: Explain the "nil error interface" with a pointer type.

**Short answer:** A **`nil` pointer of type `*T` assigned to `error` still carries dynamic type `*T`**, so the **interface is not `nil`**. The fix is to return a **plain `var err error`**, return **`nil` directly**, or avoid returning a **typed** nil through an `error` result without that pitfall. Draw the **(type, data)** pair.

---

## 12. Final Verbal Answer

**In Go, the `error` interface is a single method, `Error() string` — so errors are just values, not control-flow exceptions. You return them and check `if err != nil`. In production you pick three common patterns: package-level **sentinel errors** for stable comparisons, **custom types** with extra fields, and **wrapping** with `fmt.Errorf` and `%w` to attach context. The standard library's `errors.Is` walks the unwrap chain for comparables like sentinels, and `errors.As` finds a concrete type. Avoid comparing with `==` after wrapping, avoid typed nils when you mean "no error", use `%w` not `%v` when you need unwrap, and do not let linters see ignored errors. That is the whole model.**

---

## 13. Comprehensive Interview Questions

> Full interview question bank (comprehensive Q&A) → [[questions/T09 Error Handling Patterns - Interview Questions]]

**Preview questions:**

1. How does `errors.Is` differ from a plain value comparison, and when does the difference matter in real code?
2. How would you design error types for a public library vs an internal service?
3. What happens if a function returns `*MyError` with value `nil` in a `error` return position?

---

> See [[Glossary]] for term definitions.
