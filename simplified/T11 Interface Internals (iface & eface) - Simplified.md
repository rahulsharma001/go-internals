# T11: Interface Internals (iface & eface) — Simplified

> Companion note for [[T11 Interface Internals (iface & eface)]]: plain-English only.

## The one analogy that carries everything

Think of a **Go interface value** as a **gift box** with two parts:

1. **The label (type)** — *what are we looking at?*
2. **The contents (data)** — *what is actually inside?*

In the real implementation, the runtime needs both so it can (a) know what the thing *is* and (b) know how to call the right *methods* on that thing. That is why interfaces are not “just a pointer to data”; they are a small bundle: **type information + data pointer** (and more for non-empty interfaces — see below).

---

## eface: the box with *only* a label

**`eface`** (empty interface) is how Go stores a value of type `interface{}` or `any`.

- You still have the **“what is it?”** and **“where is the payload?”** pair.
- You **do not** have a *method list* in the value itself, because `any` promises **no** methods—only “I hold *some* concrete type and its data.”

**Analogy:** a box with a **barcode/label** (concrete type) and **what’s in the box** (pointer to the real value), but **no instruction manual** for extra behavior—`any` is maximally open-ended.

```text
eface:  [ type  |  data ]
        “label”   “contents”
```

---

## iface: the box *with* an instruction manual

**`iface`** is the representation for a **non-empty interface**—for example `io.Reader` or `fmt.Stringer`.

- Besides **type** and **data**, the runtime also needs: **“given this *abstract* type (the interface), which concrete type am I, and which **vtable** of methods applies?”**
- That extra piece is the **`itab`**: a small runtime structure that says, *for this pair (interface type, concrete type)*, here is the **method table** (the “how to do Read / String / …” for *this* concrete type under *this* interface contract).

**Analogy:** the same **gift box** (type + data), but now the box also ships with a **booklet** (`itab`) that maps **“what the world expects”** to **“how *this* concrete type fulfills it.”** Open the right page → jump to the right function.

```text
iface:  [ itab*  |  data ]
        “manual  +  contents”
```

The `itab` is not the concrete value; it is **metadata** about *how* that concrete value satisfies the interface for dynamic dispatch.

---

## itab: the instruction manual (method table)

- **`itab`** (interface table) links:
  - the **interface type** (the contract),
  - the **concrete type** (the implementer),
  - and the **list of function pointers** used for calls through that interface.
- The first time a given `(interface, concrete)` pair is needed, the runtime may **build/cache** a suitable `itab` so the next time is fast.

**Analogy pages:** *“If someone asks for `Read` on an `*os.File` viewed as an `io.Reader`, turn to slot 0 and run *this* function.”*

---

## The nil interface vs typed nil: the empty box trap

Two different “kinds of empty”:

1. **Nil interface value**  
   - **No label, no contents** in the box **as an interface** — both the interface’s type slot and the data slot are nil **from the interface’s point of view**.  
   - This is a true **nil** `io.Reader` / `error` / etc.

2. **Typed nil inside an interface**  
   - The **box still has a label** (a concrete type like `*MyError`), but the **pointer inside** is `nil`.  
   - The **interface value is not nil**, because the **type half** is set.

**Analogy:** an **empty box with no label** (nil interface) is not the same as a **box labeled `*T` with nothing inside the slot** (typed nil behind the interface). From the outside, the second box is **not empty**—it still says *what* it was supposed to be.

**Why it bites:** `if err == nil` checks the **interface bundle**, not “deep inside the pointer,” so a typed `nil` of type `*MyError` stored in an `error` is **not** equal to a bare `nil` `error`. That is the **nil interface trap**.

---

## Type assertions: peeking inside the box

- A **type assertion** (`x.(ConcreteType)`) is **opening the box** and saying: *“I believe the contents are really this; please give them to me.”*
- The **two-value form** (`v, ok := x.(T)`) is **tactful peeking**: you get the gift **or** a polite `ok == false` without a panic.
- The **one-value form** is **ripping the paper off**: if you guessed wrong, you get a **panic**—the runtime can’t “fake” a wrong unwrap.

**Analogy labels:**

| Idea | Analogy |
|------|---------|
| Safe assertion (comma-ok) | Open carefully; if wrong pattern, you still keep the present intact |
| Unsafe assertion | Tear open; wrong guess → commotion (panic) |
| `switch x.(type)` | Lay several labeled trays on the table; only one is chosen at runtime |

---

## Quick mental model checklist

- **`any` / `interface{}` → eface** — label + contents; no per-interface method table in the value.
- **Named interface (with methods) → iface** — contents + `itab` (manual for method calls).
- **`itab`** — links interface + concrete type; holds **function slots** for dispatch.
- **Nil trap** — label missing vs present with nil payload.
- **Assertions** — **peek in the box**; use comma-ok to avoid unwrapping chaos.

This note stays conceptual; for layouts, opcodes, and interview depth, use [[T11 Interface Internals (iface & eface) - Revision]] and [[T11 Interface Internals (iface & eface) - Interview Questions]].
