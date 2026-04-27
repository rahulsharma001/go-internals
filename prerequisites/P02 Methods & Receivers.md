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

### 4.1 Defining Methods — What the Compiler Actually Does

Any **named type** you define in your package can have methods. Under the hood, a method is a regular function where the receiver becomes the first parameter.

```go
package main

import "fmt"

type Config struct {
	HTTPPort int
	DBURL    string
}

func (c Config) Validate() error {
	if c.HTTPPort <= 0 || c.HTTPPort > 65535 {
		return fmt.Errorf("bad port: %d", c.HTTPPort)
	}
	if c.DBURL == "" {
		return fmt.Errorf("db url required")
	}
	return nil
}

func main() {
	cfg := Config{HTTPPort: 8080, DBURL: "postgres://localhost/mydb"}
	err := cfg.Validate()
	fmt.Println("error:", err) // error: <nil>

	bad := Config{HTTPPort: -1}
	err = bad.Validate()
	fmt.Println("error:", err) // error: bad port: -1
}
```

```
What the compiler does with cfg.Validate():

  Step 1: cfg := Config{HTTPPort: 8080, DBURL: "postgres://localhost/mydb"}
    stack 0xA0: [ HTTPPort: 8080 | DBURL: "postgres://localhost/mydb" ]

  Step 2: cfg.Validate() is rewritten by the compiler as:
    Config.Validate(cfg)    ← regular function, cfg is the first argument

  Step 3: Since Validate has a VALUE receiver, Go COPIES cfg:
    original at 0xA0: [ 8080 | "postgres://..." ]
    copy at 0xB0:     [ 8080 | "postgres://..." ]   ← Validate works on this copy
    
  Step 4: Validate reads c.HTTPPort (from the copy) → 8080 → valid
    No mutation → no problem using a copy

  KEY: the method call is just syntactic sugar for passing the struct as argument #1
```

> **In plain English:** When you write `cfg.Validate()`, Go doesn't do anything magical — it just rewrites it as `Validate(cfg)` with the receiver as the first argument. Value receiver means it copies the struct in; pointer receiver means it passes the address.

### 4.2 Value Receiver vs Pointer Receiver — Traced Through Memory

This is the most important distinction in Go methods. Here's what actually happens at the memory level:

```go
package main

import "fmt"

type UserService struct {
	db        string // simplified — normally *sql.DB
	cacheHits int
}

func (s UserService) RecordCacheHitBroken() {
	s.cacheHits++
	fmt.Printf("  inside broken: cacheHits=%d (at %p — COPY)\n", s.cacheHits, &s)
}

func (s *UserService) RecordCacheHit() {
	s.cacheHits++
	fmt.Printf("  inside fixed:  cacheHits=%d (at %p — ORIGINAL)\n", s.cacheHits, s)
}

func main() {
	svc := UserService{db: "postgres://localhost", cacheHits: 0}
	fmt.Printf("before: cacheHits=%d (at %p)\n", svc.cacheHits, &svc)

	svc.RecordCacheHitBroken()
	fmt.Printf("after broken: cacheHits=%d\n", svc.cacheHits) // still 0!

	svc.RecordCacheHit()
	fmt.Printf("after fixed:  cacheHits=%d\n", svc.cacheHits) // 1
}
// Output:
// before: cacheHits=0 (at 0xC0000A2000)
// inside broken: cacheHits=1 (at 0xC0000A2030 — COPY)
// after broken: cacheHits=0
// inside fixed:  cacheHits=1 (at 0xC0000A2000 — ORIGINAL)
// after fixed:  cacheHits=1
```

