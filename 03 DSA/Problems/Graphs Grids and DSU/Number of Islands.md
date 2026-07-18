---
type: dsa-problem
language: go
company_focus:
  - apple
  - uber
priority: P0
pattern: grid-dfs-bfs
difficulty:
leetcode_url: https://leetcode.com/problems/number-of-islands/
status: not-started
first_attempt_date:
last_attempt_date:
next_review_date:
attempt_count: 0
best_time_minutes:
needs_revisit: true
source_conversations:
  - "Graph DSA Basics | 2026-06-04 | 6a20ddd5-f634-83a2-ab1d-5faee9224afa"
  - "DFS vs BFS Understanding | 2026-06-10 | 6a290bd3-fa54-83a3-913f-6fdfa422abd2"
  - "Amazon SDE I Prep | 2026-07-13 | 6a548ae5-bf68-83ee-9235-aeb4e863e479"
---
# Number of Islands

LeetCode: https://leetcode.com/problems/number-of-islands/

## Problem summary

Count four-directionally connected components of `'1'` cells. This version keeps the grid unchanged and tolerates ragged rows.

## Pattern

[[Graphs Pattern]] — every unvisited land cell starts one component traversal.

## Brute-force intuition

Repeatedly search the grid and rescan cells to discover connectivity without visited memory, causing substantial repeated work.

## Optimal intuition

Scan each cell once. On unvisited land, increment the island count and BFS from it, marking every scheduled land cell visited.

## Dry run

For rows `110`, `010`, `001`: the first cell reaches `(0,1)` and `(1,1)`, forming island 1; `(2,2)` remains separate, forming island 2.

## Complete Go solution

```go
package main

import "fmt"

type Cell struct { Row, Col int }

func numIslands(grid [][]byte) int {
	visited := map[Cell]bool{}
	directions := []Cell{{-1, 0}, {1, 0}, {0, -1}, {0, 1}}
	islands := 0
	for row := range grid {
		for col := range grid[row] {
			start := Cell{row, col}
			if grid[row][col] != '1' || visited[start] { continue }
			islands++
			visited[start] = true
			queue := []Cell{start}
			for head := 0; head < len(queue); head++ {
				current := queue[head]
				for _, direction := range directions {
					next := Cell{current.Row + direction.Row, current.Col + direction.Col}
					if next.Row < 0 || next.Row >= len(grid) || next.Col < 0 || next.Col >= len(grid[next.Row]) { continue }
					if grid[next.Row][next.Col] != '1' || visited[next] { continue }
					visited[next] = true
					queue = append(queue, next)
				}
			}
		}
	}
	return islands
}

func main() {
	grid := [][]byte{[]byte("110"), []byte("010"), []byte("001")}
	fmt.Println(numIslands(grid), string(grid[0]))
	fmt.Println(numIslands(nil))
	fmt.Println(numIslands([][]byte{[]byte("111"), []byte("1")}))
}
```

Run: `go run main.go`.

## Complexity

`O(cells)` time and `O(land)` visited/queue space.

## Edge cases

Empty grid/rows; all water; all land; diagonal land is disconnected; ragged rows; input remains unchanged.

## Blank-editor success criteria

Finish in 35 minutes, state the visited-on-enqueue policy, compile empty/all-land/diagonal cases, then implement an in-place DFS version and compare mutation/space trade-offs.

## Re-attempt history

| Date | Minutes | Result | Hints | Modification | Next review |
| --- | ---: | --- | --- | --- | --- |
| — | — | not-attempted | — | — | after first attempt |

Observed mistakes: none recorded.

## Problem in Simple Words

Count four-directionally connected land groups.

## Example

Rows 10 and 01 contain two islands.

## Clarifying Questions

- May input be empty, invalid, or mutated?
- What duplicate, ordering, numeric, or node-identity guarantees apply?

## Pattern Recognition

- Signals in the question: grid traversal.
- Likely data structure: the structure that directly represents the invariant.
- Common wrong approach: repeated scans or state updates that lose the invariant.
- Key invariant: Starting from unseen land marks exactly one whole component.

## Approaches

### Brute Force

- Intuition: enumerate candidates directly.
- Complexity: derive during the cold attempt.
- Why it may fail: it repeats work and misses the expected bound.

### Better Approach

Use only if a genuine intermediate approach clarifies the progression.

### Optimal Approach

- Intuition and complete runnable reference: preserved above from the existing canonical note.
- Invariant: Starting from unseen land marks exactly one whole component.
- Complexity: verify the bound above during explanation.

## Small Dry Run

Reconstruct the existing dry run without looking, then add one adversarial case.

## Go-Specific Notes

Check slice initialization, map membership, pointer rewiring, queue head indexing, recursive closure declaration, heap pointer receivers, input mutation, and byte/rune semantics as applicable.

## Implementation

The pre-existing executable reference above is preserved. For practice, close this note and reproduce a complete main() or test invocation from a blank editor.

## Tests and Edge Cases

Re-run the preserved edge cases and add one case that breaks the tempting wrong approach.

## Explain Aloud

Restate → pattern → invariant → one transition → complexity → Go detail → variation, within 60–90 seconds.

## Variations and Follow-ups

Make one constraint change after a clean reconstruction.

## Mistakes I Made

None recorded. Add only observed mistakes from an actual attempt.

## Review History

Use the preserved re-attempt table above and the central tracker; never infer an attempt from the reference solution.
