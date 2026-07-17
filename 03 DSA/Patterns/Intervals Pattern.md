---
type: canonical
domain: dsa
topic: intervals
status: reference
source_conversations:
  - "DSA Plan for Working Professionals | 2025-07-14 | 6874a2d8-b030-8013-b0b6-a32294ecf165"
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Intervals Pattern

## Recognition clues

Ranges, bookings, schedules, overlaps, gaps, inserting a new range, or finding concurrent activity.

## Mental model

Sort by start so all possible overlaps arrive together. Maintain a merged frontier. The current interval either extends the last merged interval or starts a new disjoint component. Define whether touching endpoints overlap.

## Reusable Go template

```go
package main

import (
	"fmt"
	"sort"
)

type Interval struct { Start, End int }

func hasOverlap(intervals []Interval) bool {
	work := append([]Interval(nil), intervals...)
	sort.Slice(work, func(i, j int) bool { return work[i].Start < work[j].Start })
	for i := 1; i < len(work); i++ {
		if work[i].Start <= work[i-1].End { return true }
	}
	return false
}

func main() {
	fmt.Println(hasOverlap([]Interval{{5, 7}, {1, 3}, {3, 4}}))
}
```

## Complexity

Sorting solutions are `O(n log n)` time. The merge scan is `O(n)` and output may require `O(n)` space. Already sorted insert-interval scans can be `O(n)`.

## Common mistakes

- Failing to specify closed versus half-open intervals.
- Comparing with the previous input interval instead of the last merged interval.
- Sorting the caller's slice without declaring mutation.
- Replacing an end instead of taking `max(last.End,current.End)`.
- Forgetting empty input.

## Representative problems

[[Merge Intervals]], Insert Interval, Non-overlapping Intervals, Meeting Rooms, Meeting Rooms II.

## Modification questions

Preserve input; treat touching ranges as disjoint; return gaps; count maximum overlap; merge intervals arriving as a stream.

Related: [[Go Slices]], [[DSA Dashboard]].
