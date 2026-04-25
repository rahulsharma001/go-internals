# T12: Interface Design Principles (Plain English)

> Companion notes for [[T12 Interface Design Principles]] — the ideas, without the ceremony.

## Think of an interface as a **power outlet**

- The **consumer** (lamp, phone charger) decides what **shape of plug** it needs.
- The **wall** does not hand you a custom “LampOnlyOutlet™.” You standardize the **slot**, and any compliant plug fits.
- In Go, that means: **the code that *uses* a dependency often defines a tiny interface** describing exactly what it needs. Types satisfy it **implicitly** if they have the right methods—no `implements` keyword.

**Takeaway:** Interfaces describe **capability at the call site**, not a laundry list of everything a type *could* do.

---

## Small interface = a **simple tool**

| Mental picture | What it means in Go |
|----------------|----------------------|
| **Screwdriver** | One job, one grip. `Read(ctx) ([]byte, error)` is easy to reason about and mock. |
| **Swiss Army knife** | Many blades, but heavy and easy to use wrong. A 15-method `Service` interface is the same. |

**Prefer** several **small, focused** interfaces (read, write, delete, notify) that you can **compose** over one “god interface” that every caller must depend on.

---

## Interface pollution = the **50-button remote** problem

If the only thing you need is **on/off**, but the API forces everyone to carry a remote with **50 functions** (and half of them are “legacy”), that is **interface pollution**:

- Callers import **huge** surface areas they do not use.
- Tests need **giant fakes** or real dependencies.
- Changes ripple everywhere, because the contract is **fat and unstable**.

**Avoid it** by: keeping interfaces **narrow**, **stable**, and **close to the consumer**; splitting “roles”; and not abstracting *before* you have two real implementations or a clear testing need.

---

## The headline rule: **Accept interfaces, return structs**

| Direction | What to do | Why (plain English) |
|-----------|------------|---------------------|
| **Parameters** of your functions / methods | Prefer **interface types** that describe *what you need* | You stay flexible: pass a `Reader`, a `DB` handle, or a mock—same code path. |
| **Return values** (constructors, APIs) | Often prefer **concrete struct types** | Callers get a clear, documentable value; you avoid leaking abstraction layers in every return type. |

This is a **default**, not a law: sometimes returning an interface is right (e.g. hiding several implementations), but **starting** with “accept interfaces, return structs” keeps APIs honest.

---

## **Consumer-defined** interfaces (who draws the line?)

- **Consumer-defined:** The **package that needs behavior** defines `type Querier interface { Query(...) }` and accepts a `Querier`. The producer package (e.g. `*sql.DB`) just exists; it **satisfies** the interface without importing your package.
- **Producer-defined** interfaces are fine when the type **is** the product (e.g. `io.Reader` in the standard library) or you publish a real plugin API.

**Rule of thumb:** If only **your** test or **your** handler needs a seam, the interface usually belongs **where the seam is used**.

---

## **When NOT to use** an interface

Skip or delay an interface when:

- There is **only one** implementation and **no** need for a test double yet—YAGNI.
- The abstraction is **unstable**; you are still moving methods weekly.
- You would use **`interface{}` / `any` everywhere** to “be generic”—that erases the contract instead of clarifying it.
- The interface is **huge** “because someday we might…”—that is premature design, not a real seam.

**Do use** interfaces when you need **testability**, **multiple implementations**, or a **clear boundary** between packages.

---

## One-line anchors

- **[[T12 Interface Design Principles]]** in practice: **small**, **consumer-shaped**, **composable** contracts; **accept interfaces, return structs**; avoid **pollution** and **premature** abstraction.

See also: exercises in `exercises/T12 Interface Design Principles - Exercises.md` and the revision sheet in `revision/`.
