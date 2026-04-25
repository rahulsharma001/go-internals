# T09 Error Handling Patterns — Exercises

> Practice for [[T09 Error Handling Patterns]]. **Tier 1** = warm-up in the main note. Here: **Tier 2** (typed nil) and **Tier 3** (validation + `As`).

---

## Tier 2 — Fix the typed `nil` error return

**Goal:** A function is supposed to return “no error,” but the caller still sees a non-`nil` `error` because a **nil pointer** of type `*AppError` is placed inside a non-**nil** `error` **interface** value. Fix it so the happy path returns a **truly** `nil` `error`.

**The bug in plain terms:** The language stores an **(type, value)** pair inside an `error` box. A **nil pointer** can still be **typed** as `*AppError`. The box is **not empty**—so `err != nil` is true even when there is “nothing to read.”

### Broken pattern (intentionally wrong)

```go
package main

import "fmt"

type AppError struct{ Msg string }

func (e *AppError) Error() string {
	if e == nil {
		return "AppError<nil>" // String still exists; interface may be 'wrong' in other code paths
	}
	return e.Msg
}

// Returns nil *AppError on success
func load() *AppError { return nil }

// BUG: non-nil error interface, dynamic value is nil *AppError
func workBad() error { return load() }

func workFixed() error {
	err := load()
	if err == nil {
		return nil
	}
	return err
}

func main() {
	eb := workBad()
	fmt.Println("workBad: err != nil is", eb != nil) // true — surprise

	ef := workFixed()
	fmt.Println("workFixed: err != nil is", ef != nil) // false — correct
}
```

**Your task:** Re-type or refactor so **every** “success” path returns an **untyped** `nil` in the `error` return (or a named `err error` that is the **interface**-typed `nil`).

**Why this works:** The **fix** never converts a `nil` **`*AppError` pointer** *directly* into the **`error` return type**. It branches: **no pointer** means **return `error`’s** `nil` (no type inside the box).

**Alternative valid fixes:** change `load` to return `(result, err error)` with `err` as `error`; or make `load() error` and `return nil` on success; or return `error(AppErrorOrNil())` with an explicit `if err == nil { return nil }` **before** the return.

**What to observe:** `fmt.Printf("%#v\n", err)` on the **bug** often shows `(*main.AppError)(nil)` while `err != nil` is still **true**—this is the **interview** proof people ask for.

**Related reading:** [[T09 Error Handling Patterns]], **typed nil** row on [[T09 Error Handling Patterns - Revision]].

---

## Tier 3 — Mini validation library: `Validate`, wrap, `errors.As`

**Goal:** `Validate(u User) *ValidationError` returns **field-level** errors; `HandleSave` wraps with `fmt.Errorf` and `%w`; the **caller** uses **`errors.As`** to read structured fields. **All** in one runnable `main` package.

### Full program

```go
package main

import (
	"errors"
	"fmt"
)

// User is the record we validate before "save"
type User struct {
	Name  string
	Email string
	Age   int
}

// ValidationError carries machine-readable field + message (custom error type)
type ValidationError struct {
	Field, Message string
}

func (e *ValidationError) Error() string {
	return fmt.Sprintf("validation: %s: %s", e.Field, e.Message)
}

// Validate returns nil when OK, or a *ValidationError (pointer for errors.As)
func Validate(u User) *ValidationError {
	switch {
	case u.Name == "":
		return &ValidationError{Field: "Name", Message: "required"}
	case u.Email == "":
		return &ValidationError{Field: "Email", Message: "required"}
	case u.Age < 0:
		return &ValidationError{Field: "Age", Message: "must be >= 0"}
	default:
		return nil
	}
}

// HandleSave is the "service layer" — wraps with context + %w
func HandleSave(u User) error {
	if ve := Validate(u); ve != nil {
		return fmt.Errorf("save user: %w", ve)
	}
	return nil
}

func main() {
	invalid := User{Name: "", Email: "a@b.c", Age: 1}
	if err := HandleSave(invalid); err != nil {
		var ve *ValidationError
		if errors.As(err, &ve) {
			fmt.Println("as ValidationError -> Field:", ve.Field, "Message:", ve.Message)
		}
		fmt.Println("Full chain (log line):", err)
	} else {
		fmt.Println("unexpected: no error")
	}

	valid := User{Name: "Ada", Email: "a@b.c", Age: 19}
	if err := HandleSave(valid); err != nil {
		fmt.Println("unexpected failure:", err)
	} else {
		fmt.Println("valid user — no error value")
	}
}
```

### How to run

```bash
go run .
```

(From a folder containing a single `main.go` with the program above, or: `go run main.go`.)

### Expected output (observe structure + chain)

```text
as ValidationError -> Field: Name Message: required
Full chain (log line): save user: validation: Name: required
valid user — no error value
```

**What to observe**

1. **`%w`**: The outer string is `save user: …`, and `errors.As` still finds the **inner** `*ValidationError` (unwrap works).  
2. **Replace `%w` with `%v`** in `HandleSave` and re-run: `errors.As` often still **fails** to see `*ValidationError` because the **semantic wrap link** is gone—`fmt` printed the inner text, but the **chain** is not there for `As` (depending on `fmt` version / behavior: with plain `%v`, **Unwrap** is not set — **this is the lesson** in [[T09 Error Handling Patterns]]).  
3. **Typed nil:** In `HandleSave` success, `return nil` is a **true** `nil` `error` — no `*ValidationError` box involved.

**Stretch goals:** return **multiple** field errors (collect slice, custom type) while still using `%w` on an outer `ValidationBlock` with `Unwrap` on Go 1.20+ `errors.Join` — only after you are comfortable with the **single** `ValidationError` version above.

---

## Self-check (both tiers)

| Question | Pass criterion |
|----------|----------------|
| Why was `err != nil` true with a “nil” `*AppError`? | **Interface** holds **(type, value)**; **typed** `nil` is **not** the **nil interface**. |
| Why `%w` for the service layer? | Preserves **unwrap** so **`errors.As`** in HTTP handler (or `main`) still hits `*ValidationError`. |

**Related visual:** [[T09 Error Handling Patterns - Visual Map]] · **Q&A:** [[T09 Error Handling Patterns - Interview Questions]]
