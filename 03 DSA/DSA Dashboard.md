---
type: dashboard
domain: dsa
status: active
practice_source: /home/rahul/go-interview-prep
last_evidence_sync: 2026-07-17
---
# DSA Dashboard

The goal is reliable Go implementation under interview conditions, not collecting solved-note checkboxes. A problem becomes evidence only after a blank-editor attempt, a runnable invocation, an explanation, a modification, and a later re-test.

## Apple / Uber SDE-2 Core Track

Source of truth: [[DSA Practice Tracker]] · execution order: [[Apple Uber SDE2 - 75 DSA Plan]] · quick revision: [[08 Quick Revision/DSA/Sliding Window - Quick Revision|DSA quick revision]]

| Metric | Current evidence |
| --- | ---: |
| Core problems | 75 |
| Mandatory extensions | 3 |
| P0 completed | 0 |
| P1 completed | 0 |
| P2 completed | 0 |
| Timed-ready | 0 |
| Interview-ready | 0 |
| Reviews due | 0 scheduled |
| Weakest patterns | Not measurable until attempts are recorded |

### Next Recommended Work

1. Due reviews: none scheduled; do not invent review dates.
2. Incomplete P0: [[Two Sum]] cold reconstruction from the preserved reference.
3. Next new P0: [[Top K Frequent Elements]] from a blank editor.
4. Weekly mock: create one from [[DSA Mock Interview Template]] in [[03 DSA/Mocks|DSA Mocks]].

Generated notes and existing runnable references are curriculum assets, not personal completion evidence.

## Start here

1. Review [[DSA Pattern Recognition - 5 Minute Revision]].
2. Pick the day's item from [[NeetCode 150 in Go#Tier 1 — first 30 days]].
3. Open the linked pattern note, then close it before coding.
4. Preserve the attempt and update [[Timed Practice Tracker]].
5. Record an observed failure in [[DSA Mistake Log]] and schedule the re-test.

## Canonical patterns

| Priority | Pattern | Reference problems |
| ---: | --- | --- |
| 1 | [[Arrays and Hash Maps Pattern]] | [[Contains Duplicate]], [[Two Sum]], [[Group Anagrams]] |
| 2 | [[Two Pointers Pattern]] | [[3Sum]], [[Container With Most Water]] |
| 3 | [[Sliding Window Pattern]] | [[Longest Substring Without Repeating Characters]] |
| 4 | [[Stack and Queue Pattern]] | [[Valid Parentheses]], [[Daily Temperatures]] |
| 5 | [[Binary Search Pattern]] | [[Binary Search]] |
| 6 | [[Linked Lists Pattern]] | [[Reverse Linked List]] |
| 7 | [[Trees Pattern]] | [[Binary Tree Level Order Traversal]] |
| 8 | [[Heaps Pattern]] | [[Kth Largest Element in an Array]] |
| 9 | [[Intervals Pattern]] | [[Merge Intervals]] |
| 10 | [[Graphs Pattern]] | [[Number of Islands]] |
| 11 | [[Basic Dynamic Programming Pattern]] | [[Climbing Stairs]], [[House Robber]] |

## Evidence snapshot

| Evidence | Current state |
| --- | --- |
| Pattern canonicals | 11 populated |
| Selected runnable problem references | 17 populated |
| External personal implementations | 6 runnable `main.go` files observed on 2026-07-17 |
| Timed attempts performed | none recorded |
| Re-attempts performed | none recorded |
| Confirmed DSA/Go transfer gap | [[Java DSA Practice Conflicts with Go Interviews]] |

The external files are on-disk personal implementation evidence, but their timers, hint use, explanations, modifications, and re-tests are not recorded. The `neetcode/` tree is also untracked in its source repository, so it is not yet durable attempt history. The files move matching sprint tasks to `attempting` without changing the timed-attempt or readiness gates. See [[NeetCode 150 in Go#Preparation sync — 2026-07-17]].

## Interview loop

`Recognize → state invariant → brute force → optimal plan → code → run → explain → modify → record → re-test`

Supporting Go owners: [[Go Slices]], [[Go Maps]], [[Complete Go Programs]] · Runnable scaffold: [[Go DSA Template]] · Container syntax: [[Go DSA Containers]] · Initial transfer drill: [[Java-to-Go DSA Transfer Re-test]]

## Source boundary

Tiering and pattern clues were curated from the existing vault sprint and sanitized DSA extracts, especially `Amazon SDE I Prep` (2026-07-13, conversation `6a548ae5-bf68-83ee-9235-aeb4e863e479`). Historical Java solutions are prompts for fresh Go attempts, not completion evidence.
