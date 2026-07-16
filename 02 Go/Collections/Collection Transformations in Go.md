---
type: canonical
domain: go
topic: go-collection-transformations
status: implementation-needed
source_notes:
  - "[[99 Archive/Superseded Originals/root/T04 Arrays & Slice Internals]]"
  - "[[99 Archive/Superseded Originals/root/T08 Map Internals]]"
  - "[[99 Archive/Superseded Originals/exercises/T04 Arrays & Slice Internals - Exercises]]"
  - "[[99 Archive/Superseded Originals/exercises/T08 Map Internals - Exercises]]"
---

# Collection Transformations in Go

## Problem and mental model

Interview code frequently moves between slices and maps: filter a sequence, count or group values, deduplicate, index records, flatten groups, or restore stable order. The decision is driven by the required output and ownership:

| Need | Primary shape |
|---|---|
| Preserve input order | slice |
| Fast lookup or counting | map |
| Deduplicate while preserving order | slice result + map set |
| Group records by key | map of slices |
| Deterministic map output | extract keys + sort |
| Balanced contiguous groups | slice of slices |

Decide first whether the input may be mutated. Non-mutating functions are safer at boundaries; in-place transformations can save allocations when ownership is exclusive.

## Minimum executable example

```go
package main

import "fmt"

func uniqueInOrder(values []int) []int {
	seen := make(map[int]struct{}, len(values))
	out := make([]int, 0, len(values))
	for _, value := range values {
		if _, exists := seen[value]; exists {
			continue
		}
		seen[value] = struct{}{}
		out = append(out, value)
	}
	return out
}

func main() {
	input := []int{3, 1, 3, 2, 1}
	fmt.Println(uniqueInOrder(input)) // [3 1 2]
	fmt.Println(input)                // unchanged
}
```

## Core patterns

Filter to a new slice:

```go
out := make([]T, 0, len(in))
for _, value := range in {
	if keep(value) {
		out = append(out, value)
	}
}
```

Group by key:

```go
groups := make(map[K][]T)
for _, value := range in {
	key := keyFor(value)
	groups[key] = append(groups[key], value)
}
```

Build an index:

```go
byID := make(map[ID]Record, len(records))
for _, record := range records {
	byID[record.ID] = record
}
```

When duplicate keys are possible, decide explicitly whether later values overwrite, earlier values win, or duplicates are errors.

## Dry run

`uniqueInOrder` scans left to right. The map records membership but never determines output order. A value is appended only on its first occurrence, so the output is stable and the input stays unchanged. Time is proportional to input length on average; extra space grows with distinct values.

## Balanced partitioning

For `n` items and `k` non-empty groups, each group receives `n/k` elements and the first `n%k` groups receive one extra. Reject or define behavior for `k <= 0`; when empty groups are forbidden, cap `k` at `n`. This is a collection-fluency task, not a new DSA pattern canonical.

## Production use and trade-offs

Preallocating to an upper bound avoids some growth but may reserve unused space. Maps provide efficient membership and grouping but lose order. Sorting restores deterministic order at additional time and memory cost. In-place filtering is allocation-efficient but may retain references in the unused tail and surprises callers when ownership is unclear.

Success path: output order, duplicate policy, mutation policy, and empty-input behavior are explicit. Failure path: transformation silently changes its input, map iteration leaks nondeterminism, duplicate IDs overwrite unexpectedly, or nested map levels are not initialized.

## Common mistakes

- Translating Java collection APIs into unnecessary helper types instead of direct loops.
- Using global accumulators.
- Returning aliased storage when the caller expects independence.
- Forgetting stable ordering requirements.
- Failing to initialize an inner map.
- Adding capacity optimization before behavior is correct.

## Interview questions

1. How do you deduplicate while preserving first-seen order?
2. When would you choose in-place filtering?
3. How do you make grouping output deterministic?
4. What duplicate-key policy does your slice-to-map conversion use?

## Active-recall drill

Implement filter, frequency, grouping, deduplication, index-by-ID, and balanced partitioning without helper libraries. State time/space costs, then modify one function to preserve stable output and another to avoid mutating input.

## Related notes

- [[Go Slices]]
- [[Go Maps]]
- [[Balanced Slice Groups - Drill]]
- [[Map Frequency Counting - Drill]]
- [[Nested Maps and Slice Values - Drill]]
- [[Collection Transformations in Go - Quick Revision]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
