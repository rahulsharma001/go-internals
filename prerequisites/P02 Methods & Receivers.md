# P02 Methods & Receivers

> **Prerequisite note** — complete this before starting [[T07 Pointers & Pointer Semantics]] or [[T11 Interface Internals (iface & eface)]].
> Estimated time: ~25 min

---

## 1. Concept

A **method** is just a function with an extra first argument. In Go that first argument is called the **receiver**. It sits in parentheses before the method name. It tells the compiler: "this function belongs to this type."

So instead of `CreateUser(svc, ctx, email)` you write `svc.CreateUser(ctx, email)`. Same thing under the hood. The dot is nicer to read.

---

## 2. Core Insight (TL;DR)

**Your receiver choice decides: does the method work on a copy, or on the real struct?**

- **Value receiver** — Go copies your whole struct (or your whole `Config`, your whole small struct, whatever). If the method changes a field, it changes **only the copy**. The caller does not see it.
- **Pointer receiver** — Go passes the address. The method updates **the same** struct the caller has. Changes stick.

**Second big idea:** the methods you can call on `User` are not the same list as the methods you can call on `*User`. That sounds picky. It matters the second you pass a `User` into something that expects a **`Repository`** or **`UserStore`** interface. Sometimes the value type does not qualify. The pointer type does.

---

## 3. Mental Model (Lock this in)

Think **photocopy vs original document**.

Value receiver: you hand the clerk a photocopy. They scribble on the photocopy. Your original on the desk is untouched.

Pointer receiver: you tell the clerk where your desk is. They walk over and write on the original.

```go
type LineItem struct {
	SKU string
	Qty int
}

type Order struct {
	ID          string
	Paid        bool
	TotalCents  int
	Items       []LineItem
}

func (o Order) CalculateTotal() int {
	// read-only: sum from TotalCents or walk Items — copy is OK for small reads
	return o.TotalCents
}

func (o *Order) MarkPaid() {
	o.Paid = true
}
```

---

## 4. How It Works

### Defining methods

Any **named type** you define in your package can have methods. Structs are the common case. So are tiny wrapper types.

```go
type Config struct {
	HTTPPort int
	DBURL    string
}

func (c Config) Validate() error {
	if c.HTTPPort <= 0 || c.HTTPPort > 65535 {
		return errors.New("bad port")
	}
	if c.DBURL == "" {
		return errors.New("db url required")
	}
	return nil
}
```

`Validate` does not need to mutate `Config`. It only reads fields. A value receiver is fine: `Config` is small, and you are not trying to "write back" into the caller's struct.

```go
type UserID string

func (id UserID) IsEmpty() bool {
	return id == ""
}
```

Same story. Small, read-only checks. Copying a string header is cheap.

### Value receiver vs pointer receiver — the backend default

Most **services** and **repos** you write hold a `*sql.DB`, a logger, an `http.Client`, maybe a `sync.Mutex`. You almost always use a **pointer receiver** for the whole type.

Why?

1. **Mutation** — `MarkPaid`, `UpdateEmail`, `Save` need to change the receiver or something reachable only if you share the real struct.
2. **Size** — copying a fat struct every call is silly.
3. **Consistency** — if `Save` is `func (r *PostgresRepo)`, do not make `FindByID` a value receiver. Pick one style per type.

```go
type UserService struct {
	db     *sql.DB
	logger *slog.Logger
	// ...
}

func (s *UserService) CreateUser(ctx context.Context, email string) (int64, error) {
	// uses s.db, s.logger — always pointer receiver for this type
	// ...
	return 0, nil
}

func (s *UserService) GetUser(ctx context.Context, id int64) (*User, error) {
	// ...
	return nil, nil
}

func (s *UserService) UpdateEmail(ctx context.Context, id int64, email string) error {
	// ...
	return nil
}
```

### HTTP server: why your handler uses `func (srv *Server)`

Your `Server` struct usually holds `*sql.DB`, a router, maybe metrics. Handlers are `func (srv *Server) handleUsers(w, r)` so every request hits **the same** `srv`. With a value receiver, each call would get a **copy** of `Server`. The `*sql.DB` inside would still point at the real DB, but anything you store **on** `Server` itself (rate limits, per-server flags) would update only the copy. Pointer receiver keeps one shared server object.

### When a value receiver is actually nice

Use a value receiver when:

- The type is **small** and **read-only** in practice (`Config.Validate`, `UserID.IsEmpty`).
- You want each call to work on a **snapshot** and you will not write back.

Slice/map **headers** copy; backing stores are shared. If you `append` into a slice **field** and the caller must see the new length, use a pointer receiver so the header updates in place.

