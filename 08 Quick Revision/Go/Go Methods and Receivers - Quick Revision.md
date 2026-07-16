---
type: quick-revision
domain: go
topic: go-methods-receivers
canonical: "[[Go Methods and Receivers]]"
---

# Go Methods and Receivers - Quick Revision

## Mental model

The receiver is a parameter. A value receiver gets a copy of `T`; a pointer receiver gets a copied pointer that can mutate the original value.

## Selection checklist

Use a pointer receiver when the method changes receiver fields, the type should not be copied, identity is mutable, or receiver consistency requires it. A value receiver fits a small immutable value whose copies are meaningful. Do not decide from a rigid size threshold.

```go
func (c Counter) Value() int { return c.value }
func (c *Counter) Increment() { c.value++ }
```

`counter.Increment()` can be shorthand for `(&counter).Increment()` when `counter` is addressable. That convenience does not make `Counter` satisfy an interface requiring `Increment`; method sets use the exact assigned type.

## Common mistakes

- Expecting a value receiver to replace a field on the original.
- Copying a type containing synchronization state.
- Assuming automatic address-taking applies to interface assignment.
- Mixing receiver styles without a semantic reason.
- Believing a pointer receiver is required merely to modify elements of a referenced slice or map.

## Production example

Mutable services usually use pointer receivers. Small value objects can use value receivers. Replacing a slice field requires a pointer receiver even though changing existing slice elements may be visible through a value-receiver copy.

## 30-second answer

Receivers follow Go's value semantics. I use pointers for mutation, identity, or non-copyable types and values for small immutable value-like types. I keep style consistent and separately check method sets, because direct call shorthand does not determine interface satisfaction.

## Recall challenge

Predict whether scalar-field update, slice-element update, and slice-append field replacement persist under a value receiver.

Canonical: [[Go Methods and Receivers]] · Drill: [[Pointer and Value Receivers - Drill]]

