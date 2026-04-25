# T12: Interface Design Principles — Interview Questions

> Practice deck for **[[T12 Interface Design Principles]]** — 12 items, C+D Layered Accordion. Open **Full story** for depth.

**Legend:** [COMMON] = bread-and-butter. [TRICKY] = scope / judgment. [ADVANCED] = design and systems.

---

## 1. "What does 'accept interfaces, return structs' mean?" [COMMON]

**In one line:** Functions should **take** flexible interface parameters but usually **return** concrete types.

**Visualize (ASCII):**

```text
func Process(r io.Reader) *Result
             ^                    ^
        accept interface      return struct
```

**Key facts:** Default keeps **callers** decoupled from a single type while return types stay **clear**; return an interface when you **deliberately** hide multiple impls (factories, plugin boundaries).

**Interview tip:** Pair with a **when to break the rule** (e.g. `io.Reader` as return for abstraction).

<details>
<summary>Full story</summary>

"Accept interfaces" means your **function parameters** describe **capability** (`io.Reader`, `Storer`, `http.RoundTripper`) so callers can pass `*os.File`, `*bytes.Buffer`, fakes, etc. "Return structs" means **constructors and most APIs** return `*Service`, not `IService`—callers get auto-completion, zero-value semantics, and you avoid over-abstraction. Exceptions: returning a **small std interface** (`io.ReadCloser`) or **hiding** several implementations behind one type when that is the product boundary. Ties to **[[T12 Interface Design Principles]]**: small contracts at the edge, concretes in the middle.
</details>

---

## 2. "What is interface pollution and how do you avoid it?" [COMMON]

**In one line:** **Pollution** is forcing wide, bloated dependencies that callers do not use; you avoid it with **small, consumer-scoped** interfaces and restraint.

**Visualize (ASCII):**

```text
Polluted:   handler --> [ MEGA: A B C D E F G H I J ]
Clean:      handler --> [ Reader: A B ]  +  (elsewhere) [ Writer: C ]
```

**Key facts:** Huge interfaces complicate **mocks** and **refactors**; split by **role**, define near **use**, do not "future-proof" with ten unused methods.

**Interview tip:** Name a **concrete** smell (e.g. every test stub implements 20 methods) and the fix (**split** interfaces).

<details>
<summary>Full story</summary>

**Interface pollution** shows up as **wide** types imported everywhere, **fake** types that must implement rarely used methods, and changes that **break** all tests when one tangential method moves. It often comes from **premature** extraction ("we might need a cron job later, so the interface has `RunCron`"). **Avoid** by: (1) **YAGNI** on methods; (2) **consumer-defined** slices of behavior; (3) **compose** small interfaces; (4) re-evaluate when a second **real** implementation appears. This is a core **[[T12 Interface Design Principles]]** theme.
</details>

---

## 3. "Why should interfaces be small in Go?" [COMMON]

**In one line:** **Small** interfaces are easier to **implement**, **mock**, and **evolve** without breaking unrelated code.

**Visualize (ASCII):**

```text
io.Reader:   Read(p []byte) (n int, err error)   --> one job
vs
GodIface:   15 methods  --> 15 reasons to break callers
```

**Key facts:** Go favors **composing** `Reader` + `Writer` + `Closer` over one **mega**-interface; `io` package is the idiom in the stdlib.

**Interview tip:** Cite **`io.Reader`** or **`fmt.Stringer`** as canonical **one-method** types.

<details>
<summary>Full story</summary>

**Small** interfaces mean each **satisfier** is trivially substitutable, tests pass **fakes** with one method, and **refactors** touch only **relevant** call sites. Large interfaces are **cognitive** and **versioning** bottlenecks: every new method is a **breaking** or **trivial** implement burden. **[[T12 Interface Design Principles]]** pushes **role-based** small surfaces over a single "application interface."
</details>

---

## 4. "Where should interfaces be defined — at the producer or consumer?" [COMMON]

**In one line:** Often at the **consumer** (the package that **needs** the behavior); the producer’s concrete type **implicitly** satisfies it.

**Visualize (ASCII):**

```text
[ user-api ]  defines  type Lister interface { List() }
     |
     +-------- uses ----->  *sqlrepo.Repository (in db package, no Lister in its API)
```

**Key facts:** **Producer**-defined is fine for **reusable** library contracts (`io.Reader`); **app** code usually defines the **thinnest** local interface.

**Interview tip:** Contrast with Java `implements` on the **class**; Go inverts the relationship.

<details>
<summary>Full story</summary>

**Consumer-defined** keeps interfaces from **bloating** a library to satisfy one app. The **DB** package exports `*Repo` with real methods; the **HTTP** layer defines `type UserSource interface { GetUser(...) }` and takes that in the constructor. The concrete `*sql.Repo` **never** imports the HTTP package. **Producer-defined** is appropriate for **public** APIs (stdlib, shared SDK) where the **interface** *is* the product. For **[[T12 Interface Design Principles]]**, default to "define where you use" unless you are publishing a library.
</details>

