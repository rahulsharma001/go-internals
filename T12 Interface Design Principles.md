# T12 Interface Design Principles

> **Reading Guide**: Sections 1-3 and 6 are essential first read (20 min).
> Sections 4-5 deepen understanding (15 min).
> Sections 7-12 are interview-specific — read closer to interview day.
> Section 13 is your comprehensive interview Q&A bank → [[questions/T12 Interface Design Principles - Interview Questions]]
> Something not clicking? → [[simplified/T12 Interface Design Principles - Simplified]]

---

## 0. Prerequisites

Complete these before starting this topic:

- [[T11 Interface Internals (iface & eface)]]

---

## 1. Concept

**Interface design** in Go means you **name the thing you need at the call site** and you **ask for as little as possible**. A common phrasing: **accept interfaces, return concrete structs** — the **caller** states the **smallest** contract, and the **callee** returns a **type you can name** and **construct** without a registry of fake names. **Consumer-defined interfaces** live next to the code that **uses** them, not next to the big implementation file. **Structural typing** means **satisfaction** is **implicit**. The compiler checks **method sets** only. There is no **`implements` keyword** in the language.

> **In plain English:** The **lamp** owns the prong spec in its plug. The **outlet** is just a hole in the wall that matches. Nobody mails the lamp a 40-page *socket constitution* the week before the lamp ships.

---

## 2. Core Insight (TL;DR)

**Small interfaces, defined by whoever calls the shots.** Keep **one or two methods** in most local interfaces, put the **type** where the need is written, and do not mint an interface in advance for testing or for flexibility before a second real implementation exists. **Interface pollution** is the most common design mistake for people who learned stacks where large **nominal** interfaces and heavy DI wiring are normal. Teams coming from Java or C#-style class hierarchies often import the same *shape-first* habit into Go. The symptom is huge provider-owned types that force every test to **fake a whole department** when a **reception desk** was enough. **The fix is the same in production and in tests: narrow the question.**

> **In plain English:** A door lock wants **a key with one ridge pattern**. The factory that makes the key does not publish a **master list of 50 ridge jobs** the lock must learn. The lock **declares the ridge pattern** when the lock is installed.

---

## 3. Mental Model (Lock this in)

### The "power outlet" model

**Interfaces** are **shape contracts**. The **device** is the **consumer** — it says **what shape of plug** it can use. The **wall** is the **producer** — it exposes **metal in that shape** or it does not. You do **not** pre-install a **fifty-prong** wall plate **"just in case"** a future device might need a novel prong. You install the **smallest** plate that today’s gear actually uses.

> **In plain English:** A **kettle** needs **two prongs and ground**. A **phone charger** needs **USB-C**. The **house** does not try to be **a universal every-port museum**. The **kettle** does not read the **municipal wiring encyclopedia** — it just brings the **plug it has**.

### Mistake that teaches: producer-wins `UserService` with 15 methods

A team ships a **single** big interface next to a **concrete** type. The **type** in real life is one struct. The **interface** in the package header is **fifteen** methods. Tests that only care about `Get` and `Update` now **inherit** a mock that must stub **thirteen** extra methods, or a **mock generator** that **prints** a **novel**.

```go
// user/service.go — producer-defined fat interface
package user

type UserService interface {
	Register(ctx context.Context, u User) error
	Login(ctx context.Context, e, p string) (string, error)
	Get(ctx context.Context, id int64) (User, error)
	Update(ctx context.Context, u User) error
	SetPassword(ctx context.Context, id int64, p string) error
	VerifyEmail(ctx context.Context, token string) error
	List(ctx context.Context, page int) ([]User, error)
	Delete(ctx context.Context, id int64) error
	// ... 7 more methods in real life, omitted here
}

// handler/handler_test.go
type mockUserService struct{}

func (m *mockUserService) Register(ctx context.Context, u user.User) error {
	panic("not needed in this test but interface forces stub")
}
// ... 14 more method bodies you must type or generate
```

```
Step 1:  Test only needs:  Get, Update
         Fat interface needs: 15 method slots satisfied

  test brain:  [ use Get ] [ use Update ]  (2 slots)

  mock you write:
    Register   ──▶  panic/empty  (1)
    Login      ──▶  panic/empty  (2)
    Get        ──▶  real         (3)  <-- the only one you wanted
    Update     ──▶  real         (4)  <-- and this
    SetPass... ──▶  panic/empty  (5)
    ... 10 more  ──▶  noise      (6..15)  <-- dead weight, always present

  reader cost:  scroll past 15 screens of boiler
  merge pain:  every new service method = break every mock
```

