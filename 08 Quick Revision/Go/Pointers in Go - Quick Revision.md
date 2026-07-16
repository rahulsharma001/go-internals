---
type: quick-revision
domain: go
topic: pointers
canonical: "[[Pointers in Go]]"
---

# Pointers in Go - Quick Revision

## 30-second definition and mental model

A pointer value stores an address. Go passes that pointer by value; copied pointers can reach the same object. Pointers enable mutation and identity but introduce nil and shared-ownership concerns.

```go
x := 3
p := &x
*p = 4
```

## Five facts

1. `&x` takes an address; `*p` dereferences.
2. The zero pointer is `nil`.
3. Returning a pointer to a local is safe.
4. Pointer use does not by itself define stack versus heap placement.
5. Map elements are not addressable; use read-modify-write or intentional pointer values.

Common trap: saying Go passes values “by reference.”

Production example: a pointer receiver mutates a long-lived service component; the component's synchronization and nil invariants must be explicit.

Interview answer: “Everything is passed by value. A copied pointer value aliases the same pointee, so I use pointers for mutation, identity, unsafe/expensive copying, or meaningful optionality.”

Active recall: implement a nil-safe mutating helper, then redesign it to return a value.

Canonical: [[Pointers in Go]] · Related: [[Go Methods and Receivers]]

Index: [[Quick Revision Index]]
