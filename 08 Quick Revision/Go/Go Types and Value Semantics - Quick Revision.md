---
type: quick-revision
domain: go
topic: go-types-value-semantics
canonical: "[[Go Types and Value Semantics]]"
---

# Go Types and Value Semantics - Quick Revision

## Mental model

Go assignment, parameters, and returns copy values. Ask what the value contains. Copying an `int` copies the number; copying a pointer copies an address; copying a slice copies a descriptor that may share an array; copying a map copies a handle that observes the same map state.

## Minimum syntax

```go
type UserID int // new defined type
type ID = int   // alias: same type

type User struct{ Name string }
u2 := u1        // copies User fields
```

Defined types require explicit conversion even when underlying types match. Every variable has a zero value. Prefer useful zero values; use constructors when validity or defaults require controlled creation.

## Common mistake

“Maps and slices are passed by reference” is imprecise. Their values are copied; those copied values can reach shared data. A copied struct containing a slice is therefore not a deep copy.

## Production example

Defined `UserID` and `OrderID` types prevent accidental mixing at domain boundaries. Explicit pointer parameters make mutation visible.

## 30-second answer

Go is pass-by-value. The effect of a copy depends on the value's representation: plain values are independent, while copied pointers, slices, and maps can still reference shared storage. Defined types create distinct type identities; aliases do not. Zero values are guaranteed and should be useful when possible.

## Recall challenge

Predict what changes after copying a struct containing `int`, `[]string`, and `map[string]int`, then mutating each field's contents.

Canonical: [[Go Types and Value Semantics]] · Drill: [[Complete Small Executable Programs - Drill]]

Index: [[Quick Revision Index]]