### Method sets (plain words)

- `func (u User)` — counts as a method on **`User`**.
- `func (u *User)` — counts as a method on **`*User` only**, not on plain `User`.
- **`*User`** picks up **both** kinds: value-style and pointer-style.

So the pointer type has the longer list. The value type might be "missing" methods when an interface asks for them.

### Interfaces: `Repository` and `PostgresRepo`

An interface is a **list of methods**. Your concrete type **implements** the interface if it has those methods with matching signatures.

```go
type User struct {
	ID    int64
	Email string
}

type Repository interface {
	Save(ctx context.Context, u *User) error
	FindByID(ctx context.Context, id int64) (*User, error)
}

type PostgresRepo struct {
	pool *pgxpool.Pool
}

func (r *PostgresRepo) Save(ctx context.Context, u *User) error {
	// INSERT ...
	return nil
}

func (r *PostgresRepo) FindByID(ctx context.Context, id int64) (*User, error) {
	// SELECT ...
	return nil, nil
}

var _ Repository = (*PostgresRepo)(nil) // compile-time check
```

If every method uses `func (r *PostgresRepo)`, then the **value** `PostgresRepo` does not implement `Repository`. The **pointer** `*PostgresRepo` does. Pass `&repo` (or keep a `*PostgresRepo` field). A compile-time check: `var _ Repository = (*PostgresRepo)(nil)`.

Example of the gotcha:

```go
func (u *User) FullEmail() string {
	if u == nil {
		return ""
	}
	return strings.ToLower(u.Email)
}

type EmailFormatter interface {
	FullEmail() string
}

var _ EmailFormatter = (*User)(nil) // OK

// var _ EmailFormatter = User{} // compile error: value User has no FullEmail
```

The interface only accepts `*User` because `FullEmail` is on `*User`.

### What Go does for you at call sites

If the method is on `*User` but you have a `User` **variable**, `u.FullEmail()` becomes `(&u).FullEmail()` automatically. That helps **calls** only — interfaces still see `User` and `*User` as different shapes.

---

## 5. Key Rules & Behaviors

### Value receiver: copy in, mutations lost

```go
type UserService struct {
	db         *sql.DB
	cacheHits  int
}

func (s UserService) RecordCacheHit() {
	s.cacheHits++
}

func demo(db *sql.DB) {
	svc := UserService{db: db, cacheHits: 0}
	svc.RecordCacheHit()
	// svc.cacheHits still 0 — only the copy inside RecordCacheHit changed
}
```

```
MEMORY TRACE — value receiver, mutation lost (UserService):

Step 1: svc := UserService{db: db, cacheHits: 0}
  stack:
    svc ──→ [ db: ptr to real DB | cacheHits: 0 ]  at addr 0xC000

Step 2: svc.RecordCacheHit() — Go copies the whole UserService into the receiver
  stack:
    caller svc ──→ [ db: same ptr | cacheHits: 0 ]  at addr 0xC000
    receiver s ──→ [ db: same ptr | cacheHits: 1 ]  at addr 0xC010   ◄── only this copy incremented

Step 3: method returns, receiver discarded
  stack:
    svc ──→ [ cacheHits still 0 ]  at addr 0xC000
```

Note: `s.db` inside the method is still the real database pointer. You only "lost" updates to **value fields** on `UserService` itself.

### Pointer receiver: same struct, changes stick

```go
func (o *Order) AddItem(item LineItem) {
	o.Items = append(o.Items, item)
}

func (o *Order) MarkPaid() {
	o.Paid = true
}
```
(`Order` and `LineItem` are the same types from the mental model above — `append` here **needs** `*Order` so the caller sees longer `Items`.)

```
MEMORY TRACE — pointer receiver (Order.MarkPaid):

Step 1: ord := Order{ID: "o-1", Paid: false}
  stack:
    ord ──→ [ ID | Paid: false | Items header... ]  at addr 0xC000

Step 2: ord.MarkPaid() — compiler passes &ord; receiver is *Order pointing at 0xC000
  stack:
    ord ──→ [ Paid: true ]  at addr 0xC000   ◄── updated in place
    receiver *Order ──→ 0xC000

Step 3: caller sees Paid == true
```

### Method set: why `User{}` does not match an interface that needs `*User`

```
MEMORY TRACE — method sets (User vs *User):

  func (u User) IsVerified() bool      → belongs to User
  func (u *User) SetVerified(v bool)  → belongs to *User only

Interface needs SetVerified? Plain User does not qualify. *User does.
(You can still *call* u.SetVerified on a variable — Go turns it into (&u).SetVerified.
That trick does not help interface matching.)
```

### Nil pointer receiver: legal call, dangerous field access

