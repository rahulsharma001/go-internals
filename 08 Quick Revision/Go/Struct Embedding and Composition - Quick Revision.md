---
type: quick-revision
domain: go
topic: go-struct-embedding-composition
canonical: "[[Struct Embedding and Composition]]"
---

# Struct Embedding and Composition - Quick Revision

## Mental model

The outer struct contains the embedded value. Eligible fields and methods are promoted, letting `outer.Method()` select `outer.Inner.Method()`. This is composition and selector shorthand—not inheritance, subtyping, or dynamic dispatch.

```go
type Logger struct{}
func (Logger) Log(string) {}

type Service struct {
	Logger
}
```

`Service` may call the promoted `Log`. It can still select `service.Logger.Log` explicitly.

## Ambiguity

If two embedded fields promote the same name at the same depth, the short selector is ambiguous and fails to compile. Select the field path explicitly or replace embedding with named composition.

Embedding `T` versus `*T` affects promoted method sets and therefore interface satisfaction. Verify important contracts with compile-time assertions.

## Common mistake

Assuming an embedded method will dynamically call an outer method with the same name. The inner receiver remains the inner value. Also avoid embedding a large dependency merely to shorten selectors; it unintentionally expands the outer API.

## Production example

Embed a focused adapter only when promotion makes the public API clearer. Use `logger Logger` as a named field when ownership, collision avoidance, or controlled delegation matters more.

## 30-second answer

Embedding is composition with promotion. The outer value contains the inner value and can use promoted selectors, but it is not a subtype and there is no inheritance dispatch. Collisions at the same depth are ambiguous. I prefer named composition when I need explicit ownership or a smaller exposed API.

## Recall challenge

Create two embedded loggers with the same method, observe the ambiguous selector, resolve it, then refactor to named fields.

Canonical: [[Struct Embedding and Composition]] · Drill: [[Struct Embedding and Promoted Methods - Drill]]

Index: [[Quick Revision Index]]
