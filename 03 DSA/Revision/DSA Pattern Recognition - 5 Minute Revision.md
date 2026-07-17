---
type: quick-revision
domain: dsa
status: active
---
# DSA Pattern Recognition - 5 Minute Revision

| Clue | Pattern | Invariant/question |
| --- | --- | --- |
| Pair, frequency, membership, canonical signature | Hash map/set | What must be remembered from the prefix? |
| Sorted pair/triplet, compare ends | Two pointers | Which move safely eliminates candidates? |
| Longest/shortest contiguous range | Sliding window | What makes the current window valid? |
| Matching delimiters or next greater/smaller | Stack | What unresolved items does the stack hold? |
| Level traversal or shortest unweighted path | Queue/BFS | What belongs to the current level? |
| Sorted/monotonic search space | Binary search | What interval still may contain the answer? |
| Pointer rewiring | Linked list | Save `next` before changing ownership. |
| Parent answer built from children | Tree DFS | What must a child return to its parent? |
| Top/bottom `k`, repeated min/max | Heap | Which boundary item should be evicted? |
| Overlapping ranges | Sort intervals | Compare with only the last merged interval. |
| Components/connectivity | Graph DFS/BFS | When is a node marked visited? |
| Repeated choices with overlapping subproblems | DP | State, transition, base case, final answer. |

## Go recall

```text
set:       map[int]struct{}
frequency: map[T]int
stack pop: s = s[:len(s)-1]
queue:     q[head]; head++
sort:      sort.Ints(nums) or sort.Slice
heap:      Len, Less, Swap, Push, Pop
```

## Before coding

1. State brute force and its bottleneck.
2. Name the optimized state and invariant.
3. Decide input mutation policy.
4. Choose one boundary convention.
5. Predict normal and edge-case output.

## After coding

Run the complete program. Explain time and auxiliary space. Modify return shape, mutation policy, duplicate behavior, or streaming constraint. Record the first actual failure in [[DSA Mistake Log]] and schedule a re-test in [[Timed Practice Tracker]].

Sources: `Amazon SDE I Prep` (2026-07-13, `6a548ae5…`) and the existing [[Week 2 - DSA in Go]].
