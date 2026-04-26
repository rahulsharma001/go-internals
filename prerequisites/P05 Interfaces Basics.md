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

Conceptually: **which concrete type**, plus **the data** (pointer or small value).

```
MEMORY TRACE — `Notifier` with `*EmailNotifier`:
  `var n Notifier = (*EmailNotifier)(nil)` → stored type is `*EmailNotifier`, payload is nil → **`n` is not a nil interface**.
  `n = &EmailNotifier{From: "ops@co"}` → same type, payload points at the struct; `n.Notify` dispatches there.
Aha: an interface value is **type + value**, not "just a pointer."
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
MEMORY TRACE:

Step 1: strict == false → `err` is a nil `*APIError`.

Step 2: `return err` as `error` → dynamic type `*APIError`, dynamic value nil pointer → **not** a nil interface.

Step 3: Caller `if err != nil` runs even though nothing failed.

Aha: success must be **`return nil`**, not a nil `*Concrete` through `error`.
```

**Fix:** `if strict { return &APIError{…} }; return nil`, or `if err == nil { return nil }` before `return err`.

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
MEMORY TRACE — `any` from a cache:
  `var v any = &User{ID: "u1"}` → dynamic type `*User`, value points at that struct.
  `u, ok := v.(*User)` → label matches → `ok == true`. Wrong concrete type → `ok == false`, `u` is nil `*User`.
Aha: assertion is "unwrap only if the label matches."
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

## 5. Handler + `UserStore` + test

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

---

## 5.5. Practice Checkpoint

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

## 6. Gotchas, rules of thumb, interview sound bites

**Rules:** If your struct has every method the interface needs, it satisfies it automatically. **`var e error`** is nil; **`var p *APIError; e := p`** is not nil as an `error` when `p` is nil. Prefer **`v.(T), ok`**. **`*T`** methods are not on **`T`** — pass **`&T`**.

**Traps:** Typed nil through `error`. Assertion panic on bad `any`. Fat interfaces → fat mocks.

**Top 3 interview answers:** (1) Non-nil `error` with nil pointer — **dynamic type is set**, only an interface with **both** halves empty is nil; use **`return nil`**. (2) Implicit satisfaction — **decoupling**, **mocks**, define interfaces **where you use them**. (3) Assertion vs switch vs **`errors.As`** — one unwrap vs many cases vs **wrapped** errors.

**30-second version:** Interfaces are **method contracts**, satisfied **automatically**. Values are **concrete type + data**; nil only when **both** are empty. **`io.Reader` / `io.Writer`** for HTTP streams; **`any`** + assertions for caches and JSON.

---

> See [[Glossary]] for term definitions.
