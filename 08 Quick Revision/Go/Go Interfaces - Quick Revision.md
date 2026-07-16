---
type: quick-revision
domain: go
topic: go-interfaces
canonical: "[[Go Interfaces]]"
---

# Go Interfaces - Quick Revision

## Mental model

An interface is a behavior contract. Satisfaction is implicit: a concrete type with the required method set implements it. At runtime an interface value carries a dynamic type and value; it is nil only when both are absent.

```go
type Greeter interface{ Greet(string) string }

func printGreeting(g Greeter, name string) {
	fmt.Println(g.Greet(name))
}
```

Define small interfaces near consumers, wire concrete implementations in `main`, and normally return concrete types from constructors. Use compile-time assertions for intended relationships.

## Pointer and typed-nil traps

If `Greet` has a pointer receiver, pass `&value`; `value` does not satisfy the interface. Returning a nil `*Problem` as `error` creates a non-nil interface because its dynamic type is present. Return untyped `nil` on success.

Use `v, ok := x.(T)` when assertion failure is possible. The one-result form panics on mismatch.

## Common mistakes

- Creating a fat interface from every producer method.
- Inventing an interface before a real consumer needs it.
- Passing `T` where only `*T` satisfies the contract.
- Returning typed nil through `error`.
- Defining implementations but never invoking them through the interface in `main()`.

## Production example

A service consumes a one-method `UserFinder`; production passes a database repository and tests pass an in-memory fake. The service does not know either concrete type.

## 30-second answer

Go interfaces describe behavior and are satisfied implicitly through method sets. I keep them small and consumer-shaped, wire concrete values at the composition root, and watch pointer-receiver and typed-nil rules. Interfaces are useful seams, not mandatory wrappers around every struct.

## Recall challenge

Write two implementations, assertions, and `main` wiring. Convert one method to a pointer receiver and repair the assignment.

Canonical: [[Go Interfaces]] · Drills: [[Interfaces with Two Implementations - Drill]], [[Correct Interface Invocation from Main - Drill]]

Index: [[Quick Revision Index]]
