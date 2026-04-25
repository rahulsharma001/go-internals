# T12: Interface Design Principles — Exercises

> Practice for [[T12 Interface Design Principles]]. Do the tiers in order or jump to what you need.

---

## Tier 2 — Refactor: one fat `DatabaseService` → three consumer-defined interfaces

### Starting point (intentionally bad)

You inherit this **single** interface with ten methods. Every handler depends on all of them even when it only needs one concern.

```go
// database/service.go (before)
package database

import "context"

type DatabaseService interface {
	GetUserByID(ctx context.Context, id int64) (User, error)
	GetUserByEmail(ctx context.Context, email string) (User, error)
	ListUsers(ctx context.Context, limit, offset int) ([]User, error)
	CreateUser(ctx context.Context, u User) (int64, error)
	UpdateUser(ctx context.Context, u User) error
	ArchiveUser(ctx context.Context, id int64) error
	DeleteUserHard(ctx context.Context, id int64) error
	BulkImportUsers(ctx context.Context, batch []User) error
	ExportUserAudit(ctx context.Context, id int64) ([]byte, error)
	HealthCheckDB(ctx context.Context) error
}
```

**Your task**

1. In the **HTTP handlers** (or a `users` application package that consumes storage), define **three** small interfaces (names are suggested, adjust to taste):

   - `UserReader` — only methods needed to **read** user data in routes that do not mutate.
   - `UserWriter` — only methods needed to **create/update** (and related write paths you group logically).
   - `UserDeleter` — only methods needed for **delete / archive** flows.

2. Ensure **no** handler’s constructor parameter type is the full 10-method interface unless that handler truly needs every method (it should not).

3. Keep **one** concrete `*Service` (or `*Repository`) type in the `database` package that implements all three small interfaces (structural typing: same type, many interfaces).

4. **Bonus:** List which methods you put in `Reader` vs `Writer` vs `Deleter` and **why** (role boundaries, not “alphabetical”).

**Checklist**

- [ ] Each interface has **1–3** methods, not 10.
- [ ] Interfaces live **where they are used** (consumer packages), unless your team standard is otherwise.
- [ ] The concrete `database` type **does not** need to `declare` it “implements” anything.

---

## Tier 3 — Pluggable storage: `Storage` + swap implementations

**Goal:** Use [[T12 Interface Design Principles]] to build a small **pluggable** persistence layer: same business logic, different backends.

### Part A — Define the `Storage` interface

```go
// storage/storage.go
package storage

import "context"

type Storage interface {
	Get(ctx context.Context, key string) ([]byte, error)
	Set(ctx context.Context, key string, value []byte) error
	Delete(ctx context.Context, key string) error
}
```

- Keep it **only** as big as the app needs (add `Close() error` if you want—justify it).

### Part B — Implement `MemoryStorage`

- In-memory `map` guarded by a `sync.RWMutex` (or `sync.Map` if you prefer).
- `Get` returns a **not found** error (define `var ErrNotFound = errors.New("not found")` or use `fs.ErrNotExist` pattern for consistency in your app).

### Part C — Implement `FileStorage`

- Store keys as file paths under a **root directory** (sanitize keys: no `..`, no absolute paths).
- `Set` writes bytes; `Get` reads; `Delete` removes the file.
- Create parent dirs as needed on `Set`.

### Part D — Constructor injection

```go
// app/app.go (sketch)
package app

import "context"

type Greeter struct {
	store Storage
}

func NewGreeter(s Storage) *Greeter {
	return &Greeter{store: s}
}

func (g *Greeter) SaveGreeting(ctx context.Context, name string) error {
	return g.store.Set(ctx, "greeting:"+name, []byte("Hello, "+name))
}
```

**Wire in `main`:**

- Build `NewGreeter(NewMemoryStorage())` in one run.
- Build `NewGreeter(NewFileStorage("/tmp/t12-store"))` in another—**no** changes to `Greeter`.

### Part E — Demonstrate swapping

- Write a **tiny** test table or `main` that runs the same operations against **both** `MemoryStorage` and `FileStorage` (e.g. `Set` → `Get` → `Delete` → `Get` expect not found).
- **Bonus:** subtests `t.Run("memory", ...)` and `t.Run("file", ...)` sharing a helper `runStorageTests(t, store)`.

---

## Self-check (Tier 2 + 3)

- Can you explain **in one sentence** why `Greeter` should **not** take `*MemoryStorage` as a concrete type? (Hint: [[T12 Interface Design Principles]] — testability and swapping.)
- If you add `ListKeys`, do you add it to `Storage` for everyone, or split a new `Lister` role? When would you choose each?

**Related:** [[T12 Interface Design Principles]] — revision: `../revision/T12 Interface Design Principles - Revision.md`, visuals: `../visuals/`.
