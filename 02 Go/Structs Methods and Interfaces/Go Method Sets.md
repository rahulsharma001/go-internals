---
type: canonical
domain: go
topic: go-method-sets
status: implementation-needed
source_notes:
  - "[[99 Archive/Superseded Originals/prerequisites/P02 Methods & Receivers]]"
  - "[[99 Archive/Superseded Originals/prerequisites/P05 Interfaces Basics]]"
  - "[[99 Archive/Superseded Originals/root/T01 Go Type System & Value Semantics]]"
---

# Go Method Sets

## Problem and mental model

Method sets determine which methods a value exposes for interface satisfaction. They are related to receiver call shorthand but are not the same rule.

For a defined type `T`:

- the method set of `T` contains methods declared with receiver `T`;
- the method set of `*T` contains methods declared with receiver `T` or `*T`.

Therefore a value of type `T` does not satisfy an interface that requires a pointer-receiver method, while `*T` can satisfy interfaces requiring either receiver style.

## Minimum executable example

```go
package main

import "fmt"

type Renamer interface {
	Rename(string)
}

type User struct {
	name string
}

func (u *User) Rename(name string) {
	u.name = name
}

func rename(r Renamer, name string) {
	r.Rename(name)
}

func main() {
	user := User{name: "old"}
	user.Rename("direct call") // shorthand for (&user).Rename(...)
	rename(&user, "interface call")
	fmt.Println(user.name)

	// rename(user, "does not compile")
}
```

Compile-time assertions make an intended relationship explicit:

```go
var _ Renamer = (*User)(nil)
```

## Dry run

The local `user` variable is addressable, so the direct call can take its address automatically. Interface assignment checks the method set of the exact value being assigned. `User` lacks `Rename` in its method set; `*User` has it.

## Embedding effect

Embedding can promote methods into the outer type's method sets. The exact result depends on whether the embedded field is `T` or `*T` and on the embedded method receiver. Use compile-time assertions to document the interface relationships you intend instead of relying on memory in complicated designs.

## Production use and trade-offs

Method-set mismatches commonly appear during dependency wiring in `main()` or constructors. Returning concrete pointer types is often natural for mutable services and makes pointer-receiver interfaces straightforward. Value-like types can intentionally expose value methods so both `T` and `*T` satisfy read-only interfaces.

Success path: the concrete value passed at the composition root has the required method set and assertions guard important contracts. Failure path: direct calls compile due to addressability, but interface assignment fails; a constructor returns `T` while only `*T` satisfies the consumer; or embedding promotes an unintended interface.

## Common mistakes

- Treating automatic address-taking as an interface rule.
- Assuming `T` and `*T` always satisfy the same interfaces.
- Adding pointer receivers without considering existing value assignments.
- Using an interface assertion with the wrong concrete form.

## Interview questions

1. What are the method sets of `T` and `*T`?
2. Why can `v.M()` compile when assigning `v` to an interface does not?
3. How does a compile-time interface assertion help?

## Active-recall drill

Write four assignments using a value/pointer concrete type and a value/pointer receiver. Predict which compile. Then add an embedded type and repeat the method-set table.

## Related notes

- [[Go Methods and Receivers]]
- [[Go Interfaces]]
- [[Struct Embedding and Composition]]
- [[Correct Interface Invocation from Main - Drill]]
- [[Go Method Sets - Quick Revision]]

