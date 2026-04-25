# Go Memory Allocation & Value Semantics — Exercise Solutions

> Complete solutions for Practice Checkpoint exercises from [[T02 Go Memory Allocation & Value Semantics]] → Section 6.5

---

## Tier 3: Build It — Solution

### Task

Write a Go program that:
1. Creates a function returning a pointer to a local variable
2. Creates a function returning a value (no pointer)
3. Run `go build -gcflags="-m"` and verify which escapes and which doesn't
4. Bonus: create a struct larger than 128 bytes and benchmark value receiver vs pointer receiver using `testing.B`

---

### Part 1 & 2: Escape vs No-Escape

Save as `escape_demo.go`:

```go
package main

import "fmt"

// escapeToHeap returns a pointer to a local variable.
// The variable must survive after this function returns,
// so the compiler moves it to the heap.
func escapeToHeap() *int {
	x := 42
	return &x
}

// stayOnStack returns the value, not a pointer.
// Nothing needs to survive — everything stays on the stack.
func stayOnStack() int {
	x := 42
	p := &x
	return *p
}

// escapeViaChannel sends a pointer to a channel.
// Another goroutine will read it, so the data must live on the heap.
func escapeViaChannel(ch chan *int) {
	x := 99
	ch <- &x
}

// escapeUnknownSize creates a slice with a runtime-determined size.
// The compiler can't know how big it is at compile time → heap.
func escapeUnknownSize(n int) []byte {
	return make([]byte, n)
}

// stayOnStackFixedSize creates a slice with a compile-time constant size.
// The compiler knows exactly how big it is → can stay on stack.
func stayOnStackFixedSize() [64]byte {
	var buf [64]byte
	buf[0] = 'A'
	return buf
}

func main() {
	p := escapeToHeap()
	fmt.Println("escapeToHeap:", *p)

	v := stayOnStack()
	fmt.Println("stayOnStack:", v)

	ch := make(chan *int, 1)
	escapeViaChannel(ch)
	fmt.Println("escapeViaChannel:", *<-ch)

	s := escapeUnknownSize(100)
	fmt.Println("escapeUnknownSize len:", len(s))

	buf := stayOnStackFixedSize()
	fmt.Println("stayOnStackFixedSize:", buf[0])
}
```

### Running escape analysis

```bash
go build -gcflags="-m" escape_demo.go
```

### Expected output from escape analysis

```
./escape_demo.go:12:2: moved to heap: x
./escape_demo.go:18:2: x does not escape
./escape_demo.go:19:2: p does not escape
./escape_demo.go:25:2: moved to heap: x
./escape_demo.go:30:14: make([]byte, n) escapes to heap
./escape_demo.go:46:13: ... argument does not escape  (fmt calls may show escape)
```

### What to observe

- `escapeToHeap`: `x` escapes because it's returned as a pointer — someone outside this function needs it
- `stayOnStack`: `x` and `p` don't escape — the pointer is used locally and only the value is returned
- `escapeViaChannel`: `x` escapes because it's sent to a channel — another goroutine will read it
- `escapeUnknownSize`: the slice escapes because `n` is a variable — compiler doesn't know the size at compile time
- `stayOnStackFixedSize`: the array does NOT escape — fixed-size, returned by value

---

### Part 3: Value Receiver vs Pointer Receiver Benchmark

Save as `receiver_bench_test.go`:

```go
package main

import "testing"

// BigStruct is larger than 128 bytes (256 bytes here)
// to demonstrate where pointer receivers start winning on copy cost
type BigStruct struct {
	Data [256]byte
}

// SmallStruct is under 128 bytes
// to demonstrate where value receivers can be faster
type SmallStruct struct {
	X, Y, Z int64 // 24 bytes
}

func (b BigStruct) ValueMethod() int {
	return int(b.Data[0]) + int(b.Data[255])
}

func (b *BigStruct) PointerMethod() int {
	return int(b.Data[0]) + int(b.Data[255])
}

func (s SmallStruct) ValueMethodSmall() int64 {
	return s.X + s.Y + s.Z
}

func (s *SmallStruct) PointerMethodSmall() int64 {
	return s.X + s.Y + s.Z
}

// --- Big struct benchmarks ---

func BenchmarkBigValueReceiver(b *testing.B) {
	s := BigStruct{}
	s.Data[0] = 1
	s.Data[255] = 2
	for i := 0; i < b.N; i++ {
		_ = s.ValueMethod()
	}
}

func BenchmarkBigPointerReceiver(b *testing.B) {
	s := &BigStruct{}
	s.Data[0] = 1
	s.Data[255] = 2
	for i := 0; i < b.N; i++ {
		_ = s.PointerMethod()
	}
}

// --- Small struct benchmarks ---

func BenchmarkSmallValueReceiver(b *testing.B) {
	s := SmallStruct{X: 1, Y: 2, Z: 3}
	for i := 0; i < b.N; i++ {
		_ = s.ValueMethodSmall()
	}
}

func BenchmarkSmallPointerReceiver(b *testing.B) {
	s := &SmallStruct{X: 1, Y: 2, Z: 3}
	for i := 0; i < b.N; i++ {
		_ = s.PointerMethodSmall()
	}
}
```

### Running the benchmark

```bash
go test -bench=. -benchmem receiver_bench_test.go
```

### Expected output (approximate)

```
BenchmarkBigValueReceiver-8       50000000    ~25 ns/op    0 B/op    0 allocs/op
BenchmarkBigPointerReceiver-8    200000000     ~2 ns/op    0 B/op    0 allocs/op
BenchmarkSmallValueReceiver-8    500000000     ~1 ns/op    0 B/op    0 allocs/op
BenchmarkSmallPointerReceiver-8  500000000     ~1 ns/op    0 B/op    0 allocs/op
```

### What to observe

- **Big struct (256 bytes)**: Pointer receiver is significantly faster because value receiver copies 256 bytes every call. The larger the struct, the bigger the gap.
- **Small struct (24 bytes)**: Both are roughly the same speed. For small structs, value receivers are fine — the copy cost is negligible and you get cache-locality benefits.
- **0 allocs/op**: Neither escapes to heap in this benchmark — both stay on the stack. The difference is purely copy cost.
- **The ~128 byte crossover**: This is approximate. Always benchmark YOUR specific struct with YOUR access patterns. The real crossover depends on CPU cache, method complexity, and whether the pointer causes escape to heap.

---

> Back to main note → [[T02 Go Memory Allocation & Value Semantics]]
