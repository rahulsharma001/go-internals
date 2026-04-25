# T01 Go Type System & Value Semantics — Simplified

> This is the plain-English companion to [[T01 Go Type System & Value Semantics]].
> Read this when the main note feels overwhelming. Every concept is explained with real-world analogies.

---

## 1. What is this, in plain English?

Go's type system is the set of rules that says: "this thing is a number," "this thing is a string," "this thing is a User." It determines what you can do with data, what you can assign to what, and how your code talks to other code through interfaces.

If you're coming from PHP, the biggest shift is: Go decides ALL types at compile time (before your code runs), and there are no classes.

---

## 2. The one thing to remember

**Every type has three essential properties: an underlying type (what it's made of), a zero value (its safe default), and a method set (what it can do).**

---

## 3. How to picture it in your head

### Types are cookie cutters, values are the cookies

A type is like a cookie cutter — it defines the shape. A value is the actual cookie made with that cutter. You can make many cookies (values) from one cutter (type), and every cookie has the same shape.

### Defined types vs type aliases — Name tags vs photocopies

**Defined type** (`type Celsius float64`): Imagine you take a regular thermometer reading (a float64) and put it in a specially labeled jar called "Celsius." The jar looks different from a plain float64 — you can't accidentally mix it with a Fahrenheit reading. You'd have to explicitly relabel it (convert it).

**Type alias** (`type Temperature = float64`): This is just a sticky note on the same jar. "Temperature" and "float64" are the same jar with two labels. No conversion needed.

### Zero values — Every box comes pre-filled

In many languages, if you create a variable and don't give it a value, you get garbage or an error. In Go, every variable starts with a predictable, safe default:

- Numbers start at 0
- Strings start as "" (empty)
- Booleans start as false
- Pointers, slices, maps start as nil (meaning "nothing here")

Think of it like buying furniture from IKEA — every box comes with exactly the parts listed on the label, never random junk.

### Method sets — Your ID badge

Imagine you're at a building with different security levels. Your ID badge (method set) determines which doors you can open (which interfaces you satisfy).

- If you're a **value** (T), your badge only has your "value receiver" methods. Some doors won't open for you.
- If you're a **pointer** (*T), your badge has ALL methods — both value receiver and pointer receiver. Every door opens.

This is the most important thing to remember: **pointers have a VIP badge. Values have a regular badge.**

### Interfaces — Shape-based security

In PHP, you write `class Dog implements Animal`. In Go, there's no `implements` keyword. Instead, Go uses a shape-based system:

If the door requires someone who can `Bark()` and `Fetch()`, and your type has `Bark()` and `Fetch()` methods, you can walk through the door. Nobody checks your name tag — they just check if you have the right abilities.

This is called **structural typing** — "if it walks like a duck and quacks like a duck, it's a duck."

### Embedding — A helper, not a parent

In PHP, `class Dog extends Animal` means Dog IS an Animal. Dog inherits everything and can override methods.

In Go, embedding is different. It's like hiring an assistant:

```
Dog has an Animal assistant.
When someone asks Dog to Speak(), Dog says "let my Animal assistant handle that."
The assistant (Animal) does the speaking — Animal is the one performing the action.
```

Key difference from PHP inheritance: if Animal's `Speak()` method calls `self.Name()`, it calls **Animal's** `Name()`, even if Dog also has a `Name()` method. The assistant doesn't know they're working for Dog.

---

## 4. How it works under the hood (simple version)

### Defined types create real boundaries

When you write `type UserID int64`, Go creates a genuinely new type. It's like getting a new passport — even though you're the same person (same underlying int64), the passport is different. You can't use a French passport at a gate that requires an American one without going through an explicit conversion process.

This is powerful for preventing bugs:

```go
type UserID int64
type OrderID int64

var uid UserID = 42
var oid OrderID = uid  // ERROR! Can't mix user and order IDs
```

Even though both are numbers under the hood, Go won't let you accidentally use a UserID where an OrderID is expected. In PHP, both would just be `int` and you'd never catch the mistake.

### Why method sets are asymmetric

This requires understanding one thing: **when you put a value into an interface, Go makes a copy.**

Imagine you have a document. You photocopy it and put the copy in a sealed envelope (the interface). Now:

- **Reading the copy** (value receiver method) is fine — you're just looking at it.
- **Writing on the copy** (pointer receiver method) is dangerous — you'd be writing on the photocopy inside the envelope, not on your original document. Any changes would be lost when the envelope is opened.

Go prevents this silent bug by saying: "If your method needs to write (pointer receiver), I won't let you put a copy into an interface. You must put the original (a pointer) in there."

### How interfaces work internally

An interface in Go is secretly a small struct with two pieces of information:

1. **What type is inside?** (a pointer to type information)
2. **Where is the actual data?** (a pointer to the value)

Think of it as a labeled gift box:
- The label tells you what's inside (type information)
- The contents are the actual thing (data pointer)

This two-part structure is why the "nil interface trap" exists — a box can have a label but be empty, and Go considers that box "not nil" because the label is there.

### Embedding is rewiring, not inheritance

When Dog embeds Animal:

```go
type Dog struct {
    Animal       // embedded
    Breed string
}
```

Go does something simple: it takes Animal's fields and methods and makes them available directly on Dog. So instead of writing `dog.Animal.Name`, you can write `dog.Name`.

But this is just a shortcut. Under the hood, Go rewrites `dog.Speak()` as `dog.Animal.Speak()`. The method runs with Animal as the receiver, not Dog.

This means:
- Animal's methods don't know they're being called through Dog
- If Animal's method calls another method on itself, it calls Animal's version, not Dog's
- There's no "virtual method table" like in PHP/Java
- There's no `parent::` or `super` — Animal IS the one running

---

## 6. The code, explained line by line

### Example 1: Why defined types prevent bugs

```go
type Celsius float64     // a new type "Celsius" built on float64
type Fahrenheit float64  // a new type "Fahrenheit" built on float64

var temp Celsius = 100.0
var fahr Fahrenheit = temp  // COMPILE ERROR!
```

Even though both are float64 underneath, Go treats them as completely different types. You can't accidentally assign a Celsius value to a Fahrenheit variable. To convert, you must be explicit:

```go
var fahr Fahrenheit = Fahrenheit(temp)  // explicit: "yes, I know what I'm doing"
```

In PHP, both would be `float` and you'd have no compile-time protection against mixing them up.

### Example 2: The interface satisfaction rule

```go
type Speaker interface {
    Speak() string      // any type with a Speak() method satisfies this
}

type Cat struct{ Name string }

func (c *Cat) Speak() string {   // pointer receiver — only *Cat has this
    return c.Name + " meows"
}
```

Now:
```go
var s Speaker = &Cat{"Whiskers"}  // WORKS — *Cat has Speak()
var s Speaker = Cat{"Whiskers"}   // FAILS — Cat (value) does NOT have Speak()
```

Why does the value fail? Because when Go puts Cat into the interface, it makes a copy. If Speak() could modify the Cat (which pointer receivers allow), it would modify the copy, not your original Cat. Go prevents this silent bug.

Fix: either pass a pointer (`&Cat{...}`) or change to a value receiver (`func (c Cat) Speak()`).

### Example 3: The embedding trap — NOT virtual dispatch

```go
type Base struct{}
func (b Base) Name() string  { return "Base" }
func (b Base) Greet() string { return "Hello, " + b.Name() }

type Child struct{ Base }
func (c Child) Name() string { return "Child" }

child := Child{}
fmt.Println(child.Greet())  // prints "Hello, Base" — NOT "Hello, Child"!
```

What happens step by step:

1. We call `child.Greet()`
2. Child doesn't have its own `Greet()`, so Go uses the promoted one from Base
3. Inside `Base.Greet()`, it calls `b.Name()` where `b` is type `Base`
4. `b.Name()` calls **Base's** `Name()` → returns "Base"
5. Result: "Hello, Base"

In PHP, `$this->name()` inside `Greet()` would call Child's `name()` because PHP has virtual dispatch. Go doesn't — the embedded type (Base) is always the receiver.

---

## 7. The traps, explained simply

### Trap 1: Value can't satisfy pointer-receiver interface

Think of it like a sealed envelope. You put a photocopy of your document in the envelope (interface stores a copy of the value). If someone tries to write corrections on the document through the envelope, they'd be writing on the photocopy — your original stays unchanged. Go says "no, that's dangerous" and prevents it.

**Fix:** Put the original address in the envelope instead (use a pointer: `&myValue`).

### Trap 2: Embedding looks like inheritance but isn't

In PHP, `extends` gives you polymorphism — child classes can override parent methods and `$this->method()` will call the child's version.

In Go, embedding gives you convenience (shorter syntax) but NOT polymorphism. Think of it as delegation: "My assistant handles this for me, but my assistant doesn't know about my special skills."

### Trap 3: Map values can't be modified in place

```go
m := map[string]User{"alice": {"Alice"}}
m["alice"].Name = "Bob"  // COMPILE ERROR!
```

Think of a map like a post office with numbered boxes. When you open a box and look at the letter inside, Go gives you a photocopy of the letter, not the actual letter. You can't modify the photocopy and expect the original to change.

**Fix:** Take the letter out (copy), modify it, put the new letter back:
```go
u := m["alice"]     // take it out
u.Name = "Bob"      // modify
m["alice"] = u      // put it back
```

Or store pointers in the map (`map[string]*User`) so the "letters" in the boxes are just addresses pointing to the actual data.

### Trap 4: Type alias vs defined type confusion

- `type Celsius float64` — new passport. Can't use where float64 is expected without explicit conversion. Can attach methods.
- `type Temperature = float64` — just a nickname. IS float64. No conversion needed. Cannot attach methods.

If you want type safety (preventing bugs), use defined types.
If you want a convenient rename during refactoring, use aliases.

---

> Ready for the full technical version? → [[T01 Go Type System & Value Semantics]]
