# Go Type System & Value Semantics — Interview Questions

> Comprehensive interview Q&A bank for [[Go Type System & Value Semantics]].
> Sorted by frequency at top tech companies (Google, Amazon, Meta, Uber, Stripe, Cloudflare).
> Tags: `[COMMON]` = asked frequently, `[ADVANCED]` = deep understanding expected, `[TRICKY]` = gotcha/trap question

---

## Q1: Why can't a value type satisfy an interface with pointer receiver methods? [COMMON]

**Answer:**
When you assign a value to an interface, Go stores a **copy** of that value inside the interface. If Go allowed pointer-receiver methods on this copy, any mutations would affect the copy inside the interface, not the original value — silently losing writes. Go prevents this at compile time for safety. The fix: assign a pointer (`&val`) to the interface, so the interface holds a pointer and mutations go through to the original. Note that direct method calls DO allow auto-addressing (`val.Method()` becomes `(&val).Method()`), but this syntactic sugar does NOT apply to interface assignment because the interface holds a copy, not the original addressable variable.

**Interview tip:** This is the #1 most asked Go type system question. The key phrase is: "the interface stores a copy, so pointer-receiver mutations would be lost." Bonus points for explaining the method call sugar distinction.

---

## Q2: How does struct embedding differ from inheritance in OOP? Show a case where it surprises you. [COMMON]

**Answer:**
Embedding promotes the embedded type's fields and methods to the outer type for convenient access, but it's composition (delegation), not inheritance. The critical difference: when a promoted method executes, its receiver is always the embedded type, not the outer type. There's no virtual dispatch. Example: if `Base.Greet()` calls `b.Name()`, it calls `Base.Name()` even if the outer `Derived` type defines its own `Name()`. In OOP languages like Java or PHP, `this.name()` inside `greet()` would call the overridden version. This means Go embedding cannot implement the Template Method pattern or runtime polymorphism through type hierarchies — it's pure delegation with a convenience shortcut.

**Interview tip:** The interviewer is checking if you understand Go's composition philosophy. Always say "delegation, not inheritance" and give the `Greet()/Name()` example to demonstrate you know the receiver doesn't change.

---

## Q3: What is the nil interface trap? How do you avoid it in production? [TRICKY]

**Answer:**
A Go interface is a two-field struct: {type, data}. It's nil only when BOTH fields are nil. If you assign a typed nil pointer to an interface, the type field gets populated while data is nil — making the interface non-nil. This commonly causes bugs when functions return typed nil error pointers: `var err *MyError = nil; return err` returns a non-nil error interface. The fix: always return plain `nil` directly (`return nil`), never return a typed nil variable. In production, use the pattern `if err != nil { return err }; return nil` rather than declaring a typed error variable and returning it. You can detect this with `reflect.ValueOf(i).IsNil()` but it's better to prevent it architecturally.

**Interview tip:** This is a classic Go trap question. Draw the two-field interface layout: `[type: *MyError | data: nil]` is NOT nil, while `[type: nil | data: nil]` IS nil. The visual explanation is what interviewers want.

---

## Q4: Explain Go's type system. What is structural typing? [COMMON]

