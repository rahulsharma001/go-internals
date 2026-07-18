---
type: dsa-problem
language: go
company_focus:
  - apple
  - uber
priority: P0
pattern: monotonic-stack
difficulty:
leetcode_url: https://leetcode.com/problems/daily-temperatures/
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
# Daily Temperatures

LeetCode: https://leetcode.com/problems/daily-temperatures/

## Problem summary

For each day, return how many days pass before a strictly warmer temperature; return zero if none exists.

## Pattern

[[Stack and Queue Pattern]] — decreasing stack of unresolved indices.

## Brute-force intuition

For every day scan forward for the first warmer day: `O(n²)` time.

## Optimal intuition

Indices on the stack have not yet found a warmer day and their temperatures are decreasing. A warmer current day resolves and pops every colder stack top.

## Dry run

`[73,74,75,71,69,72]`: day 1 resolves day 0; day 2 resolves day 1; day 5 resolves days 4 and 3. Day 2 remains unresolved in this prefix.

## Complete Go solution

```go
package main

import "fmt"

func dailyTemperatures(temperatures []int) []int {
	answer := make([]int, len(temperatures))
	stack := []int{}
	for i, temperature := range temperatures {
		for len(stack) > 0 && temperature > temperatures[stack[len(stack)-1]] {
			previous := stack[len(stack)-1]
			stack = stack[:len(stack)-1]
			answer[previous] = i - previous
		}
		stack = append(stack, i)
	}
	return answer
}

func main() {
	fmt.Println(dailyTemperatures([]int{73, 74, 75, 71, 69, 72, 76, 73}))
	fmt.Println(dailyTemperatures([]int{30, 29, 28}))
	fmt.Println(dailyTemperatures(nil))
}
```

Run: `go run main.go`.

## Complexity

`O(n)` time—each index is pushed and popped at most once—and `O(n)` space.

## Edge cases

Empty; one day; strictly decreasing; equal temperatures do not resolve each other; final unresolved days stay zero.

## Blank-editor success criteria

Finish in 30 minutes, explain amortized `O(n)`, compile decreasing/equal cases, then return the next-warmer index rather than the distance.

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded.

## Problem in Simple Words

For each day, find the distance to its next strictly warmer day.

## Example

[55,60,58] produces [1,0,0].

## Clarifying Questions

- May input be empty, invalid, or mutated?
- What duplicate, ordering, numeric, or node-identity guarantees apply?

## Pattern Recognition

- Signals in the question: monotonic stack.
- Likely data structure: the structure that directly represents the invariant.
- Common wrong approach: repeated scans or state updates that lose the invariant.
- Key invariant: Stack indices are unresolved and temperatures decrease from bottom to top.

## Approaches

### Brute Force

- Intuition: enumerate candidates directly.
- Complexity: derive during the cold attempt.
- Why it may fail: it repeats work and misses the expected bound.

### Better Approach

Use only if a genuine intermediate approach clarifies the progression.

### Optimal Approach

- Intuition and complete runnable reference: preserved above from the existing canonical note.
- Invariant: Stack indices are unresolved and temperatures decrease from bottom to top.
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
