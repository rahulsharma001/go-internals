---
type: dsa-problem
language: go
company_focus:
  - apple
  - uber
priority: P0
pattern: two-pointers
difficulty:
leetcode_url: https://leetcode.com/problems/3sum/
status: not-started
first_attempt_date:
last_attempt_date:
next_review_date:
attempt_count: 0
best_time_minutes:
needs_revisit: true
source_conversations:
  - "Two pointer questions FAANG | 2025-12-02 | 692e82d7-f7e4-8324-964d-f935b2756421"
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# 3Sum

LeetCode: https://leetcode.com/problems/3sum/

## Problem summary

Return all unique value triplets whose sum is zero.

## Pattern

[[Two Pointers Pattern]] — sort, fix one value, and search the remaining range from both ends.

## Brute-force intuition

Enumerate every triplet and deduplicate results: `O(n³)` time.

## Optimal intuition

After sorting, fix `i`. The remaining target is `-nums[i]`; a left/right scan eliminates one side per comparison. Skip equal fixed values and equal pointer values after recording a solution.

## Dry run

Sorted `[-4,-1,-1,0,1,2]`: with fixed `-1` at index 1, `left=-1`, `right=2` gives `0`, record `[-1,-1,2]`; then `left=0`, `right=1` gives `0`, record `[-1,0,1]`.

## Complete Go solution

```go
package main

import (
	"fmt"
	"sort"
)

func threeSum(nums []int) [][]int {
	work := append([]int(nil), nums...)
	sort.Ints(work)
	result := [][]int{}
	for i := 0; i < len(work)-2; i++ {
		if i > 0 && work[i] == work[i-1] { continue }
		left, right := i+1, len(work)-1
		for left < right {
			sum := work[i] + work[left] + work[right]
			switch {
			case sum < 0: left++
			case sum > 0: right--
			default:
				result = append(result, []int{work[i], work[left], work[right]})
				left++; right--
				for left < right && work[left] == work[left-1] { left++ }
				for left < right && work[right] == work[right+1] { right-- }
			}
		}
	}
	return result
}

func main() {
	fmt.Println(threeSum([]int{-1, 0, 1, 2, -1, -4}))
	fmt.Println(threeSum([]int{0, 0, 0, 0}))
	fmt.Println(threeSum([]int{1, 2, -2, -1}))
}
```

Run: `go run main.go`.

## Complexity

`O(n²)` time and `O(n)` space here for the non-mutating sorted copy, excluding output.

## Edge cases

Fewer than three values; all zeros; many duplicates; no answer; input must remain unchanged.

## Blank-editor success criteria

Finish in 40 minutes, derive all duplicate skips, compile all-zero/no-answer cases, then change the function to solve a non-zero target without mutating input.

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded.
