# P05 Interfaces Basics

> **Prerequisite note** — complete this before starting [[T09 Error Handling Patterns]], [[T11 Interface Internals (iface & eface)]], or [[T19 Context Package Internals]].
> Estimated time: ~25 min

---

## 1. Concept

An **interface** is a contract. You write down a list of methods. Any struct that has those exact methods automatically fulfills the contract — you never write `implements` in Go.

Why does this matter? Because your HTTP handler can depend on the contract ("something that can find a user"), not on a specific database. Production passes Postgres. Tests pass a fake. The handler doesn't know and doesn't care.

---

## 2. Core Insight (TL;DR)

**If your struct has the right methods, it fits the interface. That's it.** No `implements` keyword. No registration. The compiler checks the methods automatically at the point where you assign the struct to the interface variable.

This means your handler can depend on a contract like "something that can find a user by ID" — and production passes Postgres, tests pass a fake. The handler never changes.

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

### The mistake that teaches you

Here's a bug that trips up nearly every Go developer at least once:

```go
func Validate(email string) error {
    var err *ValidationError
    if email == "" {
        err = &ValidationError{Field: "email", Reason: "required"}
    }
    return err
}

func main() {
    err := Validate("sam@co.com")
    fmt.Println(err == nil) // You'd expect: true
}
```

**What you'd expect:** `email` is valid, so `err` stays nil, so `err == nil` should be `true`.

**What actually happens:** It prints `false`. The caller thinks validation failed even though nothing went wrong.

**Why?** When you write `return err`, Go wraps the `*ValidationError` into the `error` interface. Even though the pointer is nil, Go remembers the *type* of the pointer. An interface with a type stamped on it is not nil — even if the actual data is empty. Think of a labeled envelope that happens to be empty. You'd still say "there's an envelope here" because the label is on it.

**The fix:** Return `nil` directly on the success path, never a typed nil variable:

```go
func Validate(email string) error {
    if email == "" {
        return &ValidationError{Field: "email", Reason: "required"}
    }
    return nil
}
```

You'll learn exactly *why* this happens (the two-word structure of an interface value) in §4.5 below.

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

```
What Alert sees (the interface envelope):

  n (Notifier interface):
  ┌────────────────────────────────────────────────┐
  │ label:    *EmailNotifier                       │
  │ contents: → EmailNotifier{From:"ops@acme.co"}  │
  └────────────────────────────────────────────────┘

  Alert calls n.Notify() → Go reads the label → finds *EmailNotifier's Notify → runs it
```

If you pass a `*SlackNotifier` instead, the envelope has a different label and different contents, but `Alert` doesn't care. It just calls `n.Notify()` and Go dispatches to the right method. That's the whole point.

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

### 4.5 What an interface value actually holds (and why nil is tricky)

When you store a concrete value in an interface variable, Go keeps track of **two things**:

1. **A label** — which concrete type is inside (e.g., "this is a `*EmailNotifier`")
2. **The contents** — a pointer to the actual data

Think of it like a **labeled envelope**. The label on the outside tells you what kind of thing is inside. The contents are the actual thing.

```go
var n Notifier = &EmailNotifier{From: "ops@acme.co"}
```

```
n (interface value — an envelope):
  ┌───────────────────────────────────────────┐
  │ label:    *EmailNotifier                  │
  │ contents: ──> EmailNotifier{From:"ops@.."}│
  └───────────────────────────────────────────┘
```

When you call `n.Notify(ctx, msg)`, Go reads the label to find out it's a `*EmailNotifier`, looks up its `Notify` method, and calls it.

**Now here's the tricky part: when is an interface nil?** Before reading on, think about this: if you have a nil pointer of type `*EmailNotifier` and assign it to a `Notifier` variable, is the interface nil or not?

An interface is nil **only when both the label and contents are empty** — a blank envelope with nothing written on it and nothing inside.

```go
var n Notifier                          // no label, no contents → nil
var n2 Notifier = (*EmailNotifier)(nil) // label says *EmailNotifier, contents empty → NOT nil!
```

```
n:  envelope with no label, nothing inside       → n == nil is TRUE

n2: envelope labeled "*EmailNotifier", but empty  → n2 == nil is FALSE
         ↑ the label is there, so Go says "this envelope has something"
```

`n2` has a label stamped on it. Go considers it non-nil even though there's nothing inside. This is the **typed-nil trap**. It bites you most often when returning errors (see §4.7 below).

---

### 4.6 The `error` interface and custom error types

Go's standard library defines `error` as an interface with just one method:

```go
type error interface {
	Error() string
}
```

That's it. Any struct that has an `Error() string` method is automatically a valid `error`. This is the same implicit satisfaction you learned in 4.2 — no `implements` keyword.

You use this to create custom error types that carry structured information beyond just a message string:

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

Both `*NotFoundError` and `*ValidationError` have `Error() string`, so both are valid `error` values.

```
Compiler's checklist for the error interface:
  ✓ Does *NotFoundError have Error() string?    → YES → it's a valid error
  ✓ Does *ValidationError have Error() string?  → YES → it's a valid error
```

Why does this matter? Because your handler can return these as `error`, and your middleware can figure out the right HTTP status code by checking which concrete type is inside.

---

### 4.6b Type switches — checking which concrete type is inside an interface

Now that you have custom error types, you need a way to ask: "what concrete type is actually inside this `error` interface?" That's what a **type switch** does.

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