---

## 5. "How does Go's implicit interface satisfaction differ from Java?" [COMMON]

**In one line:** Go **structurally** matches methods—**no** `implements` keyword; Java **nominally** requires declared implementation of a **named** type.

**Visualize (ASCII):**

```text
Go:    type T struct{} ; func (T) Foo()  --compiles-->  var i I = T{}  if I needs Foo
Java:  class T implements I { ... }  // explicit at declaration
```

**Key facts:** **Duck** typing with compile-time checks; **decoupling** of packages without redeclaration on the concrete type.

**Interview tip:** Mention **"if it walks like a duck"** and **test doubles** with zero ceremony.

<details>
<summary>Full story</summary>

**Java** ties a class to an interface in **source** (`implements`); the compiler checks at **declaration**. **Go** only asks: "Does this value have the **right method set**?" That enables **adapters** and **mocks** in the **test** or **client** package without **touching** third-party code. It also means **accidental** satisfaction is possible (same method names) — a reason to use **clear** method names. Central to **[[T12 Interface Design Principles]]** and **consumer-defined** edges.
</details>

---

## 6. "When should you NOT create an interface?" [TRICKY]

**In one line:** When there is **no** second implementation or **test seam** need—**YAGNI**—or the API is still **in flux**.

**Visualize (ASCII):**

```text
create interface?  -- single concrete + stable + need fake?  --> no / wait
                     -- or churning every sprint?  --> wait
```

**Key facts:** **Concretes** in internal packages are fine; **abstraction** is for **boundaries**; **`any`** is not a substitute for a **designed** contract.

**Interview tip:** Say you **revisit** when the **second** use case or **hard** test appears.

<details>
<summary>Full story</summary>

**Do not** create an interface to "look OOP" or to match another language’s patterns. **Do not** extract when only **one** type exists and tests use **real** dependencies acceptably (integration-style). **Do not** freeze an interface while method signatures **churn** weekly—you will break **fakes** and **importers** for no gain. **Do** use a concrete struct until a **seam** (mock, alternate impl) is real. This is the "when not" column of **[[T12 Interface Design Principles]]** (see also revision / visual map).
</details>

---

## 7. "How do you use interfaces for dependency injection in Go?" [COMMON]

**In one line:** **Inject** small dependencies through **constructors** (`New` **functions) as** interface-typed (or **concrete**) fields; build the graph in **`main`** and tests.

**Visualize (ASCII):**

```text
main:   repo := newSQLRepo() ; s := app.NewService(repo)
                                          ^
                              Service depends on *interface* (or *Repo) field
test:   s := app.NewService(fakeRepo{})
```

**Key facts:** **No** heavy DI **frameworks** required; **table-driven** tests swap **fakes**; same pattern for **config** and **clocks** (`Time` interfaces).

**Interview tip:** Mention **constructor injection** over **global** state.

<details>
<summary>Full story</summary>

**Dependency injection** in Go is usually **manual**: `func New(s Storage, c Clock) *App { return &App{store: s, clock: c} }`. The **`Storage`** or **`Clock`** type is a **small** interface. **Wire** in **production** with real `SQL` and **system** clock; in **unit tests**, pass `MemoryStorage` and **fake** time. **Interface**-typed fields document **seams**; **[[T12 Interface Design Principles]]** pairs this with **accept interfaces** and **testing** benefits.
</details>

---

## 8. "What is interface composition? Give an example." [COMMON]

**In one line:** **Composition** = embedding or listing **smaller** interfaces in a **bigger** one: `A` = `B` + `C`.

**Visualize (ASCII):**

```text
type ReadCloser interface {
    Reader
    Closer
}
// same as Reader's methods + Closer's methods, one type can satisfy both
```

**Key facts:** `io.ReadCloser` is the classic example; **avoid** re-listing `Read` when you embed `Reader`.

**Interview tip:** Contrast with **struct** embedding (different concept) in one **sentence** if asked.

<details>
<summary>Full story</summary>

**Interface composition** builds **larger** contracts from **smaller** ones without duplicating method lists. The **std** `io` package composes `Reader`, `Writer`, `Closer` into `ReadWriteCloser`, `ReadSeeker`, etc. A `*os.File` **satisfies** many because it has a **broad** method set, but each **function** can still only **require** `io.Reader` where that is the **true** need. Ties to **[[T12 Interface Design Principles]]**: **small** first, **compose** for wider needs, avoid **one** 20-method "everything" type.
</details>

---

## 9. "How do interfaces help with testing in Go?" [COMMON]

**In one line:** You **replace** real IO/DB/HTTP with **fakes** that satisfy the same **small** interface your code already accepts.

**Visualize (ASCII):**

```text
prod:   Handler --> *RealAPIClient
test:   Handler --> *stubAPI{ returns canned JSON }
                    (both satisfy HTTPDoer or your narrow interface)
```

