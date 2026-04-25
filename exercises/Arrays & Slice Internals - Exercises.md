# Arrays & Slice Internals — Exercise Solutions

> Complete solutions for Practice Checkpoint exercises from [[Arrays & Slice Internals]].

---

## Tier 3: Solution 1 — Generic Stack[T] with reallocation tracking

### Task

Build a generic `Stack[T]` backed by a slice. Implement Push, Pop, Peek, Len, Cap. Show that growing the stack triggers reallocation by printing the backing array address before and after pushes. Then show that pre-allocating with `slices.Grow` avoids reallocations.

### Solution

```go
package main

import (
	"fmt"
	"slices"
	"unsafe"
)

type Stack[T any] struct {
	data []T
}

func (s *Stack[T]) Push(v T) {
	s.data = append(s.data, v)
}

func (s *Stack[T]) Pop() (T, bool) {
	if len(s.data) == 0 {
		var zero T
		return zero, false
	}
	i := len(s.data) - 1
	v := s.data[i]
	s.data = s.data[:i]
	return v, true
}

func (s *Stack[T]) Peek() (T, bool) {
	if len(s.data) == 0 {
		var zero T
		return zero, false
	}
	return s.data[len(s.data)-1], true
}

func (s *Stack[T]) Len() int { return len(s.data) }
func (s *Stack[T]) Cap() int { return cap(s.data) }

func backingAddr[T any](data []T) uintptr {
	p := unsafe.SliceData(data)
	if p == nil {
		return 0
	}
	return uintptr(unsafe.Pointer(p))
}

func main() {
	const pushes = 8

	// Story 1: no pre-allocation — watch append grow
	fmt.Println("Story 1: no pre-allocation, 8 pushes:")
	var a Stack[int]
	var prevA uintptr
	for n := 1; n <= pushes; n++ {
		a.Push(n * 10)
		cur := backingAddr(a.data)
		moved := ""
		if prevA != 0 && cur != prevA {
			moved = " <-- MOVED"
		}
		fmt.Printf("  push %d: addr=%#x len=%d cap=%d%s\n",
			n, cur, a.Len(), a.Cap(), moved)
		prevA = cur
	}

	// Story 2: pre-allocate — stable address
	fmt.Println("\nStory 2: pre-allocate for 8, then 8 pushes:")
	var b Stack[int]
	b.data = slices.Grow(b.data, pushes)
	base := backingAddr(b.data)
	for n := 1; n <= pushes; n++ {
		b.Push(n * 10)
		cur := backingAddr(b.data)
		stable := "stable"
		if cur != base {
			stable = "MOVED!"
		}
		fmt.Printf("  push %d: addr=%#x len=%d cap=%d (%s)\n",
			n, cur, b.Len(), b.Cap(), stable)
	}
}
```

### Output

```
Story 1: no pre-allocation, 8 pushes:
  push 1: addr=0xc00001a0b8 len=1 cap=1
  push 2: addr=0xc00001a0d0 len=2 cap=2 <-- MOVED
  push 3: addr=0xc00001e120 len=3 cap=4 <-- MOVED
  push 4: addr=0xc00001e120 len=4 cap=4
  push 5: addr=0xc00001c180 len=5 cap=8 <-- MOVED
  push 6: addr=0xc00001c180 len=6 cap=8
  push 7: addr=0xc00001c180 len=7 cap=8
  push 8: addr=0xc00001c180 len=8 cap=8

Story 2: pre-allocate for 8, then 8 pushes:
  push 1: addr=0xc00001c1c0 len=1 cap=8 (stable)
  push 2: addr=0xc00001c1c0 len=2 cap=8 (stable)
  push 3: addr=0xc00001c1c0 len=3 cap=8 (stable)
  push 4: addr=0xc00001c1c0 len=4 cap=8 (stable)
  push 5: addr=0xc00001c1c0 len=5 cap=8 (stable)
  push 6: addr=0xc00001c1c0 len=6 cap=8 (stable)
  push 7: addr=0xc00001c1c0 len=7 cap=8 (stable)
  push 8: addr=0xc00001c1c0 len=8 cap=8 (stable)
```

### What to observe

- **Story 1:** Address changes on pushes 2, 3, 5 — each time capacity ran out and `append` allocated a new backing array. Growth: 1→2→4→8.
- **Story 2:** `slices.Grow` pre-allocates capacity 8. All pushes reuse the same address. Zero reallocations.
- Pre-allocation with `make([]T, 0, n)` or `slices.Grow` is critical in hot paths.

---

## Tier 3: Solution 2 — removeAt without pointer leak

### Task

Implement in-place `removeAt(s []T, i int) []T` that removes element at index `i` without leaking pointers in the unused capacity.

### Solution

