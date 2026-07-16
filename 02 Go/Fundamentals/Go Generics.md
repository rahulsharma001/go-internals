---
type: canonical
domain: go
topic: generics
status: learning
source_notes:
  - "[[Grouping and Collection Transformations - Drill]]"
  - "[[MIGRATION_PLAN]]"
---

# Go Generics

## Why this matters

Generics let one function or type preserve compile-time type safety across several concrete types. Use them when the algorithm is genuinely the same; keep concrete code when abstraction would hide the domain.

## Core mental model

A type parameter is an input to a declaration. Its constraint states which operations the implementation may use.

- `[T any]` accepts any type but grants no type-specific operations.
- `[T comparable]` permits `==` and `!=`, so `T` can also be a map key.
- Callers often get type inference from arguments; explicit type arguments remain available.
- Generics do not replace interfaces: type parameters express compile-time families, while interfaces commonly express runtime behavior and substitution.

## Minimum executable example

```go
package main

import "fmt"

func Index[T comparable](values []T, target T) int {
	for i, value := range values {
		if value == target {
			return i
		}
	}
	return -1
}

func main() {
	fmt.Println(Index([]int{4, 7, 9}, 7))
	fmt.Println(Index([]string{"go", "java"}, "go"))
}
```

The constraint is `comparable` because the implementation uses `==`. Both calls infer `T` from their arguments.

## Use, failure path, and interview lens

Good uses include reusable collection helpers and small containers whose behavior is identical across element types. A poor use adds type parameters to a one-off domain function, reaches for `any` and assertions inside generic code, or introduces abstraction before a concrete implementation is correct.

In an interview, explain the type parameter, justify the narrowest useful constraint, show inference, and state why a concrete function or interface might be simpler.

## Deferred depth

Advanced constraint algebra, `~` type approximation, large generic container libraries, generic framework design, compiler implementation, and performance specialization are outside the active 30-day sprint. See [[Deferred Backlog]].

## Active recall

Rewrite `Index` as `Contains`, then explain why `comparable` is required. Generalize one already-correct concrete collection helper only after stating what duplication the type parameter removes.

## Related notes

- [[Go Types and Value Semantics]]
- [[Go Interfaces]]
- [[Collection Transformations in Go]]
- [[Grouping and Collection Transformations - Drill]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
