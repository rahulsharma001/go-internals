---
type: quick-revision
domain: dsa
topic: sliding-window
review_time: under-5-minutes
---

# Sliding Window — Quick Revision

## Mental Model

A window is useful when the answer is a contiguous range and the validity condition can be repaired by moving the left boundary. Decide first whether the window is fixed-size or variable-size. In a variable window, expand right exactly once, update state, then shrink while the condition is satisfied or violated—write which one before coding. The invariant must describe the current range, not the best answer. For unique characters, the window contains no duplicates. For coverage, the window satisfies every required multiplicity only when the satisfied counter equals the number of requirements. Positive-only sum problems permit monotonic shrinking; arbitrary negative values usually break that reasoning and point toward prefix sums.

## Go and Interview Checklist

Use left and right as inclusive indices only if every length is right-left+1. Store byte counts for an explicit ASCII contract; use rune iteration if the interview requires Unicode, noting that byte indices and rune positions differ. Maps return zero for missing counts, but membership still matters for last-seen positions. Update best at the exact point the invariant is valid. Test empty input, a one-symbol window, repeated symbols outside the active range, and a case that shrinks multiple times.

## 60-Second Recall

1. Name the invariant without code.
2. State what enters, leaves, or changes the maintained state.
3. Give expected time and space complexity.
4. Name the Go representation and one edge-case test.
5. Close this note and reconstruct one linked problem from a blank editor.

## Practice Links

[[Longest Substring Without Repeating Characters]], [[Longest Repeating Character Replacement]], [[Minimum Window Substring]], [[Longest Continuous Subarray With Absolute Diff Less Than or Equal to Limit]], [[Find All Anagrams in a String]], [[Minimum Size Subarray Sum]], [[Sliding Window Maximum]], [[Subarrays With K Different Integers]]

A successful read is not completion evidence. Update [[DSA Practice Tracker]] only after a complete invocation, explanation, variation, and scheduled re-test.

