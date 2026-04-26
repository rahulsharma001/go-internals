# P01 Structs & Struct Memory Layout

> **Prerequisite note** — complete this before starting [[T07 Pointers & Pointer Semantics]], [[T08 Map Internals]], or [[T11 Interface Internals (iface & eface)]].
> Estimated time: ~25 min

---

## 1. Concept

A **struct** is your way of giving a name to a fixed set of fields. You decide the shape up front. Go doesn't have classes. You model users, orders, config, and API payloads with structs. You hang methods on those types when you need behavior.

Think of it like a form at the DMV. The boxes are printed on the sheet. You don't get new boxes mid-flight. You fill `Name`, `Email`, `Age` — same layout every time.

---

## 2. Core Insight (TL;DR)

**Structs are values.** When you assign or pass a struct, Go often **copies the whole thing** unless you use a **pointer**. If you mutate inside a function that took a copy, the caller won't see it.

**Field order changes size** sometimes. The compiler may slip in **padding** (unused bytes) so each field sits on an address the CPU likes. Two structs with the "same" fields in different order can have different `unsafe.Sizeof` results.

**Embedding** pulls another type's fields up to the outer struct for easy access. It is **not** inheritance. You're composing shapes, not building a class tree.

---

## 3. Mental Model (Lock this in)

Picture a row of lockers in order: first `Name`, then `Email`, then `Age`. The compiler might leave an empty locker between two real ones so the big locker (`int64`, say) starts on a "round" address. Reorder the lockers and the row can get shorter or longer even though you're still storing the same ideas.

**Tiny field before a big one:** a 1-byte `uint8` then an `int64` → the compiler leaves a gap so the `int64` starts on an 8-byte boundary (typical on 64-bit).

**Error-driven: you "promoted" a copy**

```go
type User struct {
    Name    string
    Email   string
    Age     int
    IsAdmin bool
}

func promoteToAdmin(u User) { u.IsAdmin = true }

func main() {
    u := User{Name: "Sam", Email: "sam@co.com", Age: 28, IsAdmin: false}
    promoteToAdmin(u)
    // u.IsAdmin is still false — photocopy problem
}
```

```
MEMORY TRACE (value parameter — copy):

  Caller: u at 0xC000  →  IsAdmin: false
  promoteToAdmin gets a COPY at 0xD000; only 0xD000 flips to true
  When the func returns, 0xD000 is discarded. 0xC000 never changed.
```

Pass `&u` and take `*User` if everyone should edit the same `User`.

---

## 4. How It Works

### 4.1 Declaration forms

```go
type User struct {
    Name    string `json:"name" db:"full_name"`
    Email   string `json:"email,omitempty" db:"email"`
    Age     int    `json:"age" db:"age_years"`
    IsAdmin bool   `json:"is_admin"`
}

row := struct {
    StatusCode int
    Body       []byte
}{StatusCode: 200, Body: []byte(`ok`)}

u := User{Name: "Ada", Email: "ada@co.com", Age: 36, IsAdmin: true}
v := User{"Grace", "grace@co.com", 31, false} // positional — order must match

pu := &User{Name: "Lin", Email: "lin@co.com", Age: 40, IsAdmin: false}
fmt.Println(pu.Name) // (*pu).Name
```

Named types are reusable; anonymous structs are one-off shapes. A pointer is an address; the compiler adds `*` for field access.

### 4.2 Zero values

New struct fields start at their **zero value**: `""`, `0`, `false`, `nil` for pointers/slices/maps.

```go
type Item struct{ SKU string; Qty int }

type Order struct {
    ID        int64
    Total     int64
    Items     []Item
    CreatedAt time.Time
}

var o Order
// o.ID == 0, o.Total == 0, o.Items == nil, o.CreatedAt is zero time
```

Handlers often `var u User` or `var o Order`, then fill from JSON or SQL.

### 4.3 Field access, nesting, embedding

**Nested** — inner struct lives **inline** inside the outer struct.

```go
type Address struct{ City string }

type Customer struct {
    Name string
    Home Address
}

c := Customer{Name: "Sam", Home: Address{City: "Austin"}}
fmt.Println(c.Home.City)
```

**Embedding** — anonymous field; inner fields promote to the outer type.

