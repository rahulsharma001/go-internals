---
type: dsa-problem
language: go
company_focus:
  - apple
  - uber
priority: P0
pattern: frequency-signature
difficulty:
leetcode_url: https://leetcode.com/problems/group-anagrams/
status: not-started
first_attempt_date:
last_attempt_date:
next_review_date:
attempt_count: 0
best_time_minutes:
needs_revisit: true
source_conversations:
  - "Neetcode 49 Naive Approach | 2025-04-29 | 68107169-0520-8013-a1a3-7b8aaac0a30b"
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Group Anagrams

LeetCode: https://leetcode.com/problems/group-anagrams/

## Problem summary

Group lowercase English words that contain the same character multiset. Group order is irrelevant.

## Pattern

[[Arrays and Hash Maps Pattern]] — canonical signature as a map key.

## Brute-force intuition

For each ungrouped word, compare it with every remaining word using sorted copies or counts: roughly `O(n²k log k)` with repeated comparisons.

## Optimal intuition

Build one `[26]int` signature per word. Arrays are comparable in Go, so the signature can directly key `map[[26]int][]string`.

## Dry run

`eat` and `tea` both produce counts with one `a`, `e`, and `t`, so both append to the same bucket. `tan` produces a different key.

## Complete Go solution

```go
package main

import "fmt"

func groupAnagrams(words []string) [][]string {
	groups := make(map[[26]int][]string)
	for _, word := range words {
		var key [26]int
		for i := 0; i < len(word); i++ { key[word[i]-'a']++ }
		groups[key] = append(groups[key], word)
	}
	result := make([][]string, 0, len(groups))
	for _, group := range groups { result = append(result, group) }
	return result
}

func main() {
	fmt.Println(groupAnagrams([]string{"eat", "tea", "tan", "ate", "nat", "bat"}))
	fmt.Println(groupAnagrams([]string{}))
	fmt.Println(groupAnagrams([]string{""}))
}
```

Run: `go run main.go`. Map iteration makes group order nondeterministic.

## Complexity

`O(nk)` time for `n` words of maximum byte length `k`, plus `O(nk)` output/storage.

## Edge cases

Empty input; empty word; duplicate words; non-lowercase/Unicode outside this key contract; nondeterministic output order.

## Blank-editor success criteria

Finish in 30 minutes, explain why `[26]int` is a valid map key and `[]int` is not, compile edge cases, then make both groups and group contents deterministic.

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded. The 2025 source discussed Java approaches; this Go reference is not evidence of a Go attempt.
