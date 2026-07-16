---
type: quick-revision
domain: go
topic: go-structs-constructors
canonical: "[[Go Structs and Constructors]]"
---

# Go Structs and Constructors - Quick Revision

## Mental model

A struct is a value of named fields. Assignment copies fields, but copied pointer/slice/map fields can still share underlying data. Go constructors are ordinary functions by convention, not language syntax.

## Minimum syntax

```go
type User struct {
	ID   int
	Name string
}

u := User{ID: 7, Name: "Rahul"}

func NewUser(name string) (*User, error) {
	if name == "" { return nil, errors.New("name required") }
	return &User{Name: name}, nil
}
```

Prefer keyed literals outside the defining package. Use the zero value or literal when creation is simple. Use `NewType` when creation must validate, normalize, supply defaults, wire dependencies, or hide fields.

## Common mistakes

- Treating constructors as mandatory.
- Using positional literals that break when field order changes.
- Assuming a struct copy deep-copies slice/map fields.
- Returning `*T` without mutation, identity, nil, or copy-safety reasons.
- Letting callers bypass invariants through exported fields.

## Production example

DTOs often have exported tagged fields for encoding. Domain values may keep fields unexported and use constructors to prevent invalid state. Configuration types benefit from useful zero values or explicit default construction.

## 30-second answer

Structs are copied values. I use keyed literals or a useful zero value for simple data and a constructor function only when creation enforces an invariant, applies defaults, or wires dependencies. Pointer versus value returns follow mutation, identity, copy safety, and nil semantics—not a fixed size threshold.

## Recall challenge

Build a validated struct constructor, call success and failure from `main`, then add one optional field without breaking callers.

Canonical: [[Go Structs and Constructors]] · Drill: [[Struct Creation and Constructors - Drill]]

Index: [[Quick Revision Index]]
