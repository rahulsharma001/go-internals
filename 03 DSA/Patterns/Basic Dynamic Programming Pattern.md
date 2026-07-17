---
type: canonical
domain: dsa
topic: basic-dynamic-programming
status: reference
source_conversations:
  - "DSA Intuition for Decode Ways | 2026-06-17 | 6a327c5f-c3e4-83ee-8fef-3cd2e2a77876"
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Basic Dynamic Programming Pattern

## Recognition clues

Count ways, minimum/maximum value, choose/skip decisions, repeated subproblems, or a result for prefix `i` built from smaller prefixes.

## Mental model

Start with the decision tree, then name the repeated state. Write four lines before code: state meaning, transition, base cases, and final answer location. Bottom-up DP evaluates those states in dependency order; space optimization keeps only values the next state needs.

## Reusable Go template

```go
package main

import "fmt"

func maxNonAdjacent(nums []int) int {
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
	fmt.Println(maxNonAdjacent([]int{2, 7, 9, 3, 1}), maxNonAdjacent(nil))
}
```

## Complexity

One-dimensional prefix DP is often `O(n)` time and `O(n)` space, reducible to `O(1)` when only a constant number of earlier states are needed.

## Common mistakes

- Coding a recurrence without defining what `dp[i]` means.
- Wrong base cases for empty or length-one input.
- Updating compressed variables in the wrong order.
- Greedily taking the local best when future choices interact.
- Memorizing a formula without deriving choices and validity.

## Representative problems

[[Climbing Stairs]], [[House Robber]], Coin Change, Decode Ways, Longest Increasing Subsequence.

## Modification questions

Return the chosen items; add forbidden states; count modulo `m`; move from minimum to number of ways; reconstruct a path instead of only returning its score.

Related: [[DSA Dashboard]].
