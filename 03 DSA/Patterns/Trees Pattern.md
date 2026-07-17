---
type: canonical
domain: dsa
topic: trees
status: reference
source_conversations:
  - "Tree Inversion Problem Explanation | 2026-05-29 | 6a198eef-e804-8321-af27-b40d6202330c"
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Trees Pattern

## Recognition clues

Hierarchy, ancestor/descendant relations, subtree properties, path aggregation, depth/height, or level-by-level traversal.

## Mental model

For DFS ask: what does the current call receive, what do children return, and what is combined here? Preorder acts before children; postorder needs child results first. BFS processes a frontier and naturally exposes levels.

## Reusable Go template

```go
package main

import "fmt"

type TreeNode struct { Val int; Left, Right *TreeNode }

func depth(root *TreeNode) int {
	if root == nil { return 0 }
	left, right := depth(root.Left), depth(root.Right)
	if left > right { return left + 1 }
	return right + 1
}

func main() {
	root := &TreeNode{Val: 1, Left: &TreeNode{Val: 2}}
	fmt.Println(depth(root), depth(nil))
}
```

## Complexity

Full traversals are `O(n)` time. Recursive DFS uses `O(h)` call-stack space; BFS uses up to `O(w)` queue space.

## Common mistakes

- Confusing depth in nodes with diameter in edges.
- Omitting the nil base case.
- Updating an aggregate but returning the wrong child summary.
- Validating a BST only against immediate children.
- Forgetting to capture queue length before a level.

## Representative problems

Invert Binary Tree, Maximum Depth, Same Tree, Diameter, Validate BST, [[Binary Tree Level Order Traversal]].

## Modification questions

Return paths, not just counts; make the traversal iterative; handle an N-ary tree; serialize nil children; return the first node at maximum depth.

Related: [[Stack and Queue Pattern]], [[Graphs Pattern]], [[DSA Dashboard]].
