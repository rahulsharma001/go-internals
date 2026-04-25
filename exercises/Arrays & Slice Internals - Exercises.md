# Arrays & Slice Internals — Exercise Solutions

> Complete solutions for Practice Checkpoint exercises from [[Arrays & Slice Internals]].

---

## Tier 3: Build It — Solution

### Task

Build a generic `Stack[T]` backed by a slice. Implement push, pop, peek, and report both used length and reserved slot count. Show that growing the stack triggers reallocation by printing a fingerprint of the backing array (the first element’s storage address) as you push. Optional but strongly recommended: show that pre-growing with the `Grow` function in the `slices` standard package holds the same backing address for a batch of pushes when you already reserved enough room.

### Solution

The program has three parts: the generic stack, a small helper that prints the **backing storage address** (the first element’s home in memory) together with the two slice header numbers you care about, and a `main` that runs two stories side by side.

**Why the backing address?** A slice is a small header. The “hotel block” in the earlier analogy is the real consecutive memory where elements live. When that block is too small, the run-time system allocates a new, larger block, copies the old elements, and the new slice points there. The address of the first stored element (or a safe stand-in for an empty block) is the easiest way to see that move in a short program. This uses the `unsafe` package in a read-only way to read where the data lives, which is a teaching pattern; production code that only needs a stack does not have to print addresses.

**Why pre-grow?** The `Grow` function from the `slices` package asks for enough reserved space so a sequence of `append` calls in the common case can fill those slots without shopping for a new block each time. Fewer block moves means fewer copies and a stable pointer for the life of that batch of operations.

**Minimum language version note:** the `slices` package and `slices.Grow` need a current Go tool-chain (1.21 or later is the usual baseline for `slices` utilities). If your install is older, update the tool-chain or replace `slices.Grow` with a manual `make` and copy loop that still reserves the same number of slots.

```go
package main

import (
	"fmt"
	"slices"
	"unsafe"
)

// Stack is a last-in, first-out collection backed by a single slice.
type Stack[T any] struct {
	data []T
}

// Push adds a value on top.
func (s *Stack[T]) Push(v T) {
	s.data = append(s.data, v)
}

// Pop removes and returns the top value, or reports that the stack is empty.
func (s *Stack[T]) Pop() (T, bool) {
	if len(s.data) == 0 {
		var zero T
		return zero, false
	}
	i := len(s.data) - 1
	v := s.data[i]
	// Shrink the visible length. We keep the same backing block; capacity
	// stays available for future Push calls without a new block until
	// the old size is passed again in pathological patterns.
	s.data = s.data[:i]
	return v, true
}

// Peek returns the top value without removing it, or false if empty.
func (s *Stack[T]) Peek() (T, bool) {
	if len(s.data) == 0 {
		var zero T
		return zero, false
	}
	return s.data[len(s.data)-1], true
}

// Len returns how many values are in the stack.
func (s *Stack[T]) Len() int { return len(s.data) }

// Cap returns how many element slots the backing array currently holds
// (reserved room before the run-time may need a new, larger array).
func (s *Stack[T]) Cap() int { return cap(s.data) }

// backingArrayAddr returns a numeric fingerprint of where the first element
// of the storage block lives, or 0 if there is no block (nil slice).
// This is for teaching only, not a stable identifier across run-times.
func backingArrayAddr[T any](data []T) uintptr {
	p := unsafe.SliceData(data)
	if p == nil {
		return 0
	}
	return uintptr(unsafe.Pointer(p))
}

func printState[T any](label string, data []T) {
	fmt.Printf("  %-28s  storage_addr=%#x  used_len=%d  reserved=%d\n",
		label, backingArrayAddr(data), len(data), cap(data),
	)
}

func main() {
	const pushes = 8

	// ---- Story 1: start with no reserved slots; watch append grow. ----
	fmt.Println("Story 1: no pre-reserved slots, eight pushes (append will grow the block):")
	var a Stack[int]
	printState("after new stack (empty)", a.data)
	var prevA uintptr
	for n := 1; n <= pushes; n++ {
		a.Push(n * 10)
		cur := backingArrayAddr(a.data)
		moved := ""
		if n > 1 && cur != prevA {
			moved = "  <-- block moved to a new storage address"
		} else if n == 1 {
			moved = "  <-- first block allocated on first element"
		}
		printState(fmt.Sprintf("after push %d", n), a.data)
		if moved != "" {
			fmt.Println(moved)
		}
		prevA = cur
	}
	fmt.Println()

	// ---- Story 2: pre-reserve enough slots, then the same eight pushes. ----
	fmt.Println("Story 2: pre-reserve for eight integers, then eight pushes (stable block):")
	var b Stack[int]
	// Request enough reserved room for eight int values without a growth step.
	// The zero-length, eight-capacity slice reuses the same block for each append.
	b.data = slices.Grow(b.data, pushes)
	printState("after pre-reserved space for eight (length still zero)", b.data)
	prevB := backingArrayAddr(b.data)
	for n := 1; n <= pushes; n++ {
		b.Push(n * 10)
		cur := backingArrayAddr(b.data)
		moved := ""
		if cur != prevB {
			moved = "  <-- block moved (unexpected in this pre-grown scenario)"
		}
		printState(fmt.Sprintf("after push %d", n), b.data)
		if moved != "" {
			fmt.Println(moved)
		}
		prevB = cur
	}
	fmt.Println()

	// named methods: Len, Cap, Peek, Pop
	fmt.Println("Named stack methods on a small string stack:")
	var t Stack[string]
	t.Push("first")
	t.Push("second")
	fmt.Printf("  Len=%d  Cap=%d  (count in use, reserved slot count)\n", t.Len(), t.Cap())
	if v, ok := t.Peek(); ok {
		fmt.Println("  Peek (top) =", v)
	}
	for t.Len() > 0 {
		if v, ok := t.Pop(); ok {
			fmt.Println("  Pop ->", v)
		}
	}
}
```

