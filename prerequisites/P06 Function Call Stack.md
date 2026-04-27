# P06 Function Call Stack

> **Prerequisite note** — complete this before starting [[T10 Defer, Panic & Recover Internals]] or [[T13 Goroutine Internals]].
> Estimated time: ~25 min

---

## 1. Concept

Let's start from the very basics.

A **function** is a named block of code that does one job. You give it some inputs, it does its work, and it gives you back a result. In Go, your entire backend is built from functions calling other functions.

**Arguments** are the inputs you pass to a function. When you write `GetUser(ctx, 42)`, you're calling the function `GetUser` and handing it two arguments: a context and the number 42.

Now here's the key question: **what happens when one function calls another?**

Go needs to remember where it was. If `HandleCheckout` calls `ValidateCart`, Go needs to pause `HandleCheckout`, run `ValidateCart`, and when `ValidateCart` is done, pick up `HandleCheckout` exactly where it left off.

The way Go tracks all of this is called the **call stack**. Think of a stack of trays in a cafeteria. Every time you call a function, Go puts a new tray on top. When that function finishes, Go takes that tray off. The tray on top is always the function that's running right now.

Each tray is called a **stack frame**. It holds everything that function call needs: the arguments you passed in, the local variables it creates, and a note saying "when I'm done, go back to line X in the function that called me."

---

## 2. Core Insight (TL;DR)

**Every function call gets its own workspace (a frame).** When the function finishes, that workspace goes away.

If function A calls function B, B's frame goes on top of A's. When B returns, B's frame is removed. A picks up where it left off.

That's it. That's the call stack. Everything else in this note builds on top of this one idea.

---

## 3. Mental Model (Lock this in)

### The cafeteria tray analogy

Imagine you're in a cafeteria. There's a spring-loaded tray dispenser. You can only touch the top tray.

- You call a function = you put a new tray on top.
- That function returns = you take that tray off.
- The tray on top is always "who's running right now."

If your handler calls a service, which calls a database query, you have three trays stacked up. The database query tray is on top. When the query finishes, its tray comes off, and the service tray is on top again.

### The mistake that teaches you

Here's a bug a fresher would actually write. You call a function to promote a user to admin, but the change never sticks:

```go
func PromoteUser(u User) {
    u.IsAdmin = true
    fmt.Println("inside PromoteUser:", u.IsAdmin) // prints true
}

func HandleRequest(w http.ResponseWriter, r *http.Request) {
    user := User{Name: "Sam", IsAdmin: false}
    PromoteUser(user)
    fmt.Println("after PromoteUser:", user.IsAdmin) // prints false!
}
```

**What you'd expect:** `user.IsAdmin` should be `true` after calling `PromoteUser`.

**What actually happens:** It's still `false`. The promotion was lost.

**Why?** When you call `PromoteUser(user)`, Go creates a new tray (frame) for `PromoteUser` and **copies** the entire `user` struct onto that tray. `PromoteUser` flips `IsAdmin` on its own copy. When it returns, that tray (and the copy) is thrown away. The original `user` on `HandleRequest`'s tray was never touched.

```
Step 1: HandleRequest calls PromoteUser(user) — Go COPIES user to the new tray

    ┌──────────────────────────┐  <-- top (running now)
    │ PromoteUser's tray       │
    │   u = {Name:"Sam",       │
    │        IsAdmin: true}    │  <-- changed the COPY
    ├──────────────────────────┤
    │ HandleRequest's tray     │
    │   user = {Name:"Sam",    │
    │           IsAdmin: false} │  <-- original, untouched
    └──────────────────────────┘

Step 2: PromoteUser returns — its tray is thrown away

    ┌──────────────────────────┐  <-- top (running now)
    │ HandleRequest's tray     │
    │   user = {Name:"Sam",    │
    │           IsAdmin: false} │  <-- still false!
    └──────────────────────────┘

    PromoteUser's tray is gone. The copy with IsAdmin=true is gone with it.
```

**The fix:** Pass a pointer so both functions work on the same data: `func PromoteUser(u *User)` and call `PromoteUser(&user)`. You'll learn more about this in [[T07 Pointers & Pointer Semantics]].

The takeaway: each function call gets its own tray with its own copies. Changes to copies don't affect the original.

---

## 4. How It Works

### 4.1 What is a function and what are arguments?

You already use functions everywhere. A handler is a function. A database query is a function. Middleware is a function that calls another function.

In Go, a function looks like this:

