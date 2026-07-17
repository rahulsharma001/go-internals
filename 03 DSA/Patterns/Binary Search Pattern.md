---
type: canonical
domain: dsa
topic: binary-search
status: reference
source_conversations:
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Binary Search Pattern

## Recognition clues

Sorted input, a monotonic predicate, a boundary such as first/last valid, or “minimum speed/capacity/time that works.”

## Mental model

Maintain an interval guaranteed to contain every remaining candidate. The midpoint test discards one half. For answer search, define a monotonic `canDo(x)` such as `false false true true`; search for the first `true`.

## Reusable Go template

```go
package main

import "fmt"

func lowerBound(nums []int, target int) int {
	left, right := 0, len(nums)
	for left < right {
		mid := left + (right-left)/2
		if nums[mid] < target { left = mid + 1 } else { right = mid }
	}
	return left
}

func main() {
	nums := []int{1, 2, 2, 4}
	index := lowerBound(nums, 2)
	fmt.Println(index, index < len(nums) && nums[index] == 2)
}
```

## Complexity

Index search is `O(log n)` time and `O(1)` space. Answer search is `O(cost(predicate) × log(range))`.

## Common mistakes

- Mixing closed `[l,r]` and half-open `[l,r)` rules.
- Returning immediately when a boundary problem requires continuing left/right.
- Infinite loops from `left = mid` without a biased midpoint.
- Forgetting the final existence check after `lowerBound`.
- Using a non-monotonic predicate.

## Representative problems

[[Binary Search]], Search in Rotated Sorted Array, Find Minimum in Rotated Sorted Array, Koko Eating Bananas.

## Modification questions

Find first/last occurrence; return insertion point; search descending input; find minimum feasible capacity; handle duplicates.

Related: [[DSA Dashboard]].
