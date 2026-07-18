---
type: dsa-problem
language: go
company_focus:
  - apple
  - uber
priority: P0
pattern: interval-sorting
difficulty:
leetcode_url: https://leetcode.com/problems/merge-intervals/
status: not-started
first_attempt_date:
last_attempt_date:
next_review_date:
attempt_count: 0
best_time_minutes:
needs_revisit: true
source_conversations:
  - "DSA Plan for Working Professionals | 2025-07-14 | 6874a2d8-b030-8013-b0b6-a32294ecf165"
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Merge Intervals

LeetCode: https://leetcode.com/problems/merge-intervals/

## Problem summary

Merge overlapping closed intervals and return them ordered by start. This implementation preserves the caller's input.

## Pattern

[[Intervals Pattern]] — sort by start and maintain the last merged frontier.

## Brute-force intuition

Repeatedly search all pairs for an overlap, merge one pair, and restart; this can become `O(n²)` and is awkward to make deterministic.

## Optimal intuition

Once sorted by start, the current interval can overlap only the last merged interval. Extend its end with `max`; otherwise append a new interval.

## Dry run

Sorted `[[1,3],[2,6],[8,10],[15,18]]`: `[2,6]` overlaps `[1,3]`, producing `[1,6]`; the later two start after the current end, so both append.

## Complete Go solution

```go
package main

import (
	"fmt"
	"sort"
)

func merge(intervals [][]int) [][]int {
	if len(intervals) == 0 { return [][]int{} }
	work := make([][]int, len(intervals))
	for i, interval := range intervals { work[i] = []int{interval[0], interval[1]} }
	sort.Slice(work, func(i, j int) bool { return work[i][0] < work[j][0] })
	result := [][]int{work[0]}
	for _, current := range work[1:] {
		last := result[len(result)-1]
		if current[0] <= last[1] {
			if current[1] > last[1] { last[1] = current[1] }
		} else {
			result = append(result, current)
		}
	}
	return result
}

func main() {
	input := [][]int{{1, 3}, {2, 6}, {8, 10}, {15, 18}}
	fmt.Println(merge(input), input)
	fmt.Println(merge([][]int{{1, 4}, {4, 5}}))
	fmt.Println(merge(nil))
}
```

Run: `go run main.go`. Each input interval is assumed to contain exactly two values with `start <= end`.

## Complexity

`O(n log n)` time and `O(n)` space for copied input/output.

## Edge cases

Empty; one interval; nested intervals; touching endpoints merge because intervals are closed; duplicates; caller input remains unchanged.

## Blank-editor success criteria

Finish in 35 minutes, state endpoint semantics and mutation policy, compile empty/nested/touching cases, then change touching intervals to remain separate.

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded.