```go
func GetUser(ctx context.Context, id int64) (*User, error) {
    // ... do work ...
    return &user, nil
}
```

The things inside the parentheses after the function name — `ctx` and `id` — are the **parameters**. They're like blank lines on a form. When someone calls `GetUser(reqCtx, 42)`, the values `reqCtx` and `42` are the **arguments** — they fill in those blank lines.

The things after the closing parenthesis — `(*User, error)` — are the **return values**. That's what the function gives back when it's done.

Here's the important part: when you call a function, **Go copies the arguments into the function's workspace**. The function works with its own copies. When it's done, Go copies the return values back to whoever called it.

---

### 4.2 What is a stack frame?

Every time you call a function, Go creates a workspace for that specific call. This workspace is called a **stack frame** (or just "frame").

Your frame holds four things:
- **The arguments** that were passed in (your copies)
- **Local variables** you create inside the function
- **A return address** — a note saying "when I'm done, go back to this line in the function that called me"
- **Space for return values** — where Go puts the results before handing them back

Think of it like a desk in an office. When you start a task (a function call), you get a fresh desk. Your papers (variables) go on that desk. When you finish the task, you hand your results to the person who asked you, and your desk gets cleared.

Here's a simple example — one function calling another:

```go
func CalculateTotal(price int, quantity int) int {
    total := price * quantity
    return total
}

func HandleOrder(w http.ResponseWriter, r *http.Request) {
    amount := CalculateTotal(50, 3)
    fmt.Fprintf(w, "Total: %d", amount)
}
```

When `HandleOrder` calls `CalculateTotal(50, 3)`, try to picture the stack in your head before reading on. How many frames are there? What's in each one?

```
Step 1: HandleOrder is running, about to call CalculateTotal

    ┌───────────────────────────┐  <-- top
    │ HandleOrder frame         │
    │   (about to call...)      │
    └───────────────────────────┘

Step 2: CalculateTotal is now running

    ┌───────────────────────────┐  <-- top (running now)
    │ CalculateTotal frame      │
    │   price = 50              │
    │   quantity = 3            │
    │   total = 150             │
    │   "go back to HandleOrder"│
    ├───────────────────────────┤
    │ HandleOrder frame         │  <-- paused, waiting
    │   amount = (waiting...)   │
    └───────────────────────────┘

Step 3: CalculateTotal returns 150, its frame is removed

    ┌───────────────────────────┐  <-- top (running again)
    │ HandleOrder frame         │
    │   amount = 150            │  <-- got the result
    └───────────────────────────┘
```

Two calls to the same function get two separate frames. If your handler calls `CalculateTotal` twice, each call gets its own desk with its own copies of `price`, `quantity`, and `total`. They don't share anything.

---

### 4.3 Stack memory vs heap memory

You've seen that variables live on a frame, and the frame goes away when the function returns. But what if you need a variable to survive after the function returns?

Go has two kinds of memory:

**Stack memory** is like scratch paper. Each function call gets a fresh sheet. When the function returns, that sheet gets thrown away. It's fast and automatic — you don't have to clean it up.

**Heap memory** is like a storage locker. Stuff you put there stays until nobody needs it anymore. It's slower, and Go's garbage collector has to come around later to clean it up.

Most of the time, you don't choose. The Go compiler figures it out for you. Here's the rule of thumb:

- If a variable is only used inside the function, it goes on the **stack** (scratch paper — fast, auto-cleanup).
- If a variable needs to survive after the function returns (like when you return a pointer to it), the compiler moves it to the **heap** (storage locker — survives longer).

Here are two functions that look similar but end up using different memory:

```go
func GetUserLocal() User {
    u := User{Name: "Sam"}
    return u
}

func NewUser(name string) *User {
    u := User{Name: name}
    return &u
}
```

In `GetUserLocal`, the variable `u` is only used inside the function and returned by copy. It lives on the stack — fast scratch paper, thrown away when the function returns.

In `NewUser`, the function returns `&u` — a pointer to `u`. If `u` was on the scratch paper and the scratch paper got thrown away, that pointer would point to garbage. So the compiler puts `u` on the heap instead, where it survives the function return.