```
svc.RecordCacheHitBroken() — VALUE receiver:

  Step 1: Go copies entire UserService into new stack slot
    original at 0x2000: [ db: "postgres://..." | cacheHits: 0 ]
    copy at 0x2030:     [ db: "postgres://..." | cacheHits: 0 ]   ← method works here
                                                 ↑ note: different address!
  Step 2: s.cacheHits++ → copy at 0x2030 becomes cacheHits: 1
  Step 3: method returns → copy is discarded
  Step 4: original at 0x2000 still has cacheHits: 0

svc.RecordCacheHit() — POINTER receiver:

  Step 1: Compiler rewrites as (*UserService).RecordCacheHit(&svc)
    Go copies 8 bytes (the address 0x2000) into the method's receiver parameter
    
  Step 2: s.cacheHits++ → follows pointer to 0x2000 → writes cacheHits: 1
    original at 0x2000: [ db: "postgres://..." | cacheHits: 1 ]   ← changed!
    
  Step 3: caller reads svc.cacheHits → 1 ✓
```

> **In plain English:** A value receiver hands the method a photocopy of the entire form. They can scribble all over it — your original stays clean. A pointer receiver hands them the actual address of the form — what they write stays permanently.

### 4.3 The Automatic &v Trick — Why Calls Work But Interfaces Don't

If a method is defined on `*User` but you have a `User` variable, Go auto-inserts `&` at the call site. But this trick **does not work** for interface satisfaction.

```go
package main

import "fmt"

type User struct {
	Name     string
	Verified bool
}

func (u *User) SetVerified() {
	u.Verified = true
}

func main() {
	u := User{Name: "rahul"}
	u.SetVerified() // works! compiler rewrites as (&u).SetVerified()
	fmt.Println(u.Verified) // true
}
```

```
Step 1: u := User{Name: "rahul", Verified: false}
  stack 0xA0: [ Name: "rahul" | Verified: false ]

Step 2: u.SetVerified()
  Compiler sees: SetVerified is on *User, but u is User (not *User)
  Auto-rewrite: (&u).SetVerified()
  Method receives pointer 0xA0
  u.Verified = true → writes at 0xA0 → Verified becomes true

Step 3: fmt.Println(u.Verified) → reads 0xA0 → true ✓

WHY this doesn't help with interfaces:

  type Verifier interface { SetVerified() }

  var v Verifier = u  // COMPILE ERROR!
  
  When Go stores u (a User value) into an interface, it COPIES u.
  The copy doesn't have a stable address.
  Go can't auto-insert & on a copy that lives inside the interface box.
  
  var v Verifier = &u  // OK! *User satisfies Verifier
```

> **In plain English:** If your friend asks "where do you live?", you can give them your address (pointer auto-insert works for direct calls). But if you mail your photo (copy into interface), the recipient can't visit you — they only have a picture, not an address.

### 4.4 Method Sets — The Rule That Breaks Interface Wiring

This is where receiver choice matters beyond "does mutation stick." It determines which interfaces your type can satisfy.

```go
package main

import (
	"context"
	"fmt"
)

type User struct {
	ID    int64
	Email string
}

type Repository interface {
	Save(ctx context.Context, u *User) error
	FindByID(ctx context.Context, id int64) (*User, error)
}

type PostgresRepo struct {
	dsn string
}

func (r *PostgresRepo) Save(ctx context.Context, u *User) error {
	fmt.Printf("saving user %d to %s\n", u.ID, r.dsn)
	return nil
}

func (r *PostgresRepo) FindByID(ctx context.Context, id int64) (*User, error) {
	fmt.Printf("finding user %d in %s\n", id, r.dsn)
	return &User{ID: id, Email: "found@test.com"}, nil
}

func main() {
	repo := PostgresRepo{dsn: "postgres://localhost/mydb"}

	// var _ Repository = repo   // COMPILE ERROR: PostgresRepo doesn't implement Repository
	var _ Repository = &repo     // OK: *PostgresRepo implements Repository

	var r Repository = &repo
	r.Save(context.Background(), &User{ID: 1, Email: "test@test.com"})
}
```

