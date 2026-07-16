---
type: coding-drill
domain: go
topic: go-slices
status: not-attempted
canonical: "[[Go Slices]]"
---

# Slice Creation and Modification - Drill

## Problem

From a blank editor, write `updatedCopy(values []int) []int` that:

1. returns an independent copy of `values`;
2. changes the second element to `20` when it exists;
3. appends `40`;
4. removes the first element when non-empty;
5. never changes the caller's slice.

In `main()`, invoke it with `[]int{1, 2, 3}` and an empty slice. Print both input and result so ownership is visible.

Expected normal output:

```text
input: [1 2 3]
result: [20 3 40]
empty: [40]
```

## Constraints and edge cases

- Do not use a global variable.
- Capture every `append` result.
- Handle zero- and one-element slices without panic.
- The result must not share modifiable elements with the input.

## Modification challenge

Rewrite it as an explicitly in-place function. State how its ownership contract changes and clear any removed pointer-like tail element in a generic description.

## Attempt record

| Date | Time | Result | Hints | Failure category |
|---|---:|---|---|---|
| | | not attempted | | |

## Re-test history

| Date | Variant | Result | Remaining mistake |
|---|---|---|---|
| | non-mutating / in-place | | |

<details>
<summary>Reference solution — reveal only after an attempt</summary>

```go
package main

import "fmt"

func updatedCopy(values []int) []int {
	out := append([]int(nil), values...)
	if len(out) > 1 {
		out[1] = 20
	}
	out = append(out, 40)
	if len(out) > 1 {
		out = out[1:]
	}
	return out
}

func main() {
	input := []int{1, 2, 3}
	result := updatedCopy(input)
	fmt.Println("input:", input)
	fmt.Println("result:", result)
	fmt.Println("empty:", updatedCopy(nil))
}
```

</details>

Related: [[Go Slices]] · [[Go Slices - Quick Revision]]