```
GetUserLocal — u stays on the stack (scratch paper):

    STACK                          HEAP
    ┌────────────────────┐
    │ GetUserLocal frame │
    │   u = {Name:"Sam"} │         (nothing here)
    └────────────────────┘
    Function returns → u is COPIED to caller → scratch paper thrown away. Done.


NewUser — u moves to the heap (storage locker):

    STACK                          HEAP
    ┌────────────────────┐         ┌─────────────────────┐
    │ NewUser frame       │         │ u = {Name:"Sam"}    │
    │   (pointer) ────────┼────────>│                     │
    └────────────────────┘         └─────────────────────┘
    Function returns → frame is gone, but u survives on the heap.
    Caller gets the pointer. Garbage collector cleans up later.
```

You don't need to memorize when this happens. Just know: **you write normal code, the compiler decides where things live.**

---

### 4.4 Push on call, pop on return

Let's build up from two frames to four, step by step.

Imagine a request hitting your API server. Here's the call chain — each function calls the next one:

```go
func ServeHTTP(w http.ResponseWriter, r *http.Request) {
    AuthMiddleware(w, r)
}

func AuthMiddleware(w http.ResponseWriter, r *http.Request) {
    // ... check JWT ...
    GetUser(w, r)
}

func GetUser(w http.ResponseWriter, r *http.Request) {
    rows, err := db.QueryContext(r.Context(), `SELECT ...`)
    // ...
}
```

`ServeHTTP` calls `AuthMiddleware`, which calls `GetUser`, which calls `db.QueryContext`. Each call adds a frame. Let's watch the stack grow:

**Two frames (handler calls service):**

```
    ┌─────────────────────────┐  <-- top
    │ GetUser frame           │  <-- running
    ├─────────────────────────┤
    │ HandleRequest frame     │  <-- paused
    └─────────────────────────┘
```

**Three frames (service calls database):**

```
    ┌─────────────────────────┐  <-- top
    │ db.QueryContext frame   │  <-- running (waiting on DB)
    ├─────────────────────────┤
    │ GetUser frame           │  <-- paused
    ├─────────────────────────┤
    │ HandleRequest frame     │  <-- paused
    └─────────────────────────┘
```

**Four frames (add middleware):**

```
    ┌─────────────────────────┐  <-- top
    │ db.QueryContext frame   │  <-- running
    ├─────────────────────────┤
    │ GetUser frame           │  <-- paused
    ├─────────────────────────┤
    │ AuthMiddleware frame    │  <-- paused
    ├─────────────────────────┤
    │ ServeHTTP frame         │  <-- paused
    └─────────────────────────┘
```

Now returns happen in reverse. The database query finishes first — its frame is removed. Then `GetUser` finishes — its frame is removed. Then `AuthMiddleware`, then `ServeHTTP`. Always one frame removed per return, always from the top.

The whole chain of "who called whom" is sitting there in the stack. That's why when something crashes, Go can print a **stack trace** — it just reads the stack from top to bottom and shows you every function that was waiting.

---

### 4.5 What is defer?

`defer` is a Go keyword that says: **"run this function call later, right before the current function exits."**

Why does this exist? Because in backend code, you constantly open things that need closing: database connections, file handles, HTTP response bodies, transactions. You want to guarantee the cleanup happens no matter how the function exits — whether it returns normally, returns early because of an error, or even crashes.

Here's the simplest possible example:

```go
func SayHello() {
    defer fmt.Println("goodbye")
    fmt.Println("hello")
}
```

When you run `SayHello()`, it prints:

```
hello
goodbye
```

Here's what happened step by step:

1. Go enters `SayHello`.
2. Go sees `defer fmt.Println("goodbye")`. It doesn't run it yet. It makes a note: "before this function exits, run `fmt.Println("goodbye")`."
3. Go runs `fmt.Println("hello")`. Prints "hello".
4. Go reaches the end of `SayHello`. Before actually leaving, it runs the deferred call. Prints "goodbye".
5. Now `SayHello` is truly done.

```
Step 1: Enter SayHello

    SayHello frame:
    ┌─────────────────────────────┐
    │ defer list: (empty)         │
    └─────────────────────────────┘

Step 2: defer fmt.Println("goodbye") — saved, NOT run yet

    SayHello frame:
    ┌─────────────────────────────┐
    │ defer list: [ "goodbye" ]   │  <-- saved for later
    └─────────────────────────────┘

Step 3: fmt.Println("hello") runs → prints "hello"

Step 4: Function ends → run defer list → prints "goodbye"

Step 5: SayHello is truly done, frame removed
```

The real reason `defer` is powerful: it works no matter HOW the function exits. Here's a real backend example:

```go
func (r *UserRepo) GetUser(ctx context.Context, id int64) (*User, error) {
    rows, err := r.db.QueryContext(ctx, `SELECT id, email FROM users WHERE id = ?`, id)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    if !rows.Next() {
        return nil, sql.ErrNoRows
    }
    var u User
    if err := rows.Scan(&u.ID, &u.Email); err != nil {
        return nil, err
    }
    return &u, nil
}
```

There are three different `return` statements in this function. `rows.Close()` runs on ALL of them. You write `defer rows.Close()` once, right after you know `rows` is valid, and you never worry about forgetting to close it.

Step by step:
1. Query the database. If that fails, return early (rows don't exist, so no Close needed — the defer wasn't registered yet).
2. Register `defer rows.Close()`. From this point on, no matter what happens, `rows.Close()` will run when this function exits.
3. Try to read rows, scan data. If anything fails, return early. The defer still runs `rows.Close()`.
4. If everything works, return the user. The defer still runs `rows.Close()`.

---

### 4.6 Defer runs in reverse order (last registered = first to run)

What if you register more than one defer? They run in reverse order — the last one you registered runs first.

Think of stacking plates. The last plate you put on top is the first one you pick up.

```go
func ProcessOrder() {
    defer fmt.Println("step 1: done")
    defer fmt.Println("step 2: done")
    defer fmt.Println("step 3: done")
    fmt.Println("processing...")
}
```

Output:

```
processing...
step 3: done
step 2: done
step 1: done
```

Step by step:
1. `defer "step 1"` is registered. Defer list: `[step 1]`
2. `defer "step 2"` is registered. Defer list: `[step 1, step 2]`
3. `defer "step 3"` is registered. Defer list: `[step 1, step 2, step 3]`
4. `"processing..."` prints.
5. Function exits. Defers run from the TOP of the list (last registered first): step 3, then step 2, then step 1.

Why does this matter in real code? Because cleanup order matters. Here's a real example — you open a database transaction, then open a temp file:

```go
func (h *Handler) ExportReport(w http.ResponseWriter, r *http.Request) error {
    tx, err := h.db.BeginTx(r.Context(), nil)
    if err != nil {
        return err
    }
    defer tx.Rollback()

    f, err := os.CreateTemp("", "report-*.csv")
    if err != nil {
        return err
    }
    defer f.Close()

    // ... write report using tx and f ...

    return tx.Commit()
}
```

Registration order: first `Rollback`, then `Close`.
Run order at exit: first `Close` (closes the file), then `Rollback` (rolls back the transaction, which is a no-op if `Commit` already succeeded).

```
Defer list (bottom = first registered):

    bottom --> [ Rollback ] [ Close ] <-- top

On exit, run from top:
    1. f.Close()       <-- close the file first
    2. tx.Rollback()   <-- then roll back (no-op if committed)
```

This is usually what you want: close inner resources before outer ones.

---

### 4.7 Named return values + defer

Before we look at the pattern, let's first understand what **named return values** are.

Normally, you write a function like this:

```go
func LoadConfig(path string) (Config, error) {
    // ...
    return cfg, nil
}
```

But Go also lets you **name** the return values:

```go
func LoadConfig(path string) (cfg Config, err error) {
    // ...
    return cfg, err
}
```

When you name them, `cfg` and `err` become real variables that exist for the entire function. They start at their zero values (`Config{}` and `nil`). You can use them like any other variable.

Now here's the trick: since named return values are real variables in the function's frame, **a defer can read and change them**.

This is incredibly useful for adding context to errors in one place instead of at every return:

```go
func LoadConfig(path string) (cfg Config, err error) {
    defer func() {
        if err != nil {
            err = fmt.Errorf("LoadConfig %q: %w", path, err)
        }
    }()

    data, err := os.ReadFile(path)
    if err != nil {
        return cfg, err
    }
    err = json.Unmarshal(data, &cfg)
    return cfg, err
}
```

Before reading the walkthrough below, try to answer: when `os.ReadFile` fails and the function hits `return cfg, err`, what does the defer see? What value does the caller end up with?

Here's the step-by-step:

1. Go enters `LoadConfig`. Two named variables exist in this frame: `cfg` (zero value) and `err` (nil).
2. The defer is registered. It's a closure — a function defined inside another function. Because `err` is a named return value, it lives in this frame for the whole call. The closure can see it and change it.
3. Say `os.ReadFile` fails. `err` gets set to something like "file not found."
4. `return cfg, err` puts the values into the return slots.
5. **Before the function actually exits**, the defer runs. It sees `err` is not nil, so it wraps it: `err` becomes `LoadConfig "/etc/app.json": file not found`.
6. NOW the function exits, and the caller gets the wrapped error.

