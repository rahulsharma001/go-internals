# T09 Error Handling Patterns — Interview Questions

#qa #go #interview

Back to: [[T09 Error Handling Patterns]]

A compact bank of **error** philosophy, **wrapping (`%w`)**, **`errors.Is` / `As`**, **sentinels vs custom** types, **typed nil**, and **API** design questions, ordered for signal at Go-heavy companies. Tags: [COMMON], [ADVANCED], [TRICKY].

**C + D (concise + deep):** each item has **in one line**, **ASCII**, **key facts**, **interview tip**, and a **Full Story** accordion.

---

## Q1: What is Go’s error handling philosophy? [COMMON]

**In one line:** Make **error returns explicit** at every call site; treat them as **normal values** (not control-flow exceptions), and reserve **`panic` for true bugs** or **unrecoverable** misconfiguration—not “file not found.”

**Visualize it:**

```
call()
   |
   v
if err != nil { return fmt.Errorf("context: %w", err) }
   |
   v
log / map to HTTP 4xx/5xx / metrics   (in handler boundary)
```

**Key facts**

- `if err != nil` is the default shape; the **type** of `err` is the **`error` interface** (`Error() string`), not a single class.  
- **Sentinels** (e.g. `io.EOF`) and **custom** structs are both idiomatic.  
- Cross-layer **wrapping** carries **cause** + **message**; API surfaces often **classify** (retryable, client fault).  
- See the mental model in [[T09 Error Handling Patterns]] and the one-pager in [[T09 Error Handling Patterns - Simplified]].

**Interview tip** — Say “**explicit, values, not only stack unwinding**” and mention **one** of: **wrapping**, **sentinel**, or **context cancellation** to show you know the ecosystem beyond `try/catch`.

> [!example]- Full Story: Philosophy vs other languages
>
> **The problem** — Many candidates default to “Go has no exceptions so error handling is bad” — interviewers want **tradeoffs** (explicit flow, `defer`, no hidden stack cost per happy path) **not** a rant.  
> **How it works** — Functions return `(T, error)` or `error` alone; the **zero value** of `T` is often meaningless on error, so read `(val, err)` and handle **err first** or document which field is valid. Libraries expose **package-level** `var ErrX` and sometimes **`Is`/`Unwrap`**. **Production** code adds **context** and uses **`errors.Is` / `As`** on boundaries.  
> **What to watch out for** — Saying `panic` is **never** used — it **is** used, sparingly, for **invariants**; also avoid claiming **`try`** exists in the language. Point to `fmt.Errorf` and **`%w`**, not ad-hoc string prefix only.

---

## Q2: Explain `errors.Is` vs `errors.As` [COMMON]

**In one line:** `Is` checks whether `err`’s unwrap **chain** matches a **target** error (identity / sentinel / custom `Is` on target), while `As` walks the same chain and, on first match, **assigns** a concrete value into a destination **pointer of that type** (e.g. `*MyErr`).

**Visualize it:**

```
errChain:  outer  -->  Unwrap  -->  middle  -->  Unwrap  -->  leaf

errors.Is(err, io.EOF)   finds leaf == io.EOF  (or target.Is behavior)

var m *MyErr
errors.As(err, &m)       sets m to first *MyErr in chain
```

**Key facts**

- Both require **`err != nil` first**; passing **nil** returns **false**.  
- `Is` second arg is a **`target` error** (often a sentinel or typed **nil** target—careful with construction).  
- `As` second arg is a **non-nil pointer** to **interface** or **pointer to concrete** type (e.g. `&v` where `v` is `*os.PathError`).  
- `As` is for **struct fields**; `Is` is for “**is this the same situation?**” **See** [[T09 Error Handling Patterns - Visual Map]] for the table.

**Interview tip** — State **unwrap chain** in the **first** sentence, then name **`Is` = compare**, **`As` = extract** — interviewers use this to filter “only read the blog title” candidates.

