---
type: canonical
domain: dsa
topic: arrays-hash-maps
status: reference
source_conversations:
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Arrays and Hash Maps Pattern

## Recognition clues

Pair lookup, duplicate detection, counts, grouping, membership, canonical signatures, or an exact subarray sum. Ask what information from the already-scanned prefix would remove a nested loop.

## Mental model

A map is memory attached to a linear scan. Decide precisely what the key and value mean before coding. Check a complement before insertion when an element cannot pair with itself. A set is `map[T]struct{}`; a frequency table is `map[T]int`.

## Reusable Go template

```go
package main

import "fmt"

func firstPair(nums []int, target int) ([]int, bool) {
	indexByValue := make(map[int]int, len(nums))
	for i, value := range nums {
		if j, ok := indexByValue[target-value]; ok {
			return []int{j, i}, true
		}
		indexByValue[value] = i
	}
	return nil, false
}

func main() {
	pair, ok := firstPair([]int{2, 7, 11, 15}, 9)
	fmt.Println(pair, ok)
}
```

## Complexity

Usually `O(n)` expected time and `O(n)` space. Hash-table operations are expected `O(1)`, not a worst-case guarantee. Sorting signatures may add `O(k log k)` per item.

## Common mistakes

- Using a slice as a Go map key; use a comparable array or string.
- Inserting before complement lookup when distinct indices are required.
- Forgetting `prefixCount[0] = 1` in prefix-sum counting.
- Assuming map iteration order is deterministic.
- Ignoring byte/rune or alphabet constraints in string signatures.

## Representative problems

[[Contains Duplicate]], [[Valid Anagram]], [[Two Sum]], [[Group Anagrams]], Product of Array Except Self, Longest Consecutive Sequence, Subarray Sum Equals K.

## Modification questions

Return all pairs; preserve deterministic group order; support Unicode; process a stream; allow negative values; return an error when no pair exists.

Related: [[Go Maps]], [[Go Slices]], [[DSA Dashboard]].
