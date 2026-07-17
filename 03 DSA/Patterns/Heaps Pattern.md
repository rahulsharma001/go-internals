---
type: canonical
domain: dsa
topic: heaps
status: reference
source_conversations:
  - "Max Heap Approaches Java | 2026-02-09 | 698a2c0f-9aa8-8321-b0d6-9e6e751d4a8d"
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Heaps Pattern

## Recognition clues

Top/bottom `k`, repeated smallest/largest extraction, merging sorted streams, scheduling by priority, or maintaining a moving boundary item.

## Mental model

A heap exposes one extreme, not a fully sorted collection. To retain the largest `k`, keep a min-heap of size `k`; its root is the smallest retained value and the eviction boundary.

## Reusable Go template

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

func main() {
	h := &IntHeap{4, 1, 3}
	heap.Init(h)
	heap.Push(h, 2)
	fmt.Println(heap.Pop(h).(int))
}
```

## Complexity

Peek is `O(1)`; push/pop are `O(log n)`; heap initialization is `O(n)`. A size-`k` selection heap is `O(n log k)` time and `O(k)` space.

## Common mistakes

- Choosing a max-heap when retaining the largest `k` needs a min-heap boundary.
- Implementing `Push`/`Pop` with value receivers.
- Expecting heap iteration order to be sorted.
- Forgetting invalid `k` handling.
- Claiming heapify initialization is `O(n log n)`.

## Representative problems

[[Kth Largest Element in an Array]], Top K Frequent Elements, K Closest Points, Merge K Sorted Lists, Task Scheduler.

## Modification questions

Process a stream; make priorities stable; retain smallest `k`; merge iterators; compare heap selection with sorting/quickselect.

Related: [[Go DSA Containers]], [[DSA Dashboard]].
