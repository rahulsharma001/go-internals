---
type: canonical
domain: dsa
topic: stack-queue
status: reference
source_conversations:
  - "Stacks in DSA overview | 2025-10-21 | 68f79a94-fefc-8321-ba40-406cd54b27f0"
  - "Amazon SDE1 Queue Problems | 2026-07-14 | 6a562860-9374-83e8-972e-1d0ef82dff76"
---
# Stack and Queue Pattern

## Recognition clues

Nested matching, undo/reversal, next greater/smaller, unresolved candidates, level order, shortest path in an unweighted graph, or first-in-first-out simulation.

## Mental model

A stack keeps the most recent unresolved item. A monotonic stack removes items whose answer the current value resolves. A queue preserves discovery order; capture the queue length before a level when level boundaries matter.

## Reusable Go template

```go
package main

import "fmt"

func nextGreater(nums []int) []int {
	answer := make([]int, len(nums))
	for i := range answer { answer[i] = -1 }
	stack := []int{}
	for i, value := range nums {
		for len(stack) > 0 && value > nums[stack[len(stack)-1]] {
			index := stack[len(stack)-1]
			stack = stack[:len(stack)-1]
			answer[index] = value
		}
		stack = append(stack, i)
	}
	return answer
}

func main() { fmt.Println(nextGreater([]int{2, 1, 3})) }
```

## Complexity

Basic push/pop/enqueue/dequeue are `O(1)` amortized. Monotonic-stack scans are `O(n)` because each index is pushed and popped once. Queue storage is `O(n)`.

## Common mistakes

- Popping or peeking an empty slice.
- Storing values when distances/positions require indices.
- Calling a monotonic scan `O(n²)` because of the nested loop.
- Processing a growing queue without fixing the current level size.
- Re-slicing a huge queue forever without eventual compaction.

## Representative problems

[[Valid Parentheses]], Min Stack, [[Daily Temperatures]], Next Greater Element, Binary Tree Level Order Traversal, Rotting Oranges.

## Modification questions

Return the invalid index; return next-greater indices; make a generic stack; cap queue memory; process multiple BFS sources.

Related: [[Go DSA Containers]], [[Trees Pattern]], [[Graphs Pattern]].
