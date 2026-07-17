---
type: canonical
domain: dsa
topic: linked-lists
status: reference
---
# Linked Lists Pattern

## Recognition clues

Pointer rewiring, in-place insertion/deletion, reversal, merging sorted nodes, cycle detection, or finding a midpoint without random access.

## Mental model

Every node owns a `Next` edge. Before overwriting an edge, save the old destination. Dummy nodes remove special cases at the head. Slow/fast pointers exploit different traversal speeds.

## Reusable Go template

```go
package main

import "fmt"

type ListNode struct { Val int; Next *ListNode }

func values(head *ListNode) []int {
	result := []int{}
	for current := head; current != nil; current = current.Next {
		result = append(result, current.Val)
	}
	return result
}

func main() {
	head := &ListNode{Val: 1, Next: &ListNode{Val: 2}}
	fmt.Println(values(head), values(nil))
}
```

## Complexity

Most single-pass operations are `O(n)` time and `O(1)` auxiliary space. Recursive traversal uses `O(n)` call-stack space.

## Common mistakes

- Losing the remainder after overwriting `Next`.
- Returning the old head after reversal.
- Dereferencing `fast.Next` without first checking `fast != nil`.
- Comparing node values instead of node identity for cycles/intersection.
- Omitting empty and single-node invocations.

## Representative problems

[[Reverse Linked List]], Merge Two Sorted Lists, Linked List Cycle, Reorder List, Remove Nth Node From End.

## Modification questions

Reverse only `[left,right]`; preserve input; merge `k` lists; detect and return cycle entry; implement doubly linked nodes.

Related: [[Go Structs and Constructors]], [[Pointers in Go]], [[DSA Dashboard]].
