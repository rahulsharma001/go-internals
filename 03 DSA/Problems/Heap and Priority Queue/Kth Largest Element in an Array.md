---
type: dsa-problem
language: go
company_focus:
  - apple
  - uber
priority: P0
pattern: heap-quickselect
difficulty:
leetcode_url: https://leetcode.com/problems/kth-largest-element-in-an-array/
status: not-started
first_attempt_date:
last_attempt_date:
next_review_date:
attempt_count: 0
best_time_minutes:
needs_revisit: true
source_conversations:
  - "Max Heap Approaches Java | 2026-02-09 | 698a2c0f-9aa8-8321-b0d6-9e6e751d4a8d"
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Kth Largest Element in an Array

LeetCode: https://leetcode.com/problems/kth-largest-element-in-an-array/

## Problem summary

Return the `k`th largest value, counting duplicates as separate positions. Reject invalid `k`.

## Pattern

[[Heaps Pattern]] — min-heap of the largest `k` values seen so far.

## Brute-force intuition

Copy and sort the entire slice, then index `len-k`: `O(n log n)` time and `O(n)` copy space.

## Optimal intuition

Keep only `k` candidates. When the min-heap grows past `k`, evict its smallest value. The root is then the `k`th largest.

## Dry run

`[3,2,1,5,6,4]`, `k=2`: after all insert/evict operations, heap holds `[5,6]`; root `5` is the second largest.

## Complete Go solution

```go
package main

import (
	"container/heap"
	"fmt"
)

type IntHeap []int
func (h IntHeap) Len() int { return len(h) }
func (h IntHeap) Less(i, j int) bool { return h[i] < h[j] }
func (h IntHeap) Swap(i, j int) { h[i], h[j] = h[j], h[i] }
func (h *IntHeap) Push(x any) { *h = append(*h, x.(int)) }
func (h *IntHeap) Pop() any { old := *h; n := len(old); x := old[n-1]; *h = old[:n-1]; return x }

func kthLargest(nums []int, k int) (int, bool) {
	if k < 1 || k > len(nums) { return 0, false }
	h := &IntHeap{}
	heap.Init(h)
	for _, value := range nums {
		heap.Push(h, value)
		if h.Len() > k { heap.Pop(h) }
	}
	return (*h)[0], true
}

func main() {
	for _, tc := range []struct{ nums []int; k int }{{[]int{3, 2, 1, 5, 6, 4}, 2}, {[]int{2, 2, 2}, 2}, {nil, 1}} {
		value, ok := kthLargest(tc.nums, tc.k)
		fmt.Println(value, ok)
	}
}
```

Run: `go run main.go`.

## Complexity

`O(n log k)` time and `O(k)` space.

## Edge cases

Invalid `k`; empty; duplicates; negative values; `k=1`; `k=len(nums)`.

## Blank-editor success criteria

Finish in 35 minutes, implement all five heap methods without a reference, compile invalid/duplicate cases, then adapt it to accept values incrementally as a stream.

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded. The historical heap source used Java; it does not count as Go completion.

## Problem in Simple Words

Return the value at descending rank k, counting duplicates.

## Example

[6,2,6,4], k=2 returns 6.

## Clarifying Questions

- May input be empty, invalid, or mutated?
- What duplicate, ordering, numeric, or node-identity guarantees apply?

## Pattern Recognition

- Signals in the question: size-k min-heap or quickselect.
- Likely data structure: the structure that directly represents the invariant.
- Common wrong approach: repeated scans or state updates that lose the invariant.
- Key invariant: A size-k heap contains the k largest processed values and its root is their kth largest.

## Approaches

### Brute Force

- Intuition: enumerate candidates directly.
- Complexity: derive during the cold attempt.
- Why it may fail: it repeats work and misses the expected bound.

### Better Approach

Use only if a genuine intermediate approach clarifies the progression.

### Optimal Approach

- Intuition and complete runnable reference: preserved above from the existing canonical note.
- Invariant: A size-k heap contains the k largest processed values and its root is their kth largest.
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
