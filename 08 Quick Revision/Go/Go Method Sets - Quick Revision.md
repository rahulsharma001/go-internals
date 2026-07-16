---
type: quick-revision
domain: go
topic: go-method-sets
canonical: "[[Go Method Sets]]"
---

# Go Method Sets - Quick Revision

## The rule

For defined type `T`:

- method set of `T`: methods with receiver `T`;
- method set of `*T`: methods with receiver `T` or `*T`.

So `*T` can satisfy an interface using either receiver style, while `T` cannot satisfy a contract requiring a pointer-receiver method.

```go
type Renamer interface{ Rename(string) }
func (u *User) Rename(name string) { u.name = name }

var _ Renamer = (*User)(nil)
// var _ Renamer = User{} // compile error
```

## Direct call trap

`user.Rename("x")` may compile because an addressable variable permits shorthand `(&user).Rename("x")`. Interface assignment does not add this shorthand: assigning `user` checks `User`'s method set exactly.

## Common mistake

Wiring a value in `main()` when only its pointer satisfies the consumer interface. This often appears after changing a method from a value to pointer receiver.

## Production example

Constructors for mutable services commonly return `*Service`, matching pointer-receiver interfaces. Compile-time assertions document intended contracts and fail close to the implementation when signatures change.

## 30-second answer

Method sets decide interface satisfaction. `T` has value-receiver methods; `*T` has both value- and pointer-receiver methods. The compiler may take an address for a direct call on an addressable value, but it does not change the type used for interface assignment. I use compile-time assertions for important contracts.

## Recall challenge

For two methods—one value receiver and one pointer receiver—write interface assignments for `T` and `*T` and predict all results.

Canonical: [[Go Method Sets]] · Drill: [[Correct Interface Invocation from Main - Drill]]

