---
type: coding-drill
domain: go
topic: map-frequency-counting
status: not-attempted
canonical: "[[Go Maps]]"
---

# Map Frequency Counting - Drill

## Problem

Implement `frequencies(words []string) map[string]int`. Count exact, case-sensitive words. From `main()`, count `go map go slice map go`, print `go=3`, `map=2`, and `slice=1` in deterministic key order, and show comma-ok lookup for a missing word.

## Constraints and edge cases

- Empty input returns an initialized empty map.
- Do not prefill keys.
- Do not depend on map iteration order.
- Explain why `counts[word]++` works for a missing key.

## Modification challenge

Make counting case-insensitive, then return the most frequent word with a documented tie-break rule.

## Attempt record

| Date | Time | Result | Hints | Failure category |
|---|---:|---|---|---|
| | | not attempted | | |

## Re-test history

| Date | Variant | Result | Remaining mistake |
|---|---|---|---|
| | exact / normalized | | |

<details>
<summary>Reference solution — reveal only after an attempt</summary>

```go
package main

import (
	"fmt"
	"sort"
)

func frequencies(words []string) map[string]int {
	counts := make(map[string]int, len(words))
	for _, word := range words {
		counts[word]++
	}
	return counts
}

func main() {
	counts := frequencies([]string{"go", "map", "go", "slice", "map", "go"})
	keys := make([]string, 0, len(counts))
	for key := range counts {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	for _, key := range keys {
		fmt.Printf("%s=%d\n", key, counts[key])
	}
	_, ok := counts["missing"]
	fmt.Println("missing present:", ok)
}
```

</details>

Related: [[Go Maps]] · [[Go Maps - Quick Revision]]

Index: [[Coding Drill Index]]
