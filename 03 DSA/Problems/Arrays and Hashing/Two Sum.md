---
type: dsa-problem
language: go
company_focus:
  - apple
  - uber
priority: P0
pattern: hash-map
difficulty:
leetcode_url: https://leetcode.com/problems/two-sum/
status: not-started
first_attempt_date:
last_attempt_date:
next_review_date:
attempt_count: 0
best_time_minutes:
needs_revisit: true
source_conversations:
  - "DSA Plan for Working Professionals | 2025-07-14 | 6874a2d8-b030-8013-b0b6-a32294ecf165"
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Two Sum

LeetCode: https://leetcode.com/problems/two-sum/

## Problem summary

Return two distinct indices whose values sum to the target; assume at most one solution in this executable version.

## Pattern

[[Arrays and Hash Maps Pattern]] — complement lookup in the scanned prefix.

## Brute-force intuition

Check every pair: `O(n²)` time and `O(1)` space.

## Optimal intuition

At index `i`, the only needed earlier value is `target-nums[i]`. Look it up before storing the current value so one element cannot match itself.

## Dry run

`[3,2,4]`, target `6`: store `3→0`; at `2`, complement `4` is missing, store `2→1`; at `4`, complement `2` maps to `1`, return `[1,2]`.

## Complete Go solution

```go
package main

import "fmt"

func twoSum(nums []int, target int) ([]int, bool) {
	indexByValue := make(map[int]int, len(nums))
	for i, value := range nums {
		if j, ok := indexByValue[target-value]; ok { return []int{j, i}, true }
		indexByValue[value] = i
	}
	return nil, false
}

func main() {
	for _, tc := range []struct{ nums []int; target int }{
		{[]int{2, 7, 11, 15}, 9}, {[]int{3, 3}, 6}, {[]int{}, 0}, {[]int{1, 2}, 9},
	} {
		indices, ok := twoSum(tc.nums, tc.target)
		fmt.Println(indices, ok)
	}
}
```

Run: `go run main.go`.

## Complexity

`O(n)` expected time and `O(n)` space.

## Edge cases

Duplicate values at distinct indices; negative values; zero; empty input; no solution.

## Blank-editor success criteria

Finish in 20 minutes, compile duplicate/no-solution cases, explain lookup-before-insert, then return a descriptive error instead of a boolean.

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded.
