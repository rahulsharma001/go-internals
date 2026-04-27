# P05 Interfaces Basics

> **Prerequisite note** — complete this before starting [[T09 Error Handling Patterns]], [[T11 Interface Internals (iface & eface)]], or [[T19 Context Package Internals]].
> Estimated time: ~20 min

---

## 1. Concept

An **interface** is a **contract**: a named list of methods. If your struct has all the methods the interface asks for, it satisfies the interface **automatically**. You never write `implements` in Go.

Callers depend on the **contract**, not on Postgres versus Stripe versus a mock. That is how you swap real dependencies in production and fakes in tests without rewriting your handlers.

---

## 2. Core Insight (TL;DR)

**Behavior is the passport.** The compiler cares whether your type has the right methods. It does not care what the struct is called.

**An interface value is a pair:** it remembers **which concrete type** is inside, and **the value itself** (often a pointer). People say **dynamic type** and **dynamic value**. Same idea.

**Nil is weird here.** A completely empty interface is nil. But you can put a **nil pointer** of a concrete type into an interface. The interface is **not** nil then. Your `if err != nil` still fires.

**`error` and `any` are interfaces you touch daily.** `error` means "something with `Error() string`." `any` means "anything goes" — you usually assert or type-switch to get specifics back.

---

## 3. Mental Model (Lock this in)

Think **USB-C**. The **interface** is the **port shape**. Your **concrete type** is the **cable**. If the plug fits, it works. Nobody stamped "certified" on the cable.

In a service: your HTTP handler might only know `UserStore` (**find user, save user**). In production you pass `PostgresUserStore`. In tests you pass `MockUserStore`. The handler never imports `database/sql`. It imports **your** small interface.

---

## 4. How It Works

### 4.1 Implicit satisfaction — `Notifier`

No `implements`. If the methods match, you are done.

```go
type Notifier interface {
	Notify(ctx context.Context, msg string) error
}

type EmailNotifier struct{ From string }

func (e *EmailNotifier) Notify(ctx context.Context, msg string) error {
	return nil // send mail…
}

type SlackNotifier struct{ WebhookURL string }

func (s *SlackNotifier) Notify(ctx context.Context, msg string) error { return nil }

type SMSNotifier struct{ Provider string }

func (s *SMSNotifier) Notify(ctx context.Context, msg string) error { return nil }

func Alert(ctx context.Context, n Notifier, text string) error {
	return n.Notify(ctx, text)
}
```

`*EmailNotifier` never declared that it "implements" `Notifier`. It just has `Notify`. Good enough. You pick email, Slack, or SMS when you wire the app.

---

### 4.2 `UserStore` / `Repository` — prod vs tests

```go
type UserStore interface {
	FindByID(ctx context.Context, id string) (*User, error)
	Save(ctx context.Context, u *User) error
}

type User struct{ ID, Email string }

type PostgresUserStore struct{} // holds *sql.DB in real code

func (p *PostgresUserStore) FindByID(ctx context.Context, id string) (*User, error) {
	return &User{ID: id}, nil
}
func (p *PostgresUserStore) Save(ctx context.Context, u *User) error { return nil }

type MockUserStore struct{ Users map[string]*User }

func (m *MockUserStore) FindByID(ctx context.Context, id string) (*User, error) {
	u, ok := m.Users[id]
	if !ok {
		return nil, fmt.Errorf("not found")
	}
	return u, nil
}
func (m *MockUserStore) Save(ctx context.Context, u *User) error {
	if m.Users == nil {
		m.Users = map[string]*User{}
	}
	m.Users[u.ID] = u
	return nil
}
```

The handler takes `UserStore`, not `*PostgresUserStore`. Tests pass `MockUserStore`. Prod passes `PostgresUserStore`. Same handler.

---

### 4.3 `PaymentProcessor` — Stripe vs Razorpay