**Refactor: consumer-defined two-method interface in the test file**

```go
// handler/handler_test.go
package handler

import "context"

// Only what this handler path calls — 2 methods, not 15
type userReadWriter interface {
	Get(ctx context.Context, id int64) (user.User, error)
	Update(ctx context.Context, u user.User) error
}

type fakeUsers struct{ got user.User }

func (f *fakeUsers) Get(ctx context.Context, id int64) (user.User, error) {
	return f.got, nil
}
func (f *fakeUsers) Update(ctx context.Context, u user.User) error {
	f.got = u
	return nil
}
```

After the refactor, the test only **plugs two holes**; production’s concrete struct can still ship all fifteen methods — the handler and test just **declare the slice they touch**.

The **concrete** `UserService` in `user` can stay **one** big struct. The **test** and the **HTTP handler** only **import** the **sliver** of behavior they use.

> **In plain English:** A **dishwasher** manual does not list every **wrench** in the city. The manual lists **inlet hose thread** and **voltage slot**. The **wrench set** in your garage is still **huge** — the **dishwasher** just names **the two threads** it **actually screws into**.

### Two more seams you will actually see

**gRPC stubs.** Generated **`FooServer`** / client types list **every** RPC. Server code embeds **`pb.UnimplementedFooServer`** so a new RPC does not brick your build while you implement it one handler at a time. Handlers that **call** gRPC should not import that whole surface: define a **narrow port** beside the caller (for example `CreateHold(ctx, orderID string) (holdID string, err error)`) and let a **small adapter** in `infra/grpc` speak protobuf. Your two-line interface stays stable; the fat stub stays behind one door.

**`time.Now` and `Clock`.** Production wants real wall time; tests want **Tuesday at 3pm** every run. Swap the seam with a **one-method interface** instead of monkey-patching globals:

```go
type Clock interface {
	Now() time.Time
}

type systemClock struct{}

func (systemClock) Now() time.Time { return time.Now() }

type frozenClock struct{ t time.Time }

func (f frozenClock) Now() time.Time { return f.t }
```

Pass a `Clock` into anything that timestamps orders or tokens. `main` uses `systemClock{}`; tests use `frozenClock{t: fixed}`. Same code path, **no** flaky midnight edge cases. Narrow `Clock` ports show up constantly because **time is never “just a detail.”**

---

## 4. How It Actually Works (Internals) [INTERMEDIATE → ADVANCED]

> **In plain English:** **blueprints** live on the **builder’s** desk, but the **key blank** is cut to match the **lock you already mounted** in the **door** you actually open every day.

### 4.1 Accept interfaces, return concrete structs

**Public** APIs that **return** a **named struct** make **callers** free to use **concrete** fields and **static** help from the type checker. **Parameters** and **struct fields** that must stay **pluggable** take **the smallest** interface the **callee** uses.

```go
type Session struct {
	UserID    int64
	ExpiresAt time.Time
}

// SessionCache is concrete — callers see a named struct, not a mystery bag.
type SessionCache struct {
	items map[string]*Session
}

func NewSessionCache() *SessionCache {
	return &SessionCache{items: make(map[string]*Session)}
}

func (c *SessionCache) Get(key string) (*Session, error) {
	s, ok := c.items[key]
	if !ok {
		return nil, fmt.Errorf("session %q not found", key)
	}
	return s, nil
}

func (c *SessionCache) Set(key string, sess *Session) error {
	if sess == nil {
		return fmt.Errorf("session is nil")
	}
	c.items[key] = sess
	return nil
}

// Accept io.Writer — the callee only needs Write.
type Logger struct{ w io.Writer }

func NewLogger(w io.Writer) *Logger { return &Logger{w: w} }
```

> **In plain English:** A **carpenter** **hands you a finished chair** to sit in. A **carpenter** also asks only for a **"thing that can drive screws"** from your **junk drawer** — a **screwdriver** or a **power drill** both qualify.

### 4.2 Small interfaces — one method is normal

`io.Reader`, `io.Writer`, and `fmt.Stringer` are **famous** because each does **one** job. The **standard library** is the **canon**: **prefer** new interfaces that read like **a single line on a name tag**.

```go
type Reader interface {
	Read(p []byte) (n int, err error)
}

type Writer interface {
	Write(p []byte) (n int, err error)
}

type Stringer interface {
	String() string
}
```

