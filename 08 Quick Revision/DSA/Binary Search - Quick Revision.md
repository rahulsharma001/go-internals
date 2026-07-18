---
type: quick-revision
domain: dsa
topic: binary-search
review_time: under-5-minutes
---

# Binary Search — Quick Revision

## Mental Model

Binary search is invariant maintenance over a monotonic search space, not merely lookup in sorted data. Choose one contract: inclusive [lo,hi] for exact search, or half-open [lo,hi) for lower-bound style searches. For answer search, define a predicate feasible(x) and prove that its truth values change at most once. Initialize bounds to known impossible/possible extremes or to the full valid answer domain. Each branch must discard mid or make progress; rehearse the two-element case to expose infinite loops.

## Go and Interview Checklist

In Go, compute mid as lo+(hi-lo)/2. Decide how sums and products may overflow and use int64 where constraints require it. For rotated arrays, at least one half is sorted; duplicates can destroy the clean logarithmic branch. For minimum feasible answers, retain mid when feasible and move hi=mid; otherwise lo=mid+1. Keep the feasibility function separate and test it directly. Dry-run absent targets, one element, two elements, pivot at an edge, and an answer equal to each bound.

## 60-Second Recall

1. Name the invariant without code.
2. State what enters, leaves, or changes the maintained state.
3. Give expected time and space complexity.
4. Name the Go representation and one edge-case test.
5. Close this note and reconstruct one linked problem from a blank editor.

## Practice Links

[[Binary Search]], [[Search in Rotated Sorted Array]], [[Find Minimum in Rotated Sorted Array]], [[Koko Eating Bananas]], [[Capacity to Ship Packages Within D Days]], [[Median of Two Sorted Arrays]]

A successful read is not completion evidence. Update [[DSA Practice Tracker]] only after a complete invocation, explanation, variation, and scheduled re-test.

