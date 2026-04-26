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
type Order struct {
	ID     string
	Paid   bool
	TotalCents int
}

func (o Order) CalculateTotal() int {
	// read-only math on a copy is fine for small structs
	return o.TotalCents
}

func (o *Order) MarkPaid() {
	o.Paid = true // writes the real Order
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

### HTTP server: why your handler uses a pointer to `Server`

Typical pattern:

```go
type Server struct {
	db     *sql.DB
	router chi.Router
}

func (srv *Server) handleUsers(w http.ResponseWriter, r *http.Request) {
	// srv.db must be THE shared DB, not a copy of Server with wrong fields
}
```

If `handleUsers` used a value receiver, every request would get a **copy** of `Server`. You would still have the same `*sql.DB` pointer **inside** the copy — so reads through the DB might work — but any field you set on `Server` itself (rate limiter state, middleware counters, whatever) would update only the copy. In real code you want one shared `Server` state. Pointer receiver.

**Rule of thumb:** struct holds `*sql.DB`, mutex, client handles, or is "the app" — use `*YourType`.

### When a value receiver is actually nice

Use a value receiver when:

- The type is **small** and **read-only** in practice (`Config.Validate`, `UserID.IsEmpty`).
- You want each call to work on a **snapshot** and you will not write back.

You still need to know what "copy" means for slices and maps inside the struct (header copied, backing store shared). If your method does `append` on a slice field and you need the new length visible to the caller, you need a pointer receiver so you update the slice header in place.

### Method sets (without the textbook voice)

Attach this picture:

- Methods declared as `func (u User)` belong to **`User`**.
- Methods declared as `func (u *User)` belong to **`\*User`** only — not to plain **`User`**.
- **`\*User`** gets **both**: all `User` methods **and** all `*User` methods.

So the pointer type is the "full" side. The plain value type might be missing methods.

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

If **every** method on `Repository` uses pointer receiver `*PostgresRepo`, then **`PostgresRepo` (value)** does not implement `Repository`. **`\*PostgresRepo`** does. So function parameters should be `Repository`, and you pass `&repo` or a field that is already a pointer.

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

If the method needs `*User` but you have a **variable** of type `User` (not a temporary), you can still write `u.FullEmail()`. The compiler turns it into `(&u).FullEmail()`. You did not type `&`. Go inserts it.

That does **not** magically give `User` new methods for interfaces. It only helps **calls**. Interface matching still uses the real method lists.

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
type Order struct {
	ID     string
	Paid   bool
	Items  []LineItem
}

type LineItem struct {
	SKU string
	Qty int
}

func (o *Order) AddItem(item LineItem) {
	o.Items = append(o.Items, item)
}

func (o *Order) CalculateTotal() int {
	total := 0
	for _, it := range o.Items {
		total += priceTable[it.SKU] * it.Qty // pretend priceTable exists
	}
	return total
}

func (o *Order) MarkPaid() {
	o.Paid = true
}
```

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

You declared:
  func (u User) IsVerified() bool
  func (u *User) SetVerified(v bool)

Callable on a value u (type User):
  u.IsVerified()     — OK
  u.SetVerified(true) — compiler rewrites to (&u).SetVerified only for this call; still *User method

For interface matching:
  "Does plain User implement an interface that only lists SetVerified?"
  User's own list does NOT include SetVerified (that lives on *User).
  So User does NOT implement. *User does.
```

### Nil pointer receiver: legal call, dangerous field access

```go
type OrderList struct {
	head *OrderNode
}

type OrderNode struct {
	order *Order
	next  *OrderNode
}

func (l *OrderList) Len() int {
	if l == nil {
		return 0
	}
	// walk l.head ...
	return 0
}

func main() {
	var list *OrderList
	fmt.Println(list.Len()) // prints 0, no panic
}
```

```
MEMORY TRACE — nil receiver:

Step 1: var list *OrderList — zero value nil
  stack:
    list ──→ nil

Step 2: list.Len() — receiver *OrderList is a copy of list, still nil
  inside Len: if l == nil { return 0 } — OK, no fields read

If you wrote return l.head.order.ID without the nil check first:
  loading l.head through nil pointer → panic
```

Calling a method with a nil receiver is allowed. **Using** `l.someField` before checking `l == nil` is what blows up.

### Consistency

If any method on `PostgresRepo` mutates state or needs `*PostgresRepo`, use pointer receivers for **all** methods on that type. Same for `UserService`, `Server`, etc.

### Decision card (what you say in a code review)

Use **pointer receiver** when:

- The struct holds `*sql.DB`, pools, loggers, HTTP clients, mutexes.
- Any method mutates the struct or slice/map fields where the caller must see updates.
- The struct is large.

Use **value receiver** when:

- The type is tiny and read-only (`Config.Validate`, IDs, small value objects).
- You explicitly want a snapshot and no write-back.

Unsure? Pointer receiver. It is the boring default for service-layer structs.

---

## 6. Code Examples (Show, Don't Tell)

### `HTTPClient` wrapper

```go
type HTTPClient struct {
	client *http.Client
	baseURL string
}

func NewHTTPClient(base string) *HTTPClient {
	return &HTTPClient{
		client:  http.DefaultClient,
		baseURL: strings.TrimRight(base, "/"),
	}
}

func (c *HTTPClient) Get(ctx context.Context, path string) (*http.Response, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseURL+path, nil)
	if err != nil {
		return nil, err
	}
	return c.client.Do(req)
}

func (c *HTTPClient) Do(req *http.Request) (*http.Response, error) {
	return c.client.Do(req)
}
```

Pointer receiver: you share one configured client, no copying structs with pointers inside.

### `Repository` again — compile-time guard

```go
var _ Repository = (*PostgresRepo)(nil)
```

This line fails at compile time if `PostgresRepo` stops implementing `Repository`. The `nil` pointer is fine; you are not calling methods here.

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
> `a.TryMarkPaidWrong()` copies `a`; only the copy gets `Paid = true`. `a.MarkPaidRight()` rewrites to `(&a).MarkPaidRight()`, so the real `a` is updated → `a.Paid` is true.
>
> `b.TryMarkPaidWrong()` still uses a **value** receiver: Go copies the struct that `b` points at, sets `Paid` on the copy, discards it — `*b` stays false. `b.MarkPaidRight()` uses a pointer receiver on the live struct → `b.Paid` becomes true.

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
> Prints `0` today because `Append` uses a value receiver. `append` may update only the **copy's** slice header. The caller's `bw.lines` never grows.
>
> Fix: `func (w *BatchWriter) Append(line string) { w.lines = append(w.lines, line) }`
>
> Same class of bug as a repo method that appends to an internal buffer with a value receiver.

---

## 7. Gotchas & Interview Traps

| Trap | Why it bites | Fast fix |
|------|--------------|----------|
| "I mutated in a method but nothing changed" | Value receiver copied your struct | Use `*Type` when mutating fields |
| Value does not implement interface | Methods only on `*T` | Pass `*T`, or change receiver to value if tiny and safe |
| `p.Method()` always copies | Compiler may pass `&p` for `*T` methods | Learn value vs pointer receivers, not just syntax |
| Nil receiver panic | You read fields before `if v == nil` | Guard first, like `Len()` on `*OrderList` |
| Mixed receivers on same type | Confuses everyone in review | One style per type; services → pointers |

---

## 8. Interview Gold Questions (Top 3)

**1. Value receiver vs pointer receiver?**

Value receiver copies the receiver value. Field writes do not affect the caller's struct. Pointer receiver shares the address; writes persist. For backend code, structs that hold DB handles, loggers, or mutable state use pointer receivers. Small read-only things (`Config.Validate`) can stay value receivers.

**2. Why do people say `T` and `*T` have different "method sets"?**

Methods on `T` attach to values of type `T`. Methods on `*T` attach to pointers. Only `*T` gets both groups. So an interface that requires a `*T` method is not satisfied by a bare `T`. That is why `var _ Formatter = (*User)(nil)` works but `User{}` might not.

**3. Nil receiver — when is it OK?**

You can call `(*T).Method` with a nil `*T` if `Method` handles `nil` before touching fields. If you access `t.Field` when `t` is nil, you panic. Useful for empty lists, optional wrappers, ORM-style helpers.

---

## 9. 30-Second Verbal Answer

A method is a function with a receiver. Value receiver means Go copies your struct; writes to fields do not stick. Pointer means you pass the address; writes stick. Types and pointer-to-types carry different lists of methods; interfaces care about that, so sometimes only `*User` implements your interface. Backend rule: pointer receivers for services, repos, servers, anything with a DB or mutex; value receivers for small read-only snapshots. Nil pointer receivers are allowed if you check `nil` before touching fields.

---

> See [[Glossary]] for term definitions.
