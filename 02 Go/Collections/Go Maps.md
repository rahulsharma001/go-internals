---
type: canonical
domain: go
topic: go-maps
status: implementation-needed
aliases:
  - T08 Map Internals
source_notes:
  - "[[99 Archive/Superseded Originals/root/T08 Map Internals]]"
  - "[[99 Archive/Superseded Originals/simplified/T08 Map Internals - Simplified]]"
  - "[[99 Archive/Superseded Originals/revision/T08 Map Internals - Revision]]"
---

# Go Maps

## Problem and mental model

A map associates comparable keys with values. The map value is a small handle to map state. Copying or passing that handle still follows Go's value semantics, but both handles can observe updates to the same map.

Maps are ideal for lookup, frequency counting, grouping, sets, and indexes. They do not preserve iteration order, and the zero value is readable but cannot be written to until initialized.

## Essential operations

```go
counts := map[string]int{"go": 1}
counts["go"]++
value, ok := counts["missing"]
delete(counts, "go")

var nilMap map[string]int
_ = nilMap["safe read"] // zero value
// nilMap["panic"] = 1  // panic: assignment to entry in nil map
```

Use the comma-ok form when “missing” differs from “present with the zero value.” Use `struct{}` or `bool` for set-like membership. A key must be comparable; slices, maps, and functions cannot be keys.

## Minimum executable example

```go
package main

import (
	"fmt"
	"sort"
)

func frequencies(words []string) map[string]int {
	counts := make(map[string]int, len(words))
	for _, word := range words {
		counts[word]++
	}
	return counts
}

func main() {
	counts := frequencies([]string{"go", "map", "go"})
	keys := make([]string, 0, len(counts))
	for key := range counts {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	for _, key := range keys {
		fmt.Printf("%s=%d\n", key, counts[key])
	}
}
```

Expected output is deterministic because the keys are sorted before printing:

```text
go=2
map=1
```

## Composite values

Appending to a slice stored in a map is direct because the result is assigned back:

```go
groups := make(map[string][]string)
groups["backend"] = append(groups["backend"], "Go")
```

For a map of struct values, an indexed value is not addressable. Use copy-edit-write:

```go
user := users[id]
user.Name = "updated"
users[id] = user
```

Alternatively store pointers when shared mutable identity is intentional, accepting nil and aliasing risks.

## Dry run and failure path

`frequencies` starts with an initialized map. A missing key lookup produces `0`, so `counts[word]++` works for both first and later occurrences. Direct iteration would produce an unspecified order, so the program collects and sorts keys.

Success path: the map is initialized, absence semantics are explicit, and order-sensitive output is sorted. Failure path: code writes to a nil map, treats missing as equivalent to stored zero, mutates a struct map value in place, or depends on iteration order.

## Production use and trade-offs

Maps are not safe for unsynchronized concurrent reads and writes. Concurrency ownership belongs in a later-stage note; at this foundation stage, keep a map owned by one goroutine or protect it using an appropriate synchronization design. Supplying a size hint can reduce growth when a reasonable estimate exists, but correctness must not depend on it.

Map values make lookup concise; slices are better when stable order and sequential traversal dominate. When deterministic output matters—tests, APIs, logs, signatures—extract and sort keys.

## Common mistakes

- Writing to a nil map.
- Omitting comma-ok when stored zero is meaningful.
- Taking the address of a map element or changing a struct field in place.
- Assuming iteration order.
- Using a slice as a key.
- Forgetting to assign an appended slice back to its map entry in more complex expressions.

## Interview questions

1. How do missing-key reads behave, and when is comma-ok required?
2. Why can a map of structs require copy-edit-write?
3. How do you make map output deterministic?
4. What does copying a map value copy?

## Active-recall drill

Implement frequency counting, grouping, a set, a nested map, and a map whose values are slices. Then modify one solution to emit stable output without changing the map itself.

## Related notes

- [[Collection Transformations in Go]]
- [[Map Frequency Counting - Drill]]
- [[Nested Maps and Slice Values - Drill]]
- [[Go Maps - Quick Revision]]
- [[Map Syntax Failure]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
