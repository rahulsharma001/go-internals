---
type: problem
domain: dsa
status: reference-not-attempted
pattern: basic-dynamic-programming
source_conversations:
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# House Robber

LeetCode: https://leetcode.com/problems/house-robber/

## Problem summary

Return the maximum sum obtainable from non-adjacent non-negative house values.

## Pattern

[[Basic Dynamic Programming Pattern]] — at each house, choose between skip and take-plus-two-back.

## Brute-force intuition

Recursively branch into taking or skipping each house, generating `O(2^n)` choice paths.

## Optimal intuition

Let `best(i)` be the best result through index `i`. Either skip `i` and keep `best(i-1)`, or take it and add `best(i-2)`. Only two previous values are needed.

## Dry run

`[2,7,9,3,1]`: best prefixes become `2,7,11,11,12`. At value `9`, taking gives `2+9=11`; at final `1`, taking gives `11+1=12`.

## Complete Go solution

```go
package main

import "fmt"

func rob(nums []int) int {
	twoBack, oneBack := 0, 0
	for _, value := range nums {
		take := twoBack + value
		skip := oneBack
		current := skip
		if take > skip { current = take }
		twoBack, oneBack = oneBack, current
	}
	return oneBack
}

func main() {
	fmt.Println(rob([]int{1, 2, 3, 1}))
	fmt.Println(rob([]int{2, 7, 9, 3, 1}))
	fmt.Println(rob(nil))
	fmt.Println(rob([]int{5}))
}
```

Run: `go run main.go`.

## Complexity

`O(n)` time and `O(1)` space.

## Edge cases

Empty; one/two houses; equal choices; zeros. Negative values are outside the original problem contract and need a stated policy.

## Blank-editor success criteria

Finish in 20 minutes, define the DP state aloud, compile empty/one/many cases, then return the chosen house indices or adapt to circular houses.

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded.
