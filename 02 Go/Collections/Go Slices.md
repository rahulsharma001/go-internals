---
type: canonical
domain: go
topic: go-slices
status: implementation-needed
source_notes:
  - "[[99 Archive/Superseded Originals/root/T04 Arrays & Slice Internals]]"
  - "[[99 Archive/Superseded Originals/simplified/T04 Arrays & Slice Internals - Simplified]]"
  - "[[99 Archive/Superseded Originals/revision/T04 Arrays & Slice Internals - Revision]]"
---

# Go Slices

## Problem and mental model

Arrays have a fixed length that is part of their type. A slice is a small value describing a window over a backing array: it has a current length and capacity and refers to element storage. Copying a slice copies the descriptor, not the elements. Two slices can therefore share storage.

This explains the two rules that cause most implementation errors: element mutation can be visible through aliases, while `append` must be assigned because it returns the resulting slice descriptor and may allocate new storage.

## Essential operations

```go
var nilSlice []int                 // nil, len 0, cap 0
empty := []int{}                   // non-nil, len 0
withLength := make([]int, 3)       // [0 0 0]
withCapacity := make([]int, 0, 3)  // len 0, cap 3
values := []int{10, 20, 30}
values = append(values, 40)
copyOfValues := append([]int(nil), values...)
```

Valid indexes are `0` through `len(s)-1`. Capacity is how far the slice can grow from its starting position before new storage is required. Do not depend on a particular capacity-growth formula.

## Minimum executable example

```go
package main

import "fmt"

func appendValue(values []int, value int) []int {
	return append(values, value)
}

func main() {
	base := []int{10, 20, 30}
	alias := base[1:]
	alias[0] = 99
	fmt.Println(base) // [10 99 30]

	base = appendValue(base, 40)
	fmt.Println(base) // [10 99 30 40]

	independent := append([]int(nil), base...)
	independent[0] = -1
	fmt.Println(base[0], independent[0]) // 10 -1
}
```

## Dry run

`alias := base[1:]` points at the same backing array starting at the second element, so `alias[0]` changes `base[1]`. `appendValue` returns a descriptor that may refer to the old or a new array; assigning the result preserves it. Expanding into a new nil slice copies the elements and creates an independent result.

## Modification patterns

- Copy: `out := append([]T(nil), in...)` or allocate and `copy`.
- Filter without changing input: allocate `out` with capacity `len(in)` and append matches.
- Filter in place: reuse `in[:0]`; document that the input storage is modified.
- Delete while preserving order: `copy(s[i:], s[i+1:]); clear(s[len(s)-1:]); s = s[:len(s)-1]`.
- Reverse: swap elements from both ends.
- Prevent append from overwriting a following region: use a full slice expression such as `part := s[:n:n]`.

When deleting elements containing pointers, strings, slices, maps, or interfaces from a long-lived backing array, clear removed slots so unreachable objects are not kept alive through stale references.

## Production use and trade-offs

Preallocate when a reasonable upper bound is known, but avoid pretending an estimate is exact. Reusing storage reduces allocations but increases aliasing risk. Copying creates isolation at a memory and CPU cost. A tiny subslice can retain a large backing array; copy the needed region when the small result will outlive the large input.

Success path: ownership is clear, returned append results are captured, and mutating vs non-mutating behavior is documented. Failure path: a helper appends without returning the new slice, a subslice unexpectedly changes its parent, or a long-lived subslice retains far more memory than intended.

## Common mistakes

- Confusing length with capacity.
- Writing to `s[len(s)]` instead of appending.
- Ignoring `append`'s returned slice.
- Assuming passing a slice copies its elements.
- Returning a subslice when an independent copy is required.
- Treating nil and empty slices as identical at serialization boundaries.

## Interview questions

1. What is copied when a slice is passed to a function?
2. Why must the result of `append` be assigned or returned?
3. How do you produce an independent slice copy?
4. When is in-place filtering a poor choice?

## Active-recall drill

From a blank editor, implement copy, filter, delete, deduplicate, and reverse. Give each a complete `main()` invocation, then convert one function from non-mutating to in-place and explain the ownership change.

## Related notes

- [[Collection Transformations in Go]]
- [[Go Slice Internals]]
- [[Slice Creation and Modification - Drill]]
- [[Balanced Slice Groups - Drill]]
- [[Go Slices - Quick Revision]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
