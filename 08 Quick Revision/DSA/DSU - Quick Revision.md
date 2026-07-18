---
type: quick-revision
domain: dsa
topic: dsu
review_time: under-5-minutes
---

# DSU — Quick Revision

## Mental Model

Disjoint Set Union maintains a partition under repeated connectivity merges. Each element has a parent; a root represents one component. Find follows parents, path compression shortens future searches, and union by size/rank attaches the smaller tree under the larger. The key signal is many undirected connectivity queries or incremental edges where the actual path is irrelevant. A failed union—both endpoints already share a root—detects a cycle. Starting with n components and decrementing only on successful union gives the component count.

## Go and Interview Checklist

Make parent and size slices of length n and initialize parent[i]=i. Find is easiest as a method or closure; iterative compression avoids recursion concerns. Be explicit about one-based input labels and allocate n+1 only when the input contract uses them. Alpha(n) is effectively constant but state the formal O(alpha(n)) amortized operation cost. DSU does not directly recover shortest paths or directed dependency order. Test isolated vertices, repeated edges, self edges if allowed, a long union chain, already-connected endpoints, and identifier-to-index mapping for account records.

## 60-Second Recall

1. Name the invariant without code.
2. State what enters, leaves, or changes the maintained state.
3. Give expected time and space complexity.
4. Name the Go representation and one edge-case test.
5. Close this note and reconstruct one linked problem from a blank editor.

## Practice Links

[[Number of Connected Components in an Undirected Graph]], [[Redundant Connection]], [[Accounts Merge]], [[Number of Islands]]

A successful read is not completion evidence. Update [[DSA Practice Tracker]] only after a complete invocation, explanation, variation, and scheduled re-test.