> [!example]- Full Story: Unwrap and the Go 1.13+ world
>
> **The problem** — After wrapping with **`fmt.Errorf("… %w", err)`**, `==` and raw **`err.Error()`** checks **break**; you need `Is`/`As`.  
> **How it works** — `errors` walks **`Unwrap()`** (and legacy **`Cause`** patterns are obsolete in new code). `Is` uses **`==`** first, then `Is` method on the **target** in some cases—read docs for the exact algorithm. `As` uses **type assertion** at each step.  
> **What to watch out for** — **`As` into a non-pointer**; **`Is` with a freshly allocated `errors.New` each time** (always new identity); mixing **`pkg/errors`** style **`Cause`** with `errors` stdlib in one codebase without discipline.

---

## Q3: How does error wrapping work with `%w`? [COMMON]

**In one line:** `fmt.Errorf` with **`%w`** builds a new **`error` value** that **still implements `Unwrap() error`**, so **`errors.Is` / `As` can traverse to the inner** cause.

**Visualize it:**

```
fmt.Errorf("op: %w", inner)  =  { Error() string, Unwrap() -> inner }
```

**Key facts**

- The **outer** `Error()` string usually concatenates **context** + **inner**’s `Error()` (implementation detail—do not **parse** it in app logic).  
- **Multiple** `%w` in one `Errorf` is a **known** / **version-specific** area — prefer **one** inner per wrap, or `errors.Join` (1.20+) for many causes.  
- Without **`Unwrap`**, **`Is` / `As` see only** the **outer** shell—treat that as a **string-only** error for inspection purposes.

**Interview tip** — If asked “how does `As` work,” **answer** in terms of **`Unwrap` chain**, not “magic in `fmt`.”

> [!example]- Full Story: Wrapping vs `pkg/errors` and alternatives
>
> **The problem** — Pre-1.13 codebases used **`github.com/pkg/errors.Wrap`**; **stdlib** is now the default for **new** code.  
> **How it works** — `fmt` creates an **opaque** struct in `errors` that holds **format** + **arg**; **`Unwrap`** returns the **wrapped** `error`. `errors.Join` (Go 1.20+) is for **OR**-style **multi**-errors with **unwrapping** by index.  
> **What to watch out for** — Wrapping **nil** (behavior is to treat carefully—often **nil** in, **nil** out); **wrapping the same** error **twice** in different layers and **losing** type information if you use **`%v`**.

---

## Q4: When should you use **sentinel** errors vs **custom** error types? [COMMON]

**In one line:** **Sentinels** for a **small, fixed set of global outcomes** (EOF, not found) compared with `errors.Is`; **custom** types when callers need **fields** or **rich behavior** (`errors.As`, methods).

**Visualize it:**

```
Sentinel:   var ErrNotFound = errors.New("not found")
Custom:     type ValidationError struct { Field string; ... }
```

**Key facts**

- Sentinels are **package-level** `var` — **compare** with **`errors.Is`**, not **`err.Error() ==`**.  
- Custom types get **`errors.As`** to avoid **parsing** strings.  
- **Overuse** of sentinels → **string** **sprawl**; **overuse** of structs → **heavy** API. **See** the **decision table** in [[T09 Error Handling Patterns - Visual Map]].

**Interview tip** — Give **one** line each: **control flow** → sentinel often enough; **API contract with data** → custom.

> [!example]- Full Story: Migration from strings to types
>
> **The problem** — **Legacy** code returns `fmt.Errorf("user %d not found", id)`; **new** code wants `ErrUserNotFound` with **id** field—refactor in steps: introduce **type**, **As** in handlers, **deprecate** string checks.  
> **What to watch out for** — **Export** sentinels when they are **public** **contract**; unexported + **wrapping** can block **other packages**’ `Is` (still often OK if you expose **IsMyErr** wrapper).

---

## Q5: What is the difference between `%w` and `%v` in `fmt.Errorf`? [TRICKY]

**In one line:** **`%w`** is for **only `error` values** and **records a wrap** so the result **`Unwrap`s**; **`%v`** (and **`%s`**) are **plain formatting**—no **stdlib** `Unwrap` from **`fmt`’s** `%v` to the inner (you get **text** in the string, not a **link** for `Is`/`As`).

**Visualize it:**

