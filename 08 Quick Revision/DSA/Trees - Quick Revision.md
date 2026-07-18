---
type: quick-revision
domain: dsa
topic: trees
review_time: under-5-minutes
---

# Trees — Quick Revision

## Mental Model

Most tree solutions are a choice between what a recursive call returns and what the current node contributes to a global or parent result. Write the return meaning in one sentence before recursion. Preorder acts before children, inorder exposes BST order, and postorder combines child results. BFS is preferable when levels or minimum unweighted depth matter. For ancestor-bound validation, pass information from every ancestor rather than comparing only parent and child. For path problems, distinguish a path that may branch at the current node from a value returned upward, which can use at most one branch.

## Go and Interview Checklist

Define the TreeNode once in the executable. In Go, recursive closures need var dfs func(*TreeNode) int followed by assignment; a named function avoids that issue. State nil-root behavior and whether node identity or only value matters. BFS queues should use a head index, and the level size must be captured before enqueuing children. Avoid package globals that leak between test cases. Test nil, one node, a skewed tree, negative values, duplicate values where invalid, and a best path that does not pass through the root.

## 60-Second Recall

1. Name the invariant without code.
2. State what enters, leaves, or changes the maintained state.
3. Give expected time and space complexity.
4. Name the Go representation and one edge-case test.
5. Close this note and reconstruct one linked problem from a blank editor.

## Practice Links

[[Binary Tree Level Order Traversal]], [[Diameter of Binary Tree]], [[Validate Binary Search Tree]], [[Lowest Common Ancestor of a Binary Tree]], [[Binary Tree Maximum Path Sum]], [[Serialize and Deserialize Binary Tree]], [[Construct Binary Tree from Preorder and Inorder]], [[Kth Smallest Element in a BST]]

A successful read is not completion evidence. Update [[DSA Practice Tracker]] only after a complete invocation, explanation, variation, and scheduled re-test.

