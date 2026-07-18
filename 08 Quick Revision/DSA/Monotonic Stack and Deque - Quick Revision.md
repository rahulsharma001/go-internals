---
type: quick-revision
domain: dsa
topic: monotonic-stack-and-deque
review_time: under-5-minutes
---

# Monotonic Stack and Deque — Quick Revision

## Mental Model

A monotonic container keeps only candidates that can still answer a future next-greater, next-smaller, range-maximum, or range-minimum query. The discarded elements are dominated: a newer element is at least as useful and survives longer. A stack resolves one-directional relationships when an arriving value proves the answer for previous indices. A deque supports a moving window: remove expired indices from the front and dominated values from the back. Store indices when distance, expiry, or width matters; values alone lose that information.

## Go and Interview Checklist

For a decreasing stack, state whether equality causes a pop—strictly warmer differs from warmer-or-equal. In histogram problems, popping discovers the first smaller boundary on the right while the new top gives the left boundary. Sentinels can flush the stack but must not corrupt widths. In Go, a stack is append and reslice; a deque can be []int with a head index. Compact occasionally only in long-lived production code, not an interview loop. Test duplicates, monotonic input, all-equal input, k=1, and an answer that expires at the window edge.

## 60-Second Recall

1. Name the invariant without code.
2. State what enters, leaves, or changes the maintained state.
3. Give expected time and space complexity.
4. Name the Go representation and one edge-case test.
5. Close this note and reconstruct one linked problem from a blank editor.

## Practice Links

[[Daily Temperatures]], [[Largest Rectangle in Histogram]], [[Sliding Window Maximum]], [[Longest Continuous Subarray With Absolute Diff Less Than or Equal to Limit]]

A successful read is not completion evidence. Update [[DSA Practice Tracker]] only after a complete invocation, explanation, variation, and scheduled re-test.

