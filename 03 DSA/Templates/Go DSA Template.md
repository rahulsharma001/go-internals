---
type: canonical
domain: dsa
topic: go-dsa-template
status: implementation-needed
---
# Go DSA Template

Use this scaffold only after writing the problem in your own words and selecting a pattern. Preserve the first raw attempt.

```go
package main

import "fmt"

func solve(nums []int) int {
	// Replace with the problem-specific invariant and implementation.
	return len(nums)
}

func main() {
	tests := []struct {
		name string
		in   []int
	}{
		{"empty", []int{}},
		{"one", []int{7}},
		{"many", []int{2, 1, 2}},
	}
	for _, tc := range tests {
		fmt.Printf("%s: %d\n", tc.name, solve(tc.in))
	}
}
```

Run with `go run main.go`; for a test-first problem use a complete table test and `go test ./...`. Before coding, state the invariant. After coding, dry-run one normal and one edge case, give time/space complexity, then modify a constraint under the timer.

Before revealing any reference note, copy this checklist into the raw attempt:

- Restate input, output, and constraints.
- Give the brute-force idea and complexity.
- Name the pattern and invariant.
- Run normal, empty/minimum, duplicate, and missing-answer cases when applicable.
- Explain complexity and perform one live modification.

Attempt record: date · minutes · result · hints · syntax/pattern/edge/complexity/communication failure · modification result · next review.

Related: [[DSA Dashboard]], [[NeetCode 150 in Go]], [[Go DSA Containers]], [[Java DSA Practice Conflicts with Go Interviews]].