```
Method set of PostgresRepo (value):
  { }   ← EMPTY! Both Save and FindByID are on *PostgresRepo

Method set of *PostgresRepo (pointer):
  { Save(...), FindByID(...) }   ← includes ALL methods (value + pointer receivers)

WHY PostgresRepo{} fails the Repository interface:

  Step 1: var _ Repository = repo
  Step 2: Go needs to store repo inside the interface → copies it
  Step 3: Repository requires Save(*User) → Save is on *PostgresRepo
  Step 4: The copy inside the interface doesn't have a stable address
  Step 5: Go can't silently take &copy because:
          a) It would create a hidden heap allocation
          b) Mutations through Save would modify the copy, not the caller's repo
  Step 6: COMPILE ERROR

  ┌──────────────────────────────────────┐
  │  Interface: Repository               │
  │  Requires: { Save, FindByID }        │
  ├──────────────────────────────────────┤
  │  PostgresRepo{}  → method set: {}    │  ← MISSING both! ✗
  │  &PostgresRepo{} → method set: {S,F} │  ← has both!    ✓
  └──────────────────────────────────────┘

Compile-time assertion pattern (catches this before runtime):
  var _ Repository = (*PostgresRepo)(nil)
```

> **In plain English:** Think of a bouncer checking your ID. `*PostgresRepo` carries a real driver's license — the bouncer (interface) lets it in. `PostgresRepo` carries a photocopy of the license — the bouncer says "this isn't valid" and rejects it. The difference matters even if the picture looks the same.

### 4.5 Real Backend Scenario: Handler → Service → Repository

Here's what method dispatch looks like when your HTTP handler calls a service, which calls a repository — all using pointer receivers:

```go
package main

import "fmt"

type User struct {
	ID    int64
	Name  string
	Email string
}

type UserRepo struct {
	store map[int64]*User
}

func (r *UserRepo) Save(u *User) {
	r.store[u.ID] = u
	fmt.Printf("  repo.Save: stored user %d at %p\n", u.ID, u)
}

type UserService struct {
	repo *UserRepo
}

func (s *UserService) CreateUser(name, email string) *User {
	u := &User{ID: 1, Name: name, Email: email}
	fmt.Printf("  service.Create: user at %p\n", u)
	s.repo.Save(u)
	return u
}

func main() {
	repo := &UserRepo{store: make(map[int64]*User)}
	svc := &UserService{repo: repo}

	fmt.Printf("repo at %p, svc at %p\n", repo, svc)
	user := svc.CreateUser("rahul", "r@test.com")
	fmt.Printf("handler got user at %p: %+v\n", user, *user)
}
// Output:
// repo at 0xC000010028, svc at 0xC000010038
// service.Create: user at 0xC000014040
// repo.Save: stored user 1 at 0xC000014040
// handler got user at 0xC000014040: {ID:1 Name:rahul Email:r@test.com}
```

```
Step 1: repo := &UserRepo{...}
  heap 0x10028: [ store: map[...] ]
  main's stack: repo = 0x10028

Step 2: svc := &UserService{repo: repo}
  heap 0x10038: [ repo: 0x10028 ]    ← svc.repo points at the same UserRepo
  main's stack: svc = 0x10038

Step 3: svc.CreateUser("rahul", "r@test.com")
  Compiler rewrites: (*UserService).CreateUser(svc, "rahul", "r@test.com")
  CreateUser's receiver s = 0x10038 (pointer to svc)
  
  Inside CreateUser:
    u := &User{...} → heap 0x14040: [ ID:1 | Name:"rahul" | Email:"r@test.com" ]
    
  Step 3a: s.repo.Save(u)
    s.repo → follows 0x10038 → gets repo pointer 0x10028
    (*UserRepo).Save(0x10028, u)
    Save's receiver r = 0x10028
    r.store[u.ID] = u → map now stores pointer 0x14040

Step 4: returns u (0x14040) to main
  main, svc, repo, and the map entry ALL reference the same User at 0x14040

POINTER CHAIN:
  main → svc(0x10038) → svc.repo(0x10028) → repo.store[1](0x14040) = User
  main → user(0x14040) = same User
  
  One User struct. Multiple pointers. Every layer mutates through the same address.
```

> **In plain English:** Think of a hospital patient chart. The front desk creates it, the doctor updates it, the lab reads it. They're all reading and writing the same physical chart — not passing photocopies around. That's pointer receivers in a handler → service → repo chain.

---

## 5. Key Rules & Behaviors

### Rule 1: Value Receiver — Copy In, Mutations Lost

The method works on a complete copy of the struct. Any field changes die when the method returns.