`switch e := err.(type)` asks Go: "look at the label on this interface envelope — what type is inside?" Each `case` branch matches a specific type. Inside that branch, `e` has the concrete type, so you can read fields like `e.Field` or `e.Resource`.

Here's what happens step by step when `err` holds a `*ValidationError{Field: "email", Reason: "required"}`:

```
Step 1: err is an interface envelope
  label:    *ValidationError
  contents: → ValidationError{Field:"email", Reason:"required"}

Step 2: type switch reads the label
  case *ValidationError → label matches! → e is now *ValidationError

Step 3: e.Error() returns "invalid email: required"
  → http.Error(w, "invalid email: required", 400)
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

When `strict` is false, `err` is a nil `*ValidationError`. Before reading the trace below, predict: what will the caller see when it checks `if err != nil`?

```
Step 1: strict == false → err is a nil *ValidationError

Step 2: return err — Go wraps *ValidationError into the error interface envelope
  Go builds the envelope:
    label:    *ValidationError   ← this is NOT empty!
    contents: (nil pointer)

Step 3: Caller does `if err != nil`
  Go checks: is the envelope completely blank? No — the label says *ValidationError.
  → interface is non-nil → condition is TRUE
  The caller thinks LoadConfig failed, even though nothing went wrong.

The fix — return nil directly:
  Go builds the envelope:
    label:    (none)
    contents: (none)
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

  v (any interface — an envelope):
    label:    *User
    contents: → User{ID:"u1"}

Step 2: u, ok := v.(*User)
  Go checks: does v's label say *User? → YES
  u = the *User pointer, ok = true

Step 3 (wrong type): cache["session:abc"] returns v = &Session{...}
  Go checks: does v's label say *User? → NO (it says *Session)
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

Why? Because `Run` is defined on `*BatchJob`, not `BatchJob`. When you write `var r JobRunner = BatchJob{}`, here's what the compiler does:

```
Step 1: Go checks — does BatchJob have all the methods JobRunner needs?
  JobRunner needs: Run(ctx context.Context) error
  BatchJob's method list: (empty — Run is defined on *BatchJob, not BatchJob)

Step 2: Run is missing from BatchJob → COMPILE ERROR
  "BatchJob does not implement JobRunner (Run method has pointer receiver)"

Step 3 (the fix): var r JobRunner = &BatchJob{}
  Go checks — does *BatchJob have Run(ctx context.Context) error? → YES
  Assignment allowed.
```

The rule is simple: if you define a method on `*T`, only `*T` gets that method. `T` by itself doesn't.

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

### 5.2 An interface is nil only when both the label and contents are empty

An interface variable holds two things: a label (which concrete type is inside) and a pointer to the contents. Only when both are empty — a blank envelope — is the interface nil.

```go
var e error               // no label, no contents → nil
var p *ValidationError    // nil *ValidationError
var e2 error = p          // label = *ValidationError, contents = empty → NOT nil
```

```
  e:  [ label: (none) | contents: (none) ]             → e == nil is true
  e2: [ label: *ValidationError | contents: (none) ]   → e2 == nil is FALSE
                                   ↑ label is set, so the interface is non-nil
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
Step 1: NewGetUserHandler(store) — store is a UserStore interface envelope
  store:
    label:    *MockUserStore
    contents: → the MockUserStore with its Users map

Step 2: store.FindByID(ctx, "1")
  Go reads store's label → finds FindByID for *MockUserStore → calls it
  MockUserStore looks up "1" in its Users map → returns the User

Step 3: json.NewEncoder(w).Encode(u)
  Writes {"ID":"1","Email":"a@b.co"} to the ResponseWriter
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the behavior (2 min)

Does this code compile? If not, which line fails and why?

```go
type Logger interface {
	Log(msg string)
}

type FileLogger struct {
	Path string
}

func (f *FileLogger) Log(msg string) {
	fmt.Println(msg)
}

func main() {
	var a Logger = &FileLogger{Path: "/var/log/app.log"} // line A
	var b Logger = FileLogger{Path: "/var/log/app.log"}   // line B
	a.Log("hello")
	b.Log("hello")
}
```

> [!success]- Answer
> **Line B fails to compile.** The `Log` method is defined on `*FileLogger` (pointer receiver), not on `FileLogger` (the value). So `*FileLogger` has the method `Logger` needs, but `FileLogger` by itself doesn't.
>
> Line A works because `&FileLogger{}` is a `*FileLogger`.
> Line B fails because `FileLogger{}` is a `FileLogger` — no pointer, no `Log` method.
>
> Fix: either use `&FileLogger{}` on line B, or define `Log` with a value receiver `func (f FileLogger) Log(msg string)`.

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
| 1 | Return nil `*ValidationError` through `error` | Caller sees `err != nil` even on success | §4.7 — the interface label is set (it says `*ValidationError`), so the envelope is non-nil even though the contents are empty |
| 2 | `v.(*User)` without comma-ok on cache `any` | Panics at runtime if wrong type | §4.8 — assertion checks the label against `*User`; mismatch with no `ok` triggers panic |
| 3 | `BatchJob{}` assigned to `JobRunner` | Compile error | §4.9 — `Run` is defined on `*BatchJob`, not `BatchJob`; pointer receiver methods don't exist on the value type |
| 4 | Fat interface with 8+ methods | Every test needs an 8-method mock | §4.10 — keep interfaces to 1-3 methods; define in the consumer package |
| 5 | Comparing two interfaces holding different concrete types | `==` returns false even if the values "look the same" | §4.5 — comparison checks both label and contents; different concrete types mean different labels |

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
