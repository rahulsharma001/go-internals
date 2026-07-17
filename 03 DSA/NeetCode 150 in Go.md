---
type: roadmap
domain: dsa
topic: neetcode-150
status: implementation-needed
---
# NeetCode 150 in Go

NeetCode 150 is the central set; this note schedules attempts rather than pre-filling a solution encyclopedia. A problem counts only after a preserved Go attempt, runnable invocation/tests, dry run, modification, mistake capture, and scheduled re-test.

## Tier 1 — first 30 days

This is a 24-problem execution set, not 24 problems to finish in one pass. The first 17 have populated reference notes; the remaining seven are scheduled only after the earlier pattern has one timed re-attempt.

| Days | Pattern | Problems | Gate |
| --- | --- | --- | --- |
| 1–4 | [[Arrays and Hash Maps Pattern]] | [[Contains Duplicate]]; [[Valid Anagram]]; [[Two Sum]]; [[Group Anagrams]] | Four cold Go attempts |
| 5–7 | [[Two Pointers Pattern]] | Valid Palindrome; [[3Sum]]; [[Container With Most Water]] | 3Sum duplicate handling re-tested |
| 8–10 | [[Sliding Window Pattern]] | Best Time to Buy and Sell Stock; [[Longest Substring Without Repeating Characters]] | State window invariant before code |
| 11–13 | [[Stack and Queue Pattern]] | [[Valid Parentheses]]; [[Daily Temperatures]] | Explain unresolved-index stack |
| 14–15 | [[Binary Search Pattern]] | [[Binary Search]]; Search in Rotated Sorted Array | Boundary variant modification |
| 16–17 | [[Linked Lists Pattern]] | [[Reverse Linked List]]; Merge Two Sorted Lists | Empty/one/many invocation |
| 18–20 | [[Trees Pattern]] | Maximum Depth; [[Binary Tree Level Order Traversal]] | DFS/BFS choice explained |
| 21–22 | [[Heaps Pattern]] / [[Intervals Pattern]] | [[Kth Largest Element in an Array]]; [[Merge Intervals]] | Heap-vs-sort and mutation trade-off |
| 23–25 | [[Graphs Pattern]] | [[Number of Islands]]; Clone Graph | Visited policy stated |
| 26–27 | [[Basic Dynamic Programming Pattern]] | [[Climbing Stairs]]; [[House Robber]] | State/transition/base case from memory |
| 28–30 | Mixed | three weakest re-attempts plus two 45-minute mocks | No new problem until evidence review |

## Tier 2 — important after day 30

Encode/Decode Strings; Trapping Rain Water; Minimum Window Substring; Car Fleet; Find Minimum Rotated Array; Reorder List; Remove Nth Node; LRU Cache; Validate BST; Lowest Common Ancestor; Kth Smallest BST; Construct Tree; Time Based Key-Value Store; K Closest Points; Task Scheduler; Insert Interval; Non-overlapping Intervals; Rotting Oranges; Pacific Atlantic; Course Schedule; Graph Valid Tree; Combination Sum; Permutations; Subsets; Word Search; Climbing Stairs; House Robber; Coin Change; Longest Increasing Subsequence.

## Tier 3 — advanced/lower priority

The remaining NeetCode 150 problems, especially tries, advanced graphs, 2-D DP, greedy, bit manipulation, and math/geometry, stay deferred until Tier 1 has timed modification and re-test evidence.

## Problem-note contract

Each created problem record contains: own-words statement; recognition clue; brute force; optimal intuition; detailed dry run; complete Go solution below the attempt boundary; complexity; edge cases; personal mistakes only when observed; modification; and re-attempt history.

Start: [[DSA Dashboard]] · Template: [[Go DSA Template]] · Sprint: [[Week 2 - DSA in Go]] · Tracker: [[Timed Practice Tracker]] · Mistake: [[DSA Mistake Log]].

## Sources

- `Amazon SDE I Prep` · 2026-07-13 · conversation `6a548ae5-bf68-83ee-9235-aeb4e863e479` (pattern prioritization and URLs).
- `45-Day Backend Interview Plan` · 2026-05-23 · conversation `6a11f5e6-8020-8321-8234-5e3661848716` (bounded Go interview practice).
- Existing [[Week 2 - DSA in Go]] task set. No task status was changed.