```go
type AuditLog struct {
    UserID    int64
    Action    string
    Timestamp time.Time
}

type APIResponse struct {
    AuditLog
    StatusCode int
    Body       []byte
    Headers    map[string]string
}

resp := APIResponse{
    AuditLog: AuditLog{UserID: 42, Action: "GET /orders", Timestamp: time.Now()},
    StatusCode: 200,
    Body:       []byte(`{"ok":true}`),
    Headers:    map[string]string{"Content-Type": "application/json"},
}
fmt.Println(resp.UserID, resp.AuditLog.UserID) // same field, two spellings
```

One flat layout in memory — not subclassing.

### 4.4 Struct tags

Those backtick strings on `User` in §4.1 are **tags**. Normal code ignores them. **`encoding/json`**, SQL helpers, and validators read them with **reflection**. JSON uses `name` on the wire; the DB column can be `full_name`. `omitempty` skips zero values in JSON output. Only **exported** fields (capital letter) participate in `json` and most scanners.

### 4.5 Memory layout, alignment, padding

Fields sit in **declaration order**. The compiler adds **padding** so each field starts at a valid **alignment** for its type. Putting a 1-byte `bool` before an `int64` often wastes 7 bytes.

```go
type Config struct {
    Debug    bool  // 1 byte
    MaxConns int64 // often needs 8-byte alignment
}

type ConfigTidy struct {
    MaxConns int64
    Debug    bool
}
```

```
MEMORY TRACE (padding — Config vs reordered):

  Config:     [ Debug 1 ][ 7 bytes pad ][ MaxConns 8 ]
  ConfigTidy: [ MaxConns 8 ][ Debug 1 ][ maybe tail pad for arrays ]
```

When it matters (huge `[]Config`, hot paths), measure `unsafe.Sizeof` on the arch you ship.

## 5. Key Rules & Behaviors

### Structs are value types (assignment copies)

```go
u := User{Name: "A", Email: "a@x.com", Age: 20, IsAdmin: false}
v := u
v.Age = 99 // u.Age still 20
```

```
MEMORY TRACE (assignment):

  u at 0xC000, v at 0xC040 — two User blobs; only v's Age changes
```

### Zero value is usable

```go
type OrderTotals struct{ Sum int64; Count int }

func addLine(t OrderTotals, amount int64) OrderTotals {
    t.Sum += amount
    t.Count++
    return t
}

var acc OrderTotals
acc = addLine(acc, 1000)
```

Small totals often use "pass value, return updated struct."

### Comparison rules

`==` works only if **every field type is comparable**. Slices, maps, and functions break that.

```go
type UserKey struct{ ID int64; Email string }

type OrderLine struct {
    ID    int64
    Total int64
    Items []Item // slice — whole struct is not comparable with ==
}

var a, b UserKey
_ = a == b
// var x, y OrderLine; _ = x == y // compile error
```

Compare orders by ID, or use `slices.Equal` on `Items`, or write your own helper.

### Field ordering affects memory size

Reorder `bool` / `int16` / `int64` in a `Config`-style struct and print `unsafe.Sizeof` — same data, smaller struct when big fields come first. Same lesson as §4.5.

### Embedding is not inheritance

Promoted methods still take the **embedded** value as the receiver (same `AuditLog` inside `APIResponse` in §4.3). No superclass, no vtable — just names lifted for convenience.

### Unexported fields stay in the package

```go
package users

type User struct {
    Name      string
    emailHash string // other packages can't read or set this
}

func NewUser(name, hash string) User { return User{Name: name, emailHash: hash} }
```

## 6. Code Examples (Show, Don't Tell)

### POST /users — JSON body into a struct

`User` is defined once in §4.1 (HTTP + SQL tags on the same type).

```go
func createUser(w http.ResponseWriter, r *http.Request) {
    var u User
    if err := json.NewDecoder(r.Body).Decode(&u); err != nil {
        http.Error(w, "bad json", http.StatusBadRequest)
        return
    }
    // svc.CreateUser(r.Context(), u)
}
```

`Decode` needs `&u`. Hand the filled `u` to your service by value or `&u` depending on whether it mutates.

### Database row → struct

```go
func loadUser(ctx context.Context, db *sql.DB, id int64) (User, error) {
    var u User
    row := db.QueryRowContext(ctx,
        `SELECT full_name, email, age, is_admin FROM users WHERE id = ?`, id)
    err := row.Scan(&u.Name, &u.Email, &u.Age, &u.IsAdmin)
    return u, err
}
```

### Config file at startup

