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

Attempt record: date · minutes · result · hints · syntax/pattern/edge/complexity/communication failure · modification result · next review.

Related: [[NeetCode 150 in Go]], [[Java DSA Practice Conflicts with Go Interviews]].
