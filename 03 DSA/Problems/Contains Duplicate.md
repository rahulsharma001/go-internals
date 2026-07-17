---
type: problem
domain: dsa
status: reference-not-attempted
pattern: arrays-hash-maps
source_conversations:
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Contains Duplicate

LeetCode: https://leetcode.com/problems/contains-duplicate/

## Problem summary

Return whether any integer occurs at least twice.

## Pattern

[[Arrays and Hash Maps Pattern]] — remember values already scanned.

## Brute-force intuition

Compare every pair. This directly checks the definition but repeats work: `O(n²)` time and `O(1)` space.

## Optimal intuition

Maintain a set. If the current value is already present, the answer is known immediately; otherwise insert it.

## Dry run

For `[1,2,3,1]`: set `{}` → add `1` → add `2` → add `3` → the final `1` exists, so return `true`.

## Complete Go solution

```go
package main

import "fmt"

func containsDuplicate(nums []int) bool {
	seen := make(map[int]struct{}, len(nums))
	for _, value := range nums {
		if _, exists := seen[value]; exists { return true }
		seen[value] = struct{}{}
	}
	return false
}

func main() {
	tests := [][]int{{1, 2, 3, 1}, {1, 2, 3}, {}, {7, 7}}
	for _, nums := range tests { fmt.Println(containsDuplicate(nums)) }
}
```

Run: `go run main.go`.

## Complexity

`O(n)` expected time and `O(n)` space.

## Edge cases

Empty/one element return false; adjacent/non-adjacent duplicates; negative numbers; repeated zero.

## Blank-editor success criteria

Finish in 15 minutes, compile, invoke empty/unique/duplicate inputs, explain why a set is sufficient, then modify it to return the first duplicated value plus a boolean.

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded.