```
fmt.Errorf("a: %w", e)  →  err with Unwrap() == e
fmt.Errorf("a: %v", e)  →  err typically NOT wrapping e for stdlib (no Is/As through)
```

**Key facts**

- **Since Go 1.20**, the docs emphasize **`%w` is the** wrapping **verb**; multiple `%w` has specific rules.  
- **`%v` on an `error` still prints the `Error()` string** — good for **logs**, bad as **the only** path for **`Is`**.  
- **`errors.Is`** on a **`%v`–only** outer error **does not** see the inner in the same way as a **`%w`** error.

**Interview tip** — If they want **tricky**: mention **`Println(err)`** uses `Error()` only—**no** `Unwrap` for logging **either** way.

> [!example]- Full Story: Why `%v` in libraries hurt debugging
>
> **The problem** — Middleware does `return fmt.Errorf("auth: %v", err)`; downstream **`errors.Is`**, `Is(err, token.ErrExpired)` is **false** even though the **string** “expired” **appears**. **Fix** — **`%w`**, or return **`err`** **as-is** with **separate** **context** in **structured** logs.  
> **What to watch out for** — **Re-wrap** the **same** error **repeatedly** (stack of identical causes); also **%w** with **non-error** (compile error—good).

---

## Q6: What is the **typed nil** error trap? [TRICKY]

**In one line:** Returning a **nil** pointer of **concrete** type `*T` in a **return slot typed `error`** yields a **non-nil** `error` because the **interface** holds `(*T, nil)` — **dynamically typed**, **statically** “nil **pointer**.”

**Visualize it:**

```
var p *AppError = nil
return p   // as error:  ( *AppError, nil )  → err != nil  == true
return nil // as error:  ( nil,  nil  )     → err != nil  == false
```

**Key facts**

- **Test** with `if err == nil` after **converting** through `error` in **humble** `return` — **fails** for typed nil. **Fix:** `if err == nil { return nil }` **or** return **`err error` variable** with **no** `*T` in the box.  
- Printing the bad `error` with `%#v` often shows `(*main.AppError)(nil)` while `err != nil` stays true. **See** Tier 2 in [[T09 Error Handling Patterns - Exercises]].

**Interview tip** — **Draw** the **(type, value)** pair; interviewers use this to check **interface** model knowledge.

> [!example]- Full Story: Where it bites in real code
>
> **The problem** — Named return `e *AppError` with a bare `return` after `e` was set to a non-`nil` value earlier, or returning a `nil` `*AppError` through a result typed as `error`, breaks the usual `if err != nil` guard. Database transaction helpers are a classic place: the helper looks successful but the interface still carries a type. **Fix** — return `nil` with interface type, e.g. `var e error; return e`, or split into `(*Result, error)` with a true `nil` `error` on success.

---

## Q7: How would you design error handling for a **REST** API? [ADVANCED]

**In one line:** **Map domain errors to stable HTTP** codes, **log** internal **causes** with **trace** ids, **return** **sanitized** **JSON** **bodies**—do not **leak** **stack** or **internal** **paths** to **clients**.

**Visualize it:**

```
handler -> service -> repository
   |         |            |
  HTTP    wrap %w     sql.Err / sentinel
  map 4xx/5xx  \___________/
```

**Key facts**

- **Handler** is the only place that knows **Request** / **ResponseWriter**; **lower** layers return **`error`** + **types**.  
- **Use** `errors.As` to detect **`ValidationError`** (400) vs **NotFound** (404) vs **throttle** (429). **Logging:** **always** `err` with **request id**.  
- **Idempotency** and **retries** — classify **transient** vs **permanent** (often a **field** on custom error or **wrapper** type).

**Interview tip** — Name **one** **leak** you avoid (e.g. **SQL** text) and **one** **observability** win (correlation id).

> [!example]- Full Story: Patterns beyond one project
>
> **The problem** — GIN/Echo middleware may `recover` from `panic`; that path is different from business `error` handling. If you publish an OpenAPI schema, align `errors.As` targets with **stable** error **codes** in the body instead of `strings.Contains` on `err.Error()`.  
> **What to watch out for** — Specifying a unique JSON body for every possible `500` when a single “retry with same idempotency key” response is enough for clients.