```
LoadConfig frame:

    ┌────────────────────────────────────┐
    │ named: cfg = Config{}, err = nil   │  <-- start
    │ defer: [ wrap-err closure ]        │
    └────────────────────────────────────┘

After os.ReadFile fails:

    ┌────────────────────────────────────┐
    │ named: cfg = Config{}              │
    │        err = "file not found"      │  <-- set by ReadFile
    │ defer: [ wrap-err closure ]        │
    └────────────────────────────────────┘

return cfg, err triggers. BEFORE exiting, defer runs:

    ┌────────────────────────────────────┐
    │ named: cfg = Config{}              │
    │        err = "LoadConfig: file..." │  <-- wrapped by defer
    └────────────────────────────────────┘

Caller receives the wrapped error.
```

---

### 4.8 Each goroutine gets its own stack

A **goroutine** is Go's version of a lightweight thread. When your server handles multiple requests at the same time, each request runs in its own goroutine.

The key thing: **each goroutine has its own call stack**. Two goroutines handling two requests both run `ServeHTTP` with the same source code, but they have completely separate stacks, separate frames, and separate local variables. They don't interfere with each other.

Go starts each goroutine with a small stack (a few KB) and grows it automatically when the call chain gets deeper. You don't manage this yourself.

---

### 4.9 Stack overflow

If a function keeps calling itself (recursion) and never stops, frames keep piling up on the stack. Eventually the stack runs out of room. That's a **stack overflow**.

A simple example:

```go
func CountForever(n int) {
    CountForever(n + 1)
}
```

Every call to `CountForever` adds a frame. Nothing ever returns, so nothing ever removes a frame. After enough calls, the goroutine's stack is full and Go crashes with: `runtime: goroutine stack exceeds limit`.

A more realistic backend version: a JSON decoder that handles nested objects by calling itself, with no limit on depth:

```go
func decodeValue(d *decoder) error {
    if d.peek() == '{' {
        return decodeObject(d)
    }
    return nil
}
```

A malicious API client sends deeply nested JSON — thousands of `{` inside each other. Each level is a new function call, a new frame. The stack fills up and your service crashes.

The fix: add a depth counter and refuse to go deeper than a limit (say 100 levels).

---

## 5. Key Rules & Behaviors

### Every call creates a new frame

Even if you call the same function twice in a row, each call gets its own fresh workspace. Two calls to `GetUser` in the same handler means two separate frames, not one shared one.

### When a function returns, its frame is gone

All the local variables in that frame disappear. If you need something to survive after the function returns, Go's compiler will put it on the heap for you (like when you return a pointer to a local variable).

### Defer runs when the function exits, not when the line runs

`defer` doesn't run the call immediately. It saves it for later. The call runs right before the function returns — no matter which `return` statement you hit.

### Multiple defers run in reverse order

Last registered, first to run. Think of stacking plates — the last plate on top is the first one off.

### Defer evaluates arguments immediately

This is a subtle one. When you write `defer fmt.Println(x)`, Go captures the VALUE of `x` right then and there — not when the defer actually runs later.

```go
func Example() {
    x := 1
    defer fmt.Println(x)
    x = 2
    defer fmt.Println(x)
}
```

Output: `2` then `1`. The first defer captured `x = 1`. The second defer captured `x = 2`. They run in reverse order (2 then 1), but each uses the value of `x` at the moment they were registered.

If you want the defer to use the value of `x` at the time it RUNS (not when it was registered), use a closure:

```go
defer func() { fmt.Println(x) }()
```

The closure doesn't capture the value — it captures the variable itself. So it reads whatever `x` is when the defer finally runs.

---

## 6. Code Examples (Show, Don't Tell)

### The pattern you'll actually ship: rows + defer

```go
func (r *OrderRepo) GetOrdersByUser(ctx context.Context, userID int64) ([]Order, error) {
    rows, err := r.db.QueryContext(ctx, `SELECT id, total FROM orders WHERE user_id = ?`, userID)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    var orders []Order
    for rows.Next() {
        var o Order
        if err := rows.Scan(&o.ID, &o.Total); err != nil {
            return nil, err
        }
        orders = append(orders, o)
    }
    return orders, rows.Err()
}
```