Interview story you can steal: **“I build interfaces like stickers — one verb per sticker.”**

> **In plain English:** A **stove knob** is **"hot / off"**. A **separate** knob is **"timer"**. The **kitchen** does not ship one **"mega-knob"** with **dozen** rings unless you are buying a **spaceship** — and even then, **one knob, one job** is easier to fix at 2 a.m.

### 4.3 Interface composition

**Embed** one interface in another. **`io.ReadWriter`** is **`Reader` + `Writer`**, not a **third** list of ad-hoc method names. **Composition** lets you build **"need both"** without inventing a **new** long **interface** for every **pairing**.

```go
type ReadWriter interface {
	Reader
	Writer
}
```

`*bytes.Buffer` has both `Read` and `Write`, so it satisfies `ReadWriter` without a third invented method list.

> **In plain English:** A **duffel** with **"carry strap"** and **"zip top"** is two **patches** sewn on, not a **mystery bag** you cannot describe without **reading the entire luggage museum**.

### 4.4 Consumer-defined interfaces (point of use)

**Define the interface in the file that needs it**, or in a **small** test helper file. If **Package A** calls **only** `FindByID` on orders, the **one-method** `orderReader` in **Package A** is the **right** contract. The **Postgres** package does **not** have to own your **3-line** `interface` **unless** the **entire** org shares one **on purpose**.

```go
// a/api.go
package a

import (
	"context"
	"example/orders"
)

// Consumer-owned — names exactly what a.Server needs for this route
type orderReader interface {
	FindByID(ctx context.Context, id string) (*orders.Order, error)
}

type Server struct {
	Orders orderReader
}
```

The `orders` package can still ship a fat `*PostgresOrderStore`; **this** server only peeks through the `FindByID` keyhole.

> **In plain English:** A **cafe** menu board lists **"oat milk available"** because **this** **cafe** **steams** drinks. The **oat farm** does not ship a **300-page** **"approved cafe manifesto"** to every **corner shop**.

### 4.5 Dependency injection (DI) via constructor parameters

**DI** here means you build your struct with values passed in. Often those values are **interfaces** for seams you swap in tests or in config-driven code. A `NewCheckoutHandler(deps...)` that takes an `OrderStore` is normal Go shape. No framework is required. The interface width is still driven by the struct you are constructing, not by every interface in the dependency tree.

Your **`CheckoutHandler`** needs to **persist orders**. Do **not** pass it `*PostgresOrderStore` as the field type if the handler only calls `Save` and `FindByID`. Pass an **`OrderStore` interface** with exactly those methods. In **`main`**, wire `NewPostgresOrderStore(db)`. In **tests**, pass **`MockOrderStore`** (or a hand-written fake) that implements the same two lines. The handler stays dumb about whether Postgres, SQLite, or an in-memory slice backs the contract.

```go
type Order struct {
	ID         string
	TotalCents int64
}

// OrderStore is the seam — consumer-named, two methods, backend-shaped.
type OrderStore interface {
	Save(ctx context.Context, order *Order) error
	FindByID(ctx context.Context, id string) (*Order, error)
}

type CheckoutHandler struct {
	Orders OrderStore
}

func NewCheckoutHandler(store OrderStore) *CheckoutHandler {
	return &CheckoutHandler{Orders: store}
}
```

> **In plain English:** A **suit** **order form** has **"chest"** and **"inseam"** lines. The **tailor** **does not** measure **shoe size** on the same page — unless **this** order **involves** shoes. **The form** matches **this** **fitting**.

---

## 5. Key Rules & Behaviors

### Rule 1: Keep interfaces to one or two methods — the "smaller is better" rule

**Why:** Every method in an interface is a promise you must keep. Third parties and mocks pay per method in noise. Each new method you add is another stub line in every fake.

```go
// Good local shape: one verb, real backend job
type WebhookDispatcher interface {
	Dispatch(ctx context.Context, url string, body []byte) error
}
```

One verb on the contract means one stub line in a fake — not a whole alphabet of empty methods.

> **In plain English:** A **thermostat** has **"target temp"** and **"hold"** — it does **not** have **"also reorder furnace filters"** on the same **dial** unless you are building **comedy** hardware.

---

### Rule 2: Define interfaces where they are consumed, not where they are implemented

**Why:** The file that calls a method knows which names sit on this hot path. The implementation file may sprawl. Pull the contract to the call site so the contract matches reality.

