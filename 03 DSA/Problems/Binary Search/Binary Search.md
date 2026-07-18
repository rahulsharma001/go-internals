---
type: dsa-problem
language: go
company_focus:
  - apple
  - uber
priority: P0
pattern: binary-search
difficulty:
leetcode_url: https://leetcode.com/problems/binary-search/
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
# Binary Search

LeetCode: https://leetcode.com/problems/binary-search/

## Problem summary

Return the index of a target in an ascending sorted slice, or `-1` when absent.

## Pattern

[[Binary Search Pattern]] — closed interval `[left,right]` containing every remaining candidate.

## Brute-force intuition

Scan from left to right: `O(n)` time.

## Optimal intuition

Compare the midpoint with target. Sorted order proves which half cannot contain the target. This version consistently uses a closed interval and `left <= right`.

## Dry run

`[-1,0,3,5,9,12]`, target `9`: mid index 2 gives `3`, discard left half; mid index 4 gives `9`, return 4.

## Complete Go solution

```go
package main

import "fmt"

func search(nums []int, target int) int {
	left, right := 0, len(nums)-1
	for left <= right {
		mid := left + (right-left)/2
		switch {
		case nums[mid] == target: return mid
		case nums[mid] < target: left = mid + 1
		default: right = mid - 1
		}
	}
	return -1
}

func main() {
	nums := []int{-1, 0, 3, 5, 9, 12}
	for _, target := range []int{9, -1, 12, 2} { fmt.Println(target, search(nums, target)) }
	fmt.Println(search(nil, 1))
}
```

Run: `go run main.go`.

## Complexity

`O(log n)` time and `O(1)` space.

## Edge cases

Empty; one value; first/last value; absent target; duplicates (any matching index is allowed here).

## Blank-editor success criteria

Finish in 15 minutes, state the interval invariant, compile both boundaries and missing target, then modify it to return the first occurrence among duplicates.

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded.

## Problem in Simple Words

Find a target index in ascending data or return absence.

## Example

[2,6,10], target 6 returns index 1.

## Clarifying Questions

- May input be empty, invalid, or mutated?
- What duplicate, ordering, numeric, or node-identity guarantees apply?

## Pattern Recognition

- Signals in the question: binary search.
- Likely data structure: the structure that directly represents the invariant.
- Common wrong approach: repeated scans or state updates that lose the invariant.
- Key invariant: If the target exists, it remains inside the active interval.

## Approaches

### Brute Force

- Intuition: enumerate candidates directly.
- Complexity: derive during the cold attempt.
- Why it may fail: it repeats work and misses the expected bound.

### Better Approach

Use only if a genuine intermediate approach clarifies the progression.

### Optimal Approach

- Intuition and complete runnable reference: preserved above from the existing canonical note.
- Invariant: If the target exists, it remains inside the active interval.
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
