---
type: problem
domain: dsa
status: reference-not-attempted
pattern: two-pointers
source_conversations:
  - "Two pointer questions FAANG | 2025-12-02 | 692e82d7-f7e4-8324-964d-f935b2756421"
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Container With Most Water

LeetCode: https://leetcode.com/problems/container-with-most-water/

## Problem summary

Choose two vertical lines that maximize `min(height[left],height[right]) × (right-left)`.

## Pattern

[[Two Pointers Pattern]] — shrink the range while eliminating the limiting wall.

## Brute-force intuition

Calculate every pair's area: `O(n²)` time.

## Optimal intuition

Start at maximum width. The shorter wall limits area. Moving the taller wall only reduces width without increasing the limiting height, so move the shorter wall.

## Dry run

For `[1,8,6,2,5,4,8,3,7]`, ends give area `8`; move left because height `1` is shorter. At indices `1` and `8`, area is `7×7=49`, the maximum.

## Complete Go solution

```go
package main

import "fmt"

func maxArea(height []int) int {
	left, right, best := 0, len(height)-1, 0
	for left < right {
		limit := height[left]
		if height[right] < limit { limit = height[right] }
		if area := limit * (right-left); area > best { best = area }
		if height[left] <= height[right] { left++ } else { right-- }
	}
	return best
}

func main() {
	fmt.Println(maxArea([]int{1, 8, 6, 2, 5, 4, 8, 3, 7}))
	fmt.Println(maxArea([]int{1, 1}))
	fmt.Println(maxArea(nil))
}
```

Run: `go run main.go`.

## Complexity

`O(n)` time and `O(1)` space.

## Edge cases

Empty/one element return zero; exactly two lines; equal heights; zeros.

## Blank-editor success criteria

Finish in 25 minutes, give the elimination proof before code, compile minimum input, then return the selected indices as well as the area.

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded.
