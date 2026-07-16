---
type: canonical
domain: go
topic: interface-internals
status: learning
aliases:
  - T11 Interface Internals (iface & eface)
source_notes:
  - "[[99 Archive/Superseded Originals/root/T11 Interface Internals (iface & eface)]]"
---

# Go Interface Internals

## Why this matters

The language-level model is that an interface value contains a dynamic type and dynamic value. This explains typed nil, assertions, equality panics, and some allocation costs. Runtime struct names are implementation detail.

## Mental model and core concepts

An interface is a labeled box: the label is the dynamic type and the contents are the dynamic value. The interface is nil only when neither exists. Therefore an interface holding a nil `*T` is not nil.

```go
package main

import "fmt"

type problem struct{}
func (*problem) Error() string { return "problem" }

func maybeError() error {
	var p *problem
	return p
}

func main() {
	err := maybeError()
	fmt.Println(err == nil) // false
	if p, ok := err.(*problem); ok { fmt.Println(p == nil) }
}
```

Method sets decide interface satisfaction. Type assertions inspect the dynamic type; the two-result form avoids panic. A type switch handles several dynamic types. Comparing interface values requires comparable dynamic values; comparing interfaces containing slices or maps can panic.

## Under the hood and trade-offs

Runtime implementations use metadata and data references to support dynamic dispatch. Names such as `iface`, `eface`, and `itab` describe particular implementations and may change; do not build application logic on them. Interface conversion or boxing can affect escape and allocation, but measure a real hot path.

Interfaces improve substitution and consumer-focused design. They add indirection and can hide concrete behavior. Prefer small interfaces at the consuming boundary and concrete types until substitution is useful.

## Production success and failure

Success: return a literal `nil` error on success, use `errors.Is/As` for error inspection, keep interface ownership with consumers, and avoid interface equality unless dynamic comparability is guaranteed. Failure: returning a typed nil pointer, using a single-result assertion on external data, or using `any` to avoid modeling.

## Google / Senior Interview Lens

Begin with dynamic type/value, demonstrate typed nil, connect method sets, and explain safe assertions. Runtime tables are a follow-up, not the entry point. Be ready to discuss allocations only with measurement.

## Active recall

Predict nil and equality results for concrete pointers, slices stored in `any`, and method-set variants. Repair an API that returns a typed nil error.

## Related notes

- [[Go Interfaces]]
- [[Go Method Sets]]
- [[Go Error Handling]]
- [[Go Interface Internals - Quick Revision]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