**WHY (§4.2):** From §4.2, the compiler passes the struct as the first argument by value — Go copies every byte into a new stack slot. The method increments the copy's field. When the stack frame dies, the copy dies with it.

```go
type BatchWriter struct {
	lines []string
}

func (w BatchWriter) AppendBroken(line string) {
	w.lines = append(w.lines, line) // appends to copy's slice header
}
```

```
Step 1: bw := BatchWriter{lines: nil}
  stack 0xA0: [ lines: {ptr: nil, len: 0, cap: 0} ]

Step 2: bw.AppendBroken("hello")
  Copy at 0xB0: [ lines: {ptr: nil, len: 0, cap: 0} ]   ← copy of the header
  append creates backing array → copy's header: {ptr: 0xD0, len: 1, cap: 1}
  Method returns → copy at 0xB0 is gone

Step 3: bw.lines at 0xA0 still {ptr: nil, len: 0, cap: 0}
  The new backing array at 0xD0 is now unreachable → GC will free it

FIX: func (w *BatchWriter) Append(line string) { w.lines = append(...) }
  Now append updates the ORIGINAL header at 0xA0
```

> **In plain English:** You gave the clerk a photocopy of your notebook's table of contents. They added a page to their photocopy. Your notebook still has the old table of contents.

### Rule 2: Pointer Receiver — Changes Stick Through the Address

The method receives a pointer to the original struct. Field writes go through that address and are visible to the caller.

**WHY (§4.2, §4.5):** From §4.2, pointer receiver passes 8 bytes (the address). The method writes to `s.field` which the compiler turns into `*s + offset(field)` — a write to the same memory the caller holds.

```go
func (o *Order) AddItem(item LineItem) {
	o.Items = append(o.Items, item)
}

func (o *Order) MarkPaid() {
	o.Paid = true
}
```

```
Step 1: ord := Order{ID: "o-1", Paid: false, Items: nil}
  stack 0xA0: [ ID:"o-1" | Paid:false | Items:{nil,0,0} ]

Step 2: ord.MarkPaid() → compiler passes &ord (0xA0)
  Method writes: *(0xA0 + offset(Paid)) = true
  stack 0xA0: [ ID:"o-1" | Paid:true | Items:{nil,0,0} ]   ← changed!

Step 3: ord.AddItem(LineItem{SKU:"X", Qty:2}) → compiler passes &ord (0xA0)
  append creates backing array, updates Items header at 0xA0
  stack 0xA0: [ ID:"o-1" | Paid:true | Items:{ptr:0xD0, len:1, cap:1} ]
  Caller sees both Paid=true and the new item ✓
```

> **In plain English:** You told the clerk "my desk is room 3A." They walked over and wrote on your actual document. When you go back to your desk, the changes are there.

### Rule 3: Method Sets — The Interface Gate

`T` can only call methods with value receivers. `*T` can call methods with both value and pointer receivers. This determines interface satisfaction.

**WHY (§4.3, §4.4):** From §4.3, Go auto-inserts `&` for direct calls but NOT for interface matching. From §4.4, the interface stores a copy of `T`, which doesn't have a stable address — Go can't safely create a pointer to it.

```go
type Notifier interface {
	Notify(msg string)
}

type EmailNotifier struct { addr string }
func (n *EmailNotifier) Notify(msg string) { fmt.Println("emailing", n.addr, msg) }

// var _ Notifier = EmailNotifier{}    // COMPILE ERROR
var _ Notifier = &EmailNotifier{}      // OK
```

```
Method set lookup:

  EmailNotifier  (value)  → { }                ← Notify is *EmailNotifier only
  *EmailNotifier (pointer) → { Notify(string) } ← includes pointer receiver methods

  Interface Notifier requires: { Notify(string) }
  
  EmailNotifier{}  → {} vs {Notify} → MISSING → compile error
  &EmailNotifier{} → {Notify} vs {Notify} → MATCH → OK
```

> **In plain English:** The bouncer checks your method set list. `*EmailNotifier` has all the stamps. `EmailNotifier` is missing the pointer-receiver stamps. No entry.

