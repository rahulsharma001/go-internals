---
type: dsa-problem
language: go
company_focus:
  - apple
  - uber
priority: P0
pattern: prefix-suffix
difficulty:
leetcode_url: https://leetcode.com/problems/product-of-array-except-self/
status: not-started
first_attempt_date:
last_attempt_date:
next_review_date:
attempt_count: 0
best_time_minutes:
needs_revisit: true
---

# Product of Array Except Self

## Problem in Simple Words

For each position, multiply every input value except the one there without division.

## Example

[2,3,5] → [15,10,6].

## Clarifying Questions

- What are the empty-input and no-answer contracts?
- May the input be mutated, and are duplicates or overflow relevant?
- Which ordering, alphabet, or numeric assumptions are guaranteed?

## Pattern Recognition

- Signals in the question: prefix suffix constraints and repeated local decisions.
- Likely data structure: choose the smallest structure that directly preserves the invariant below.
- Common wrong approach: enumerate or rebuild overlapping state without exploiting the stated structure.
- Key invariant: Before the backward pass, result[i] is the product strictly left of i; suffix holds the product strictly right.

## Approaches

### Brute Force

- Intuition: enumerate candidate answers and validate each directly.
- Complexity: derive from the candidate count and validation cost before coding.
- Why it may fail: repeated work exceeds the intended interview constraint.

### Better Approach

Record a meaningful intermediate approach during the first attempt; omit it if none improves the brute force cleanly.

### Optimal Approach

- Intuition: maintain only the state required by the invariant.
- Invariant: Before the backward pass, result[i] is the product strictly left of i; suffix holds the product strictly right.
- Complexity: O(n) time and O(1) auxiliary space excluding output.

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