```go
type PaymentProcessor interface {
	Charge(ctx context.Context, amountCents int64, currency string) (chargeID string, err error)
}

type StripeProcessor struct{ SecretKey string }

func (s *StripeProcessor) Charge(ctx context.Context, amountCents int64, currency string) (string, error) {
	return "ch_stripe_123", nil
}

type RazorpayProcessor struct{ KeyID, KeySecret string }

func (r *RazorpayProcessor) Charge(ctx context.Context, amountCents int64, currency string) (string, error) {
	return "pay_rp_456", nil
}
```

Checkout depends on `PaymentProcessor`. You do not fork the handler when the business picks a provider.

---

### 4.4 The `error` interface — `APIError`, `NotFoundError`, `ValidationError`

Stdlib: `error` is anything with `Error() string`. Custom types drive HTTP status via a **type switch**:

```go
type APIError struct{ Code int; Message string }

func (e *APIError) Error() string { return e.Message }

type NotFoundError struct{ Resource, ID string }

func (e *NotFoundError) Error() string {
	return fmt.Sprintf("%s %s not found", e.Resource, e.ID)
}

type ValidationError struct{ Field, Reason string }

func (e *ValidationError) Error() string {
	return fmt.Sprintf("invalid %s: %s", e.Field, e.Reason)
}

func WriteError(w http.ResponseWriter, err error) {
	switch e := err.(type) {
	case *ValidationError:
		http.Error(w, e.Error(), http.StatusBadRequest)
	case *NotFoundError:
		http.Error(w, e.Error(), http.StatusNotFound)
	case *APIError:
		if e.Code >= 400 && e.Code < 600 {
			http.Error(w, e.Error(), e.Code)
			return
		}
		fallthrough
	default:
		http.Error(w, "internal error", http.StatusInternalServerError)
	}
}
```

If errors are wrapped with `fmt.Errorf("...: %w", err)`, use **`errors.As`** to peel to `*ValidationError` and friends.

### 4.5 `io.Reader` / `io.Writer`, and `any`

`io.Reader` / `io.Writer` are the stream contracts. `r.Body` reads the request; `ResponseWriter` writes the response. Taking `io.Reader` in `ParseJSONBody` and `io.Writer` in `WriteJSON` lets you test with `bytes.Buffer` without HTTP.

```go
func ParseJSONBody(r io.Reader, v any) error { return json.NewDecoder(r).Decode(v) }
func WriteJSON(w io.Writer, v any) error     { return json.NewEncoder(w).Encode(v) }
```

`any` is `interface{}` with no methods — JSON `map[string]any`, caches, plugin boundaries. You assert or type-switch to get a concrete type back.

---

### 4.6 Interface value = **(type, value)** pair

An interface variable on the stack holds two words: a **type descriptor** (what concrete type is inside) and a **data pointer** (where the actual value lives). When both words are zero, the interface is nil. When either word is set, it is not nil.

```go
var n Notifier = &EmailNotifier{From: "ops@acme.co"}
n.Notify(context.Background(), "server down")
```

```
Step 1: var n Notifier = &EmailNotifier{From: "ops@acme.co"}

  stack 0xC000060000: n
    [0x00] tab  → itab for (*EmailNotifier, Notifier)
    [0x08] data → 0xC000080000

  heap  0xC000080000: EmailNotifier{ From: "ops@acme.co" }

Step 2: n.Notify(ctx, "server down")
  Runtime reads n.tab → finds Notify in the method table → calls (*EmailNotifier).Notify
  with receiver = 0xC000080000 (the data pointer).

Step 3: var n2 Notifier = (*EmailNotifier)(nil)

  stack 0xC000060010: n2
    [0x00] tab  → itab for (*EmailNotifier, Notifier)  ← NOT zero!
    [0x08] data → 0x0 (nil pointer)

  n2 != nil is TRUE — tab is set, so the interface is non-nil.
  A nil interface needs BOTH words to be zero.
```

---

### 4.7 The nil trap — `*APIError(nil)` inside `error`

```go
func LoadConfig(strict bool) error {
	var err *APIError
	if strict {
		err = &APIError{Code: 400, Message: "invalid"}
	}
	return err // BUG when strict == false
}
```