```go
type Cart struct {
	items []LineItem
}

func (c *Cart) ItemCount() int {
	if c == nil {
		return 0
	}
	return len(c.items)
}

var cart *Cart
_ = cart.ItemCount() // OK: ItemCount checks nil before c.items
```

```
MEMORY TRACE — nil receiver:

Step 1: var cart *Cart — nil
Step 2: cart.ItemCount() — receiver *Cart is still nil; if c == nil { return 0 } — no field read → OK

If you started with return len(c.items) with no nil check:
  reading c.items through nil → panic
```

Calling a method with a nil receiver is allowed. **Using** `c.items` (or any field) before `if c == nil` is what blows up.

**Consistency:** if `Save` is `func (r *PostgresRepo)`, make `FindByID` a pointer receiver too. Same for `UserService`, `Server`, any type that holds DB or mutable state.

**Code review one-liner:** pointer when the struct has a DB connection, mutex, or is big; value when it is tiny and read-only. Unsure? Pointer.

---

## 6. Code Examples (Show, Don't Tell)

### `HTTPClient` wrapper

```go
type HTTPClient struct {
	client  *http.Client
	baseURL string
}

func (c *HTTPClient) Get(ctx context.Context, path string) (*http.Response, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseURL+path, nil)
	if err != nil {
		return nil, err
	}
	return c.client.Do(req)
}
```

Pointer receiver: one shared `baseURL` and `client`, no struct copy on every outbound call.

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

```go
package main

import "fmt"

type Order struct {
	ID    int
	Paid  bool
}

func (o Order) TryMarkPaidWrong() {
	o.Paid = true
}

func (o *Order) MarkPaidRight() {
	o.Paid = true
}

func main() {
	a := Order{ID: 1, Paid: false}
	b := &Order{ID: 2, Paid: false}

	a.TryMarkPaidWrong()
	a.MarkPaidRight()
	b.TryMarkPaidWrong()
	b.MarkPaidRight()

	fmt.Println(a.Paid, b.Paid)
}
```

> [!success]- Answer
> `true true`
>
> Wrong methods copy the struct; `MarkPaidRight` uses `*Order`. For `a`, the pointer call fixes `a`. For `b`, the value call updates only a temp; the pointer call fixes the real order.

### Tier 2: Fix the Bug (5 min)

```go
package main

import "fmt"

type BatchWriter struct {
	lines []string
}

func (w BatchWriter) Append(line string) {
	w.lines = append(w.lines, line)
}

func main() {
	var bw BatchWriter
	bw.Append("first")
	bw.Append("second")
	fmt.Println(len(bw.lines))
}
```

> [!success]- Answer
> Prints `0`. Value receiver → `append` updates only the copy's slice header. Fix: `func (w *BatchWriter) Append(...) { w.lines = append(w.lines, line) }` — same bug pattern as an in-memory repo buffer.

---

## 7. Gotchas & Interview Traps

| Trap | Why it bites | Fast fix |
|------|--------------|----------|
| "I mutated in a method but nothing changed" | Value receiver copied your struct | Use `*Type` when mutating fields |
| Value does not implement interface | Methods only on `*T` | Pass `*T`, or change receiver to value if tiny and safe |
| `p.Method()` always copies | Compiler may pass `&p` for `*T` methods | Learn value vs pointer receivers, not just syntax |
| Nil receiver panic | You read fields before `if v == nil` | Guard first, like `ItemCount` on `*Cart` |
| Mixed receivers on same type | Confuses everyone in review | One style per type; services → pointers |

---

## 8. Interview Gold Questions (Top 3)

**1. Value receiver vs pointer receiver?**

Copy vs address. Value: writes do not stick on the caller's struct. Pointer: they do. Services/repos/servers → pointers. Tiny read-only config helpers → values.

**2. Why do people say `T` and `*T` have different method lists?**

Value type gets only `func (T)` methods. Pointer type gets those **plus** `func (*T)` methods. An interface that only exists on `*T` is not satisfied by bare `T` — pass `*User` or use a value receiver on tiny read-only helpers.

**3. Nil receiver — when is it OK?**

OK if the method checks `nil` before field access (`*Cart` item count). Panic if you read `t.Field` first. Common for optional carts, empty trees, lazy loaders.

---

## 9. 30-Second Verbal Answer

Methods hang off a receiver. Value = copy; field writes do not stick. Pointer = shared struct; writes stick. `User` vs `*User` carry different method lists, so interfaces may need the pointer. Default pointers for DB/mutex/big service structs; values for tiny read-only things. Nil `*T` is fine if you guard before touching fields.

---

> See [[Glossary]] for term definitions.
