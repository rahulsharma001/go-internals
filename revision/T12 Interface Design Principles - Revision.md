# T12: Interface Design Principles — Revision

> 60-second scan for [[T12 Interface Design Principles]]. Use the grid, trace the flow once, then hit the quick-fire.

---

## Recall grid (10 rows)

| # | Topic | One phrase |
|---|--------|------------|
| 1 | **Accept interfaces, return structs** | Parameters accept *capabilities*; return concrete types unless you need to hide impls. |
| 2 | **Small interfaces** | Few methods per interface; easier mocks and clearer contracts. |
| 3 | **Consumer-defined** | Define the interface in the *package that uses* the behavior (often), not the producer’s mega-type. |
| 4 | **Interface pollution** | Bloated, unused methods on every import; over-abstracted “future-proof” fat APIs. |
| 5 | **Composition** | Build bigger behavior from small interfaces (`io.ReadCloser` = `Reader` + `Closer`). |
| 6 | **When NOT to use** | Single impl, no test seam, unstable API, or abusing `any` instead of a real contract. |
| 7 | **Structural typing** | No `implements` — a type satisfies an interface *if* it has the right methods. |
| 8 | **`io.Reader` and methods** | `Read([]byte) (n int, err error)`; `EOF` means normal end, not always an “error” in the bad sense. |
| 9 | **Dependency injection** | Pass small interfaces (or concretes) into constructors; wire in `main` / tests. |
| 10 | **Testing benefit** | Fake or stub the narrow interface; no heavy DB/FS/network in unit tests. |

---

## Core visual: consumer-defined flow (ASCII)

```text
  [ HTTP handler / use case ]     defines locally:
         |                        type JobRunner interface { Run(ctx) error }
         |                                 |
         v                                 v
  needs only "Run"  ---------------->  *Worker (concrete) implements Run()
         ^                                 (implicit — no "implements" keyword)
         |
  [ tests ] pass fake "runner"   ---->  mockRunner{...}
```

**Read it:** the **dashed contract** is drawn by whoever **calls** the behavior; the **concrete** type sits in its own package and never imports the handler to “register” the interface.

---

## Quick-fire (3) — Q + verbal answer

**Q1.** You have one storage struct with five methods, but a handler only calls `Get`. What do you expose to that handler?  
**Verbal answer:** A **tiny** `Getter` (or `Reader`) interface (or the concrete if you are sure you never need a fake)—**not** the full five-method surface. Prefer **consumer-shaped** small interfaces for that handler.

**Q2.** Someone returns `io.Reader` from a factory and also returns a concrete `*bufio.Reader` everywhere else “for consistency.” What’s the tension?  
**Verbal answer:** **Accept interfaces, return structs** is the default: returning **concrete** types keeps APIs clear; return an **interface** when you **intentionally** hide multiple implementations. Don’t return interfaces “by habit.”

**Q3.** When is a fat interface a “role interface” problem?  
**Verbal answer:** A **role interface** is **small** and named after *behavior* (`Reader`, `Writer`). A **fat** interface mixes many roles—split into **composable** pieces so each consumer depends on *its* role only.

---

## One pointer back

Full topic: **[[T12 Interface Design Principles]]** — for narrative + exercises: `simplified/`, `exercises/`, `visuals/`, `questions/`.
