---
type: canonical
domain: go
topic: go-struct-embedding-composition
status: implementation-needed
source_notes:
  - "[[99 Archive/Superseded Originals/prerequisites/P01 Structs & Struct Memory Layout]]"
  - "[[99 Archive/Superseded Originals/root/T01 Go Type System & Value Semantics]]"
  - "[[99 Archive/Superseded Originals/root/T12 Interface Design Principles]]"
---

# Struct Embedding and Composition

## Problem and mental model

Composition builds a type from other values. A named field makes delegation explicit. An embedded field omits the field name and promotes eligible fields and methods so callers may use a shorter selector.

Embedding is not inheritance. The outer type contains the embedded value; it is not a subtype, and method calls do not use class-style dynamic dispatch. Promotion is selector shorthand governed by method sets and ambiguity rules.

## Minimum executable example

```go
package main

import "fmt"

type Logger struct {
	prefix string
}

func (l Logger) Log(message string) {
	fmt.Println(l.prefix + ": " + message)
}

type Service struct {
	Logger
	name string
}

func (s Service) Start() {
	s.Log(s.name + " started") // promoted Logger.Log
}

func main() {
	service := Service{
		Logger: Logger{prefix: "INFO"},
		name:   "payments",
	}
	service.Start()
	service.Logger.Log("explicit delegation also works")
}
```

## Dry run

`Service` contains a `Logger` value. `service.Log` is shorthand for selecting the promoted `service.Logger.Log`; the explicit form remains available. `Service` can define its own `Log` method to take precedence for `service.Log`, but calls inside `Logger` still use `Logger` behavior rather than dispatching to the outer type.

## Ambiguity and name collisions

If two embedded fields promote the same name at the same depth, the short selector is ambiguous and does not compile. Select the path explicitly:

```go
report.ConsoleLogger.Log("console")
report.FileLogger.Log("file")
```

If collisions are likely or the relationship should be obvious, use named composition:

```go
type Service struct {
	logger Logger
}

func (s Service) Start() {
	s.logger.Log("started")
}
```

## Method-set effect

Embedding affects promoted method sets. Embedding `T` and embedding `*T` can produce different interface satisfaction. Do not infer a complicated result from call shorthand; add compile-time assertions for contracts the outer type is meant to satisfy and consult [[Go Method Sets]].

## Production use and trade-offs

Embedding is useful for focused reusable behavior such as a small logger adapter or common metadata when promotion makes the public API clearer. Named composition is better when dependency ownership should be explicit, collisions are possible, or delegation needs control.

Success path: the “has-a” relationship is clear, promoted methods are intentional, and interface satisfaction is verified. Failure path: embedding is treated as inheritance, two promoted names become ambiguous, or the outer type unintentionally exposes methods that should have remained internal.

## Common mistakes

- Calling embedding inheritance or assuming substitutability.
- Expecting an embedded method to dispatch to an outer override.
- Ignoring promoted method-set differences between embedded `T` and `*T`.
- Embedding a large concrete dependency only to save selector typing.
- Hiding meaningful ownership that a named field would communicate.

## Interview questions

1. What does method promotion do, and what does it not do?
2. How is an ambiguous promoted selector resolved?
3. When would you replace embedding with a named field?

## Active-recall drill

Embed a component with one method, invoke the promoted method, create a same-name collision, resolve it explicitly, and then refactor to named composition. Explain which API is clearer and why.

## Related notes

- [[Go Method Sets]]
- [[Go Interfaces]]
- [[Struct Embedding and Promoted Methods - Drill]]
- [[Struct Embedding and Composition - Quick Revision]]
- [[Embedding Correct but Construction or Invocation Wrong]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