### Rule 4: Nil Receiver — Legal Call, Dangerous Field Access

You can call a method on a nil pointer. The method runs. But if it tries to read a field without checking nil first, it panics.

**WHY (§4.2, §4.4 from T07):** The method receives `nil` (address 0x0) as its receiver. The call itself is fine — it's just a function call. But reading `c.items` means "read memory at 0x0 + offset" which hits unmapped memory → SIGSEGV → panic.

```go
type Cart struct {
	items []string
}

func (c *Cart) ItemCount() int {
	if c == nil {
		return 0 // safe: checked before field access
	}
	return len(c.items)
}

func (c *Cart) FirstItemUnsafe() string {
	return c.items[0] // PANIC if c is nil — reads through nil pointer
}

func main() {
	var cart *Cart // nil
	fmt.Println(cart.ItemCount())      // 0 — safe
	// fmt.Println(cart.FirstItemUnsafe()) // PANIC
}
```

```
cart.ItemCount() with nil receiver:

  Step 1: cart = nil (0x0)
  Step 2: Go calls (*Cart).ItemCount(nil)
    receiver c = 0x0
  Step 3: if c == nil → true → return 0
    No field access → no crash ✓

cart.FirstItemUnsafe() with nil receiver:

  Step 1: cart = nil (0x0)
  Step 2: Go calls (*Cart).FirstItemUnsafe(nil)
    receiver c = 0x0
  Step 3: c.items → reads memory at 0x0 + offset(items) → SIGSEGV → panic!
```

> **In plain English:** Calling a nil-receiver method is like phoning an empty office — the phone rings, someone picks up. But if they try to open a filing cabinet that doesn't exist (field access), they crash.

### Rule 5: Consistency — One Receiver Style Per Type

If `Save` is `func (r *PostgresRepo)`, make `FindByID` a pointer receiver too. Mixing confuses code reviewers and creates subtle bugs where some methods see the real struct and others see a copy.

**WHY (§4.4):** From §4.4, interface satisfaction depends on the method set. If you mix receivers, `PostgresRepo` might implement some interfaces but not others depending on which methods are pointer vs value. Consistency eliminates this entire class of bugs.

```go
// WRONG: mixed receivers
type BadRepo struct {
	pool  string
	cache map[string]string
}
func (r BadRepo) FindByID(id string) string  { return r.cache[id] }  // value
func (r *BadRepo) Save(id, val string)       { r.cache[id] = val }   // pointer

// PROBLEM: BadRepo{} satisfies an interface needing FindByID
// but NOT an interface needing Save. Confusing.

// RIGHT: all pointer receivers
type GoodRepo struct {
	pool  string
	cache map[string]string
}
func (r *GoodRepo) FindByID(id string) string { return r.cache[id] }
func (r *GoodRepo) Save(id, val string)       { r.cache[id] = val }
```

```
Mixed receivers create confusing method sets:

  BadRepo  → { FindByID }       ← has value receiver method only
  *BadRepo → { FindByID, Save } ← has both

  Consistent pointer receivers:
  GoodRepo  → { }                ← no methods on value
  *GoodRepo → { FindByID, Save } ← everything is here, clean

  Rule of thumb:
    Struct has *sql.DB, sync.Mutex, or mutable state? → ALL pointer receivers
    Struct is tiny, immutable, read-only (like UserID)? → ALL value receivers
    Never mix.
```

> **In plain English:** If one doctor writes on the real patient chart and another doctor writes on a photocopy, the chart becomes inconsistent. Pick one style — "everyone writes on the real chart" (pointer) or "everyone gets a photocopy" (value) — and stick with it.

---

## 6. Code Examples (Show, Don't Tell)

### Example 1: Method Call — What the Compiler Actually Generates

The simplest possible method call, traced through memory to show the compiler rewrite.

```go
package main

import "fmt"

type Counter struct {
	n int
}

func (c *Counter) Inc() {
	c.n++
}

func main() {
	ctr := Counter{n: 0}
	fmt.Printf("before: n=%d, ctr at %p\n", ctr.n, &ctr)
	ctr.Inc()
	fmt.Printf("after:  n=%d, ctr at %p\n", ctr.n, &ctr)
}
// Output:
// before: n=0, ctr at 0xC0000A6058
// after:  n=1, ctr at 0xC0000A6058
```

