# P01 Structs & Struct Memory Layout

> **Prerequisite note** — complete this before starting [[T07 Pointers & Pointer Semantics]], [[T08 Map Internals]], or [[T11 Interface Internals (iface & eface)]].
> Estimated time: ~25 min

---

## 1. Concept

A **struct** is your way of giving a name to a fixed set of fields. You decide the shape up front. Go doesn't have classes. You model things like users, orders, and config with structs. Then you hang methods on those types if you need behavior.

Think of it like a form at the DMV. The boxes are printed on the sheet. You don't get new boxes mid-flight. You fill `Name`, `Email`, `Age` — same layout every time.

---

## 2. Core Insight (TL;DR)

**Structs are values.** When you assign or pass a struct, Go often **copies the whole thing** unless you use a **pointer**. If you mutate inside a function that took a copy, the caller won't see it.

**Field order changes size** sometimes. The compiler may slip in **padding** (unused bytes) so each field sits on an address the CPU likes. Two structs with the "same" fields in different order can have different `unsafe.Sizeof` results.

**Embedding** pulls another type's fields up to the outer struct for easy access. It is **not** inheritance. You're composing shapes, not building a class tree.

---

## 3. Mental Model (Lock this in)

Picture a row of lockers in order: first `Name`, then `Email`, then `Age`. The compiler might leave an empty locker between two real ones so the big locker (`int64`, say) starts on a "round" address. Reorder the lockers and the row can get shorter or longer even though you're still storing the same ideas.

**ASCII: why a tiny field before a big one wastes space**

```go
type User struct {
    Age   uint8 // 1 byte
    Score int64 // 8 bytes — wants to start on an 8-byte boundary
}
```

```
Source order:     [ Age | Score ]
Memory (typical): [ Age ][ 7 bytes unused ][ Score takes 8 bytes ]
```

**Error-driven example: you "updated" a copy**

```go
type User struct {
    Name  string
    Email string
    Age   int
    IsAdmin bool
}

func promoteToAdmin(u User) {
    u.IsAdmin = true
}

func main() {
    u := User{Name: "Sam", Email: "sam@co.com", Age: 28, IsAdmin: false}
    promoteToAdmin(u)
    // u.IsAdmin is still false — you changed a photocopy, not Sam's row in your sheet
}
```

```
MEMORY TRACE (value parameter — copy):

  Caller: u at 0xC000  →  IsAdmin: false
  promoteToAdmin gets a COPY at 0xD000
  Inside the func: only 0xD000 flips to true
  When the func returns, 0xD000 is thrown away. 0xC000 never changed.
```

Pass `&u` and take `*User` in the function if everyone should edit the same `User`.

---

## 4. How It Works

### 4.1 Declaration forms

```go
type User struct {
    Name    string
    Email   string
    Age     int
    IsAdmin bool
}

// One-off shape (handy in tests or handlers)
row := struct {
    StatusCode int
    Body       []byte
}{StatusCode: 200, Body: []byte(`ok`)}

u := User{Name: "Ada", Email: "ada@co.com", Age: 36, IsAdmin: true}
v := User{"Grace", "grace@co.com", 31, false} // positional — order must match the type

pu := &User{Name: "Lin", Email: "lin@co.com", Age: 40, IsAdmin: false}
fmt.Println(pu.Name) // compiler turns this into (*pu).Name
```

Named types are reusable. Anonymous structs are "this shape, right here only." A pointer to a struct is just an address; `pu.Name` still feels like dot access because the compiler adds the star for you.

### 4.2 Zero values

Declare a struct without setting fields and every field is its **zero value**: `""` for strings, `0` for numbers, `false` for bools, `nil` for pointers, slices, maps.

```go
type Order struct {
    ID        int64
    Total     int64
    Items     []Item
    CreatedAt time.Time
}

var o Order
// o.ID == 0, o.Total == 0, o.Items == nil, o.CreatedAt is the zero time
```

That's safe to pass around. You're not reading garbage memory. For a handler, you often start with an empty `User` or `Order`, then fill it from JSON or a SQL row.

### 4.3 Field access, nesting, embedding

**Nested struct** — one field's type is another struct. The inner struct lives **inline** inside the outer one (not automatically a pointer).

```go
type Address struct {
    City string
}

type User struct {
    Name    string
    Home    Address
}

u := User{Name: "Sam", Home: Address{City: "Austin"}}
fmt.Println(u.Home.City) // "Austin"
```

**Embedding** — anonymous field. The inner type's fields and methods can be used as if they lived on the outer struct.

```go
type AuditLog struct {
    UserID    int64
    Action    string
    Timestamp time.Time
}

type APIResponse struct {
    AuditLog          // embedded — no extra field name
    StatusCode int
    Body       []byte
    Headers    map[string]string
}

resp := APIResponse{
    AuditLog:   AuditLog{UserID: 42, Action: "GET /orders", Timestamp: time.Now()},
    StatusCode: 200,
    Body:       []byte(`{"ok":true}`),
    Headers:    map[string]string{"Content-Type": "application/json"},
}
fmt.Println(resp.UserID)           // promoted — same as resp.AuditLog.UserID
fmt.Println(resp.AuditLog.UserID)  // explicit path, same bits
```

