---
type: quick-revision
domain: dsa
topic: dynamic-programming
review_time: under-5-minutes
---

# Dynamic Programming — Quick Revision

## Mental Model

Dynamic programming is a precise definition of reusable state. Before code, write: what dp state means, base cases, transition, evaluation order, and where the answer lives. One-dimensional take/skip problems often reduce to two rolling values. Subset sum must update target sums backward so one input value is not reused in the same iteration. Sequence comparison usually uses a two-dimensional prefix or suffix table. Interval games store the best score difference the current player can force, which removes the need to model both absolute totals.

## Go and Interview Checklist

Prefer the clear table first; compress space only after verifying dependencies. In Go, allocate n+1 when state zero is a real base case and choose a safe sentinel that will not overflow when incremented. Distinguish unreachable from a legitimate zero result. For LIS patience sorting, tails stores minimal possible tails, not an actual subsequence; lower-bound replacement preserves strict increase. Dry-run the smallest non-trivial transition. Test amount zero, impossible targets, zeros/duplicates, all-decreasing input, empty strings, and negative choices if the contract permits them.

## 60-Second Recall

1. Name the invariant without code.
2. State what enters, leaves, or changes the maintained state.
3. Give expected time and space complexity.
4. Name the Go representation and one edge-case test.
5. Close this note and reconstruct one linked problem from a blank editor.

## Practice Links

[[Coin Change]], [[House Robber]], [[Longest Increasing Subsequence]], [[Partition Equal Subset Sum]], [[Longest Common Subsequence]], [[Predict the Winner]]

A successful read is not completion evidence. Update [[DSA Practice Tracker]] only after a complete invocation, explanation, variation, and scheduled re-test.

