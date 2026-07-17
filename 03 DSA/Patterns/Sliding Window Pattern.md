---
type: canonical
domain: dsa
topic: sliding-window
status: reference
source_conversations:
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Sliding Window Pattern

## Recognition clues

Longest/shortest/count of a contiguous substring or subarray where state can be updated by adding the right element and removing the left element.

## Mental model

The window `[left,right]` is a candidate with an explicit validity rule. Expand right to gain information. Shrink left while invalid, or while valid when seeking a minimum. Fixed windows enforce size; variable windows enforce a predicate.

## Reusable Go template

```go
package main

import "fmt"

func longestAtMostKDistinct(s string, k int) int {
	if k <= 0 { return 0 }
	count := map[byte]int{}
	left, best := 0, 0
	for right := 0; right < len(s); right++ {
		count[s[right]]++
		for len(count) > k {
			count[s[left]]--
			if count[s[left]] == 0 { delete(count, s[left]) }
			left++
		}
		if size := right-left+1; size > best { best = size }
	}
	return best
}

func main() { fmt.Println(longestAtMostKDistinct("eceba", 2)) }
```

## Complexity

Usually `O(n)` time because each boundary advances at most `n` times; space is the tracked alphabet/domain, often `O(k)` or `O(Σ)`.

## Common mistakes

- Not writing the validity predicate.
- Using a window for exact sums when negative values break monotonic shrink behavior.
- Shrinking only once when `while` is required.
- Updating a minimum before the window is valid or a maximum after it is invalid.
- Claiming Unicode support while indexing bytes.

## Representative problems

Best Time to Buy and Sell Stock, [[Longest Substring Without Repeating Characters]], Minimum Size Subarray Sum, Permutation in String, Longest Repeating Character Replacement.

## Modification questions

Return the range/substring; count all valid windows; move from ASCII to runes; change fixed to variable window; accept a stream.

Related: [[Arrays and Hash Maps Pattern]], [[DSA Dashboard]].