---

## Q8: Why shouldn’t you use **`panic`** for error handling? [COMMON]

**In one line:** **`panic`** **unwinds the stack** like a **hard stop**; **expected** **failures** (I/O, validation) should be **`error` values** so **callers** can **decode**, **retry**, and **return** **HTTP 4xx** without **killing** **concurrent** **work** **accidentally**.

**Visualize it:**

```
panic  -->  defer runs  -->  (maybe recover)  -->  STILL not for "file missing"
err    -->  caller chooses path                 -->  normal
```

**Key facts**

- **Recover** is for **truly** **exceptional** or **package** **boundary** (e.g. **template** **must** **not** **kill** **server**). **User** **input** **errors** → **`error`**, not **panic**.  
- **Libraries** that **panic** on **common** **cases** are **hard** to **use** **safely**. **Init** / **main** can **log.Fatal** (process exit) **or** **panic** for **unrecoverable** **misconfig** — different context.

**Interview tip** — Contrast **`panic` + `recover`** **scope** (usually **Goroutine**-local) with **`error` propagation** — shows you know **recover** is **not** **try/catch** **semantics** **globally**.

> [!example]- Full Story: When panic is still idiomatic
>
> **The problem** — Do not use `panic` for an expected “bad key” in an HTTP handler: return a 4xx with `error` and structured logs. A genuine programmer mistake (e.g. index out of range on a slice you proved non-empty) may still `panic` in a tight loop during tests. In production, unreachable branches sometimes call a small `must` or `bug()` helper that logs and `panic`s—use sparingly.  
> **What to watch out for** — Relying on `recover` from `json.Unmarshal` into `interface{}` and blind type assertion; prefer the `v, ok :=` form or unmarshal into a concrete struct / `map[string]any` with validation.

---

## Q9: What is **`errors.New`**’s return type **internally**? [TRICKY]

**In one line:** `errors.New` returns **`error`**, and **concretely** a **private** **struct** in the **`errors`** **package** that **holds the string**; it is not **`string`** and not **`*string`**—it is a **small** **value** that **implements** **`Error() string`**.

**Visualize it:**

```
errors.New("x")  -->  [opaque struct]{ s: "x" }  // implements error
```

**Key facts**

- **Compare** with **`errors.Is`**, not **`==`** to another **`New("x")` unless** the **variable** is **shared** (identity). **Two** `New("x")` **are** **not** `==`.  
- `fmt.Errorf` with **no** `%w` is **similar** **opaque** **implementation**; **`%w`** **adds** **Unwrap** **field** **(conceptually)**.

**Interview tip** — If pressed “what struct?”—say **unexported** in **`errors`** and **intentionally** **opaque** to **discourage** **asserting** to **it** (use `Is` / `As` on **own** **types**).

> [!example]- Full Story: Why two `New` with same string differ
>
> **The problem** — **Tests** use **`errors.Is`** **after** **wrap**; **same** string **is** not **enough**—you need **sentinel** **variable** **identity** or **custom** **Is** **method** on a **type** you **own**.

---

## Q10: How do you create **custom** error types that work with **`errors.As`**? [COMMON]

**In one line:** **Define a type** with **`Error() string`**, return **a pointer to it** (or **value**, but **pointer** is common) from your **API**, **wrap** with **`%w`**, and in the **caller** declare **`var target *MyType`**, then **`errors.As(err, &target)`** — **the type must match** the **dynamically** **stored** **value** (or **be assignable**).

**Visualize it:**

```
type E struct { Code int }
func (e *E) Error() string { ... }

// return &E{...}
// var x *E; errors.As(wrapped, &x)
```

**Key facts**

- **Pointer vs value** — If you **return** `&E`, **`As` into** `*E` **pointer**; if **value** `E`, **`As` into** `*E` or `E` per **assignability** rules.  
- **Implement** `Unwrap` **only** if your **type** **wraps** **another** **error**; **`As` still** **walks** **inner** **if** you **return** `Unwrap` **from** **fmt**’s **%w** **outer** **layer** **wrapping** **your** **type** **inside** **(chain)**. **Exercise:** [[T09 Error Handling Patterns - Exercises]] **Tier 3**.