```go
type Config struct {
    Port     int    `json:"port"`
    DBHost   string `json:"db_host"`
    MaxConns int    `json:"max_conns"`
    Debug    bool   `json:"debug"`
}

func LoadConfig(path string) (Config, error) {
    var c Config
    b, err := os.ReadFile(path)
    if err != nil {
        return c, err
    }
    return c, json.Unmarshal(b, &c)
}
```

### Service: when to use `*` on `User`

```go
func SendWelcomeEmail(u User) { /* read-only; copy is fine */ }

func SetAdmin(u *User, admin bool) { u.IsAdmin = admin }
```

```
MEMORY TRACE (pointer — mutation sticks):

  Caller holds u at 0xE000. SetAdmin(&u, true) passes 0xE000.
  Writes go through that address; caller sees IsAdmin == true after return.
```

### JSON response envelope (`OrderDTO`)

```go
type OrderDTO struct {
    ID        int64     `json:"id"`
    Total     int64     `json:"total"`
    CreatedAt time.Time `json:"created_at"`
}

func writeOrder(w http.ResponseWriter, dto OrderDTO) {
    body, _ := json.Marshal(struct {
        Data OrderDTO `json:"data"`
    }{Data: dto})
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    w.Write(body)
}
```

Use `json:"-"` on fields you want in Go (`StatusCode`, `Headers` on an `APIResponse`) but not in the JSON body.

### `Order` copy shares `Items` backing array

```go
a := Order{ID: 1, Items: []Item{{SKU: "A", Qty: 1}}}
b := a
b.Items[0].Qty = 5
// a.Items[0].Qty is 5 too
```

```
MEMORY TRACE (struct copy, slice header):

  a.Items points at backing array 0x9000
  b := a copies the Order; b.Items still points 0x9000
  Editing b.Items[0] edits that shared array — a sees it
```

Deep copy line items when you need independence (`slices.Clone`, `append` into a new slice, etc.).

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

```go
package main

import "fmt"

type User struct {
    Name string
    Age  int
}

func bumpAge(u User) {
    u.Age++
}

func main() {
    u := User{Name: "Kim", Age: 30}
    bumpAge(u)
    fmt.Println(u.Age)
}
```

> [!success]- Answer
> Prints `30`.
>
> `bumpAge` receives a **copy** of `u`. The `++` runs on the copy. Kim's struct in `main` never changes.

### Tier 2: Fix the Bug (5 min)

```go
package main

import "fmt"

type Config struct {
    Port   int
    Debug  bool
    DBHost string
}

func enableDebug(c Config) {
    c.Debug = true
}

func main() {
    var cfg Config
    enableDebug(cfg)
    fmt.Println(cfg.Debug)
}
```

> [!success]- Answer
> Prints `false` as written. `enableDebug` flips a copy.
>
> Fix: pass a pointer.
>
> ```go
> func enableDebug(c *Config) { c.Debug = true }
>
> func main() {
>     var cfg Config
>     enableDebug(&cfg)
>     fmt.Println(cfg.Debug) // true
> }
> ```
>
> **Interview line:** Caller-visible mutation needs `*T`, not `T`.

## 7. Gotchas & Interview Traps

| Trap | Why it bites | Fast fix |
|------|--------------|----------|
| Big struct by value in a hot path | Full copy every call | Profile; try `*T` |
| Java-style inheritance expectations | Embedding only promotes names | Compose; add wrappers |
| `==` or slice field / `b := a` on `Order` | Slices aren't comparable; `Items` shares backing array | Compare by ID / `slices.Equal`; clone `Items` if needed |
| JSON missing / padding shocks | Unexported fields, bad tags, field order | Export + tags; `unsafe.Sizeof` on target arch |

## 8. Interview Gold Questions (Top 3)

**1) Classes?** No — named types, methods, composition; embedding isn't inheritance; capitalization exports across packages.

**2) Pass by value?** Full copy unless you pass `*T`; mutate caller state via pointer or return value.

**3) Same fields, different size?** Order changes padding and array stride — measure `unsafe.Sizeof` on target hardware.

## 9. 30-Second Verbal Answer

Structs model users, orders, config, responses as fixed field layouts. They're **values**: copy on assign/call unless you use a pointer for one shared record. Padding depends on field order. `==` needs every field comparable. Tags wire `json` and DB mappers. Embedding is composition with promoted names, not subclassing.

> See [[Glossary]] for term definitions.
