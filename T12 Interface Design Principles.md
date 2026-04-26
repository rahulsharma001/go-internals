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

**Small interfaces, defined by whoever calls the shots.** Keep **one or two methods** in most local interfaces, put the **type** where the need is written, and do not mint an interface in advance for testing or for flexibility before a second real implementation exists. **Interface pollution** is the most common design mistake for people who learned stacks where large **nominal** interfaces and heavy DI wiring are normal. Teams coming from `Java` or C#-style class hierarchies often import the same *shape-first* habit into Go. The symptom is huge provider-owned types that force every test to **fake a whole department** when a **reception desk** was enough. **The fix is the same in production and in tests: narrow the question.**

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

```
Before (fat mock):
  test ⇄  [ 15 method holes you must "plug"  ]

After (consumer 2-method interface at call site):
  test ⇄  [ Get ][ Update ]  = 2 method holes only

  production *user.Service struct may still have 15 methods
  the test and handler *declare* the 2-line contract they need
```

The **concrete** `UserService` in `user` can stay **one** big struct. The **test** and the **HTTP handler** only **import** the **sliver** of behavior they use.

> **In plain English:** A **dishwasher** manual does not list every **wrench** in the city. The manual lists **inlet hose thread** and **voltage slot**. The **wrench set** in your garage is still **huge** — the **dishwasher** just names **the two threads** it **actually screws into**.

---

## 4. How It Actually Works (Internals) [INTERMEDIATE → ADVANCED]

> **In plain English:** **blueprints** live on the **builder’s** desk, but the **key blank** is cut to match the **lock you already mounted** in the **door** you actually open every day.

### 4.1 Accept interfaces, return concrete structs

**Public** APIs that **return** a **named struct** make **callers** free to use **concrete** fields and **static** help from the type checker. **Parameters** and **struct fields** that must stay **pluggable** take **the smallest** interface the **callee** uses.

```go
type Cache struct{ store map[string]int }

// Return concrete — callers can see Cache is a struct, extend later.
func NewCache() *Cache {
	return &Cache{store: make(map[string]int)}
}

// Accept io.Writer — the Callee only needs Write.
type Logger struct{ w io.Writer }

func NewLogger(w io.Writer) *Logger { return &Logger{w: w} }
```

```
Constructor returns:
  *Cache  ──▶  concrete type in caller's hand (fields visible at compile time if exported)

Parameter accepts:
  w io.Writer  ──▶  any type with Write([]byte)(int,error) matches at compile time
                 no "implements" line — the method set is the proof
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

```
Reader:     [ Read ]
Writer:     [ Write ]
Stringer:   [ String ]

  interview story:  "I build interfaces like stickers — one verb per sticker"
```

> **In plain English:** A **stove knob** is **"hot / off"**. A **separate** knob is **"timer"**. The **kitchen** does not ship one **"mega-knob"** with **dozen** rings unless you are buying a **spaceship** — and even then, **one knob, one job** is easier to fix at 2 a.m.

### 4.3 Interface composition

**Embed** one interface in another. **`io.ReadWriter`** is **`Reader` + `Writer`**, not a **third** list of ad-hoc method names. **Composition** lets you build **"need both"** without inventing a **new** long **interface** for every **pairing**.

```go
type ReadWriter interface {
	Reader
	Writer
}
```

```
ReadWriter
   ┌────────────┐
   │  Reader   │
   ├────────────┤
   │  Writer   │
   └────────────┘

  concrete *bytes.Buffer:  has Read, Write, -> satisfies ReadWriter
```

> **In plain English:** A **duffel** with **"carry strap"** and **"zip top"** is two **patches** sewn on, not a **mystery bag** you cannot describe without **reading the entire luggage museum**.

### 4.4 Consumer-defined interfaces (point of use)

**Define the interface in the file that needs it**, or in a **small** test helper file. If **Package A** calls **only** `Log`, the **one-method** `Logger` in **Package A** is the **right** `Logger`. The **huge** logging library does **not** have to own your **3-line** `interface` **unless** the **entire** org shares one **on purpose**.

```go
// a/api.go
package a

import "context"

// Consumer-owned — names exactly what a.Server needs
type userLookup interface {
	ByID(ctx context.Context, id int64) (string, error)
}

type Server struct {
	Users userLookup
}
```

```
Producer package "users"  ──concrete *Repo──▶  has many methods
Consumer package "a"      ──interface userLookup (1 method)──▶  only sees ByID
```

> **In plain English:** A **cafe** menu board lists **"oat milk available"** because **this** **cafe** **steams** drinks. The **oat farm** does not ship a **300-page** **"approved cafe manifesto"** to every **corner shop**.

### 4.5 Dependency injection (DI) via constructor parameters

**DI (dependency injection)** here means you build your struct with values passed in. Often those values are **interfaces** for seams you swap in tests or in config-driven code. A `NewServer(deps...)` that takes `DB` and `Log` as interfaces is normal Go shape. No framework is required. The interface width is still driven by the struct you are constructing, not by every interface in the dependency tree.

```go
type Store interface {
	Save(ctx context.Context, k string, v int) error
}