```go
// consumer: checkout/service.go
type PaymentCapturer interface {
	Capture(ctx context.Context, paymentID string, cents int64) error
}
```

Checkout names **`Capture` only**; the payments package can keep a twenty-method client without exporting that whole surface through checkout.

> **In plain English:** A **table** in a **restaurant** lists **"tap water"** and **"sparkling"** for **this** **meal** — the **bottling plant** is **not** your **dinner** **menu** **author**.

---

### Rule 3: Do not create interfaces for a single implementation

**Why:** A type with no second real alternative is not a seam yet. A concrete struct is easier to read and to refactor. When a second implementation really appears, then extract the smallest interface from the call sites that duplicate the same two or three lines.

```go
// One prod implementation today — a struct is enough.
type PriceBook struct{ /* file-backed */ }

// Later, if two implementations exist, extract the shared surface then.
// type priceSource interface { QuoteUSD(code string) (decimal.Decimal, error) }
```

**Today** you might only have `*PriceBook` — that is not a crime. **After** a second real implementation shows up, extract the **shared** two-line surface at the call sites.

> **In plain English:** You **do not** buy a **spare** **car** **key** on **day one** of **owning** **one** **car** — you **copy** a **key** the **day** you get a **spouse** who also **drives** **or** the **day** you **lose** one.

---

### Rule 4: Accept interfaces, return concrete structs

**Why:** Return values you can name in package docs and tests with low surprise. Accept the weakest type that still solves the problem here. That is the intersection of every provider you are willing to plug in.

```go
func NewReporter(w io.Writer) *Reporter {
	return &Reporter{w: w}
}

type Reporter struct{ w io.Writer }

func (r *Reporter) Line(s string) { fmt.Fprintln(r.w, s) }
```

> **In plain English:** A **cafe** **hands you a branded cup** you can **refill** — the **cafe** still **pours** from **any** **carafe** that **pours** — **glass**, **metal**, **thermal**.

---

### Rule 5: Use interface composition instead of large interfaces

**Why:** A huge interface is one tight bundle. Compose smaller interfaces and use struct embedding in concrete types when you need both behaviors in one object, instead of minting a new fifteen-line interface type for one call.

```go
type Job interface {
	Do(ctx context.Context) error
}
type Report interface {
	Title() string
}
type ReportJob interface {
	Job
	Report
}
```

`ReportJob` is still **two named stickers** (`Do`, `Title`) — not a mystery blob with seven anonymous verbs.

> **In plain English:** A **camping** **tool** is **knife** **plus** **bottle opener** **plus** **scissors** in **one** **handle** — you still **name** the **parts** you **bought** — you do **not** call it **"black metal mystery"** **unless** you are **hiding** **something**.

---

## 6. Code Examples (Show, Do not Tell)

### Example A: Consumer-defined interface for tests — mock only what you need

**Trap:** you import the provider's huge exported `interface` and stub the whole surface. **Fix:** a two-method or one-method interface in the test file or the package under test. List only what the code under test calls on this path.

```go
// service_test.go
type sessionLoader interface {
	ByID(ctx context.Context, id string) (*Session, error)
}
```

The system under test talks to **`ByID` only**; the real session service can keep forty methods the test never imports.

> **In plain English:** A driving exam only checks parallel park and a stop sign on this route. The whole vehicle manual is not the page on the examiner's clipboard.

### Example B: Interface composition — `io.Reader` + `io.Writer`

```go
var rw io.ReadWriter
rw = new(bytes.Buffer) // *bytes.Buffer is both Reader and Writer
_ = rw
```

Same buffer, three satisfied interfaces — still built from **one-method** ideas glued together.

> **In plain English:** A **garden** **hose** **both** **sucks** and **blows** **if** the **pump** **supports** it — the **"hose contract"** is still **"fits thread A"** **plus** **"fits thread B"** **on** the **label**, **not** **a** **mystery** **tube**.

### Example C: Wrong way — producer-defined fat interface forces test bloat

See Section 3, **Mistake that teaches**, for the 15-method `UserService` story and the consumer-defined two-method fix. The moral fits on one screen. If mocks hurt, shrink the question the type asks, not the number of files in the implementation package.

---

## 6.5. Practice Checkpoint

**All** tasks run in the **Go Playground**: https://go.dev/play/

### Tier 1: Spot interface pollution (2 min)

Which **interface** lines look like **pollution**? Which look **fine**?

