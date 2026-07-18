---
type: dsa-problem
language: go
company_focus:
  - apple
  - uber
priority: P0
pattern: sweep-line-heap
difficulty:
leetcode_url: https://leetcode.com/problems/meeting-rooms-ii/
status: not-started
first_attempt_date:
last_attempt_date:
next_review_date:
attempt_count: 0
best_time_minutes:
needs_revisit: true
curriculum: core
---

# Meeting Rooms II

## Problem in Simple Words

Find the minimum number of rooms required for all meetings.

## Example

[0,5],[2,4],[5,8] → 2 rooms.

## Clarifying Questions

- What are the empty-input and no-answer contracts?
- May the input be mutated, and are duplicates, disconnected input, or overflow relevant?
- What ordering or validity guarantees does the input provide?

## Pattern Recognition

- Signals in the question: sweep line heap constraints.
- Likely data structure: select the smallest state that preserves the invariant.
- Common wrong approach: repeat traversal or state reconstruction for every candidate.
- Key invariant: Active end times represent exactly the meetings not finished before the next start.

## Approaches

### Brute Force

- Intuition: enumerate candidates or simulate every choice directly.
- Complexity: derive candidate count and repeated validation cost before coding.
- Why it may fail: overlapping work or exponential branching violates the intended constraint.

### Better Approach

Record a real intermediate improvement during the first attempt when one exists.

### Optimal Approach

- Intuition: preserve only the frontier/state needed by the invariant.
- Invariant: Active end times represent exactly the meetings not finished before the next start.
- Complexity: O(n log n) time.

## Small Dry Run

Trace the original example, including every state transition that changes the answer.

## Go-Specific Notes

Use sort.Slice with a strict comparator, decide whether touching intervals overlap, and copy input before sorting when mutation is not allowed.

## Implementation

Prompt-first workspace: implement a complete Go package with main() or a table-driven test before adding solution code to this note.

~~~go
// Blank-editor implementation workspace.
~~~

Run: go run . or go test ./....

## Tests and Edge Cases

- Empty/minimum input and invalid parameters where allowed
- Duplicate, negative, disconnected, skewed, or boundary input as applicable
- A case that breaks the tempting wrong approach
- Mutation and deterministic-output expectations

## Explain Aloud

In 60–90 seconds: restate, name the pattern, state the invariant, trace one transition, give complexity, mention one Go choice, and discuss one variation.

## Variations and Follow-ups

Change one constraint and reconstruct the affected logic without reading the note.

## Mistakes I Made

Record only observed mistakes from an actual attempt.

## Review History

| Date | Attempt | Minutes | Result | Hint used | Modification | Next review |
| --- | ---: | ---: | --- | --- | --- | --- |

