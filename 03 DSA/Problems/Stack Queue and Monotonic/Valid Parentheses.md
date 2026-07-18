---
type: dsa-problem
language: go
company_focus:
  - apple
  - uber
priority: P0
pattern: stack
difficulty:
leetcode_url: 
status: not-started
first_attempt_date:
last_attempt_date:
next_review_date:
attempt_count: 0
best_time_minutes:
needs_revisit: true
---
# Valid Parentheses

## Problem summary

Return whether every bracket closes the most recent unmatched bracket of the same type.

## Pattern

[[Stack and Queue Pattern]] — LIFO matching for nested structure.

## Brute-force intuition

Repeatedly remove `()`, `[]`, and `{}` until no change; this can take `O(n²)` time due to repeated string rebuilding.

## Optimal intuition

Push opening brackets. A closing bracket must match the stack top; reject early on an empty stack or wrong type. The stack must be empty at the end.

## Dry run

`([{}])`: push `(`, `[`, `{`; each close matches and pops in reverse order; the final stack is empty. `(]` fails at the first close.

## Complete Go solution

```go
package main

import "fmt"

func isValid(s string) bool {
	opening := map[byte]byte{')': '(', ']': '[', '}': '{'}
	stack := []byte{}
	for i := 0; i < len(s); i++ {
		if expected, closing := opening[s[i]]; closing {
			if len(stack) == 0 || stack[len(stack)-1] != expected { return false }
			stack = stack[:len(stack)-1]
		} else {
			stack = append(stack, s[i])
		}
	}
	return len(stack) == 0
}

func main() {
	for _, input := range []string{"()[]{}", "([{}])", "(]", "]", "("} {
		fmt.Println(input, isValid(input))
	}
}
```

Run: `go run main.go`. Input is assumed to contain only bracket characters.

## Complexity

`O(n)` time and `O(n)` space.

## Edge cases

Empty string; early close; wrong close; leftover open; deeply nested input; non-bracket policy.

## Blank-editor success criteria

Finish in 20 minutes, test early-close/wrong-pair/leftover cases, then return the first invalid byte index (or `-1`).

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded.

## Problem in Simple Words

Check that each closing bracket matches the latest unmatched opening bracket.

## Example

{[()]} is valid; {(]) is not.

## Clarifying Questions

- May input be empty, invalid, or mutated?
- What duplicate, ordering, numeric, or node-identity guarantees apply?

## Pattern Recognition

- Signals in the question: stack.
- Likely data structure: the structure that directly represents the invariant.
- Common wrong approach: repeated scans or state updates that lose the invariant.
- Key invariant: The stack is exactly the unmatched opening-bracket prefix.

## Approaches

### Brute Force

- Intuition: enumerate candidates directly.
- Complexity: derive during the cold attempt.
- Why it may fail: it repeats work and misses the expected bound.

### Better Approach

Use only if a genuine intermediate approach clarifies the progression.

### Optimal Approach

- Intuition and complete runnable reference: preserved above from the existing canonical note.
- Invariant: The stack is exactly the unmatched opening-bracket prefix.
- Complexity: verify the bound above during explanation.

## Small Dry Run

Reconstruct the existing dry run without looking, then add one adversarial case.

## Go-Specific Notes

Check slice initialization, map membership, pointer rewiring, queue head indexing, recursive closure declaration, heap pointer receivers, input mutation, and byte/rune semantics as applicable.

## Implementation

The pre-existing executable reference above is preserved. For practice, close this note and reproduce a complete main() or test invocation from a blank editor.

## Tests and Edge Cases

Re-run the preserved edge cases and add one case that breaks the tempting wrong approach.

## Explain Aloud

Restate → pattern → invariant → one transition → complexity → Go detail → variation, within 60–90 seconds.

## Variations and Follow-ups

Make one constraint change after a clean reconstruction.

## Mistakes I Made

None recorded. Add only observed mistakes from an actual attempt.

## Review History

Use the preserved re-attempt table above and the central tracker; never infer an attempt from the reference solution.
