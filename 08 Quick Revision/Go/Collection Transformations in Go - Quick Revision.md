---
type: quick-revision
domain: go
topic: go-collection-transformations
canonical: "[[Collection Transformations in Go]]"
---

# Collection Transformations in Go - Quick Revision

## Decision table

| Need | Shape |
|---|---|
| Preserve order | slice |
| Lookup/count/set | map |
| Stable dedupe | result slice + seen map |
| Group by key | map of slices |
| Deterministic map output | keys slice + sort |
| Balanced contiguous chunks | slice of slices |

## Core loops

Filter to a new result with `out := make([]T, 0, len(in))`, range over input, and append matches. Group with `groups[key] = append(groups[key], value)`. Build an index with `byID[record.ID] = record` after deciding whether duplicate IDs overwrite or fail.

## Common mistake

The transformation's ownership contract is implicit. An in-place filter unexpectedly changes shared input, map iteration leaks unstable ordering, or a duplicate silently overwrites a record.

## Production example

Convert database rows to an ID index for repeated lookup, then emit a stable response using the original slice order or sorted keys. Preallocate from a reasonable upper bound only after correctness is clear.

## 30-second answer

I choose slices for order and maps for lookup, counting, or grouping. I state whether the input may be mutated, define duplicate and missing-key behavior, and restore order explicitly when needed. Stable dedupe uses both a result slice and a membership map; grouping uses a map of slices.

## Recall challenge

Write stable dedupe, index-by-ID, group-by-key, and balanced partitioning. State mutation, order, duplicate policy, and time/space cost for each.

Canonical: [[Collection Transformations in Go]] · Drills: [[Balanced Slice Groups - Drill]], [[Nested Maps and Slice Values - Drill]]

