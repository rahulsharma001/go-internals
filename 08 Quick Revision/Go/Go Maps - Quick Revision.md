---
type: quick-revision
domain: go
topic: go-maps
canonical: "[[Go Maps]]"
---

# Go Maps - Quick Revision

## Mental model

A map connects comparable keys to values. Copying a map value copies a handle; updates through either handle reach the same map state. Iteration order is unspecified.

## Minimum syntax

```go
counts := make(map[string]int)
counts["go"]++
value, ok := counts["go"]
delete(counts, "go")

groups := map[string][]string{}
groups["backend"] = append(groups["backend"], "Go")
```

Nil-map reads return the value type's zero value. Nil-map writes panic. Use comma-ok when missing differs from a stored zero.

## Common mistakes

- Writing to a nil map.
- Depending on iteration order.
- Using a slice, map, or function as a key.
- Trying to update a field of a struct stored directly in a map; use copy-edit-write.
- Omitting comma-ok when absence matters.

## Production example

Use a map to index records by ID or group them by status. For deterministic API output, tests, or signatures, extract keys and sort them before traversal. Do not share a map across concurrent readers/writers without an ownership or synchronization design.

## 30-second answer

Go maps provide lookup and grouping with comparable keys. Missing reads return zero, and comma-ok distinguishes absence. The zero map is readable but not writable. Map iteration order is unspecified, map elements are not addressable, and concurrent access needs explicit design. Copying a map variable does not clone its entries.

## Recall challenge

Implement frequency counting, grouping, a set, and stable output. Explain the absent-versus-zero policy for each.

Canonical: [[Go Maps]] · Drills: [[Map Frequency Counting - Drill]], [[Nested Maps and Slice Values - Drill]]

