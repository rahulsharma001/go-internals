---
type: canonical
domain: dsa
topic: graphs
status: reference
source_conversations:
  - "Graph DSA Basics | 2026-06-04 | 6a20ddd5-f634-83a2-ab1d-5faee9224afa"
  - "DFS vs BFS Understanding | 2026-06-10 | 6a290bd3-fa54-83a3-913f-6fdfa422abd2"
---
# Graphs Pattern

## Recognition clues

Connectivity, components, routes, prerequisites, grids of adjacent cells, spreading processes, shortest unweighted paths, or dependency cycles.

## Mental model

Separate representation, traversal frontier, and visited policy. DFS fully explores one branch/component; BFS expands by distance layers. Mark visited when scheduling a node, not after processing, to prevent duplicate work.

## Reusable Go template

```go
package main

import "fmt"

func reachable(graph map[int][]int, start int) map[int]bool {
	visited := map[int]bool{start: true}
	queue := []int{start}
	for head := 0; head < len(queue); head++ {
		node := queue[head]
		for _, next := range graph[node] {
			if visited[next] { continue }
			visited[next] = true
			queue = append(queue, next)
		}
	}
	return visited
}

func main() {
	graph := map[int][]int{1: {2, 3}, 2: {3}, 3: {}}
	fmt.Println(reachable(graph, 1)[3])
}
```

## Complexity

Adjacency-list traversal is `O(V+E)` time and `O(V)` visited/frontier space. Grid traversal is `O(rows×cols)` when each cell is processed once.

## Common mistakes

- Marking visited too late.
- Treating an undirected edge as one-way.
- Mutating the input grid without stating it.
- Using BFS for weighted shortest paths without justification.
- Forgetting disconnected components or ragged-grid assumptions.

## Representative problems

[[Number of Islands]], Clone Graph, Flood Fill, Rotting Oranges, Course Schedule, Graph Valid Tree.

## Modification questions

Avoid input mutation; return component sizes; make edges directed; return shortest path; handle multiple sources; detect a cycle.

Related: [[Stack and Queue Pattern]], [[Trees Pattern]], [[DSA Dashboard]].