```
Step 1: ctr := Counter{n: 0}
  stack 0x6058: [ n: 0 ]

Step 2: ctr.Inc()
  Compiler rewrites: (*Counter).Inc(&ctr)
  Inc receives pointer 0x6058 (8 bytes)
  c.n++ → writes at 0x6058 → n becomes 1

Step 3: main reads ctr.n → 0x6058 → 1 ✓
```

### Example 2: HTTPClient Wrapper — Real Service Pattern

A common pattern: wrapping `*http.Client` with a base URL and shared config.

```go
package main

import (
	"context"
	"fmt"
	"net/http"
)

type HTTPClient struct {
	client  *http.Client
	baseURL string
}

func NewHTTPClient(baseURL string) *HTTPClient {
	return &HTTPClient{
		client:  &http.Client{},
		baseURL: baseURL,
	}
}

func (c *HTTPClient) Get(ctx context.Context, path string) (*http.Response, error) {
	url := c.baseURL + path
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	return c.client.Do(req)
}

func main() {
	client := NewHTTPClient("https://api.example.com")
	fmt.Printf("client at %p, inner http.Client at %p\n", client, client.client)
}
```

```
Step 1: NewHTTPClient("https://api.example.com")
  Compiler detects: return &HTTPClient{...} → escapes to heap
  heap 0xC000010040: [ client: 0xC000012000 | baseURL: "https://api.example.com" ]
                        │
                        └──→ heap: *http.Client at 0xC000012000

Step 2: client.Get(ctx, "/users")
  Compiler rewrites: (*HTTPClient).Get(client, ctx, "/users")
  Method receives pointer 0xC000010040
  Reads c.baseURL and c.client through that pointer
  
  WHY pointer receiver: 
  - HTTPClient is ~32 bytes (pointer + string header) — not huge, but shared
  - More importantly: every handler shares ONE HTTPClient instance
  - Value receiver would copy the struct every call — wasteful and wrong if
    you ever add state (rate limiter, circuit breaker)
```

### Example 3: Value Receiver for Small Read-Only Types

When the type is small and you never mutate it, value receivers are cleaner.

```go
package main

import "fmt"

type UserID string

func (id UserID) IsEmpty() bool {
	return id == ""
}

func (id UserID) String() string {
	if id == "" {
		return "<empty>"
	}
	return string(id)
}

func main() {
	var empty UserID
	known := UserID("usr_abc123")

	fmt.Println(empty.IsEmpty())  // true
	fmt.Println(known.IsEmpty())  // false
	fmt.Println(known.String())   // usr_abc123
}
```

```
known.IsEmpty():

  Step 1: known = UserID("usr_abc123")
    stack: [ string header: ptr + len = 16 bytes ]

  Step 2: IsEmpty() copies the 16-byte string header
    copy: [ same ptr | same len ]
    Compares copy == "" → false

  Step 3: Original untouched. Copy is tiny (16 bytes). No pointer needed.

  WHY value receiver is fine here:
  - UserID is 16 bytes (string header) — tiny
  - Methods are read-only — no mutation
  - No shared state — each call is independent
  - Copying 16 bytes is cheaper than pointer indirection + potential GC overhead
```

### Example 4: The Interface Wiring Bug — Traced End to End

The most common compile error when wiring services together:

```go
package main

import "fmt"

type Saver interface {
	Save(data string) error
}

type FileStore struct {
	path string
}

func (f *FileStore) Save(data string) error {
	fmt.Printf("saving '%s' to %s\n", data, f.path)
	return nil
}

func process(s Saver) {
	s.Save("important data")
}

func main() {
	store := FileStore{path: "/tmp/data.txt"}

	// process(store)  // COMPILE ERROR: FileStore does not implement Saver
	process(&store)    // OK: *FileStore implements Saver
}
```

