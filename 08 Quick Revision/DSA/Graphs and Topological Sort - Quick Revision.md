---
type: quick-revision
domain: dsa
topic: graphs-and-topological-sort
review_time: under-5-minutes
---

# Graphs and Topological Sort — Quick Revision

## Mental Model

Start by naming vertices, edges, direction, and whether weights exist. DFS/BFS answers reachability and components; multi-source BFS gives earliest unweighted arrival; Dijkstra handles non-negative weighted shortest paths. Topological sort applies to directed dependency graphs. Kahn’s algorithm tracks remaining indegree and emits zero-indegree vertices; processing fewer than V proves a cycle. DFS coloring uses unvisited, visiting, and done states; an edge to visiting is a back edge. For an inferred alphabet, create vertices for every observed character and add only the first differing-character edge between adjacent words.

## Go and Interview Checklist

Initialize every adjacency list deliberately and deduplicate edges if repeated edges would inflate indegree. In Go, make(map[T][]T) supports append to a missing key, while nested maps need explicit initialization. Use []int plus a head index for BFS. Keep visited ownership local to one run. Alien Dictionary must reject the invalid prefix case where a longer word precedes its exact prefix. Test disconnected vertices, duplicate edges, a self-cycle, multiple valid orders, empty adjacency, and a cycle hidden outside the source component.

## 60-Second Recall

1. Name the invariant without code.
2. State what enters, leaves, or changes the maintained state.
3. Give expected time and space complexity.
4. Name the Go representation and one edge-case test.
5. Close this note and reconstruct one linked problem from a blank editor.

## Practice Links

[[Clone Graph]], [[Course Schedule]], [[Course Schedule II]], [[Alien Dictionary]], [[Rotting Oranges]], [[Word Ladder]], [[Network Delay Time]], [[Number of Connected Components in an Undirected Graph]]

A successful read is not completion evidence. Update [[DSA Practice Tracker]] only after a complete invocation, explanation, variation, and scheduled re-test.

