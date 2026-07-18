---
type: dsa-problem
language: go
company_focus:
  - apple
  - uber
priority: P0
pattern: one-dimensional-dp
difficulty:
leetcode_url: https://leetcode.com/problems/house-robber/
status: not-started
first_attempt_date:
last_attempt_date:
next_review_date:
attempt_count: 0
best_time_minutes:
needs_revisit: true
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

## Problem in Simple Words

Maximize the sum selected from non-adjacent positions.

## Example

[4,1,5] returns 9.

## Clarifying Questions

- May input be empty, invalid, or mutated?
- What duplicate, ordering, numeric, or node-identity guarantees apply?

## Pattern Recognition

- Signals in the question: one-dimensional dynamic programming.
- Likely data structure: the structure that directly represents the invariant.
- Common wrong approach: repeated scans or state updates that lose the invariant.
- Key invariant: At each index, best is max(skip current, take current plus best two positions back).

## Approaches

### Brute Force

- Intuition: enumerate candidates directly.
- Complexity: derive during the cold attempt.
- Why it may fail: it repeats work and misses the expected bound.

### Better Approach

Use only if a genuine intermediate approach clarifies the progression.

### Optimal Approach

- Intuition and complete runnable reference: preserved above from the existing canonical note.
- Invariant: At each index, best is max(skip current, take current plus best two positions back).
- Complexity: verify the bound above during explanation.

## Small Dry Run

Reconstruct the existing dry run without looking, then add one adversarial case.

## Go-Specific Notes

Check slice initialization, map membership, pointer rewiring, queue head indexing, recursive closure declaration, heap pointer receivers, input mutation, and byte/rune semantics as applicable.

## Implementation

The pre-existing executable reference above is preserved. For practice, close this note and reproduce a complete main() or test invocation from a blank editor.

## Tests and Edge Cases

Re-run the preserved edge cases and add one case that breaks the tempting wrong approach.

## Explain Aloud

Restate → pattern → invariant → one transition → complexity → Go detail → variation, within 60–90 seconds.

## Variations and Follow-ups

Make one constraint change after a clean reconstruction.

## Mistakes I Made

None recorded. Add only observed mistakes from an actual attempt.

## Review History

Use the preserved re-attempt table above and the central tracker; never infer an attempt from the reference solution.
