---
type: problem
domain: dsa
status: reference-not-attempted
pattern: basic-dynamic-programming
source_conversations:
  - "DSA Intuition for Decode Ways | 2026-06-17 | 6a327c5f-c3e4-83ee-8fef-3cd2e2a77876"
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Climbing Stairs

LeetCode: https://leetcode.com/problems/climbing-stairs/

## Problem summary

Count distinct ways to reach step `n` when each move climbs one or two steps. This implementation returns 1 for `n=0` (the empty sequence) and 0 for negative input.

## Pattern

[[Basic Dynamic Programming Pattern]] — ways to reach `i` come from `i-1` and `i-2`.

## Brute-force intuition

Recursively try a one-step and two-step move at every state. The decision tree repeats the same remaining-step subproblems, taking exponential time.

## Optimal intuition

Define `ways(i)` as ways to reach step `i`. The final move came from exactly `i-1` or `i-2`, so `ways(i)=ways(i-1)+ways(i-2)`. Keep only two states.

## Dry run

Base `ways(0)=1`, `ways(1)=1`; then `ways(2)=2`, `ways(3)=3`, `ways(4)=5`.

## Complete Go solution

```go
package main

import "fmt"

func climbStairs(n int) int {
	if n < 0 { return 0 }
	if n <= 1 { return 1 }
	twoBack, oneBack := 1, 1
	for step := 2; step <= n; step++ {
		twoBack, oneBack = oneBack, twoBack+oneBack
	}
	return oneBack
}

func main() {
	for _, n := range []int{-1, 0, 1, 2, 5} { fmt.Println(n, climbStairs(n)) }
}
```

Run: `go run main.go`.

## Complexity

`O(n)` time and `O(1)` space.

## Edge cases

Negative policy; zero; one; integer overflow for sufficiently large `n`.

## Blank-editor success criteria

Finish in 15 minutes, write state/transition/base/answer before code, compile `0/1/2`, then allow steps of sizes `{1,2,3}`.

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded.