```go
type Doer interface{ Do() }

// package app
type DataLayer interface {
	Query() error
	Save() error
	Migrate() error
	Archive() error
	Reindex() error
}

// package handler
type SingleGetter interface{ Get(id int) string }
```

**Hint:** **Pollution** here means *many unrelated methods on one contract* with no evidence that every caller needs the full surface. **Single verb** or **single use** is usually **not** pollution.

> [!success]- Answer
> - `Doer` (1 method) -- **fine**. Small, focused, single-verb interface. Classic Go style.
> - `DataLayer` (5 methods) -- **pollution**. Five unrelated operations in one contract. No single caller likely needs all of them. Should be split: `Querier`, `Saver`, `Migrator`, etc. at the consumer site.
> - `SingleGetter` (1 method) -- **fine**. Consumer-defined, one method, named for exactly what the caller needs.

### Tier 2: Refactor a fat interface into consumer-defined narrow interfaces (5 min)

**Given** a **ten-method** `PlatformAPI` in **one** file, **list** the **one-line** **interfaces** you would place in **handler**, **sync**, and **billing** if each only calls **two** **methods** today. **Do** **not** **edit** the **concrete** **impl** **yet** — only **re-home** the **type** **declarations** as **an exercise in naming**.

> [!success]- Answer
> ```go
> // package handler -- only needs user lookup
> type UserFetcher interface {
>     GetUser(id int) (User, error)
>     ListUsers(filter Filter) ([]User, error)
> }
>
> // package sync -- only needs data sync
> type DataSyncer interface {
>     PullChanges(since time.Time) ([]Change, error)
>     PushChanges(changes []Change) error
> }
>
> // package billing -- only needs payment
> type PaymentProcessor interface {
>     Charge(userID int, amount Money) error
>     Refund(txID string) error
> }
> ```
> The concrete `PlatformAPI` struct in the `platform` package still has all 10 methods. Each consumer package defines only what it needs. Tests mock 2 methods, not 10.

### Tier 3: Build it (15 min)

**Design** a **pluggable** **order** **persistence** **layer** with an **in-memory** **map** and a **Postgres**-backed implementation. The **app** should **see** a **small** **`OrderStore` interface** with **`Save`** and **`FindByID`**. The **`main`** should **construct** the **concrete** **type** and **pass** it to **`NewCheckoutHandler`**. **Tests** use the **in-memory** **impl** only. **No** **global** **singletons**.

> Full solutions with explanations → [[exercises/T12 Interface Design Principles - Exercises]]

---

## 7. Edge Cases & Gotchas

**Interface pollution** — You exported a “kitchen sink” contract and now every mock repeats fifteen empty methods. The fix is boring: **chisel** the interface down to what **this** package calls, **compose** rare unions from small pieces, and let the fat concrete type live where it belongs.

**`any` sprawl** — If every helper takes `any`, readers cannot see the story at compile time. **Return concrete types** from your own packages. Keep `any` for real boundaries: JSON decode, plugin edges, generated glue — not for “I was too lazy to name a struct.”

**Exporting interfaces too early** — The moment an interface is public, strangers import it and you freeze a shape you barely understand. Keep **narrow** interfaces **unexported** until several call sites **repeat** the same slice of methods on purpose.

**Pointer to interface** — `*io.Reader` is almost never what you want; you end up explaining your program to the next reader twice. Pass `io.Reader` or a concrete `*bytes.Buffer`. Reach for `*SomeInterface` only when an API you do not control truly demands it.

> **In plain English:** A giant master key ring jangles and tears pockets. A small ring for home and a separate ring for office is boring, and boring is cheaper to lose in a couch cushion hunt.

---

## 8. Performance & Tradeoffs

**Implicit satisfaction** — There is no `implements` keyword at runtime. The compiler proves method sets match once, statically. Good interview line: structural matching is a **compile-time** proof, not a ceremony you re-enact on every call like hand-writing a foreign vtable.

**Storing a value in an interface-typed variable** — A non-empty interface with methods uses the runtime **iface** pair: two words. The first time a given interface type meets a given concrete type, the runtime may build one **itab** and reuse it. **itab** is the cached interface table from T11. See [[T11 Interface Internals (iface & eface)]]. Hot loops that re-box concrete values into an interface each iteration can add work — **pprof** turns that hunch into numbers.

**Dynamic dispatch** — Calls through an interface use **itab** function slots. In a tight inner loop on **one** concrete type, sometimes you keep a concrete type in the API on purpose so the compiler can inline.

