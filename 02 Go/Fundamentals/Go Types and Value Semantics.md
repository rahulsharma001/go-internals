---
type: canonical
domain: go
topic: go-types-value-semantics
status: implementation-needed
aliases:
  - T01 Go Type System & Value Semantics
source_notes:
  - "[[99 Archive/Superseded Originals/root/T01 Go Type System & Value Semantics]]"
---

# Go Types and Value Semantics

## Problem and mental model

Go passes arguments and assigns variables by value: the destination receives a copy of the source value. The important question is therefore not “reference or value?” but “what does this value contain?” An `int` contains the number itself. A pointer contains an address. A slice contains a small descriptor that refers to a backing array. A map contains a handle to map state. Copying each still follows value semantics, but the copied value may continue to reach shared data.

## Essential concepts

- `type UserID int` creates a new defined type. It does not implicitly assign to `int` or another defined type with the same underlying type.
- `type ID = int` creates an alias: `ID` and `int` are the same type.
- Every variable has a zero value. Useful zero values reduce constructor requirements, but constructors are appropriate when the zero value would be invalid.
- Assignment, parameter passing, and return all copy values.
- Whether two values can be compared depends on their types. Slices, maps, and functions are not comparable, except that each may be compared with `nil` where the language permits it.
- Untyped constants are converted when the destination type can represent them.

## Minimum executable example

```go
package main

import "fmt"

type UserID int

type User struct {
	ID   UserID
	Name string
}

func renameCopy(u User, name string) {
	u.Name = name
}

func renameOriginal(u *User, name string) {
	u.Name = name
}

func main() {
	u := User{ID: UserID(7), Name: "Rahul"}
	renameCopy(u, "copy")
	fmt.Println(u.Name) // Rahul

	renameOriginal(&u, "updated")
	fmt.Println(u.Name) // updated
}
```

## Dry run

`renameCopy` receives a new `User` value, so changing its `Name` changes only the copy. `renameOriginal` still receives its pointer argument by value, but the copied pointer identifies the same `User`, so dereferencing it changes `u`.

## Production use and trade-offs

Defined types make domain boundaries visible: a `UserID` cannot be accidentally exchanged with an `OrderID` without conversion. Zero-value-friendly types are easier to compose. Pointer use can express mutation or optional presence, but it also introduces aliasing and possible `nil` handling. Choose based on semantics, not a fixed size threshold.

Success path: conversions are explicit, zero values are intentional, and mutation is visible in the function signature. Failure path: two defined types are mixed without conversion, a copied struct is mutated with no effect on the caller, or shared data inside a copied descriptor is mistaken for a deep copy.

## Common mistakes

- Saying Go “passes maps by reference.” Go copies a map value; the copies refer to the same map state.
- Assuming a struct copy deep-copies slice or map fields.
- Using aliases when a distinct domain type was intended.
- Adding a constructor even though the zero value is already useful.
- Expecting conversion between defined types to be implicit.

## Interview questions

1. What is the difference between a defined type and a type alias?
2. If all arguments are passed by value, why can a function mutate through a pointer, map, or slice?
3. When is a zero value preferable to a constructor?

## Active-recall drill

Without running code, predict what changes after copying a struct containing a number, a slice, and a map. Then verify with a complete program and explain which parts were copied and which underlying data remained shared.

## Related notes

- [[Go Slices]]
- [[Go Maps]]
- [[Go Structs and Constructors]]
- [[Go Methods and Receivers]]
- [[Complete Go Programs]]
- [[Go Types and Value Semantics - Quick Revision]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
