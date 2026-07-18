---
type: dsa-problem
language: go
company_focus:
  - apple
  - uber
priority: P0
pattern: pointer-reversal
difficulty:
leetcode_url: 
status: not-started
first_attempt_date:
last_attempt_date:
next_review_date:
attempt_count: 0
best_time_minutes:
needs_revisit: true
---
# Reverse Linked List

## Problem summary

Reverse a singly linked list in place and return the new head.

## Pattern

[[Linked Lists Pattern]] — save the outgoing edge before rewiring it.

## Brute-force intuition

Copy node values into a slice and build a new reversed list: `O(n)` time and `O(n)` extra space, but it does not reverse the original nodes.

## Optimal intuition

Maintain `previous`, `current`, and saved `next`. Redirect `current.Next` to `previous`, then advance both pointers. At termination, `previous` is the new head.

## Dry run

For `1→2→3`: save `2`, point `1→nil`; save `3`, point `2→1`; save `nil`, point `3→2`; return `3`.

## Complete Go solution

```go
package main

import "fmt"

type ListNode struct { Val int; Next *ListNode }

func reverseList(head *ListNode) *ListNode {
	var previous *ListNode
	for current := head; current != nil; {
		next := current.Next
		current.Next = previous
		previous = current
		current = next
	}
	return previous
}

func printList(head *ListNode) {
	for current := head; current != nil; current = current.Next { fmt.Printf("%d ", current.Val) }
	fmt.Println()
}

func main() {
	head := &ListNode{1, &ListNode{2, &ListNode{3, nil}}}
	printList(reverseList(head))
	printList(reverseList(&ListNode{Val: 7}))
	printList(reverseList(nil))
}
```

Run: `go run main.go`.

## Complexity

`O(n)` time and `O(1)` auxiliary space.

## Edge cases

Nil list; one node; two nodes; do not reuse the old head as if it remained the head.

## Blank-editor success criteria

Finish in 20 minutes, draw the three pointers, compile nil/one/many cases, then explain or implement reversal of a subrange `[left,right]`.

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded.
