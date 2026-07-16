---
type: quick-revision
domain: go
topic: go-slices
canonical: "[[Go Slices]]"
---

# Go Slices - Quick Revision

## Mental model

A slice is a copied descriptor over a backing array. It has length and capacity. Slice copies can share elements. `append` returns the resulting descriptor and may use new storage, so always assign or return it.

## Minimum syntax

```go
var nilSlice []int
empty := []int{}
fixedLen := make([]int, 3)
growing := make([]int, 0, 8)
growing = append(growing, 10)
clone := append([]int(nil), growing...)
```

Valid indexes stop at `len-1`; capacity is not indexable length. A nil slice and empty non-nil slice usually behave alike, but serialization or API contracts can distinguish them.

## Common mistakes

- Ignoring the result of `append`.
- Assuming a subslice is independent.
- Confusing `make([]T, n)` with `make([]T, 0, n)`.
- Returning a tiny subslice that retains a large backing array.
- Deleting pointer-like elements without clearing the unused tail.

## Production example

Copy an incoming byte region when the small result will outlive a large request buffer. Use in-place filtering only when ownership is exclusive and documented.

## 30-second answer

A slice is a value containing a view of an array. Passing it copies the view, so element mutations may be shared. Append can reuse or replace the backing array and returns the new view, which must be captured. I copy when isolation or lifetime requires it and reuse storage only with clear ownership.

## Recall challenge

Write copy, filter, delete, and reverse from a blank editor. Which mutate input? Which allocate?

Canonical: [[Go Slices]] · Drills: [[Slice Creation and Modification - Drill]], [[Balanced Slice Groups - Drill]]

Index: [[Quick Revision Index]]