Embedding is great for cross-cutting stuff (audit metadata, tracing IDs). It's still one flat memory layout: the `AuditLog` fields sit inside `APIResponse` at fixed offsets. You're not "subclassing."

### 4.4 Struct tags

Tags are little strings after a field. Normal Go code ignores them. **Reflection** reads them — `encoding/json`, many SQL scanners, validators.

```go
type User struct {
    Name    string `json:"name" db:"full_name"`
    Email   string `json:"email,omitempty" db:"email"`
    Age     int    `json:"age" db:"age_years"`
    IsAdmin bool   `json:"is_admin"`
}
```

Wire name `name` in JSON, column `full_name` in the DB, same Go field. `omitempty` skips the field in JSON output when it's the zero value. Export fields with a **capital** first letter or `json` won't see them.

### 4.5 Memory layout, alignment, padding

Fields land in **declaration order** in memory. The compiler inserts padding so each field starts at an address that's valid for that field's type (alignment). Misordering small types before big ones can balloon size.

```go
type Config struct {
    Debug   bool   // 1 byte
    MaxConns int64 // often wants 8-byte alignment
}

type ConfigTidy struct {
    MaxConns int64
    Debug    bool
    // struct may still get tail padding if you make arrays of ConfigTidy
}
```

```
MEMORY TRACE (padding — Config vs reordered):

  Config:        [ Debug 1 byte ][ 7 bytes padding ][ MaxConns 8 bytes ]
  ConfigTidy:    [ MaxConns 8 bytes ][ Debug 1 byte ][ maybe tail padding ]
```

You don't need to obsess on every struct. When you care (hot paths, huge slices of structs), measure with `unsafe.Sizeof` on the platform you ship.

---

## 5. Key Rules & Behaviors

### Structs are value types (assignment copies)

```go
u := User{Name: "A", Email: "a@x.com", Age: 20, IsAdmin: false}
v := u
v.Age = 99
// u.Age is still 20
```

```
MEMORY TRACE (assignment):

  u at 0xC000, v at 0xC040 — two separate User blobs with the same starting text
  Changing v.Age only touches 0xC040
```

### Zero value is usable

```go
type OrderTotals struct {
    Sum   int64
    Count int
}

func addLine(t OrderTotals, amount int64) OrderTotals {
    t.Sum += amount
    t.Count++
    return t
}

var acc OrderTotals
acc = addLine(acc, 1000)
```

`acc` starts real and all zeros. You can pass it in and assign the returned struct. Pattern: small aggregates updated by return values instead of pointers.

### Comparison rules

`==` and `!=` work on structs **only if every field type is comparable**. Slices, maps, and functions break that.

```go
type UserKey struct {
    ID    int64
    Email string
}

type Order struct {
    ID    int64
    Total int64
    Items []Item // slice — makes Order non-comparable
}

var a, b UserKey
_ = a == b
// var x, y Order; _ = x == y // compile error
```

If you need "are these orders the same?" with slice fields, compare fields yourself or use something like `slices.Equal` on `Items`.

### Field ordering affects memory size

```go
import "unsafe"

type ConfigLoose struct {
    Debug    bool
    Port     int16
    MaxConns int64
}

type ConfigTight struct {
    MaxConns int64
    Port     int16
    Debug    bool
}

func main() {
    println(unsafe.Sizeof(ConfigLoose{})) // often larger
    println(unsafe.Sizeof(ConfigTight{})) // often smaller — same info, tighter packing
}
```

Same ingredients, different shelf order, different box size.

### Embedding is not inheritance

```go
type AuditLog struct {
    UserID    int64
    Action    string
    Timestamp time.Time
}

func (a AuditLog) Summary() string {
    return fmt.Sprintf("user %d %s", a.UserID, a.Action)
}

type ExportJob struct {
    AuditLog
    Bucket string
}

job := ExportJob{
    AuditLog: AuditLog{UserID: 1, Action: "export", Timestamp: time.Now()},
    Bucket:   "backups",
}
fmt.Println(job.Summary()) // promoted — runs on the embedded AuditLog value
```

Promoted methods still use the embedded value as the receiver unless you define a method on the outer type. No hidden vtables. Compose explicit types.

### Unexported fields stay in the package

```go
package users

type User struct {
    Name     string
    emailHash string // lowercase — not visible outside `users`
}

func NewUser(name, hash string) User {
    return User{Name: name, emailHash: hash}
}
```

Another package can read `Name`. It cannot touch `emailHash`. That's how you hide implementation details while still using a struct.

---

## 6. Code Examples (Show, Don't Tell)

### POST /users — JSON into a struct

```go
type User struct {
    Name    string `json:"name"`
    Email   string `json:"email"`
    Age     int    `json:"age"`
    IsAdmin bool   `json:"is_admin"`
}

func createUser(w http.ResponseWriter, r *http.Request) {
    var u User
    if err := json.NewDecoder(r.Body).Decode(&u); err != nil {
        http.Error(w, "bad json", http.StatusBadRequest)
        return
    }
    // pass u to your service layer...
}
```

