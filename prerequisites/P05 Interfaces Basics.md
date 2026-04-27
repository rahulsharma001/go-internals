# P05 Interfaces Basics

> **Prerequisite note** — complete this before starting [[T09 Error Handling Patterns]], [[T11 Interface Internals (iface & eface)]], or [[T19 Context Package Internals]].
> Estimated time: ~25 min

---

## 1. Concept

An **interface** is a contract. You write down a list of methods. Any struct that has those exact methods automatically fulfills the contract — you never write `implements` in Go.

Why does this matter? Because your HTTP handler can depend on the contract ("something that can find a user"), not on a specific database. Production passes Postgres. Tests pass a fake. The handler doesn't know and doesn't care.

---

## 2. Core Insight (TL;DR)

**Behavior is the passport.** The compiler checks whether your type has the right methods. It does not check the name.

**An interface value is a pair.** It remembers **which concrete type** is inside, and **a pointer to the actual data**. People call these the **dynamic type** and **dynamic value**.

**Nil is weird.** An interface is nil only when **both** halves are empty. If you stuff a nil pointer of a concrete type into an interface, the "type" half is set — so the interface is **not** nil. This is the single most common interface bug in Go.

---

## 3. Mental Model (Lock this in)

Think **USB-C**. The interface is the **port shape**. Your concrete type is the **cable**. If the plug fits, it works. Nobody stamped "certified" on the cable — it just fits or it doesn't.

```
  Interface (the port):         Concrete type (the cable):
  ┌──────────────────┐          ┌──────────────────┐
  │  UserStore       │          │  PostgresUserStore│
  │  - FindByID()    │  ◄─fits──│  - FindByID()    │
  │  - Save()        │          │  - Save()         │
  └──────────────────┘          └──────────────────┘
                                ┌──────────────────┐
          same port ◄──fits─────│  MockUserStore   │
                                │  - FindByID()    │
                                │  - Save()         │
                                └──────────────────┘
```

Your handler plugs into the port. It doesn't know which cable is on the other end.

**The mistake that teaches you:** what if you return a nil pointer through an interface? You'd expect `err == nil` to be true. It's not — the interface remembers the *type* of the pointer, so it's non-nil. You'll see this fully in §4.5.

---

## 4. How It Works

### 4.1 What is an interface, exactly?

An interface is a type you declare with the keyword `interface`. Inside the braces, you list method signatures — just the name, parameters, and return types. No implementation. Think of it as a checklist: "whatever you give me must have these methods."

```go
type Notifier interface {
	Notify(ctx context.Context, msg string) error
}
```

This says: "A `Notifier` is anything that has a method called `Notify`, which takes a context and a string, and returns an error."

That's it. No fields. No constructor. Just a method list.

---

### 4.2 How does a struct fulfill an interface?

You write a struct, and you give it a method with the **exact same signature** as the one in the interface. You don't write `implements`. You don't register anything. The compiler figures it out automatically.

```go
type EmailNotifier struct {
	From string
}

func (e *EmailNotifier) Notify(ctx context.Context, msg string) error {
	fmt.Printf("sending email from %s: %s\n", e.From, msg)
	return nil
}
```

Does `*EmailNotifier` have a method called `Notify(ctx context.Context, msg string) error`? Yes. So `*EmailNotifier` is a valid `Notifier`. Done.

You can have multiple structs that all fulfill the same interface:

```go
type SlackNotifier struct {
	WebhookURL string
}

func (s *SlackNotifier) Notify(ctx context.Context, msg string) error {
	fmt.Printf("posting to Slack %s: %s\n", s.WebhookURL, msg)
	return nil
}
```

`*SlackNotifier` also has `Notify` with the right signature. So it's also a valid `Notifier`.

```
Compiler's checklist for Notifier:
  ✓ Does *EmailNotifier have Notify(ctx, string) error?  → YES → accepted
  ✓ Does *SlackNotifier have Notify(ctx, string) error?  → YES → accepted
  ✗ Does *User have Notify(ctx, string) error?           → NO  → rejected
```

---

### 4.3 Using an interface as a parameter

Here's where interfaces become powerful. You write a function that takes the **interface type** as a parameter — not any specific struct.

```go
func Alert(ctx context.Context, n Notifier, msg string) error {
	return n.Notify(ctx, msg)
}
```

`Alert` doesn't know or care whether `n` is an `*EmailNotifier` or a `*SlackNotifier`. It just calls `n.Notify`. Whatever concrete type you pass in, Go dispatches to that type's `Notify` method.

Here's what happens step by step when you call `Alert`:

```go
email := &EmailNotifier{From: "ops@acme.co"}
Alert(ctx, email, "server down")
```

```
Step 1: You pass &EmailNotifier{From: "ops@acme.co"} as the Notifier parameter.
        Go wraps it into an interface value:
          n = { type: *EmailNotifier, data: pointer to the EmailNotifier struct }

Step 2: Alert calls n.Notify(ctx, "server down").
        Go looks at the type half of n → it's *EmailNotifier.
        Go finds *EmailNotifier's Notify method and calls it.

Step 3: (*EmailNotifier).Notify runs → prints "sending email from ops@acme.co: server down"
```

If you pass a `*SlackNotifier` instead, same flow, different method gets called. The `Alert` function doesn't change at all. That's the whole point.

---

### 4.4 The real-world pattern: swapping implementations

In a backend service, you use interfaces to swap between real and fake implementations. The most common case: your handler talks to a **database interface**, not a specific database.

```go
type UserStore interface {
	FindByID(ctx context.Context, id string) (*User, error)
	Save(ctx context.Context, u *User) error
}
```

This says: "A `UserStore` is anything that can find a user by ID and save a user." Now you write two structs that fulfill this:

**Production:** talks to Postgres.

```go
type PostgresUserStore struct {
	DB *sql.DB
}

func (p *PostgresUserStore) FindByID(ctx context.Context, id string) (*User, error) {
	// real SQL query here
	return &User{ID: id, Email: "user@example.com"}, nil
}

func (p *PostgresUserStore) Save(ctx context.Context, u *User) error {
	// real INSERT/UPDATE here
	return nil
}
```

**Tests:** stores users in a map. No database needed.

```go
type MockUserStore struct {
	Users map[string]*User
}

func (m *MockUserStore) FindByID(ctx context.Context, id string) (*User, error) {
	u, ok := m.Users[id]
	if !ok {
		return nil, fmt.Errorf("user %s not found", id)
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

Your handler takes `UserStore` — it doesn't know which one it gets:

```go
func NewGetUserHandler(store UserStore) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := r.URL.Query().Get("id")
		u, err := store.FindByID(r.Context(), id)
		if err != nil {
			http.Error(w, err.Error(), http.StatusNotFound)
			return
		}
		json.NewEncoder(w).Encode(u)
	}
}
```

```
In production:
  store = &PostgresUserStore{DB: db}   → FindByID hits Postgres

In tests:
  store = &MockUserStore{Users: map[string]*User{"1": {ID: "1"}}}
                                        → FindByID reads from the map

Same handler. Different backends. Zero code changes.
```

This is the core value of interfaces in Go: **your business logic never imports the database package.**

---

### 4.5 What an interface value looks like in memory

This is important because it explains the nil trap.

When you assign a concrete value to an interface variable, Go stores **two things** on the stack: a **type descriptor** (which concrete type is inside) and a **data pointer** (where the actual struct lives on the heap).

```go
var n Notifier = &EmailNotifier{From: "ops@acme.co"}
```

```
stack 0xC000060000: n (Notifier interface — 16 bytes, two words)
  [0x00] tab  → type descriptor: "this is a *EmailNotifier"
  [0x08] data → 0xC000080000

heap  0xC000080000: EmailNotifier{ From: "ops@acme.co" }
```

When you call `n.Notify(ctx, msg)`, Go reads the tab to find out the concrete type, looks up the `Notify` method for that type, and calls it with the data pointer as the receiver.

**Why this matters for nil:** an interface is nil only when **both** words are zero.

```go
var n Notifier                          // tab=0, data=0 → nil
var n2 Notifier = (*EmailNotifier)(nil) // tab=*EmailNotifier, data=0 → NOT nil!
```

```
n:  [tab = 0x0              | data = 0x0]  → n == nil is TRUE
n2: [tab = *EmailNotifier   | data = 0x0]  → n2 == nil is FALSE
                               ↑ tab is set, so Go says "this interface holds something"
```

`n2` has a type stamped on it — Go considers it non-nil even though the data pointer is zero. This is the typed-nil trap, and it bites you most often with the `error` interface (§4.7).

---

### 4.6 The `error` interface and custom error types

The standard library defines `error` as an interface with one method:

```go
type error interface {
	Error() string
}
```

Any struct with an `Error() string` method is automatically a valid `error`. You use this to create custom error types that carry structured information:

```go
type NotFoundError struct {
	Resource string
	ID       string
}

func (e *NotFoundError) Error() string {
	return fmt.Sprintf("%s %s not found", e.Resource, e.ID)
}

type ValidationError struct {
	Field  string
	Reason string
}