**Decision check** — is this line a seam or a guess?

1. Will a second real implementation exist soon? If no, stay concrete.
2. Is the consumer file the only place that names these methods? If yes, the interface belongs next to that code.
3. Does the mock feel huge? If yes, the interface is too wide. Read the call graph again.

> **In plain English:** A luggage tag is light. A full costume wardrobe on each suitcase is heavy to roll through the airport. Keep each flight’s abstraction load small.

---

## 9. Common Misconceptions

Someone tells you **“Go has no polymorphism.”** That is the **nominal** brain speaking. Go has **ad-hoc polymorphism**: small interfaces, structural typing, swap implementations without a class tree. No inheritance is not the same as no polymorphism — it is **polymorphism without a family crest**.

Someone quotes **SOLID** and hears “interface on every return.” In Go, **interface segregation** usually means **split the fat file** and **name tiny behaviors at the call site**, not **wrap every constructor** in an abstraction you do not need yet.

Someone says **“a bigger interface is more flexible.”** In practice the opposite happens: a wide contract **locks every caller** into the same dozen methods. **Small** pieces **compose**; **big** slabs **don’t**.

Someone promises **“we can add the interface later for free.”** Later still means **touching call sites**, **updating tests**, and **arguing about names**. Budget that work the way you would budget a schema migration — honestly.

---

## 10. Related Tooling & Debugging

Use **`go doc`** on `io.Reader`-style interfaces to see how the stdlib advertises tiny behaviors, **gopls “find implementations”** to prove your test fake matches the two-line port you invented, **staticcheck** for stale patterns (per project config), and **`go test -bench` + pprof** when you suspect interface dispatch in a hot loop. Tools show **shape**; they do not choose your seams for you.

> **In plain English:** A magnifying glass does not fix the faucet. It shows which washer is the wrong size. Tools reveal shape. The design call is still yours.

---

## 11. Three answers worth memorizing

### Q1: Why accept interfaces, return concrete structs?

**Nutshell answer:** Return a **stable** concrete name so documentation and static understanding stay easy. Accept the **weakest** interface only at the seam you really swap: time, I/O, storage, outbound RPC. Do not thread huge interfaces into every leaf helper.

> **In plain English:** Ship a sealed box with a part number on the side. For loading the truck, accept any box that has a handle.

### Q2: Where do you define interfaces — producer or consumer?

**Nutshell answer:** Default to the **consumer** file that calls the methods. Move a shared name up to package scope only when several real call sites repeat the same two or three method lines on purpose.

> **In plain English:** The person who turns the lock names the key shape. The key blank factory still sells many shapes. The lock does not import the whole factory catalog on its faceplate.

### Q3: What is interface pollution? How do you fix it?

**Nutshell answer:** **Pollution** is a wide provider-owned contract that every test and adapter must fake whole. You fix it with one or two method interfaces at the point of use, plus composition of smaller standard-like pieces when you need more than one behavior.

> **In plain English:** A universal remote with eighty buttons in a room that only needs volume. Trade it for a volume knob. Store the rest in a drawer.

---

## 12. Final Verbal Answer

If someone asks me about interface design in Go, I’d tell them the whole thing is about **naming the smallest behavior you actually call** and putting that name **next to the code that calls it**. Interfaces are **not** a hierarchy game — satisfaction is **implicit**, there’s no `implements` line, and the compiler just checks method sets. The habit that keeps codebases sane is **accept narrow interfaces, return concrete structs**, so constructors and call sites stay readable. When tests hurt, it’s almost never “we need a bigger mock framework” — it’s **interface pollution**: a fat contract that makes you stub a whole department. The fix is the same in prod and in tests: **narrow the method set**, often to one or two verbs, and **compose** bigger behavior from small pieces when you truly need more than one sticker.

---

## 13. Comprehensive Interview Questions

> Full interview question bank → [[questions/T12 Interface Design Principles - Interview Questions]]

**Preview** — full layered answers live in the bank file above.

1. What is **structural typing**, and how does it differ from **nominal typing** you have seen in other ecosystems?
2. When is a new interface warranted versus a concrete struct only?
3. How do you compose interfaces? Name a standard library example besides `io.ReadWriter`.

Runtime shapes such as **iface**, **eface**, and **itab** are covered in [[T11 Interface Internals (iface & eface)]]. Term definitions live in [[Glossary]].

---

> See [[Glossary]] for term definitions.
