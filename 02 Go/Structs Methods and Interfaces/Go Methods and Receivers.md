---
type: canonical
domain: go
topic: go-methods-receivers
status: implementation-needed
source_notes:
  - "[[99 Archive/Superseded Originals/prerequisites/P02 Methods & Receivers]]"
  - "[[99 Archive/Superseded Originals/root/T01 Go Type System & Value Semantics]]"
---

# Go Methods and Receivers

## Problem and mental model

A method is a function with a receiver. The receiver is a parameter and is passed by value like every other argument. A value receiver receives a copy of `T`; a pointer receiver receives a copied `*T` that can reach the original value.

Receiver choice communicates semantics. Use a pointer receiver when the method must mutate receiver fields, the type should not be copied, or consistent pointer semantics are important. Use a value receiver for small, immutable value-like types. Keep receiver style consistent unless there is a clear reason to mix it.

## Minimum executable example

```go
package main

import "fmt"

type Counter struct {
	value int
}

func (c Counter) Value() int {
	return c.value
}

func (c *Counter) Increment() {
	c.value++
}

func main() {
	counter := Counter{}
	fmt.Println(counter.Value()) // 0
	counter.Increment()          // compiler can take &counter here
	fmt.Println(counter.Value()) // 1
}
```

## Dry run

`Value` receives a copy and only reads it. `Increment` receives the address of `counter` and changes the original field. `counter.Increment()` is convenient shorthand for `(&counter).Increment()` because `counter` is addressable. This call convenience does not change method-set rules for interface satisfaction.

## Receiver decision checklist

Choose a pointer receiver when any is true:

- the method changes a receiver field or replaces a slice/map/pointer field;
- copying the receiver is unsafe or misleading, such as a type containing a mutex;
- the type represents mutable identity or a service;
- other methods already require pointer receivers and consistency is clearer.

A value receiver is a good fit when the type is a small value, methods do not mutate it, copies are independent and meaningful, and the value should satisfy interfaces directly.

Do not use a pointer receiver only because a field is a map or a slice. Mutating elements through a copied descriptor may already be visible; replacing the descriptor field itself requires a pointer receiver. Make this distinction explicit.

## Nil receivers

Calling a method through a nil pointer receiver is syntactically legal. It is safe only if the method checks for nil before dereferencing. Prefer avoiding surprising nil-receiver contracts unless they give the type a clear zero/nil behavior.

## Production use and trade-offs

Pointer receivers avoid copying and permit mutation, but introduce aliasing and possible nil pointers. Value receivers make mutation impossible through receiver fields and can simplify reasoning, but copying types that contain synchronization state or large mutable graphs is wrong even if compilation succeeds.

Success path: receiver choice matches mutation and identity, method sets are understood, and the type is not copied unsafely. Failure path: a value receiver silently loses a field update, a pointer-only method prevents a value from satisfying an interface, or mixed receiver styles make behavior unpredictable.

## Common mistakes

- Expecting a value receiver to update a scalar or replace a slice field.
- Assuming automatic `&value` also makes `T` satisfy pointer-receiver interfaces.
- Copying a type containing synchronization primitives.
- Selecting receiver style by a fixed size rule.
- Using a pointer receiver for mutation but passing copies of the containing struct elsewhere.

## Interview questions

1. Why is a pointer receiver still passed by value?
2. When can a value-receiver method appear to mutate shared state?
3. Why can `value.Method()` compile while `value` still fails an interface assignment?

## Active-recall drill

Implement one value method and one mutating pointer method. Predict behavior before running. Then change the mutating method to a value receiver, explain the failure, and repair it without changing the caller.

## Related notes

- [[Go Method Sets]]
- [[Go Interfaces]]
- [[Pointer and Value Receivers - Drill]]
- [[Go Methods and Receivers - Quick Revision]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