```
Step 1: strict == false → err is a nil *APIError

  stack 0xC000060000: err *APIError = nil (0x0)

Step 2: return err — Go converts *APIError to error interface

  The return slot is an error (interface = two words):
    [0x00] tab  → itab for (*APIError, error)   ← NOT zero!
    [0x08] data → 0x0 (nil pointer)

Step 3: Caller does `if err != nil`
  tab is non-zero → interface is non-nil → condition is TRUE
  The caller thinks something failed, even though nothing went wrong.

Step 4 (the fix): return nil — Go stores both words as zero
    [0x00] tab  → 0x0
    [0x08] data → 0x0
  Now `err != nil` is false. Correct behavior.
```

**Fix:** `if strict { return &APIError{…} }; return nil`, or guard with `if err == nil { return nil }` before `return err`.

---

### 4.8 Type assertion — e.g. cache value as `any`

```go
func GetUserFromCache(get func(string) (any, bool), key string) (*User, bool) {
	v, ok := get(key)
	if !ok {
		return nil, false
	}
	u, ok := v.(*User)
	return u, ok
}
```

`v.(T)` panics if wrong. Use **`v.(T), ok`** on untrusted or dynamic data.

```
Step 1: Cache returns v = &User{ID: "u1"}

  stack 0xC000060000: v (any = eface, two words)
    [0x00] _type → descriptor for *User
    [0x08] data  → 0xC000080000

  heap  0xC000080000: User{ ID: "u1" }

Step 2: u, ok := v.(*User)
  Runtime checks: does v._type match *User? → YES
  u = 0xC000080000 (same pointer), ok = true

Step 3 (wrong type): v holds a *Session instead
  Runtime checks: does v._type match *User? → NO
  u = nil, ok = false
  Without the `, ok` form this would panic.
```

---

### 4.9 Type switch

```go
func AuditChannel(ctx context.Context, n Notifier) string {
	switch x := n.(type) {
	case *EmailNotifier:
		return "email:" + x.From
	case *SlackNotifier:
		return "slack"
	case *SMSNotifier:
		return "sms:" + x.Provider
	default:
		return "unknown"
	}
}
```

`n.(type)` only works in a `switch`. In each case, `x` has the **concrete** type.

---

### 4.10 Pointer receivers vs value receivers

Methods on **`*T`** are not on **`T`**.

```go
type JobRunner interface{ Run(ctx context.Context) error }
type BatchJob struct{}
func (b *BatchJob) Run(ctx context.Context) error { return nil }

// var r JobRunner = BatchJob{}  // compile error
var r JobRunner = &BatchJob{} // OK
```

Services usually pass `&T` for mutable state or DB handles.

---

### 4.11 Compile-time guard + small interfaces

```go
var _ UserStore = (*PostgresUserStore)(nil)
var _ Notifier = (*EmailNotifier)(nil)
```

If someone deletes a method, the build breaks. Prefer **small** interfaces (often one to three methods). Fat interfaces mean fat mocks.

---

## 5. Key Rules & Behaviors

### 5.1 Implicit satisfaction — no `implements`

If your struct has every method the interface lists, it satisfies the interface. The compiler checks this at assignment time, not at declaration time.

```go
var store UserStore = &PostgresUserStore{} // compiles if methods match
```

```
Compiler check at this line:
  Does *PostgresUserStore have FindByID(ctx, string) (*User, error)? → YES
  Does *PostgresUserStore have Save(ctx, *User) error?               → YES
  Assignment allowed.
```

You never type `implements`. If you rename a method in the interface and forget to rename it on the struct, you get a compile error at the assignment — not at the struct definition.

---

### 5.2 Interface value is two words — both must be zero for nil

An interface variable holds **tab** (type descriptor) and **data** (pointer to the value). Only when both are zero is the interface nil.

```go
var e error               // tab=0, data=0 → nil
var p *APIError           // nil *APIError
var e2 error = p          // tab=itab(*APIError,error), data=0 → NOT nil
```