func (e *ValidationError) Error() string {
	return fmt.Sprintf("invalid %s: %s", e.Field, e.Reason)
}
```

Both `*NotFoundError` and `*ValidationError` have `Error() string`, so both are valid `error` values. Your handler can return them, and your middleware can inspect them:

```go
func WriteError(w http.ResponseWriter, err error) {
	switch e := err.(type) {
	case *ValidationError:
		http.Error(w, e.Error(), http.StatusBadRequest)
	case *NotFoundError:
		http.Error(w, e.Error(), http.StatusNotFound)
	default:
		http.Error(w, "internal error", http.StatusInternalServerError)
	}
}
```

The `switch e := err.(type)` is a **type switch**. It asks: "what concrete type is inside this `error` interface?" Each `case` branch matches a specific type, and inside that branch, `e` has the concrete type — so you can read `e.Field`, `e.Resource`, etc.

```
When err holds a *ValidationError{Field: "email", Reason: "required"}:

  err interface value:
    [tab]  → *ValidationError
    [data] → pointer to the struct

  type switch checks tab:
    case *ValidationError → MATCH → e is now *ValidationError
    → calls http.Error(w, "invalid email: required", 400)
```

---

### 4.7 The nil trap — returning a typed nil through `error`

This is the most common interface bug in Go. Read this carefully.

```go
func LoadConfig(strict bool) error {
	var err *ValidationError
	if strict {
		err = &ValidationError{Field: "config", Reason: "strict mode"}
	}
	return err // BUG when strict == false
}
```

When `strict` is false, `err` is a nil `*ValidationError`. You'd expect `return err` to return nil. But it doesn't — here's why:

```
Step 1: strict == false → err is a nil *ValidationError
  stack: err = nil (a nil pointer of type *ValidationError)

Step 2: return err — Go converts *ValidationError to the error interface
  Go builds the interface value:
    [0x00] tab  → *ValidationError   ← this is NOT zero!
    [0x08] data → 0x0 (nil pointer)

Step 3: Caller does `if err != nil`
  Go checks: is tab zero? No. → interface is non-nil → condition is TRUE.
  The caller thinks LoadConfig failed, even though nothing went wrong.

The fix — return nil directly:
  Go builds the interface value:
    [0x00] tab  → 0x0
    [0x08] data → 0x0
  Now `if err != nil` is false. Correct.
```

**Fix:** never return a concrete error variable on the success path. Use early returns:

```go
func LoadConfig(strict bool) error {
	if strict {
		return &ValidationError{Field: "config", Reason: "strict mode"}
	}
	return nil // both words zero — truly nil
}
```

---

### 4.8 Type assertion — pulling a concrete type out of `any`

Sometimes you have an interface value (especially `any`, which is `interface{}` with no methods) and you need to get the concrete type back out. That's a **type assertion**.

```go
func GetUserFromCache(cache map[string]any, key string) (*User, bool) {
	v, ok := cache[key]
	if !ok {
		return nil, false
	}
	u, ok := v.(*User)  // type assertion: "I believe v holds a *User"
	return u, ok
}
```

`v.(*User)` asks Go: "is the concrete type inside `v` actually `*User`?" If yes, you get the pointer back. If no, `ok` is false and `u` is nil.

```
Step 1: cache["user:1"] returns v = &User{ID: "u1"} stored as `any`

  v (any interface — two words):
    [tab]  → *User
    [data] → 0xC000080000 (pointer to User struct on heap)

Step 2: u, ok := v.(*User)
  Go checks: does v's tab match *User? → YES
  u = 0xC000080000 (the same pointer), ok = true

Step 3 (wrong type): cache["session:abc"] returns v = &Session{...}
  Go checks: does v's tab match *User? → NO
  u = nil, ok = false
```

**Always use the comma-ok form** (`v.(*User), ok`) when you're not 100% sure of the type. Without the `, ok`, a wrong type causes a **panic** at runtime.

---

### 4.9 Pointer receivers and interfaces

There's one rule that catches people: if you define a method on `*T` (pointer receiver), only `*T` has that method — not `T` itself.

```go
type JobRunner interface {
	Run(ctx context.Context) error
}

type BatchJob struct{}

func (b *BatchJob) Run(ctx context.Context) error { return nil }
```

```
// var r JobRunner = BatchJob{}   // COMPILE ERROR — BatchJob has no Run
var r JobRunner = &BatchJob{}     // OK — *BatchJob has Run
```

Why? Because `Run` is defined on `*BatchJob`, not `BatchJob`. Go doesn't automatically take the address of a value to make an interface assignment work.

```
Method list for BatchJob:   (empty — no methods defined on the value)
Method list for *BatchJob:  Run(ctx, error)