### Output

Run with `go run` (save the code as `main.go` in a module folder). The numeric **storage_addr** line will not match the sample below, because the run-time system picks fresh memory each time. The **pattern** is what you should compare.

```text
Story 1: no pre-reserved slots, eight pushes (append will grow the block):
  after new stack (empty)       storage_addr=0x0  used_len=0  reserved=0
  after push 1                  storage_addr=0xc00009a040  used_len=1  reserved=1
  <-- first block allocated on first element
  after push 2                  storage_addr=0xc00009a060  used_len=2  reserved=2
  <-- block moved to a new storage address
  after push 3                  storage_addr=0xc0000b8000  used_len=3  reserved=4
  <-- block moved to a new storage address
  after push 4                  storage_addr=0xc0000b8000  used_len=4  reserved=4
  after push 5                  storage_addr=0xc0000ba000  used_len=5  reserved=8
  <-- block moved to a new storage address
  after push 6                  storage_addr=0xc0000ba000  used_len=6  reserved=8
  after push 7                  storage_addr=0xc0000ba000  used_len=7  reserved=8
  after push 8                  storage_addr=0xc0000ba000  used_len=8  reserved=8

Story 2: pre-reserve for eight integers, then eight pushes (stable block):
  after pre-reserved space for eight (length still zero)  storage_addr=0xc0000ba040  used_len=0  reserved=8
  after push 1                  storage_addr=0xc0000ba040  used_len=1  reserved=8
  after push 2                  storage_addr=0xc0000ba040  used_len=2  reserved=8
  after push 3                  storage_addr=0xc0000ba040  used_len=3  reserved=8
  after push 4                  storage_addr=0xc0000ba040  used_len=4  reserved=8
  after push 5                  storage_addr=0xc0000ba040  used_len=5  reserved=8
  after push 6                  storage_addr=0xc0000ba040  used_len=6  reserved=8
  after push 7                  storage_addr=0xc0000ba040  used_len=7  reserved=8
  after push 8                  storage_addr=0xc0000ba040  used_len=8  reserved=8

Named stack methods on a small string stack:
  Len=2  Cap=2  (count in use, reserved slot count)
  Peek (top) = second
  Pop -> second
  Pop -> first
```

### What to observe

- **First story:** each time **reserved** (capacity) runs out, the next push that needs more room allocates a new backing block, copies old elements, and the **storage address** changes. You see a step pattern: grow from one slot, then two, then four, then eight for this run (exact growth rules are in the run-time, but doubling after small sizes is normal).

- **Second story:** `slices.Grow` with room for eight elements creates one backing block. Every push reuses the same **storage address** because the slice never needs a larger block in this loop. The **used** count goes up, **reserved** stays at eight, and the pointer stays put.

- **Header versus hotel:** the slice is the small record (not printed here) pointing at a block. Printing the block address is how you *see* when the run-time has moved the guests to a new hotel. Two slice values can share one block until a grow happens and only the updated slice (the one you assigned from `append`) sees the new block if you are not careful.

- **Length versus capacity in the table:** **used_len** is what `Len` returns (elements you treat as in the stack). **reserved** is what `Cap` returns (the backing array’s slot count). The small string example at the end shows `Peek` reading the last slot without changing length, and `Pop` shrinking length while keeping the same backing array until you push more than the reserved count again.

---