**Interview tip** — **Show** **field** access **after** `As` for **400** **responses** — **exercise** in **exercises** **note**.

> [!example]- Full Story: Interfaces as As targets
>
> **The problem** — `As` can target a pointer to interface when you want the first error in the chain that implements a small behavior interface (e.g. `interface { Code() int }`). The exact assignability rules are in `go doc errors.As`—a rare but strong follow-up in senior rounds.

---

## Q11: When should you **NOT** wrap an error? [ADVANCED]

**In one line:** When **adding** a **wrap** would **repeat** **noise**, **leak** **secrets** / **PII** **to** **logs**, or **break** **stable** **sentinel** **classification** *without* **a** **clear** **context** **gain**—**sometimes** return **canonical** `err` **or** **map** to **new** **safe** error **at** **trust** **boundary**.

**Visualize it:**

```
  OK to wrap:   db.Query + user action context
  Skip wrap:    password wrong -> log generic "unauthorized" only
```

**Key facts**

- **Auth**—return **`ErrUnauthorized`**, **log** **reason** **server**-side. **Client**—**no** **“user 1234”** in **string**.  
- **When** the **child** is **already** **fully** **contexted** and **one** more **string** is **redundant** **—** return **as-is** or **join** with **structured** **logging** only. **See** **[[T09 Error Handling Patterns]]** **policy** table.

**Interview tip** — Cite **security** and **SRE** **noise**—two different **mature** **angles**.

> [!example]- Full Story: Wrapping **grpc** / **status** **errors
>
> **The problem** — gRPC `status` already carries a code, message, and **details** protos; wrapping the same `status.Error` ten times in `fmt.Errorf` only adds log noise. Prefer `status.FromError`, attach typed details at the gRPC edge, and map once to your HTTP/JSON contract.

---

## Q12: How does **`errors.Is` handle** **wrapped** error **chains**? [COMMON]

**In one line:** `Is` **compares** the **error** to **the** **target** **using** a **defined** **algorithm**—first **equals**, then **Unwrap** **recursion**; if **target** has **`Is` method**, that **can** **participate**—it **stops** when **a** **match** is **found** or **chain** **ends**.

**Visualize it:**

```
Is(err, T):
  for cur := err; cur != nil; cur = Unwrap(cur) {
      if is(cur, T) { return true }   // abstract "match"
  }
  return false
```

**Key facts**

- **Exact** **algorithm** in **`errors`** **source** (Go 1.13+); **know** “**unfold** + **test** at **each** **step**” **in** **interview**. **Sentinel** **at** **bottom** of **deep** `fmt.Errorf` **stack** is **findable** because **`%w`**.  
- If **`Is`** **is** **false** **but** **string** **contains** **EOF**, you **forgot** **`%w`**.

**Interview tip** — **Contrast** with **`As`**: `Is` **stops** at **value** **match**; `As` **needs** **type** **slot** **to** **fill**.

> [!example]- Full Story: Custom **Is** on **sentinels** **and** **`fmt`**
>
> **The problem** — **`url.Error`** and **other** **types** **override** **behavior**—`Is(ErrFileClosed)` **across** **types** is **subtle**; **rare** **interview** follow-up. **Rely** on **doc**+**`go doc errors.Is`**.

---

## Quick index

| # | Topic | Tag |
|---|--------|-----|
| 1 | Philosophy | COMMON |
| 2 | Is vs As | COMMON |
| 3 | %w | COMMON |
| 4 | Sentinel vs custom | COMMON |
| 5 | %w vs %v | TRICKY |
| 6 | Typed nil | TRICKY |
| 7 | REST | ADVANCED |
| 8 | panic | COMMON |
| 9 | errors.New | TRICKY |
| 10 | Custom + As | COMMON |
| 11 | When not wrap | ADVANCED |
| 12 | Is + chain | COMMON |

**Related** — **[[T09 Error Handling Patterns - Simplified]]** · **[[T09 Error Handling Patterns - Visual Map]]** · **[[T09 Error Handling Patterns - Revision]]** · **[[T09 Error Handling Patterns - Exercises]]**
