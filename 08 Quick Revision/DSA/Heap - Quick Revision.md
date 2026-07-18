---
type: quick-revision
domain: dsa
topic: heap
review_time: under-5-minutes
---

# Heap — Quick Revision

## Mental Model

A heap maintains only the next extreme, not a fully sorted collection. Use a min-heap for the smallest frontier item or to retain the k largest values; use a max-heap by reversing Less. K-way merge pushes one current node per source and replaces it with that source’s successor. Two heaps maintain a median: every lower-half value is at most every upper-half value, and sizes differ by at most one. Greedy scheduling heaps often withhold the last-used item to prevent immediate reuse.

## Go and Interview Checklist

Go’s container/heap interface requires Len, Less, Swap, Push(any), and Pop() any. Push and Pop mutate the slice and therefore need pointer receivers; callers use type assertions. heap.Pop removes the element placed at the end by Swap, so implement Pop by shortening the underlying slice and zeroing a removed pointer when relevant. Decide tie-breaking for deterministic tests. Validate k and empty-stream behavior. Test duplicates, k=1, k=n, empty source lists, odd/even median counts, and equal priorities.

## 60-Second Recall

1. Name the invariant without code.
2. State what enters, leaves, or changes the maintained state.
3. Give expected time and space complexity.
4. Name the Go representation and one edge-case test.
5. Close this note and reconstruct one linked problem from a blank editor.

## Practice Links

[[Top K Frequent Elements]], [[Kth Largest Element in an Array]], [[Merge K Sorted Lists]], [[Find Median from Data Stream]], [[Reorganize String]], [[Meeting Rooms II]]

A successful read is not completion evidence. Update [[DSA Practice Tracker]] only after a complete invocation, explanation, variation, and scheduled re-test.