**Key facts:** **Table-driven** + **fakes**; keep interfaces **as small as the unit under test** needs.

**Interview tip:** Say **"test double"** and **"narrow surface"** in the same answer.

<details>
<summary>Full story</summary>

If **constructors** take **`PaymentGateway`** with **one** method `Charge`, tests pass **`fakeGateway`** that records **calls** and never hits Stripe. If you passed `*RealClient` **concretely**, you would need **network** or **httptest** servers for every test. **Interfaces** (when **not** overused) are **seams** for **determinism** and **speed**. This is a primary **why** in **[[T12 Interface Design Principles]]** for defining interfaces.
</details>

---

## 10. "What's wrong with using empty interface (any) everywhere?" [TRICKY]

**In one line:** **`any`** erases **type information**; you lose **compiler** help and push **assertions** to **runtime**.

**Visualize (ASCII):**

```text
func F(v any)     vs     func F(r io.Reader)
        |                        |
  reflect / panic path           compile-time contract
```

**Key facts:** Use **`any`** for **generic** data (JSON decode targets, `Println`-style) not for **domain** **dependencies**; prefer **concrete** or **small** **named** interfaces.

**Interview tip:** Mention **`interface{}` vs `any`** = **alias** only (Go 1.18+), same **problem**.

<details>
<summary>Full story</summary>

`any` is **`interface{}`**: every value can go in, **nothing** is guaranteed out without **type switches** and **type assertions** that can **panic**. It **hides** bugs until **run time**. For **APIs** that should be **testable** and **documented**, you want **`DoThing(r io.Reader)`** or **`Storer`**, not **`DoThing(v any)`**. Reserve **`any`** for **truly** heterogeneous containers or **API** boundaries (e.g. `map[string]any` for JSON) with **careful** validation. **[[T12 Interface Design Principles]]** is about **intentional** contracts, not **erasure**.
</details>

---

## 11. "How would you design a pluggable storage layer using interfaces?" [ADVANCED]

**In one line:** Define a **narrow** `Storage` (e.g. `Get` / `Set` / `Delete`), **implement** in-memory and file (or S3) structs, **inject** via **`New`**, **swap** in `main` and tests.

**Visualize (ASCII):**

```text
      Storage interface
           /    \
  MemoryStore   FileStore   (or S3Store)
         \      /
          \    /
         App in main: NewApp(NewMemory()) / NewApp(NewFile(dir))
```

**Key facts:** **Errors** and **context** in signatures; **optional** `Close` if needed; **integration** test each impl.

**Interview tip:** Walk **accept interfaces, return structs** and **one** test **per** impl with shared **helper**.

<details>
<summary>Full story</summary>

**Design** `Storage` with only operations the **app** **actually** needs—avoid **copy-pasting** a cloud SDK’s entire surface. **Each** `Memory`, `File`, `S3` type **implements** the same **three** methods. **App** and **HTTP** handlers **depend on** `Storage`, not `*S3Client`. **Wire** in **`main`**: `store := newFileStorage(path)`; tests use `newMemoryStore()`. **Swapping** is a **one-line** `main` change. Optional: **wrap** for **caching** or **metrics** (decorator with same `Storage` interface). See exercises in **[[T12 Interface Design Principles]]** (Tier 3) for a hands-on match.
</details>

---

## 12. "What's the difference between a fat interface and a role interface?" [ADVANCED]

**In one line:** A **fat** interface bundles many **unrelated** concerns; a **role** interface is **small** and named for **one** behavior a caller needs.

**Visualize (ASCII):**

```text
Fat:     ┌────────────────────────────────────┐
         │  DoA DoB DoC DoD DoE (everything)  │
         └────────────────────────────────────┘
Role:    [Reader] [Writer] [Notifier]  ... compose at use site
```

**Key facts:** **Role** = **Interface Segregation** in practice; **fat** = **pollution** and **fake** bloat; **refactor** by **splitting** along **call** patterns.

**Interview tip:** Map **"role"** to **"consumer-defined slice"** of a larger concrete type.

<details>
<summary>Full story</summary>

A **fat** `Repository` with **fifteen** methods forces every **handler** to depend on **fifteen** even when it only **reads** two **query** results. A **role** design exposes **`UserReader`**, **`UserWriter`**, **`AuditLogger`**—often **in** the packages that use them. The same **`*db.Repository`** struct **satisfies** all of them **at once**; **structural** typing makes this **cheap**. The **concrete** type stays **fat**; the **interface** is **not**. That is the heart of **[[T12 Interface Design Principles]]** vs. **"one `IDatabase` to rule them all`."**
</details>

---

## Map back

Topic hub: **[[T12 Interface Design Principles]]** · Simplified: `../simplified/` · Exercises: `../exercises/` · Revision: `../revision/` · Visuals: `../visuals/`
