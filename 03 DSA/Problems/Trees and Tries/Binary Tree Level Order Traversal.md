---
type: dsa-problem
language: go
company_focus:
  - apple
  - uber
priority: P0
pattern: breadth-first-search
difficulty:
leetcode_url: https://leetcode.com/problems/binary-tree-level-order-traversal/
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
# Binary Tree Level Order Traversal

LeetCode: https://leetcode.com/problems/binary-tree-level-order-traversal/

## Problem summary

Return node values grouped by depth from left to right.

## Pattern

[[Trees Pattern]] plus [[Stack and Queue Pattern]] — BFS with a fixed level size.

## Brute-force intuition

Compute height, then recursively collect every level separately; a skewed tree can take `O(n²)` time.

## Optimal intuition

The queue holds the current frontier followed by later nodes. Capture `levelSize := len(queue)-head` before processing, consume exactly that many nodes, and enqueue their children.

## Dry run

For `3 / 9,20 / 15,7`: queue starts `[3]`, size 1 produces `[3]`; queue frontier becomes `[9,20]`, size 2 produces `[9,20]`; then `[15,7]`.

## Complete Go solution

```go
package main

import "fmt"

type TreeNode struct { Val int; Left, Right *TreeNode }

func levelOrder(root *TreeNode) [][]int {
	if root == nil { return [][]int{} }
	result := [][]int{}
	queue := []*TreeNode{root}
	for head := 0; head < len(queue); {
		levelSize := len(queue) - head
		level := make([]int, 0, levelSize)
		for i := 0; i < levelSize; i++ {
			node := queue[head]
			head++
			level = append(level, node.Val)
			if node.Left != nil { queue = append(queue, node.Left) }
			if node.Right != nil { queue = append(queue, node.Right) }
		}
		result = append(result, level)
	}
	return result
}

func main() {
	root := &TreeNode{Val: 3, Left: &TreeNode{Val: 9}, Right: &TreeNode{Val: 20, Left: &TreeNode{Val: 15}, Right: &TreeNode{Val: 7}}}
	fmt.Println(levelOrder(root))
	fmt.Println(levelOrder(&TreeNode{Val: 1}))
	fmt.Println(levelOrder(nil))
}
```

Run: `go run main.go`.

## Complexity

`O(n)` time and `O(n)` queue/output space; auxiliary frontier space is `O(width)` conceptually.

## Edge cases

Nil; single node; left/right-skewed; sparse tree; ensure children added during a level are not processed in that same level.

## Blank-editor success criteria

Finish in 30 minutes, explain level-size capture, compile nil/single/skewed cases, then return bottom-up level order.

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded.
