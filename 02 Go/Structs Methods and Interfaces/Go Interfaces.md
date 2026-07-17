---
type: canonical
domain: go
topic: go-interfaces
status: implementation-needed
source_notes:
  - "[[99 Archive/Superseded Originals/prerequisites/P05 Interfaces Basics]]"
  - "[[99 Archive/Superseded Originals/root/T01 Go Type System & Value Semantics]]"
  - "[[99 Archive/Superseded Originals/root/T11 Interface Internals (iface & eface)]]"
  - "[[99 Archive/Superseded Originals/root/T12 Interface Design Principles]]"
---

# Go Interfaces

## Problem and mental model

An interface describes required behavior as a method set. A concrete type satisfies it implicitly by having those methods; there is no `implements` declaration. This lets consumers depend on a capability while `main()` chooses a concrete implementation.

At the value level, think of an interface as carrying a concrete dynamic type and a concrete dynamic value. An interface is nil only when neither is present. Runtime representation details remain in [[Go Interface Internals]] and are not part of this usage-first canonical.

## Minimum executable example

```go
package main

import "fmt"

type Greeter interface {
	Greet(string) string
}

type FormalGreeter struct{}

func (FormalGreeter) Greet(name string) string {
	return "Hello, " + name
}

type CasualGreeter struct{}

func (CasualGreeter) Greet(name string) string {
	return "Hi, " + name
}

func printGreeting(g Greeter, name string) {
	fmt.Println(g.Greet(name))
}

func main() {
	printGreeting(FormalGreeter{}, "Rahul")
	printGreeting(CasualGreeter{}, "Rahul")
}
```

The caller depends on `Greeter`; both concrete types satisfy it without mentioning the interface in their declarations.

## Pointer receivers and method sets

If an implementation method has a pointer receiver, pass a pointer to the interface:

```go
type Counter struct{ n int }
func (c *Counter) Greet(name string) string { c.n++; return name }

var g Greeter = &Counter{} // valid
// var g Greeter = Counter{} // does not satisfy Greeter
```

See [[Go Method Sets]] for the exact rule.

## Typed nil

```go
type Problem struct{}
func (*Problem) Error() string { return "problem" }

func bad() error {
	var p *Problem
	return p
}
```

`bad()` returns a non-nil interface containing dynamic type `*Problem` and dynamic value `nil`. Return an untyped `nil` on success:

```go
func good(ok bool) error {
	if ok {
		return nil
	}
	return &Problem{}
}
```

## Assertions and type switches

Use `value, ok := x.(T)` when a failed assertion is possible. The one-result form panics on mismatch. A type switch is useful at a genuinely heterogeneous boundary, but repeated assertions can signal that the interface does not express the behavior the consumer actually needs.

Document important implementations at compile time:

```go
var _ Greeter = FormalGreeter{}
var _ Greeter = CasualGreeter{}
```

## Production use and trade-offs

Interfaces create substitution seams for external services, storage, clocks, and test fakes. They also add indirection and can hide useful concrete APIs. Use them at real behavior boundaries, keep them small, and let consumers define the minimum capability they require.

Success path: the consumer owns a narrow contract, `main()` supplies a concrete implementation, method sets match, and nil success is truly nil. Failure path: a pointer implementation is passed as a value, a typed nil escapes through `error`, or `any` and assertions replace a clear contract.

## Common mistakes

- Defining an interface before a consumer needs substitution.
- Using a large producer-owned interface for every operation.
- Returning a typed nil pointer as `error`.
- Using the panic form of an assertion on untrusted data.
- Forgetting to invoke the interface from `main()`.

## Interview questions

1. How does implicit interface satisfaction help decoupling?
2. Why can an error be non-nil while holding a nil pointer?
3. How do pointer receivers affect satisfaction?
4. When is `any` appropriate?

## Active-recall drill

Define a one-method consumer interface, write two implementations, add compile-time assertions, and wire each from `main()`. Then convert one method to a pointer receiver and repair the program.

## Related notes

- [[Go Method Sets]]
- [[Interface Design in Go]]
- [[Interfaces with Two Implementations - Drill]]
- [[Correct Interface Invocation from Main - Drill]]
- [[Go Interfaces - Quick Revision]]
- [[Interface Implementation Correct but Main Invocation Wrong]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
