---
type: coding-drill
domain: go
topic: nested-maps-slice-values
status: not-attempted
canonical: "[[Go Maps]]"
---

# Nested Maps and Slice Values - Drill

## Problem

Build `Skills`, a `map[string]map[string][]string`, representing team → engineer → skills. Implement `addSkill` that initializes missing nested maps and appends a skill.

From `main()`, add two skills for Rahul in backend and one skill for Ada in platform, then print those exact slices using explicit keys.

Expected output:

```text
[Go PostgreSQL]
[Kubernetes]
```

## Constraints and edge cases

- The zero outer map passed to `addSkill` must be initialized before the call; explain why the function cannot replace a nil outer map without returning it.
- Initialize missing inner maps.
- Appending to a missing slice value should work.
- Do not depend on map iteration order.

## Modification challenge

Prevent duplicate skills while preserving insertion order. Then change the value to a struct and demonstrate copy-edit-write.

## Attempt record

| Date | Time | Result | Hints | Failure category |
|---|---:|---|---|---|
| | | not attempted | | |

## Re-test history

| Date | Variant | Result | Remaining mistake |
|---|---|---|---|
| | append / dedupe | | |

<details>
<summary>Reference solution — reveal only after an attempt</summary>

```go
package main

import "fmt"

type Skills map[string]map[string][]string

func addSkill(skills Skills, team, engineer, skill string) {
	if skills[team] == nil {
		skills[team] = make(map[string][]string)
	}
	skills[team][engineer] = append(skills[team][engineer], skill)
}

func main() {
	skills := make(Skills)
	addSkill(skills, "backend", "Rahul", "Go")
	addSkill(skills, "backend", "Rahul", "PostgreSQL")
	addSkill(skills, "platform", "Ada", "Kubernetes")

	fmt.Println(skills["backend"]["Rahul"])
	fmt.Println(skills["platform"]["Ada"])
}
```

</details>

Related: [[Go Maps]] · [[Collection Transformations in Go]]