JobRunner needs: Run(ctx, error)
  BatchJob  → no Run method → FAIL
  *BatchJob → has Run       → OK
```

In practice, you almost always use pointer receivers for types that hold state (`*sql.DB`, loggers, caches), so you almost always assign `&MyStruct{}` to interfaces.

---

### 4.10 Compile-time guard and keeping interfaces small

You can add a line to your code that fails at build time if a struct stops fulfilling an interface:

```go
var _ UserStore = (*PostgresUserStore)(nil)
```

This doesn't run any code. It just tells the compiler: "please verify that `*PostgresUserStore` has all the methods `UserStore` needs." If someone removes or renames a method, the build breaks immediately.

**Keep interfaces small.** One to three methods is the sweet spot. A 10-method interface means you need a 10-method mock for every test. That's painful. If you only need `FindByID` in your handler, your interface should only have `FindByID`.

---

### 4.11 `io.Reader`, `io.Writer`, and `any`

Two interfaces you'll see everywhere in Go's standard library:

- **`io.Reader`** — has one method: `Read([]byte) (int, error)`. Anything that can be read from (files, HTTP request bodies, buffers) is an `io.Reader`.
- **`io.Writer`** — has one method: `Write([]byte) (int, error)`. Anything that can be written to (files, HTTP response writers, buffers) is an `io.Writer`.

```go
func ParseJSONBody(r io.Reader, v any) error {
	return json.NewDecoder(r).Decode(v)
}
```

This function works with an HTTP request body, a file, or a `bytes.Buffer` in tests — because they all have `Read`.

**`any`** is `interface{}` — an interface with zero methods. Everything fulfills it. You see it in JSON unmarshaling (`map[string]any`), caches, and generic containers. The trade-off: you lose type safety and need type assertions to get concrete values back out (§4.8).

---

## 5. Key Rules & Behaviors

### 5.1 Implicit satisfaction — no `implements`

If your struct has every method the interface lists, it fulfills the interface. The compiler checks this at the point where you assign the struct to the interface variable, not at the struct definition.

```go
var store UserStore = &PostgresUserStore{}
```

```
Compiler check at this line:
  Does *PostgresUserStore have FindByID(ctx, string) (*User, error)? → YES
  Does *PostgresUserStore have Save(ctx, *User) error?               → YES
  Assignment allowed.
```

If you rename a method in the interface and forget to update the struct, you get a compile error at the assignment — not somewhere deep in the call chain.

---

### 5.2 Interface value is two words — both must be zero for nil

An interface variable holds **tab** (type descriptor) and **data** (pointer to the value). Only when both are zero is the interface nil.

```go
var e error               // tab=0, data=0 → nil
var p *ValidationError    // nil *ValidationError
var e2 error = p          // tab=*ValidationError, data=0 → NOT nil
```

```
  e:  [tab=0x0 | data=0x0]               → e == nil is true
  e2: [tab=*ValidationError | data=0x0]   → e2 == nil is FALSE
                              ↑ tab is set, so the interface is non-nil
```

This is why you always `return nil` on the success path — never a typed nil through an interface.

---

### 5.3 Pointer receiver methods are NOT on the value type

If you define `func (b *BatchJob) Run()`, only `*BatchJob` has `Run` — not `BatchJob`. Assigning a bare `BatchJob{}` to an interface that needs `Run()` won't compile.

```go
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

Services and repositories almost always use pointer receivers because they hold mutable state (`*sql.DB`, connection pools, caches). So you almost always pass `&MyStruct{}` to interfaces.

---

### 5.4 Use the comma-ok form for type assertions on untrusted data

`v.(*User)` without the second return value **panics** if the concrete type doesn't match. Always use `v.(*User), ok` when the type isn't guaranteed.

```go
u, ok := v.(*User)
if !ok {
    // v held something else — handle gracefully
}
```

```
With comma-ok:    v.(*User) → wrong type → ok=false, u=nil  (safe)
Without comma-ok: v.(*User) → wrong type → PANIC             (crash)
```

---

### 5.5 Keep interfaces small — define them where you use them

One to three methods is the sweet spot. A 10-method interface means a 10-method mock in every test.

Define the interface in the **consumer** package (your handler), not next to the implementation (your postgres package). The handler knows what it needs. The implementation just provides it.

```go
var _ UserStore = (*PostgresUserStore)(nil) // compile-time guard
```

If someone deletes a method from `PostgresUserStore`, this line breaks the build immediately.

---

## 6. Code Examples (Show, Don't Tell)

