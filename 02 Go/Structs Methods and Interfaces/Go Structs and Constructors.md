---
type: canonical
domain: go
topic: go-structs-constructors
status: implementation-needed
source_notes:
  - "[[99 Archive/Superseded Originals/prerequisites/P01 Structs & Struct Memory Layout]]"
  - "[[99 Archive/Superseded Originals/root/T01 Go Type System & Value Semantics]]"
---

# Go Structs and Constructors

## Problem and mental model

A struct groups named fields into one value. Struct assignment copies the fields. If a field is itself a pointer, slice, map, or interface, the copied field may still reach shared data.

Go has no constructor syntax. A function conventionally named `NewType` is useful when creation needs validation, defaults, dependency injection, or hidden fields. Otherwise, a keyed literal or the zero value is often clearer.

## Essential syntax

```go
type User struct {
	ID    int
	Name  string
	Email string
}

zero := User{}
keyed := User{ID: 1, Name: "Rahul"}
pointer := &User{ID: 2, Name: "Ada"}
```

Prefer keyed literals outside the defining package. Positional literals couple callers to field order and break easily when fields change. Unexported fields can be initialized only within their package.

## Minimum executable example

```go
package main

import (
	"errors"
	"fmt"
	"strings"
)

type User struct {
	name  string
	email string
}

func NewUser(name, email string) (*User, error) {
	name = strings.TrimSpace(name)
	email = strings.TrimSpace(email)
	if name == "" {
		return nil, errors.New("name is required")
	}
	if !strings.Contains(email, "@") {
		return nil, errors.New("email is invalid")
	}
	return &User{name: name, email: email}, nil
}

func (u User) String() string {
	return fmt.Sprintf("%s <%s>", u.name, u.email)
}

func main() {
	user, err := NewUser("Rahul", "rahul@example.com")
	if err != nil {
		fmt.Println("create user:", err)
		return
	}
	fmt.Println(user)

	_, err = NewUser("", "invalid")
	fmt.Println(err) // name is required
}
```

## Dry run

The constructor normalizes inputs, rejects invalid state, and returns a pointer to the valid value. `main()` exercises both success and failure. Because the fields are unexported, outside callers must use the constructor and cannot bypass these invariants.

## Constructor decision

Use a literal or zero value when all of the following are true: fields may be set independently, defaults are zero values, and no invalid intermediate state is exposed. Use a constructor when creation must enforce an invariant, wire dependencies, normalize inputs, or hide representation.

Return `T` when copying is natural and no shared identity or mutation is needed. Return `*T` when methods mutate the value, identity matters, the type should not be copied, or `nil` is a meaningful failure result. Do not choose solely from a rigid byte threshold.

## Production use and trade-offs

DTOs often use exported fields and tags so encoders can populate them. Domain values may use unexported fields plus constructors to protect invariants. Configuration structs often benefit from a usable zero value or explicit defaults. Constructor growth can become awkward; an options pattern is appropriate only when the number of optional settings actually justifies it.

Success path: valid objects are easy to create and invalid states are rejected at the boundary. Failure path: positional literals silently bind the wrong field order, callers bypass validation, or a constructor hides simple zero-value semantics behind unnecessary ceremony.

## Common mistakes

- Treating a constructor as mandatory in Go.
- Using positional literals across packages.
- Forgetting that copying a struct does not deep-copy slice or map fields.
- Returning a pointer with no semantic reason.
- Returning a partially valid object together with an error without documenting that contract.

## Interview questions

1. When should a Go type have a constructor function?
2. What does copying a struct containing a slice copy?
3. Why are keyed literals safer than positional literals?

## Active-recall drill

Create a domain type with one invariant, a constructor returning `(T, error)` or `(*T, error)`, and a complete `main()` covering valid and invalid input. Then add an optional field without breaking existing callers.

## Related notes

- [[Go Types and Value Semantics]]
- [[Go Methods and Receivers]]
- [[Struct Creation and Constructors - Drill]]
- [[Go Structs and Constructors - Quick Revision]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