You decode into `&u` because `Decode` fills an existing value through a pointer. The tags map JSON keys to fields.

### Scanning a database row

```go
type User struct {
    Name    string `db:"full_name"`
    Email   string `db:"email"`
    Age     int    `db:"age"`
    IsAdmin bool   `db:"is_admin"`
}

func loadUser(ctx context.Context, db *sql.DB, id int64) (User, error) {
    var u User
    row := db.QueryRowContext(ctx,
        `SELECT full_name, email, age, is_admin FROM users WHERE id = ?`, id)
    err := row.Scan(&u.Name, &u.Email, &u.Age, &u.IsAdmin)
    return u, err
}
```

The struct is your row-shaped container. Scanners differ by library; the idea is the same: one struct, one record shape.

### Config at startup

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
    if err := json.Unmarshal(b, &c); err != nil {
        return c, err
    }
    return c, nil
}
```

One blob of settings. Pass `Config` by value if it's small and read-mostly; use `*Config` if many packages need to share one live instance.

### Service layer — value vs pointer

```go
type User struct {
    Name    string
    Email   string
    Age     int
    IsAdmin bool
}

// Copies the whole User — fine for small structs, or when you want immutability
func SendWelcomeEmail(u User) { /* ... */ }

// Mutates the same User the caller has — admin dashboard, profile updates
func SetAdmin(u *User, admin bool) {
    u.IsAdmin = admin
}
```

```
MEMORY TRACE (pointer — mutation sticks):

  Caller: u at 0xE000
  SetAdmin(&u, true) passes 0xE000 into the function
  The function writes IsAdmin through that address
  After return, caller's u at 0xE000 shows IsAdmin == true
```

### API response shape with tags

```go
type APIResponse struct {
    StatusCode int               `json:"-"`              // don't emit in JSON body
    Body       json.RawMessage   `json:"data"`
    Headers    map[string]string `json:"-"`
}

type OrderDTO struct {
    ID        int64     `json:"id"`
    Total     int64     `json:"total"`
    CreatedAt time.Time `json:"created_at"`
}

func writeOrder(w http.ResponseWriter, o OrderDTO) {
    payload, _ := json.Marshal(APIResponse{Body: mustJSON(o)})
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    w.Write(payload)
}
```

Tags control what clients see. `json:"-"` keeps internal fields off the wire.

### Copying an `Order` shares the `Items` slice

```go
type Item struct {
    SKU  string
    Qty  int
}

type Order struct {
    ID        int64
    Total     int64
    Items     []Item
    CreatedAt time.Time
}

a := Order{ID: 1, Items: []Item{{SKU: "A", Qty: 1}}}
b := a
b.Items[0].Qty = 5
// a.Items[0].Qty is also 5 — slice header was copied, backing array is shared
```

Copying the struct duplicates the **slice header** (pointer, len, cap), not the whole `[]Item` array. That's the usual backend gotcha when you "duplicate" an order in memory.

---

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

---

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
> **Interview line:** If the function must persist changes visible to the caller, take `*T`, not `T`.

---

## 7. Gotchas & Interview Traps

| Trap | Why it bites | Fast fix / mental rule |
|------|--------------|------------------------|
| Huge struct in a hot loop by value | Full copy every call | Profile first; switch to `*T` if copies hurt |
| Expecting Java-style inheritance | Embedding promotes names; it's not a superclass | Be explicit about composition; add wrapper methods if needed |
| `==` on `Order` with `Items []Item` | Slices aren't comparable | Compare IDs, or field-by-field with `slices.Equal` |
| JSON missing after `Marshal` | Field not exported or `json:"-"` | Capitalize field names; check tags |
| Surprise shared mutation after `b := a` for orders | Slice maps share backing arrays | Copy slice with `append([]Item(nil), a.Items...)` if you need independence |
| Padding shock after reordering | Alignment and tail padding | `unsafe.Sizeof` on the target arch |

---

## 8. Interview Gold Questions (Top 3)

**1) Are Go structs classes?** No. You define named types and attach methods. There's no built-in inheritance. You compose with struct fields and embedding. Visibility is package-level and driven by capital letters on names.

**2) What happens when you pass a struct to a function?** The struct is copied byte-for-byte into the parameter unless you pass a pointer. Mutations on a value parameter don't affect the caller. Return the updated struct or take `*T` when you need shared mutation.

**3) Why can two structs with the same fields have different sizes?** Declaration order changes padding and trailing alignment (important for arrays of the struct). Measure with `unsafe.Sizeof` on the machine you care about.

---

## 9. 30-Second Verbal Answer

A struct is a fixed layout of named fields — your main tool for modeling users, orders, config, and responses in Go. It's a **value type**: assignment and calls copy the whole thing unless you use a pointer. Pointers mean "one shared record everyone reads and writes through." The compiler may add padding between fields for alignment, so order can change size. `==` only works when every field is comparable — watch slices inside DTOs. Tags are hints for `json`, SQL helpers, and validators; they don't change normal field access. Embedding promotes fields and methods but isn't inheritance — it's composition with sugar.

---

> See [[Glossary]] for term definitions.
