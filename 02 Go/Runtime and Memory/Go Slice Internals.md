---
type: canonical
domain: go
topic: slice-internals
status: learning
aliases:
  - T04 Arrays & Slice Internals
source_notes:
  - "[[99 Archive/Superseded Originals/root/T04 Arrays & Slice Internals]]"
  - "[[99 Archive/Superseded Originals/simplified/T04 Arrays & Slice Internals - Simplified]]"
  - "[[99 Archive/Superseded Originals/revision/T04 Arrays & Slice Internals - Revision]]"
---

# Go Slice Internals

## Scope and mental model

The language-level canonical is [[Go Slices]]. Internally, a slice value describes a window over backing storage with a data reference, length, and capacity. Copying the descriptor can create aliases; `append` returns a new descriptor and may reuse or replace the backing array.

## Runtime-relevant consequences

- Element mutation is visible through slices that overlap the same backing array.
- An append within available capacity may reuse storage and overwrite a region visible through another alias.
- An append that needs more capacity allocates backing storage and copies elements; do not depend on a particular growth formula.
- A full slice expression such as `s[:n:n]` limits the resulting capacity and forces a later append past that limit to separate storage.
- A small live subslice can retain a much larger backing array. Copy the needed region when lifetime and profile evidence justify it.
- Removed pointer-bearing elements can keep referenced objects reachable until their slots are cleared or the backing array dies.

## Diagnostic example

```go
package main

import "fmt"

func main() {
	base := []int{1, 2, 3, 4}
	part := base[:2:2]
	part = append(part, 9)
	part[0] = 7
	fmt.Println(base) // [1 2 3 4]
	fmt.Println(part) // [7 2 9]
}
```

The capped capacity makes the append allocate separate backing storage. The program relies on documented slice behavior, not a runtime growth constant.

## Production and interview lens

Use this model to diagnose aliasing, allocation rate, and retained memory. Confirm performance claims with benchmarks and profiles. In interviews, explain descriptor copying, append reassignment, aliasing, capacity, and retention; label exact header layout and growth policy as implementation details.

## Related notes

- [[Go Slices]]
- [[Go Memory Allocation and Escape Analysis]]
- [[Go Garbage Collector]]
- [[Go Runtime Overview]]

Parent MOC: [[Go Map of Content]]