```
  e:  [tab=0x0 | data=0x0]        → e == nil is true
  e2: [tab=itab | data=0x0]       → e2 == nil is FALSE
                 ↑ tab is set, so the interface has a type even though the pointer is nil
```

This is why you never return a typed nil through an interface. Always `return nil` on the success path.

---

### 5.3 Pointer receiver methods are NOT on the value type

If you define `func (b *BatchJob) Run()`, only `*BatchJob` has `Run` — not `BatchJob`. Trying to assign a bare `BatchJob{}` to an interface that needs `Run()` won't compile.

```go
type JobRunner interface{ Run(ctx context.Context) error }
type BatchJob struct{}
func (b *BatchJob) Run(ctx context.Context) error { return nil }

// var r JobRunner = BatchJob{}   // compile error — BatchJob has no Run
var r JobRunner = &BatchJob{}     // OK — *BatchJob has Run
```

```
Method list for BatchJob:   (empty)
Method list for *BatchJob:  Run(ctx, error)

JobRunner needs: Run(ctx, error)
  BatchJob  → missing Run → FAIL
  *BatchJob → has Run     → OK
```

Services and repositories almost always use pointer receivers because they hold mutable state (`*sql.DB`, connection pools, caches).

---

### 5.4 Use the comma-ok form for type assertions on untrusted data

`v.(T)` without the second return value **panics** if the concrete type doesn't match. Always use `v.(T), ok` when the type isn't guaranteed — caches, JSON `any` values, plugin boundaries.

```go
u, ok := v.(*User)
if !ok {
    // v held something else — handle gracefully
}
```

---

### 5.5 Keep interfaces small — define them where you use them

One to three methods is the sweet spot. A 10-method interface means a 10-method mock. Define interfaces in the **consumer** package, not next to the implementation. The handler package defines `UserStore`; the postgres package just implements the methods.

```go
var _ UserStore = (*PostgresUserStore)(nil) // compile-time guard
```

If someone deletes a method from `PostgresUserStore`, this line breaks the build immediately.

---

## 6. Code Examples (Show, Don't Tell)

### Handler + `UserStore` + test

The handler depends on the `UserStore` interface. Production wires in Postgres; tests wire in a map-backed mock. The handler code never changes.

```go
func NewGetUserHandler(store UserStore) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := r.URL.Query().Get("id")
		u, err := store.FindByID(r.Context(), id)
		if err != nil {
			WriteError(w, err)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_ = WriteJSON(w, u)
	}
}

func TestGetUser(t *testing.T) {
	store := &MockUserStore{Users: map[string]*User{"1": {ID: "1", Email: "a@b.co"}}}
	h := NewGetUserHandler(store)
	rec := httptest.NewRecorder()
	h(rec, httptest.NewRequest(http.MethodGet, "/?id=1", nil))
	if rec.Code != http.StatusOK {
		t.Fatal(rec.Code)
	}
}
```

```
Step 1: NewGetUserHandler(store) — store is UserStore interface
  stack 0xC000060000: store
    [0x00] tab  → itab for (*MockUserStore, UserStore)
    [0x08] data → 0xC000080000

  heap  0xC000080000: MockUserStore{ Users: map[...] }

Step 2: store.FindByID(ctx, "1")
  Runtime reads store.tab → finds FindByID in method table
  Calls (*MockUserStore).FindByID with receiver 0xC000080000
  Returns &User at 0xC000090000

Step 3: WriteJSON(w, u) — u is *User
  Encoder writes {"ID":"1","Email":"a@b.co"} to the ResponseWriter
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the behavior (2 min)

```go
func pickNotifier(useEmail bool) Notifier {
	var n *EmailNotifier
	if useEmail {
		n = &EmailNotifier{}
	}
	return n
}

