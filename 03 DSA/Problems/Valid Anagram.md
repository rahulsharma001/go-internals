---
type: problem
domain: dsa
status: reference-not-attempted
pattern: arrays-hash-maps
source_conversations:
  - "Golang Implementation Fluency Issues | 2026-07-15 | 6a5778fc-3758-83ee-9998-cba2bb1b0577"
---
# Valid Anagram

## Problem summary

Given two lowercase English strings, return whether one is a rearrangement of the other.

## Pattern

[[Arrays and Hash Maps Pattern]] — compare frequency signatures.

## Brute-force intuition

Sort both strings and compare them: `O(n log n)` time and `O(n)` space for byte copies.

## Optimal intuition

Lengths must match. Increment a 26-slot count for `s` and decrement for `t`; every final count must be zero. The fixed array makes the lowercase-English constraint explicit.

## Dry run

`anagram` versus `nagaram`: each letter adds once and subtracts once, leaving all zeros. `rat` versus `car` leaves non-zero counts for `t` and `c`.

## Complete Go solution

```go
package main

import "fmt"

func isAnagram(s, t string) bool {
	if len(s) != len(t) { return false }
	var count [26]int
	for i := 0; i < len(s); i++ {
		count[s[i]-'a']++
		count[t[i]-'a']--
	}
	for _, value := range count {
		if value != 0 { return false }
	}
	return true
}

func main() {
	fmt.Println(isAnagram("anagram", "nagaram"))
	fmt.Println(isAnagram("rat", "car"))
	fmt.Println(isAnagram("", ""))
}
```

Run: `go run main.go`.

## Complexity

`O(n)` time and `O(1)` auxiliary space for the fixed alphabet.

## Edge cases

Different lengths; empty strings; repeated letters; non-lowercase/Unicode input is outside this implementation's contract.

## Blank-editor success criteria

Finish in 15 minutes, state the alphabet assumption, compile three cases, then modify the implementation to support arbitrary Unicode using `map[rune]int`.

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded. Historical Java work does not count as this Go attempt.