### Full handler + test with interface swap

This ties together everything from Section 4: the handler depends on the `UserStore` interface, prod wires Postgres, tests wire a mock.

```go
func NewGetUserHandler(store UserStore) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := r.URL.Query().Get("id")
		u, err := store.FindByID(r.Context(), id)
		if err != nil {
			http.Error(w, err.Error(), http.StatusNotFound)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(u)
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
Step 1: NewGetUserHandler(store) — store is a UserStore interface value
  stack 0xC000060000: store
    [0x00] tab  → *MockUserStore (the concrete type)
    [0x08] data → 0xC000080000 (pointer to the MockUserStore on heap)

Step 2: store.FindByID(ctx, "1")
  Go reads store's tab → finds FindByID for *MockUserStore → calls it
  MockUserStore looks up "1" in its Users map → returns &User at 0xC000090000

Step 3: json.NewEncoder(w).Encode(u)
  Writes {"ID":"1","Email":"a@b.co"} to the ResponseWriter
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

(`Notifier` / `EmailNotifier` / `Notify` as in §4.2.)

> [!success]- Answer
> Prints **`false`**.
>
> `pickNotifier` returns a `Notifier` interface. When `useEmail` is false, `n` is a nil `*EmailNotifier`, but `return n` wraps it into the interface: **tab = `*EmailNotifier`, data = nil**. The tab is set, so the interface is non-nil. Use **`return nil`** when there's no notifier to return.

### Tier 2: Fix the bug (5 min)

`SaveDraft` should return **no error** when the email is valid. Callers still see `err != nil`. Fix it.

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
> **Problem:** When `email` is non-empty, `err` is a nil `*ValidationError`, but `return err` puts **tab = `*ValidationError`** and **data = nil** into the `error` interface. The interface is non-nil.
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
| 1 | Return nil `*ValidationError` through `error` | Caller sees `err != nil` even on success | §4.7 — the interface tab word is set, so the interface is non-nil even though the data pointer is zero |
| 2 | `v.(*User)` without comma-ok on cache `any` | Panics at runtime if wrong type | §4.8 — assertion checks the tab against `*User`; mismatch with no `ok` triggers panic |
| 3 | `BatchJob{}` assigned to `JobRunner` | Compile error | §4.9 — `Run` is defined on `*BatchJob`, not `BatchJob`; pointer receiver methods don't exist on the value type |
| 4 | Fat interface with 8+ methods | Every test needs an 8-method mock | §4.10 — keep interfaces to 1-3 methods; define in the consumer package |
| 5 | Comparing two interfaces holding different concrete types | `==` returns false even if the values "look the same" | §4.5 — comparison checks both tab and data; different concrete types mean different tabs |

---

## 8. Interview Gold Questions (Top 3)

**Q1: Why can a nil pointer inside an `error` interface cause `err != nil` to be true?**

An interface value is two words: a type descriptor and a data pointer. When you assign a nil `*ValidationError` to an `error`, the type descriptor is set — Go knows the concrete type is `*ValidationError`. Only when **both** words are zero is the interface nil. The fix: always `return nil` as `error` on the success path, never return a typed nil through the interface.

**Q2: How does Go know a struct fulfills an interface without `implements`?**

The compiler checks at the assignment site. When you write `var store UserStore = &PostgresUserStore{}`, it verifies that `*PostgresUserStore` has every method `UserStore` declares — matching names, parameter types, and return types. If anything is missing, you get a compile error right there. This is **structural typing**. The advantage: your Postgres package never imports the interface — the handler package owns it. That keeps dependencies pointing inward.

**Q3: When should you use a type assertion vs a type switch vs `errors.As`?**

Use `v.(*User), ok` when you expect one specific concrete type — like pulling a `*User` from a cache. Use a type switch when you need to branch on several types — like `WriteError` matching `*ValidationError`, `*NotFoundError`, `*APIError`. Use `errors.As` when the error might be **wrapped** with `fmt.Errorf("...: %w", err)` — it walks the wrap chain looking for a match, which a plain type switch can't do.

---

## 9. 30-Second Verbal Answer

"Interfaces in Go are method contracts — if your struct has the right methods, it fulfills the interface automatically. There's no `implements` keyword. Under the hood, an interface value is two words: a type descriptor and a data pointer. That's why a nil pointer inside an interface is not a nil interface — the type word is still set. In practice, you use interfaces to decouple handlers from implementations. Your handler takes `UserStore`, prod passes Postgres, tests pass a mock. Keep them small — one to three methods — and define them in the consumer package, not next to the implementation."

---

> See [[Glossary]] for term definitions.
