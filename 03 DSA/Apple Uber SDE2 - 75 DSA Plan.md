---
type: curriculum-plan
domain: dsa
language: go
company_focus: [apple, uber]
core_problem_count: 75
status: active
---

# Apple Uber SDE2 - 75 DSA Plan

This is an execution queue, not completion evidence. Work P0 before P1/P2, begin from a blank editor, run a complete main/test invocation, explain aloud, change one constraint, and schedule reviews from the actual attempt date.

## Operating Loop

1. Due reviews before new work.
2. One incomplete P0 before any P1/P2.
3. Code without the note; use hints only after recording the blocked point.
4. Update [[DSA Practice Tracker]] and record only observed mistakes.
5. A problem reaches interview-ready only after a timed cold reconstruction, passing tests, explanation, variation, and spaced re-test.

## 12-Week Adjustable Schedule

Default: 8 new DSA, 3 new LLD, 4–6 DSA repetitions, 2 LLD repetitions, one timed mock, and one retrospective. Completed rows are never reset; when regenerating a week, replace already-completed new work with the highest-priority due or unstarted row.

| Week | New / focused DSA work | New LLD work | Repetition | Mock |
| ---: | --- | --- | --- | --- |
| 1 | Two Sum; Group Anagrams; Top K Frequent; Product Except Self; Longest Consecutive; Subarray Sum K; Valid Parentheses; Binary Search | Bounded Queue; Worker Pool; TTL Cache | Reconstruct 4 of the week’s DSA problems at +1d/+3d; repeat 2 LLD designs | 45-minute DSA baseline |
| 2 | 3Sum; Container Water; Longest Substring; Character Replacement; Minimum Window; Daily Temperatures; RPN; Reverse List | LRU Cache; Token Bucket; Priority Worker Pool | Repeat weak Week 1 P0s at +7d; rebuild Bounded Queue and Worker Pool | Sliding-window timed mock |
| 3 | Merge Lists; Cycle II; Reorder List; LRU Cache DSA; Rotated Search; Rotated Minimum; Koko; Merge Intervals | Pub Sub; Middleware Chain; Router | Week 1 +14d plus Week 2 +7d failures; TTL and LRU LLD | Pointers and binary-search mock |
| 4 | Insert Interval; Non-overlap; Meeting Rooms II; Level Order; Diameter; Validate BST; LCA; Max Path Sum | In-Memory File System; Retry Executor; Circuit Breaker | 4–6 weakest P0 reconstructions; Token Bucket and Priority Pool | Trees/intervals mock |
| 5 | Number of Islands; Clone Graph; Course Schedule; Course Schedule II; Alien Dictionary; Components; Redundant Connection; Accounts Merge | Idempotency Store; Singleflight; Connection Pool | Repeat Week 3/4 graph prerequisites and two infrastructure designs | Graph/topological mock |
| 6 | Kth Largest; Merge K Lists; Coin Change; House Robber; LIS; Sliding Window Maximum; Longest Abs-Diff Window; Task Scheduler | Delayed Job Queue; Cron Scheduler; Ack Queue | P0 cumulative set: 4 DSA cold reconstructions and 2 LLD shutdown drills | Mixed P0 midpoint mock |
| 7 | Continuous Subarray Sum; First Missing Positive; Rotate Image; Find Anagrams; Min Size Subarray; Decode String; Largest Histogram; Remove Nth | KV Store; LFU Cache; Expiring Priority Queue | Due P0 + selected P1 at +1d/+3d; rebuild Delayed Queue and Scheduler | P1 arrays/stacks mock |
| 8 | Copy Random List; Ship Capacity; Median Two Arrays; Gas Station; Arrows; Serialize Tree; Construct Tree; Kth BST | Fan-Out/Fan-In; Batch Processor; Semaphore | 4–6 due DSA; Ack Queue and one weak concurrency package | P1 structures mock |
| 9 | Implement Trie; Rotting Oranges; Word Ladder; Network Delay; Stream Median; Reorganize String; Partition Equal Subset; LCS | Sliding-Window Limiter; Bulkhead; Deadline Budget | Cumulative P0 random sample plus two LLD reconstructions | Graph/heap/DP mock |
| 10 | Spiral Matrix; Subarrays K Distinct; Basic Calculator II; Word Search II; Predict the Winner; two weakest P0 variations; one failed mock problem | Resilient API Client; Durable Scheduler; Metrics Aggregator | Due +14d items; one infrastructure problem from blank editor | Hard mixed mock |
| 11 | Eight weakest tracker rows, prioritizing reconstruction-needed P0/P1; no forced novelty | Splitwise; Inventory Reservation; Notification Service | Six DSA repeats and two full LLD rebuilds | 90-minute LLD machine-coding mock |
| 12 | Eight interview-set problems sampled without pattern labels | Feature Flags; Train Platforms; one weakest unattempted LLD | All due reviews; two failed mocks repeated cold | Full coding mock plus retrospective |

Weekly retrospective: what compiled, what failed, recurring Go syntax/ownership mistakes, time lost, next review dates, and exactly one process change.

## Curriculum Source of Truth

The numbered source of truth is the 75-row core table in [[DSA Practice Tracker]]. The three DP extensions remain separately tracked and never inflate the core count.