Step by step:
1. Query the database. If it fails, return immediately. `rows` doesn't exist yet, so no Close needed.
2. `defer rows.Close()` is registered. From now on, `rows.Close()` will run no matter how the function exits.
3. Loop through rows, scanning each one into an `Order`. If any scan fails, return early — defer still closes rows.
4. If everything works, return the orders. Defer still closes rows.

You write the cleanup ONCE. It runs on ALL exit paths.

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

Before running this code, predict what it prints:

```go
func main() {
    fmt.Println("start")
    defer fmt.Println("first defer")
    defer fmt.Println("second defer")
    defer fmt.Println("third defer")
    fmt.Println("end")
}
```

> [!success]- Answer
> ```
> start
> end
> third defer
> second defer
> first defer
> ```
> "start" and "end" print in order. Then defers run in reverse: third, second, first.

### Tier 2: Fix the Bug (5 min)

This function is supposed to log the error with context when it fails, but the log always shows `<nil>`. Can you spot why?

```go
func (h *Handler) CreateOrder(w http.ResponseWriter, r *http.Request) (err error) {
    defer func() {
        if err != nil {
            h.log.Printf("CreateOrder failed: %v", err)
        }
    }()

    var req OrderRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        return err
    }
    return h.orderService.Create(r.Context(), req)
}
```

> [!success]- Answer
> The problem is **variable shadowing**. Look at line `if err := json.NewDecoder...`. That `:=` creates a NEW variable called `err` that only exists inside the `if` block. It does NOT update the outer named return `err` that the defer is watching.
>
> The deferred closure reads the outer `err`, which is still `nil` because it was never assigned.
>
> Fix: use `=` instead of `:=` to assign to the outer `err`:
> ```go
> var req OrderRequest
> if err = json.NewDecoder(r.Body).Decode(&req); err != nil {
>     return err
> }
> ```
> Now the outer `err` gets set, and the defer sees it.

---

## 7. Gotchas & Interview Traps

| Trap | What happens | How to explain it |
|------|-------------|-------------------|
| Defer in a loop | Every iteration registers a new defer. They ALL run when the **function** exits, not when each iteration ends. If you're opening 1000 files in a loop, you have 1000 pending Close calls. | "Defer is tied to the function, not the loop. If you need per-iteration cleanup, wrap the loop body in a helper function." |
| `defer f(x)` vs `defer func() { f(x) }()` | `defer f(x)` captures the VALUE of x right now. `defer func() { f(x) }()` reads x when the defer actually runs. | "Direct call = snapshot of the value. Closure = live reference to the variable." |
| Infinite recursion | Every call adds a frame. No returns means no frames get removed. Stack fills up. | "Each call adds a tray to the stack. No limit on depth = stack overflow." |
| Assuming goroutines share a stack | Two goroutines running the same function have completely separate stacks and separate variables. | "Same code, different stacks. Each goroutine is its own cafeteria tray stack." |

**Stack vs heap in one sentence:** Go puts variables on the stack (fast, auto-cleanup) when they die with the function, and on the heap (slower, garbage-collected) when they need to survive longer. The compiler decides, not you.

---

## 8. Interview Gold Questions (Top 3)

**Q1: What is a stack frame, and what happens when you call a function vs when it returns?**

Every time you call a function, Go creates a workspace called a frame. It holds the arguments, local variables, where to go back when done, and space for return values. Calling a function puts a new frame on top of the stack. Returning removes that frame. The last one added is always the first one removed.

**Q2: Why do defers run in reverse order, and when are the arguments captured?**

Defers stack up as you register them. The last one registered runs first when the function exits — like stacking plates. For `defer f(x)`, the value of `x` is captured the moment that line runs. A closure like `defer func() { f(x) }()` reads `x` later, when the defer actually executes — it sees whatever `x` is at that point.

**Q3: How can a defer change what the caller receives?**

If your function uses named return values like `(err error)`, then `err` is a real variable in the function's frame for the whole call. A defer can read it and change it. The caller gets whatever value `err` has AFTER the defer runs. That's how people wrap errors with context in one central place instead of at every return statement.

---

## 9. 30-Second Verbal Answer

"Every function call in Go creates a stack frame — a workspace holding arguments, local variables, and a return address. Calling pushes a frame, returning pops it. Defer lets you register cleanup calls that run automatically when the function exits, in reverse order — last registered, first to run. If you use named return values, a defer can read and change them before the caller gets the result, which is great for wrapping errors with context. Each goroutine has its own stack, and if you recurse without stopping, the stack fills up and you get a stack overflow."

---

> See [[Glossary]] for term definitions.
