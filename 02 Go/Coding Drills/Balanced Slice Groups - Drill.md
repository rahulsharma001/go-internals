---
type: coding-drill
domain: go
topic: balanced-slice-groups
status: not-attempted
canonical: "[[Collection Transformations in Go]]"
---

# Balanced Slice Groups - Drill

## Problem

Implement `balancedGroups(values []int, groupCount int) ([][]int, error)`. Produce contiguous, non-empty groups whose sizes differ by at most one. Earlier groups receive any remainder.

Examples:

- `[1 2 3 4 5 6 7]`, `3` → `[[1 2 3] [4 5] [6 7]]`
- `[1 2]`, `5` → `[[1] [2]]`
- any values, `0` → error

Invoke all three cases from `main()` and handle the error.

## Constraints and edge cases

- Preserve input order.
- Do not create empty groups.
- Do not mutate elements.
- Decide and document whether group slices may share the input backing array. The reference solution does share it.

## Modification challenge

Return independent group copies, then adapt the function for `[]string` without using `any`.

## Attempt record

| Date | Time | Result | Hints | Failure category |
|---|---:|---|---|---|
| | | not attempted | | |

## Re-test history

| Date | Variant | Result | Remaining mistake |
|---|---|---|---|
| | shared / copied groups | | |

<details>
<summary>Reference solution — reveal only after an attempt</summary>

```go
package main

import (
	"errors"
	"fmt"
)

func balancedGroups(values []int, groupCount int) ([][]int, error) {
	if groupCount <= 0 {
		return nil, errors.New("group count must be positive")
	}
	if len(values) == 0 {
		return [][]int{}, nil
	}
	if groupCount > len(values) {
		groupCount = len(values)
	}

	base := len(values) / groupCount
	remainder := len(values) % groupCount
	groups := make([][]int, 0, groupCount)
	start := 0
	for i := 0; i < groupCount; i++ {
		size := base
		if i < remainder {
			size++
		}
		end := start + size
		groups = append(groups, values[start:end])
		start = end
	}
	return groups, nil
}

func main() {
	for _, test := range []struct {
		values []int
		groups int
	}{
		{[]int{1, 2, 3, 4, 5, 6, 7}, 3},
		{[]int{1, 2}, 5},
		{[]int{1, 2}, 0},
	} {
		result, err := balancedGroups(test.values, test.groups)
		if err != nil {
			fmt.Println("error:", err)
			continue
		}
		fmt.Println(result)
	}
}
```

</details>

Related: [[Go Slices]] · [[Collection Transformations in Go]]