```go
package main

import "fmt"

func removeAt[T any](s []T, i int) []T {
	copy(s[i:], s[i+1:])
	var zero T
	s[len(s)-1] = zero // clear tail to prevent pointer/GC leak
	return s[:len(s)-1]
}

func main() {
	names := []string{"alice", "bob", "charlie", "dave"}
	fmt.Println("Before:", names, "len:", len(names), "cap:", cap(names))

	names = removeAt(names, 1) // remove "bob"
	fmt.Println("After:", names, "len:", len(names), "cap:", cap(names))

	ptrs := []*int{ptr(1), ptr(2), ptr(3), ptr(4)}
	fmt.Println("\nPointer slice before:", deref(ptrs))
	ptrs = removeAt(ptrs, 2) // remove *3
	fmt.Println("Pointer slice after:", deref(ptrs))
}

func ptr(v int) *int { return &v }
func deref(s []*int) []int {
	out := make([]int, len(s))
	for i, p := range s {
		out[i] = *p
	}
	return out
}
```

### Output

```
Before: [alice bob charlie dave] len: 4 cap: 4
After: [alice charlie dave] len: 3 cap: 4

Pointer slice before: [1 2 3 4]
Pointer slice after: [1 2 4]
```

### What to observe

- `copy(s[i:], s[i+1:])` shifts elements left, overwriting the removed position.
- Setting the tail slot to the zero value prevents GC leaks for pointer/struct slices.
- Without zeroing, the old pointer at `s[3]` (now hidden in cap) still references the removed object.

---

## Tier 3: Solution 3 — Rotate by three-reverse trick

### Task

Implement in-place left rotation of a slice by `k` positions using the three-reverse trick.

### Solution

```go
package main

import "fmt"

func reverse[T any](s []T) {
	for i, j := 0, len(s)-1; i < j; i, j = i+1, j-1 {
		s[i], s[j] = s[j], s[i]
	}
}

func rotateLeft[T any](s []T, k int) {
	n := len(s)
	if n == 0 {
		return
	}
	k = k % n
	if k < 0 {
		k += n
	}
	reverse(s[:k])
	reverse(s[k:])
	reverse(s)
}

func main() {
	data := []int{1, 2, 3, 4, 5, 6, 7}
	fmt.Println("Before:", data)
	rotateLeft(data, 3)
	fmt.Println("After rotateLeft by 3:", data)
}
```

### Output

```
Before: [1 2 3 4 5 6 7]
After rotateLeft by 3: [4 5 6 7 1 2 3]
```

### What to observe

- Three-reverse trick: reverse [1,2,3]→[3,2,1], reverse [4,5,6,7]→[7,6,5,4], reverse all→[4,5,6,7,1,2,3].
- O(n) time, O(1) space — no allocation, purely in-place.
- Classic interview question testing slice manipulation fundamentals.

---

## Tier 3: Solution 4 — Safe line reader with three-index slice

### Task

Implement a safe line reader that uses `data[:pos:pos]` (three-index slice) to prevent append from overwriting data in a reused buffer.

### Solution

```go
package main

import "fmt"

func splitLines(data []byte) [][]byte {
	var lines [][]byte
	start := 0
	for i, b := range data {
		if b == '\n' {
			line := data[start:i:i] // cap pinned to i
			lines = append(lines, line)
			start = i + 1
		}
	}
	if start < len(data) {
		line := data[start:len(data):len(data)]
		lines = append(lines, line)
	}
	return lines
}

func main() {
	buf := []byte("hello\nworld\nfoo\n")
	lines := splitLines(buf)
	for i, l := range lines {
		fmt.Printf("line %d: %q  (len=%d, cap=%d)\n", i, l, len(l), cap(l))
	}

	// Demonstrate safety: appending to line 0 does NOT overwrite line 1
	lines[0] = append(lines[0], '!')
	fmt.Printf("\nAfter appending '!' to line 0:\n")
	fmt.Printf("  line 0: %q\n", lines[0])
	fmt.Printf("  line 1: %q  (unchanged — three-index prevented overwrite)\n", lines[1])
}
```

### Output

```
line 0: "hello"  (len=5, cap=5)
line 1: "world"  (len=5, cap=5)
line 2: "foo"  (len=3, cap=3)

After appending '!' to line 0:
  line 0: "hello!"
  line 1: "world"  (unchanged — three-index prevented overwrite)
```

### What to observe

- `data[start:i:i]` pins capacity to exactly the line length. Append to line 0 forces a new allocation.
- Without the third index, `data[start:i]` would have capacity extending to the end of `data`, and `append(lines[0], '!')` would overwrite the `\n` or the start of "world".
- This pattern is essential when parsing a shared buffer into multiple sub-slices.

---
