---
type: problem
domain: dsa
status: reference-not-attempted
pattern: sliding-window
source_conversations:
  - "Two pointer questions FAANG | 2025-12-02 | 692e82d7-f7e4-8324-964d-f935b2756421"
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Longest Substring Without Repeating Characters

LeetCode: https://leetcode.com/problems/longest-substring-without-repeating-characters/

## Problem summary

Return the maximum byte length of a substring with no repeated byte. This version explicitly assumes ASCII input.

## Pattern

[[Sliding Window Pattern]] — the current window contains unique bytes.

## Brute-force intuition

Start at every index and extend until a repeat, rebuilding state: `O(n²)` time.

## Optimal intuition

Store the index after each byte's last occurrence. When a repeated byte is inside the current window, jump `left` past it; never move `left` backward.

## Dry run

`abba`: `a` gives best 1, `b` gives 2, second `b` jumps `left` to 2, final `a` was last seen before `left`, so window `ba` restores best 2.

## Complete Go solution

```go
package main

import "fmt"

func lengthOfLongestSubstring(s string) int {
	lastAfter := map[byte]int{}
	left, best := 0, 0
	for right := 0; right < len(s); right++ {
		if next, seen := lastAfter[s[right]]; seen && next > left { left = next }
		lastAfter[s[right]] = right + 1
		if size := right-left+1; size > best { best = size }
	}
	return best
}

func main() {
	for _, input := range []string{"abcabcbb", "bbbbb", "abba", ""} {
		fmt.Println(input, lengthOfLongestSubstring(input))
	}
}
```

Run: `go run main.go`.

## Complexity

`O(n)` time and `O(Σ)` space, bounded by the byte alphabet in this implementation.

## Edge cases

Empty; all same; repeat immediately outside the current window (`abba`); Unicode requires a deliberate rune-index contract.

## Blank-editor success criteria

Finish in 30 minutes, state the invariant and why `left` never retreats, compile `abba`, then return the substring and implement a rune-aware variant.

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded.