func main() {
	x := pickNotifier(false)
	fmt.Println(x == nil)
}
```

(`Notifier` / `EmailNotifier` / `Notify` as in §4.1.)

> [!success]- Answer
> Prints **`false`**.
>
> `pickNotifier` returns a `Notifier`. When `useEmail` is false, `n` is a nil `*EmailNotifier`, but the return wraps **type `*EmailNotifier`** with a **nil pointer**. That is **not** a nil interface. Use **`return nil`** when there is no notifier.

### Tier 2: Fix the bug (5 min)

`SaveDraft` should return **no error** when the email is valid. Callers still see `err != nil`. Fix it. (The same pattern burns you on **`UserStore.Save`** when you accumulate a `*ValidationError` in a variable and return it on the happy path.)

```go
func SaveDraft(ctx context.Context, email string) error {
	var err *ValidationError
	if email == "" {
		err = &ValidationError{Field: "email", Reason: "required"}
	}
	return err
}
```

> [!success]- Answer
> **Problem:** When `email` is non-empty, `err` is a nil `*ValidationError`, but `return err` still puts **dynamic type `*ValidationError`** and **nil pointer** into the `error`. The interface value is non-nil.
>
> **Fix:**
>
> ```go
> func SaveDraft(ctx context.Context, email string) error {
> 	if email == "" {
> 		return &ValidationError{Field: "email", Reason: "required"}
> 	}
> 	return nil
> }
> ```

---

## 7. Gotchas & Interview Traps

| # | Trap | What happens | Why (§4 link) |
|---|------|-------------|---------------|
| 1 | Return nil `*APIError` through `error` | Caller sees `err != nil` even on success | §4.7 — the interface tab word is set to `itab(*APIError, error)`, so the interface is non-nil even though the data pointer is zero |
| 2 | `v.(T)` without comma-ok on cache `any` | Panics at runtime if wrong type | §4.8 — assertion checks `_type` against `T`; mismatch with no `ok` receiver triggers panic |
| 3 | `BatchJob{}` assigned to `JobRunner` | Compile error | §4.10 — `*BatchJob` has `Run`, but `BatchJob` does not; pointer receiver methods don't promote to the value type |
| 4 | Fat interface with 8+ methods | Every test needs an 8-method mock | §4.11 — keep interfaces to 1-3 methods; define in the consumer package |
| 5 | Comparing two interfaces with different concrete types | `==` returns false even if the values "look the same" | §4.6 — comparison checks both tab and data; different concrete types → different tabs |

---

## 8. Interview Gold Questions (Top 3)

**Q1: Why can a nil pointer inside an `error` interface cause `err != nil` to be true?**

An interface value is two words: type descriptor and data pointer. When you assign a nil `*APIError` to an `error`, the type descriptor is set (it knows the concrete type is `*APIError`) even though the data pointer is zero. Only when **both** words are zero is the interface nil. The fix: always `return nil` as `error` on the success path, never a typed nil through the interface.

**Q2: How does Go know a struct satisfies an interface without `implements`?**

The compiler checks at the assignment site. When you write `var store UserStore = &PostgresUserStore{}`, it verifies that `*PostgresUserStore` has every method `UserStore` declares — matching names, parameter types, and return types. If anything is missing, you get a compile error right there. This is called **structural typing** or **implicit satisfaction**. The advantage: your Postgres package never imports the interface — the handler package owns it. That keeps dependencies pointing inward.

**Q3: When should you use a type assertion vs a type switch vs `errors.As`?**

Use `v.(*User), ok` when you expect one specific type — like pulling a `*User` from a cache. Use a type switch when you need to branch on several concrete types — like `WriteError` matching `*ValidationError`, `*NotFoundError`, `*APIError`. Use `errors.As` when the error might be **wrapped** with `fmt.Errorf("...: %w", err)` — it unwraps the chain looking for a match, which a plain type switch can't do.

---

## 9. 30-Second Verbal Answer

"Interfaces in Go are method contracts — if your struct has the methods, it satisfies the interface automatically, no `implements` keyword. Under the hood, an interface value is two words: a type descriptor and a data pointer. That's why a nil pointer inside an interface is not a nil interface — the type word is still set. In practice, you use interfaces to decouple handlers from implementations — your handler takes `UserStore`, prod passes Postgres, tests pass a mock. Keep them small — one to three methods — and define them in the consumer package, not next to the implementation."

---

> See [[Glossary]] for term definitions.
