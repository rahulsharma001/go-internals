---
type: coding-drill
domain: go
topic: grouping-collection-transformations
status: not-attempted
canonical: "[[Collection Transformations in Go]]"
---

# Grouping and Collection Transformations - Drill

## Problem

Given users with `Name`, `Team`, and `Active`, implement a transformation that filters inactive users and returns `map[string][]User` grouped by team. Preserve input order inside each group without mutating the input.

Input: `{A, backend, true}`, `{B, platform, false}`, `{C, backend, true}`. Expected output for key `backend`: `[{A backend true} {C backend true}]`; key `platform` must be absent.

## Constraints and starter signature

```go
func groupActiveByTeam(users []User) map[string][]User
```

- O(n) expected processing before any requested sorting.
- Do not use globals.
- Do not depend on map iteration order.
- Provide a complete `main()` that prints explicit keys and proves the input is unchanged.

## Edge cases and implementation checklist

- Nil/empty input; empty team; all inactive; duplicate names; one user.
- Initialize the map before writes.
- Append to the slice stored for each key.
- State whether returned `User` values share nested reference fields if the struct later gains them.

## Modification challenge

Return teams in stable alphabetical order and deduplicate users by name within a team. The existing type-parameter variation is preserved in [[Go Generics]], but it remains outside the active 30-day sprint and should be attempted only after the concrete version works and the topic is deliberately scheduled.

## Attempt record and re-test history

| Date | Time | Result | Hints | Failure category |
|---|---:|---|---|---|
| | | not attempted | | |

| Re-test date | Variant | Result | Remaining mistake |
|---|---|---|---|
| | stable / dedupe; generic deferred | | |

Related: [[Collection Transformations in Go]] · [[Go Maps]] · [[Go Slices]] · [[Go Generics]]

Index: [[Coding Drill Index]]
