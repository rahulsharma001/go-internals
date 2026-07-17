---
type: template
domain: dsa
topic: go-containers
status: reference
---
# Go DSA Containers

Minimal executable syntax for the containers most often needed in interviews. Rebuild the relevant part from memory; do not paste the whole file into attempts.

```go
package main

import (
	"container/heap"
	"fmt"
)

type IntHeap []int

func (h IntHeap) Len() int           { return len(h) }
func (h IntHeap) Less(i, j int) bool { return h[i] < h[j] }
func (h IntHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *IntHeap) Push(x any)        { *h = append(*h, x.(int)) }
func (h *IntHeap) Pop() any {
	old := *h
	n := len(old)
	x := old[n-1]
	*h = old[:n-1]
	return x
}

func main() {
	set := map[int]struct{}{2: {}}
	freq := map[int]int{}
	freq[2]++

	stack := []int{1, 2}
	top := stack[len(stack)-1]
	stack = stack[:len(stack)-1]

	queue := []int{10, 20}
	head := 0
	front := queue[head]
	head++

	h := &IntHeap{5, 1, 3}
	heap.Init(h)
	heap.Push(h, 2)
	minimum := heap.Pop(h).(int)

	_, exists := set[2]
	fmt.Println(exists, freq[2], top, stack, front, queue[head:], minimum)
}
```

Run: `go run main.go`.

Common errors: reading an empty stack; retaining a growing queue prefix; writing all five `heap.Interface` methods with the wrong pointer/value receivers; type-asserting outside `Push`/`Pop`; and using a value where an index is needed.

Related: [[Stack and Queue Pattern]], [[Heaps Pattern]], [[Go Slices]], [[Go Maps]].