**Answer:**
Go is statically typed with structural typing for interfaces. Unlike nominal typing (Java, C#) where a type must explicitly declare `implements SomeInterface`, Go uses structural typing — if a type has all the methods an interface requires, it satisfies that interface automatically. This enables decoupled design: you can define an interface in the consumer package and any type from any package satisfies it without modification. Go also has defined types (`type X int` creates a new distinct type) and type aliases (`type X = int` creates another name for the same type). Every type has an underlying type (determines convertibility), a zero value (guaranteed safe default), and a method set (determines interface satisfaction).

**Interview tip:** The phrase "structural typing" or "implicit interface satisfaction" is what the interviewer wants to hear. Connect it to the practical benefit: "I can accept `io.Reader` and any type with `Read()` works — even types the interface author never knew about."

---

## Q5: What's the difference between `type X int` and `type X = int`? When do you use each? [COMMON]

**Answer:**
`type X int` creates a **defined type** — a brand new type with `int` as its underlying type. `X` and `int` are distinct types: assignment between them requires explicit conversion. You can attach methods to `X`. Use this for domain modeling and type safety (e.g., `type UserID int64` prevents accidentally using an OrderID where UserID is expected). `type X = int` creates a **type alias** — `X` is literally another name for `int`. No conversion needed, can't attach methods. Use this for gradual refactoring (renaming types without breaking callers) and cross-package type exposure. In practice, defined types are far more common; aliases are a specialized refactoring tool.

**Interview tip:** Give a concrete example like `type UserID int64` vs `type OrderID int64` preventing accidental misuse. This shows you understand the practical value, not just the syntax.

---

## Q6: What are Go's method set rules? Why is there an asymmetry between T and *T? [COMMON]

**Answer:**
A value of type `T` has a method set containing only value-receiver methods. A pointer `*T` has a method set containing BOTH value-receiver and pointer-receiver methods. The asymmetry exists because: value-receiver methods work on a copy, so they're safe to call on anything. Pointer-receiver methods need an addressable value to take its address. When a value is stored in an interface, it's a copy — and copies inside interfaces are not addressable. If Go allowed pointer-receiver methods on interface-stored copies, mutations would silently affect the copy, not the original. So Go restricts `T`'s method set to prevent this class of bugs. This rule directly affects interface satisfaction: if any method is a pointer receiver, only `*T` satisfies the interface.

**Interview tip:** The interviewer wants the complete chain: method set → interface satisfaction → why the asymmetry exists (mutation safety). Don't just state the rule — explain the reasoning.

---

## Q7: What is a zero value in Go? Why does it matter for API design? [COMMON]

**Answer:**
Every Go variable is automatically initialized to its type's zero value — there is no uninitialized memory. Numeric types → 0, bool → false, string → "", pointers/slices/maps/channels/interfaces → nil, structs → all fields zeroed. This matters for API design because idiomatic Go types are designed so their zero value is useful: `sync.Mutex{}` is ready to lock, `bytes.Buffer{}` is an empty buffer ready for writes, `http.Client{}` works with sensible defaults. The principle "make the zero value useful" reduces the need for constructors and initialization functions. When you can't make the zero value useful (e.g., a type needs a non-zero configuration), provide a `NewX()` constructor.

**Interview tip:** Mention specific standard library examples (`sync.Mutex`, `bytes.Buffer`) to show you know the idiom. Contrast with languages like Java where uninitialized object fields can cause NullPointerException.

---

## Q8: How does Go handle polymorphism without classes or inheritance? [COMMON]

**Answer:**
Go achieves polymorphism through interfaces and composition. Interfaces define behavior contracts (method sets) that any type can satisfy implicitly. Runtime polymorphism happens through interface values: when you call a method on an interface variable, Go performs dynamic dispatch using the interface's internal type table (itab) to find the concrete method implementation. Composition replaces inheritance through struct embedding, which promotes fields and methods from embedded types. However, embedding is delegation, not virtual dispatch — the embedded type is always the receiver. For the Template Method pattern, Go uses function values or strategy interfaces instead of inheritance-based overriding.

**Interview tip:** This is a design philosophy question. Show you understand Go's intentional choice: "Go favors small interfaces and composition because they create less coupling than deep inheritance hierarchies."

---

## Q9: What's the "accept interfaces, return structs" principle? [COMMON]

**Answer:**
Functions should accept interface parameters (for flexibility) and return concrete struct types (for usability). Accepting interfaces means callers can pass any type that satisfies the contract — enabling testing with mocks and loose coupling between packages. Returning concrete types gives callers access to all fields and methods without type assertions, makes the API explicit about what's returned, and avoids forcing callers to depend on an interface they might not need. Example: `func ProcessData(r io.Reader) *Result` — accepts any reader (files, buffers, HTTP bodies) but returns a concrete Result. This principle keeps interfaces small and defined by the consumer, not the producer.

**Interview tip:** This is a Go design pattern question. The interviewer is checking if you know Go idioms for package design. Mention that interfaces should be defined where they're consumed, not where they're implemented.

---

## Q10: Can you embed an interface in a struct? What happens? [TRICKY]

**Answer:**
Yes, you can embed an interface in a struct, and the compiler will consider the struct as satisfying that interface — because the interface's methods are promoted to the struct. However, this is a trap: the embedded interface field is nil by default, so calling any promoted method at runtime panics with a nil pointer dereference. This compiles successfully but crashes at runtime. The legitimate use case is for partial interface implementation: you embed the interface, then override specific methods on the struct, and ensure the embedded field is initialized with a real implementation for the remaining methods. This pattern is used in testing (partial mocks) and decorators, but requires careful initialization.

**Interview tip:** This is a "do you know the sharp edges" question. Mention that it compiles but panics at runtime — the distinction between compile-time safety and runtime behavior is the point.

---

## Q11: How do type assertions and type switches work? What's the performance cost? [ADVANCED]

**Answer:**
Type assertion (`v := i.(ConcreteType)`) extracts the concrete value from an interface, panicking if the type doesn't match. The comma-ok form (`v, ok := i.(ConcreteType)`) is safe — returns false instead of panicking. Type switch (`switch v := i.(type)`) checks multiple types efficiently. Under the hood, Go uses the interface's itab (interface table) hash to look up the concrete type — this is an O(1) cached lookup after the first check for a given type pair. Performance is generally very fast (single-digit nanoseconds) because of itab caching. However, relying heavily on type assertions can indicate a design smell — prefer interface methods for polymorphism and reserve type assertions for cases where you genuinely need to access type-specific behavior.

**Interview tip:** Mention itab caching for the performance question. Saying "use comma-ok form to avoid panics" shows practical awareness.

---

## Q12: What are comparable types in Go? Why does it matter? [COMMON]

**Answer:**
Comparable types are those that support `==` and `!=` operators and can be used as map keys. Comparable: bool, numeric, string, pointer, channel, interface, arrays (if element type is comparable), structs (if all fields are comparable). NOT comparable: slices, maps, functions. This matters because: (1) map keys MUST be comparable — `map[[]int]string` won't compile. (2) Interface comparison compares both type and value — two interfaces are equal only if they hold the same type AND the same value. (3) Comparing interfaces holding non-comparable types panics at runtime, not compile time. Go 1.20 added the `comparable` constraint for generics, but with a subtlety: interface types satisfy `comparable` at compile time but may panic at runtime if the underlying value isn't comparable.

**Interview tip:** The runtime panic with non-comparable interface values is the tricky part. Mention that `interface{}` values can be compared with `==` but will panic if the underlying concrete type isn't comparable (like a slice).

---

## Q13: How would you design a plugin system in Go without inheritance? [ADVANCED]

**Answer:**
Use small interfaces and the strategy pattern. Define a minimal interface for the plugin contract (e.g., `type Handler interface { Handle(ctx context.Context, req Request) Response }`). Plugin authors implement this interface with their own concrete types. The host system accepts the interface and calls methods through dynamic dispatch. For lifecycle management, define separate interfaces (`Initializer`, `Closer`) and check with type assertions: `if c, ok := plugin.(Closer); ok { c.Close() }`. For configuration, accept `func` options or a config struct. This is more flexible than inheritance because plugins don't need to know about or depend on a base class — they just implement the method set. Standard library example: `http.Handler` with its single `ServeHTTP` method enables the entire middleware ecosystem.

**Interview tip:** This is a system design question testing Go idioms. Reference `http.Handler` as the canonical example of interface-based extensibility.

---

## Q14: What happens when you assign a struct with unexported fields to an interface? [TRICKY]

**Answer:**
It works fine for interface satisfaction — unexported (lowercase) fields don't affect the method set. A type satisfies an interface based on its exported methods only. However, there are nuances: (1) Structs with unexported fields cannot be created by external packages using struct literal syntax (they can use exported constructors). (2) If you copy such a struct (which happens during interface assignment), the unexported fields are copied too — this can be dangerous with types like `sync.Mutex` that must not be copied. The `go vet` tool catches mutex copies. (3) Reflection can access unexported fields but cannot modify them.

**Interview tip:** The mutex-copy angle is what makes this question interesting. Mention `go vet` and the danger of copying types that contain `sync.Mutex`.

---

## Q15: How do you enforce that a type implements an interface at compile time? [COMMON]

**Answer:**
Use the compile-time assertion pattern: `var _ MyInterface = (*MyType)(nil)`. This creates a package-level variable (discarded by the compiler) that attempts to assign a nil pointer of your type to the interface. If `*MyType` doesn't have the required methods, the compiler produces a clear error showing which methods are missing. This costs zero runtime — it's purely a compile-time check. It's especially valuable for types that implement interfaces from other packages, where the implementation might drift. Place these assertions near the type definition. Example: `var _ io.ReadCloser = (*MyFile)(nil)` ensures MyFile always implements ReadCloser.

**Interview tip:** This is a practical Go pattern question. Showing you use this pattern in real code demonstrates you care about compile-time safety.

---

> Back to main note → [[Go Type System & Value Semantics]]