type App struct{ s Store }

func NewApp(s Store) *App { return &App{s: s} }
```

```
main / test
   │
   ├─▶ concrete *diskStore   ─┐
   └─▶ fake in-memory        ─┴──▶  both satisfy Store when Save matches
         │
         └──▶  NewApp(store)  wraps interface field *inside* App
```

> **In plain English:** A **suit** **order form** has **"chest"** and **"inseam"** lines. The **tailor** **does not** measure **shoe size** on the same page — unless **this** order **involves** shoes. **The form** matches **this** **fitting**.

---

## 5. Key Rules & Behaviors

### Rule 1: Keep interfaces to one or two methods — the "smaller is better" rule

**Why:** Every method in an interface is a promise you must keep. Third parties and mocks pay per method in noise. Each new method you add is another stub line in every fake.

```go
// Good local shape: one verb
type Notifier interface {
	Notify(ctx context.Context, msg string) error
}
```

```
Notifier
   [ Notify ]

  vs fat local interface
   [ A ][ B ][ C ][ D ]...  <- each letter is a future mock line item
```

> **In plain English:** A **thermostat** has **"target temp"** and **"hold"** — it does **not** have **"also reorder furnace filters"** on the same **dial** unless you are building **comedy** hardware.

---

### Rule 2: Define interfaces where they are consumed, not where they are implemented

**Why:** The file that calls a method knows which names sit on this hot path. The implementation file may sprawl. Pull the contract to the call site so the contract matches reality.

```go
// consumer: checkout/service.go
type payer interface {
	Charge(ctx context.Context, cents int64) error
}
```

```
checkout owns "payer"
  callers see:  [ Charge only ]

payments owns BigStripeClient with 20 methods
  checkout does not re-export all 20 as one interface
```

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

```
today:
  *PriceBook  (only implementation)

  interface { ... }  with one impl  ->  indirection, no second branch yet

after second impl appears:
  two concrete types, same small method set
  -> now an interface is justified at call sites
```

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

```
NewReporter returns:  *Reporter  (concrete, stable name)
 NewReporter takes:   io.Writer   (any writer works)
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

```
ReportJob = Job + Report  (two stickers, not one unlabeled blob)

  [ Do ]  +  [ Title ]
```

> **In plain English:** A **camping** **tool** is **knife** **plus** **bottle opener** **plus** **scissors** in **one** **handle** — you still **name** the **parts** you **bought** — you do **not** call it **"black metal mystery"** **unless** you are **hiding** **something**.

---

## 6. Code Examples (Show, Do not Tell)

### Example A: Consumer-defined interface for tests — mock only what you need

**Trap:** you import the provider's huge exported `interface` and stub the whole surface. **Fix:** a two-method or one-method interface in the test file or the package under test. List only what the code under test calls on this path.

```go
// service_test.go
type readID interface {
	ByID(ctx context.Context, id int) (string, error)
}
```

```
test-defined readID:  [ ByID only ]

  SUT  ──▶  readId impl (fake)  with one method
  real DB still has 40 methods; test never mentions them
```

> **In plain English:** A driving exam only checks parallel park and a stop sign on this route. The whole vehicle manual is not the page on the examiner's clipboard.

### Example B: Interface composition — `io.Reader` + `io.Writer`

```go
var rw io.ReadWriter
rw = new(bytes.Buffer) // *bytes.Buffer is both Reader and Writer
_ = rw
```

```
*bytes.Buffer
  satisfies Reader  ──Read
  satisfies Writer  ──Write
  satisfies ReadWriter  (embedded pair, still two one-method ideas)
```

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

**Design** a **pluggable** **storage** **layer** with an **in-memory** **map** and a **file-backed** **JSON** file. The **app** should **see** a **small** **`Store` interface** with **Get** and **Set**. The **main** should **construct** the **concrete** **type** and **pass** it to **`NewService`**. **Tests** use the **in-memory** **impl** only. **No** **global** **singletons**.

> Full solutions with explanations → [[exercises/T12 Interface Design Principles - Exercises]]

---

## 7. Edge Cases & Gotchas

| Gotcha | What goes wrong | Fix |
|--------|----------------|-----|
| Interface pollution | Giant local or exported interface; mocks and adapters multiply | Chisel to one or two methods at use sites; compose the rare union only when needed |
| Empty interface abuse | `any` everywhere; readers lose the static story | Return concrete types; reserve `any` for real boundaries such as encoding or plugin ABI, not internal helpers |
| Exporting interfaces early | You freeze a shape before you know the real call patterns | Keep narrow interfaces unexported until repeated call sites prove the same slice of surface |
| Pointer to interface | `*io.Reader` is almost never what you want; indirection gets fuzzy | Pass `io.Reader` or a concrete pointer; avoid `*SomeInterface` unless a rare API truly requires it |

