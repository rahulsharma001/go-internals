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
