---
type: quick-revision
domain: dsa
status: implementation-needed
---
# Go DSA Syntax - 5 Minute Revision

```text
seen := make(map[int]int)
if index, ok := seen[target-x]; ok { return []int{index, i} }
seen[x] = i

stack = append(stack, value)
value = stack[len(stack)-1]
stack = stack[:len(stack)-1]

for head := 0; head < len(queue); head++ {
	current := queue[head]
	_ = current
}
```

- Copy before sorting when input mutation is not allowed: `work := append([]int(nil), nums...)`.
- A `[26]int` is comparable and can be a map key; a `[]int` cannot.
- Tree/list nodes are usually pointers; check `nil` before dereference.
- Prefer queue head indexes over repeatedly doing `queue = queue[1:]` in long traversals.
- Use `mid := left + (right-left)/2` and keep one boundary convention.
- Go strings index bytes. State the ASCII/lowercase constraint or use runes deliberately.
- `container/heap` is a min-heap when `Less(i,j)` uses `<`.

Blank-editor gate: recreate map lookup, stack pop, queue scan, a node constructor, and the minimal heap from [[Go DSA Containers]] in 20 minutes, compile it, then change one value type.

Related: [[Go Maps]], [[Go Slices]], [[Complete Go Programs]], [[DSA Pattern Recognition - 5 Minute Revision]].