> **In plain English:** A giant master key ring jangles and tears pockets. A small ring for home and a separate ring for office is boring, and boring is cheaper to lose in a couch cushion hunt.

---

## 8. Performance & Tradeoffs

| Question | What happens | When it matters |
|----------|--------------|-----------------|
| Implicit satisfaction | No `implements` keyword at runtime. The compiler proves method sets match. That proof is static. | Good interview line: structural match is a **compile-time** check, not a ceremony you pay for on every line of code as if you hand-wrote a foreign vtable. |
| Storing a value in an interface-typed variable | A non-empty interface with methods uses the runtime **iface** pair: two words. The first time a given interface type meets a given concrete type, the runtime may build one **itab** and reuse it. **itab** is the cached interface table from T11. See [[T11 Interface Internals (iface & eface)]]. | Hot loops that re-box concrete values into an interface each iteration can add work. Measure with the **pprof** profiler if you suspect it. |
| Dynamic dispatch | Calls through an interface use **itab** function slots. | Tight inner loops on one concrete type sometimes keep a concrete type in the API on purpose to help the compiler inline. |

**Decision check** — is this line a seam or a guess?

1. Will a second real implementation exist soon? If no, stay concrete.
2. Is the consumer file the only place that names these methods? If yes, the interface belongs next to that code.
3. Does the mock feel huge? If yes, the interface is too wide. Read the call graph again.

> **In plain English:** A luggage tag is light. A full costume wardrobe on each suitcase is heavy to roll through the airport. Keep each flight’s abstraction load small.

---

## 9. Common Misconceptions

| Misconception | Reality |
|---------------|---------|
| "Go has no polymorphism" | Go has **ad-hoc polymorphism** through small interfaces and structural typing. No class inheritance tree is not the same as no polymorphism. |
| "SOLID means interfaces on every return" | The **interface segregation** idea in Go usually means **split big files** and **name small behaviors** at the call site, not blanket interface types. |
| "A bigger interface is more flexible" | A bigger interface locks more callers into one contract. Smaller composed pieces swap more cleanly. |
| "We can add the interface later for free" | Later still means refactors across call sites. Budget the work honestly. |

---

## 10. Related Tooling & Debugging

| Tool | Relevance to interface design |
|------|------------------------------|
| `go doc` on a standard interface | See which concrete types in a package document that they satisfy common interfaces. |
| gopls "find implementations" | Prove a concrete type matches a small local interface you introduced. |
| staticcheck | Flags some stale or suspicious patterns in older code; rules vary by project lint config. |
| `go test -bench` with **pprof** | Turn "does this interface boundary in a hot loop cost me" into numbers. |

> **In plain English:** A magnifying glass does not fix the faucet. It shows which washer is the wrong size. Tools reveal shape. The design call is still yours.

---

## 11. Interview Gold Questions

### Q1: Why accept interfaces, return concrete structs?

**Nutshell answer:** Return a **stable** concrete name so documentation and static understanding stay easy. Accept the **weakest** interface only at the seam you really swap: time, I/O, storage. Do not thread huge interfaces into every leaf helper.

> **In plain English:** Ship a sealed box with a part number on the side. For loading the truck, accept any box that has a handle.

### Q2: Where do you define interfaces — producer or consumer?

**Nutshell answer:** Default to the **consumer** file that calls the methods. Move a shared name up to package scope only when several real call sites repeat the same two or three method lines on purpose.

> **In plain English:** The person who turns the lock names the key shape. The key blank factory still sells many shapes. The lock does not import the whole factory catalog on its faceplate.

### Q3: What is interface pollution? How do you fix it?

**Nutshell answer:** **Pollution** is a wide provider-owned contract that every test and adapter must fake whole. You fix it with one or two method interfaces at the point of use, plus composition of smaller standard-like pieces when you need more than one behavior.

> **In plain English:** A universal remote with eighty buttons in a room that only needs volume. Trade it for a volume knob. Store the rest in a drawer.

---

## 12. Final Verbal Answer

Interfaces in Go are **small** contracts you define **next to the code that needs them**, not a giant table owned by the implementation package. **Structural typing** means satisfaction is **implicit** at compile time. There is no `implements` line. The habit that wins interviews is **accept narrow interfaces, return named structs** so call sites and constructors stay legible. The smell is **interface pollution**: fat types that bloat every mock. The fix is the same every time. **Narrow the method set** to one or two verbs. **Define the interface** where you call those verbs. Compose bigger behavior from small pieces when you must, not from one kitchen-sink type.

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
