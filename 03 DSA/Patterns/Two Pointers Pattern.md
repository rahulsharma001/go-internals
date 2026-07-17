---
type: canonical
domain: dsa
topic: two-pointers
status: reference
source_conversations:
  - "Two pointer questions FAANG | 2025-12-02 | 692e82d7-f7e4-8324-964d-f935b2756421"
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Two Pointers Pattern

## Recognition clues

Sorted pair/triplet search, comparing both ends, in-place compaction, partitions, or a proof that one pointer move eliminates candidates.

## Mental model

Pointers represent the remaining search space. Every move must be justified: in a sorted pair search, a sum that is too small eliminates the current left value; in container area, the shorter wall is the only wall whose replacement might increase the limiting height.

## Reusable Go template

```go
package main

import "fmt"

func pairInSorted(nums []int, target int) ([]int, bool) {
	left, right := 0, len(nums)-1
	for left < right {
		sum := nums[left] + nums[right]
		switch {
		case sum == target:
			return []int{left, right}, true
		case sum < target:
			left++
		default:
			right--
		}
	}
	return nil, false
}

func main() {
	indices, ok := pairInSorted([]int{1, 2, 4, 7}, 6)
	fmt.Println(indices, ok)
}
```

## Complexity

The scan is commonly `O(n)` time and `O(1)` space; sorting first makes it `O(n log n)` time and may mutate input.

## Common mistakes

- Applying opposite pointers without sorted/monotonic structure.
- Moving both pointers without proving it is safe.
- Failing to skip duplicates after recording a 3Sum result.
- Losing original indices after sorting.
- Using `left <= right` when the problem requires two distinct elements.

## Representative problems

Valid Palindrome, Two Sum II, [[3Sum]], [[Container With Most Water]], Move Zeroes, Sort Colors.

## Modification questions

Return indices rather than value; preserve caller input; support all unique pairs; change exact target to closest target; stream the input.

Related: [[Go Slices]], [[DSA Dashboard]].
