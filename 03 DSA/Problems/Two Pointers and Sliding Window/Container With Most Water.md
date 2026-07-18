---
type: dsa-problem
language: go
company_focus:
  - apple
  - uber
priority: P0
pattern: two-pointers
difficulty:
leetcode_url: https://leetcode.com/problems/container-with-most-water/
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

## Problem in Simple Words

Choose two heights whose width times shorter height is maximal.

## Example

[3,1,3] has area 6 from the outer pair.

## Clarifying Questions

- May input be empty, invalid, or mutated?
- What duplicate, ordering, numeric, or node-identity guarantees apply?

## Pattern Recognition

- Signals in the question: two pointers.
- Likely data structure: the structure that directly represents the invariant.
- Common wrong approach: repeated scans or state updates that lose the invariant.
- Key invariant: The shorter boundary is the only boundary whose movement could improve the limiting height.

## Approaches

### Brute Force

- Intuition: enumerate candidates directly.
- Complexity: derive during the cold attempt.
- Why it may fail: it repeats work and misses the expected bound.

### Better Approach

Use only if a genuine intermediate approach clarifies the progression.

### Optimal Approach

- Intuition and complete runnable reference: preserved above from the existing canonical note.
- Invariant: The shorter boundary is the only boundary whose movement could improve the limiting height.
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
