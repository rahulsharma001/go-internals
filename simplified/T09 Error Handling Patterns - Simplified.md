# T09 Error Handling Patterns — Simplified

> This is the plain-English companion to [[T09 Error Handling Patterns]].  
> Read this when the main note feels heavy or jargon-dense.

---

**How long is this?** About **forty to fifty** percent the length of the main note (by intent)—enough to carry the same arc (what an error is, the three big patterns, how to *look inside* wrapped errors, and the sharp corners), with **stories** instead of spec language. Proofs, long API tables, and deep dives stay in **[[T09 Error Handling Patterns]]** plus the **exercise** and **interview** notes.

**Reading order:** 1) what you are actually holding, 2) three ways people build errors, 3) opening envelopes and tracking packages, 4) where trips happen.

**Simplified does not mean “skip care”:** the same invariants are here—just told with **mailrooms, letters, and complaint forms** instead of interface tables.

---

## 1. What is an `error` in Go (not magic)

**Why it matters:** If you picture “a special class called Error,” you will be confused by nil behavior. Go is simpler.

An **`error` is a small interface: “something that can return a string message.”** That is the whole public contract: one method, usually called **`Error()`**, that returns text you can log or show.

There is no required base type, no required stack trace, no required code field. **Anything** with that method can be treated as an error. Think of a **form that always has a “summary line” at the top**—different departments use different form layouts, but everyone agrees there is a readable summary.

The main note in [[T09 Error Handling Patterns]] names the exact method and shows how the standard library builds these values; here, remember: **error = message box**, not “exception object” in the Java sense.

---

## 2. Pattern A — Sentinels: named slips everyone recognizes

**Why it matters:** Sometimes you do not need details—only “did we hit the exact situation we already agreed on?”

A **sentinel** is a **fixed, shared error value** you compare with `errors.Is` (not `==` on the interface in real code, once wrapping enters the room). In plain terms: a **red stamp** the office always uses for “out of paper,” and everyone looks for *that stamp*, even if the note is clipped inside a **folder of paperwork** (a wrapped error).

- **Pluses:** tiny, easy to name in docs (“returns `io.EOF` when…”), good for “no more data” and similar control flow.  
- **Minuses:** one message string; not great when you need **fields** (user id, file path) unless you add something richer.

`io.EOF` is the letter carrier everyone knows: *no letter today, and that is normal, not a disaster.*

The deep comparison rules live under **sentinels and `errors.Is`** in [[T09 Error Handling Patterns]].

---

## 3. Pattern B — Custom types: a whole complaint form

**Why it matters:** APIs often need “which field failed?” or “which HTTP status?”

A **custom error** is a **struct (or other type) you design** with extra fields, **plus** the `Error()` method so it still fits the `error` interface. Picture a **complaint form** with boxes for *department, reference number, and short description*—the summary line is still there (what `Error()` prints), but a caller can also **read the form** if they know the type.

You usually reach for this when a sentinel string would force brittle string parsing. The main file shows `errors.As` in full; the next section gives the “opening the right form” image.

---

## 4. Pattern C — Wrapping: a note inside a carrier envelope

**Why it matters:** Call stacks are deep; the user-facing story often needs *what failed high up* and *what low-level detail actually broke*.

**Wrapping** means: take an inner error, put it **inside a new error string** (often with `fmt.Errorf("…: %w", err)`), and keep a **link** to the original so `errors.Is` and `errors.As` can still find the inner stamp or custom form. Physical analogy: you receive an **envelope** (“payment processing failed: …”) and inside is the **original letter** from the bank (“insufficient funds”). The outer envelope is what the handler prints first; the inner letter is what you match against known patterns.

- **`%w`:** “attach the inner error as part of the chain” (keeps the link).  
- **`%v`:** “print the inner text, but do not preserve wrap semantics for `Is`/`As` the same way” in typical usage—treat it as *photocopying the text onto the cover* without the official routing slip.

The exact `fmt` verbs and when each is appropriate are spelled out in [[T09 Error Handling Patterns]].

---

## 5. Opening envelopes: `errors.Is` vs `errors.As`

**Why it matters:** These two answer **different** questions. Mixing them up is a very common interview slip.

- **`errors.Is(err, target)`** — *Is a particular **named stamp** in this pile of nested envelopes, anywhere in the chain?*  
  Use when you have **sentinels** or a specific **wrapped** value and you only care *yes/no*.

- **`errors.As(err, &ptr)`** — *Is there a **specific kind of form** in here, and if so, give me a **typed pointer** to the first match?*  
  Use when you need **fields** on a custom type. You hand over an empty clipboard (`var ve *ValidationError`) and `As` **fills in** the pointer if a matching value exists inside the wrappings.

`Is` = “find the **same ink stamp** (identity up the design we care about).”  
`As` = “find the **form type** and let me work with it as a struct again.”

Unwrap order and the way `Unwrap` links work are drawn in the **revision and visuals** notes linked from [[T09 Error Handling Patterns]].

---

## 6. The typed-nil trap: an empty box that still has a label

**Why it matters:** This is the bug that makes you swear `err != nil` is “wrong.” It is not—the **interface** is non-nil.

If a function returns a **typed pointer** to your custom error, and that pointer is **`nil`**, you might still be returning a **non-nil `error` interface value**. Analogy: you hand someone a **labeled tray** that says `*AppError`—the **tray** exists, so the handler thinks “there is an error,” even though the **card inside the slot** is empty.

**Fixes in spirit:** return **untyped** `nil` for “no error,” or assign to a plain `error` variable before returning, or use a named return `err error` and `return err` with care—**always** the stories in the exercises note **fix this with real code**: [[T09 Error Handling Patterns - Exercises|exercises]] (Tier 2).

This is a **traps** focus in the main **[[T09 Error Handling Patterns]]** file—read that table before shipping production APIs.

---

## 7. Practical habits (short)

**Why it matters:** Style questions show up in code review, not just interviews.

- **When to wrap:** crossing a **layer** (HTTP handler → service → repository) when you can add **actionable** context (“saving user profile:” …) without duplicating the entire essay each time.  
- **When not to wrap:** when there is **nothing to add** except noise, or when you would **leak secrets**; sometimes log and return a **sanitized** sentinel instead. The main note and **[[T09 Error Handling Patterns - Interview Questions|interview Q11]]** go deeper.  
- **Tools:** `errcheck` nudges you where you ignored a returned error; it does not fix design, but it **stops silent drops**.

---

## 8. Bridge: where the rest of the course lives

**Performance / tooling / interviews:** the big **[[T09 Error Handling Patterns]]** file carries the full pattern gallery, `panic` vs `error` policy, and API handler sketches. The **[[T09 Error Handling Patterns - Visual Map|visual map]]** is the one-page **concept map and decision table**. The **[[T09 Error Handling Patterns - Revision|revision card]]** is a **single sheet** the night before. The **[[T09 Error Handling Patterns - Exercises|exercises]]** make the **typed nil** and **validation** stories **runnable on your machine**.

If you only remember **three** things from this simplified page: **(1)** `error` is a **message interface**; **(2)** you choose **stamps, forms, or envelopes**; **(3)** **`Is` finds stamps, `As` recovers whole forms**—and **never** return a **typed nil pointer** as an `error` without meaning to.

---

## Related

- **Main:** [[T09 Error Handling Patterns]]  
- **Exercises:** [[T09 Error Handling Patterns - Exercises]]  
- **Revision:** [[T09 Error Handling Patterns - Revision]]  
- **Visual map:** [[T09 Error Handling Patterns - Visual Map]]  
- **Interview Q&A:** [[T09 Error Handling Patterns - Interview Questions]]