```
WHY process(store) fails:

  Step 1: store is FileStore (value type)
  Step 2: process expects Saver interface
  Step 3: Go checks: does FileStore's method set include Save(string) error?
    Method set of FileStore: { }   ← Save is on *FileStore only!
    MISSING → compile error

  Step 4: process(&store) — &store is *FileStore
    Method set of *FileStore: { Save(string) error }
    MATCH → OK

  The fix is always the same: pass &store or store the pointer in a field.
```

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
> For `a`: TryMarkPaidWrong copies a, sets copy's Paid = true, copy dies → a.Paid still false. MarkPaidRight takes &a, sets real a.Paid = true → a.Paid is true.
> For `b`: TryMarkPaidWrong copies *b into method, sets copy's Paid = true, copy dies → b.Paid still false. MarkPaidRight takes b (already a pointer), sets b.Paid = true → b.Paid is true.

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
> Prints `0`. Value receiver → `append` updates only the copy's slice header. The original's header still says len: 0. Fix: `func (w *BatchWriter) Append(...) { w.lines = append(w.lines, line) }` — pointer receiver ensures the original slice header gets the new length and pointer.

---

## 7. Gotchas & Interview Traps

| Trap | What Happens | Because (§4 link) | Fix |
|------|-------------|-------------------|-----|
| "I mutated in a method but nothing changed" | Value receiver copied the struct; mutation died with the copy | §4.2 — value receiver copies entire struct into new stack slot. Field writes go to the copy, not the original | Use `*Type` receiver when mutating fields |
| Value type doesn't implement interface | Compile error: missing method | §4.4 — method set of `T` only includes value receiver methods. Pointer receiver methods are on `*T` only. Interface checks method set, not individual calls | Pass `*T` instead, or change receiver to value if the type is small and safe |
| `v.Method()` works but `var i Interface = v` doesn't | Auto-insert of `&` only works for direct calls, not interface assignment | §4.3 — compiler rewrites `v.Method()` as `(&v).Method()` for convenience, but can't do the same for interface storage because the copy inside the interface has no stable address | Always pass `&v` into interfaces when methods use pointer receivers |
| Nil receiver panic | Method called on nil pointer, tried to read a field | §4.5 (Rule 4) — nil pointer is address 0x0. Method call is fine, but field access reads 0x0 + offset → unmapped memory → SIGSEGV | Guard with `if r == nil { return ... }` before any field access |
| Mixed receivers on same type | Some methods see original, others see copy; interfaces partially satisfied | §4.4 + Rule 5 — method set of `T` includes only value methods, `*T` includes both. Mixed receivers create confusing partial interface matches | One style per type: pointer for service/repo types, value for tiny read-only types |

### Gotcha Deep Dive: Slice Append in Value Receiver

This is the most common beginner trap in Go services — an in-memory buffer that never grows:

```go
type InMemoryRepo struct {
	users []User
}

func (r InMemoryRepo) SaveBroken(u User) {
	r.users = append(r.users, u)
}
```

```
Step 1: repo := InMemoryRepo{users: nil}
  stack 0xA0: [ users: {ptr: nil, len: 0, cap: 0} ]   ← 24-byte slice header

Step 2: repo.SaveBroken(User{...})
  Go copies the 24-byte slice header into the method:
  original at 0xA0: [ users: {nil, 0, 0} ]
  copy at 0xB0:     [ users: {nil, 0, 0} ]

Step 3: append(r.users, u) inside the method
  append sees len=0, cap=0 → allocates new backing array on heap
  copy's header at 0xB0: [ users: {ptr: 0xD0, len: 1, cap: 1} ]
  heap 0xD0: [ User{...} ]

Step 4: method returns → copy at 0xB0 is gone
  original at 0xA0: [ users: {nil, 0, 0} ]   ← STILL EMPTY!
  heap 0xD0 is now unreachable → will be garbage collected

FIX: func (r *InMemoryRepo) Save(u User)
  Now append updates the ORIGINAL header at 0xA0
```

> **In plain English:** You told the clerk "here's a copy of my table of contents." They added a new entry to their copy and put it in the shredder when they left. Your table of contents never changed.

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
