---
type: dsa-problem
language: go
company_focus:
  - apple
  - uber
priority: P1
pattern: in-place-index-placement
difficulty:
leetcode_url: https://leetcode.com/problems/first-missing-positive/
status: not-started
first_attempt_date:
last_attempt_date:
next_review_date:
attempt_count: 0
best_time_minutes:
needs_revisit: true
---

# First Missing Positive

## Problem in Simple Words

Return the smallest positive integer absent from an unsorted slice.

## Example

[3,1,-2] → 2.

## Clarifying Questions

- What are the empty-input and no-answer contracts?
- May the input be mutated, and are duplicates or overflow relevant?
- Which ordering, alphabet, or numeric assumptions are guaranteed?

## Pattern Recognition

- Signals in the question: in place index placement constraints and repeated local decisions.
- Likely data structure: choose the smallest structure that directly preserves the invariant below.
- Common wrong approach: enumerate or rebuild overlapping state without exploiting the stated structure.
- Key invariant: A value v in [1,n] belongs at index v-1; each swap fixes or discards a candidate.

## Approaches

### Brute Force

- Intuition: enumerate candidate answers and validate each directly.
- Complexity: derive from the candidate count and validation cost before coding.
- Why it may fail: repeated work exceeds the intended interview constraint.

### Better Approach

Record a meaningful intermediate approach during the first attempt; omit it if none improves the brute force cleanly.

### Optimal Approach

- Intuition: maintain only the state required by the invariant.
- Invariant: A value v in [1,n] belongs at index v-1; each swap fixes or discards a candidate.
- Complexity: O(n) time and O(1) auxiliary space.

## Small Dry Run

Trace the example and write the maintained state after each decisive update.

## Go-Specific Notes

Use explicit map membership checks; choose comparable keys and preallocate only when the size estimate is sound.

## Implementation

Prompt-first workspace: close this note and write a complete package plus main() or a table-driven test. Do not paste a memorized solution here before the first attempt.

~~~go
// Blank-editor implementation workspace.
~~~

Run: go run . or go test ./....

## Tests and Edge Cases

- Empty/minimum input and invalid parameters when the contract permits them
- Duplicates and boundary values
- A case that breaks the common wrong approach
- Input mutation and deterministic-output expectations

## Explain Aloud

In 60–90 seconds: restate the contract, name the pattern, state the invariant, trace one update, give complexity, mention one Go-specific choice, and answer one follow-up.

## Variations and Follow-ups

Change one constraint after the first correct run and reconstruct the affected part without reading a solution.

## Mistakes I Made

Record only observed mistakes from an actual attempt.

## Review History

| Date | Attempt | Minutes | Result | Hint used | Modification | Next review |
| --- | ---: | ---: | --- | --- | --- | --- |

