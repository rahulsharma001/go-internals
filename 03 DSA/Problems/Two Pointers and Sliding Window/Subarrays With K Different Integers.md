---
type: dsa-problem
language: go
company_focus:
  - apple
  - uber
priority: P2
pattern: at-most-k-window
difficulty:
leetcode_url: https://leetcode.com/problems/subarrays-with-k-different-integers/
status: not-started
first_attempt_date:
last_attempt_date:
next_review_date:
attempt_count: 0
best_time_minutes:
needs_revisit: true
---

# Subarrays With K Different Integers

## Problem in Simple Words

Count ranges containing exactly k distinct values.

## Example

[1,2,1], k=2 → 3.

## Clarifying Questions

- What are the empty-input and no-answer contracts?
- May the input be mutated, and are duplicates or overflow relevant?
- Which ordering, alphabet, or numeric assumptions are guaranteed?

## Pattern Recognition

- Signals in the question: at most k window constraints and repeated local decisions.
- Likely data structure: choose the smallest structure that directly preserves the invariant below.
- Common wrong approach: enumerate or rebuild overlapping state without exploiting the stated structure.
- Key invariant: Exactly(k) equals atMost(k) minus atMost(k-1).

## Approaches

### Brute Force

- Intuition: enumerate candidate answers and validate each directly.
- Complexity: derive from the candidate count and validation cost before coding.
- Why it may fail: repeated work exceeds the intended interview constraint.

### Better Approach

Record a meaningful intermediate approach during the first attempt; omit it if none improves the brute force cleanly.

### Optimal Approach

- Intuition: maintain only the state required by the invariant.
- Invariant: Exactly(k) equals atMost(k) minus atMost(k-1).
- Complexity: O(n) time and O(k) space.

## Small Dry Run

Trace the example and write the maintained state after each decisive update.

## Go-Specific Notes

Use half-open window reasoning where possible; clarify whether string indices are bytes or runes.

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

