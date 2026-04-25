# Go Type System & Value Semantics — Exercise Solutions

> Complete solutions for Practice Checkpoint exercises from [[T01 Go Type System & Value Semantics]] → Section 6.5

---

## Tier 3: Build It — Solution

### Task

1. Create a `Shape` interface with `Area() float64`
2. Implement it for `Circle` (value receiver) and `Rectangle` (pointer receiver)
3. Write a function `printArea(s Shape)` and call it with both types
4. Observe which requires `&` and which doesn't. Then verify with `var _ Shape = Circle{}` and `var _ Shape = (*Rectangle)(nil)` compile-time checks.

---

### Solution

Save as `shapes.go` (runnable in [Go Playground](https://go.dev/play/)):

```go
package main

import (
	"fmt"
	"math"
)

// Shape is a minimal interface — one method.
// Any type with Area() float64 satisfies it implicitly.
type Shape interface {
	Area() float64
}

// Circle uses a VALUE receiver for Area().
// This means both Circle and *Circle satisfy Shape.
type Circle struct {
	Radius float64
}

func (c Circle) Area() float64 {
	return math.Pi * c.Radius * c.Radius
}

// Rectangle uses a POINTER receiver for Area().
// This means ONLY *Rectangle satisfies Shape (not Rectangle).
type Rectangle struct {
	Width, Height float64
}

func (r *Rectangle) Area() float64 {
	return r.Width * r.Height
}

// printArea accepts any Shape — it doesn't care about the concrete type.
// This is Go's structural typing: if it has Area(), it's a Shape.
func printArea(s Shape) {
	fmt.Printf("  Type: %T, Area: %.2f\n", s, s.Area())
}

// Compile-time interface satisfaction checks.
// These lines produce zero runtime code — they ONLY verify at compile time
// that the type satisfies the interface.
var _ Shape = Circle{}            // Circle (value) satisfies Shape ✅
var _ Shape = (*Rectangle)(nil)   // *Rectangle satisfies Shape ✅

// Uncommenting the next line would cause a compile error:
// var _ Shape = Rectangle{}      // Rectangle (value) does NOT satisfy Shape ❌

func main() {
	fmt.Println("=== Circle (value receiver) ===")

	c := Circle{Radius: 5.0}
	printArea(c)      // ✅ value works — Circle has Area() via value receiver
	printArea(&c)     // ✅ pointer also works — *Circle inherits value methods

	fmt.Println()
	fmt.Println("=== Rectangle (pointer receiver) ===")

	r := Rectangle{Width: 4.0, Height: 6.0}
	// printArea(r)   // ❌ COMPILE ERROR: Rectangle (value) lacks Area()
	printArea(&r)     // ✅ pointer works — *Rectangle has Area()

	fmt.Println()
	fmt.Println("=== Why the asymmetry? ===")
	fmt.Println("  Circle.Area() uses value receiver → available on Circle AND *Circle")
	fmt.Println("  Rectangle.Area() uses pointer receiver → available ONLY on *Rectangle")
	fmt.Println("  Because interface stores a COPY — pointer receiver on a copy would")
	fmt.Println("  mutate the copy, not the original. Go prevents this at compile time.")
}
```

### Output

```
=== Circle (value receiver) ===
  Type: main.Circle, Area: 78.54
  Type: *main.Circle, Area: 78.54

=== Rectangle (pointer receiver) ===
  Type: *main.Rectangle, Area: 24.00

=== Why the asymmetry? ===
  Circle.Area() uses value receiver → available on Circle AND *Circle
  Rectangle.Area() uses pointer receiver → available ONLY on *Rectangle
  Because interface stores a COPY — pointer receiver on a copy would
  mutate the copy, not the original. Go prevents this at compile time.
```

### What to observe

1. **`printArea(c)` works** — Circle has a value receiver, so both `Circle` and `*Circle` satisfy Shape
2. **`printArea(r)` would NOT compile** (try uncommenting it!) — Rectangle only has a pointer receiver, so only `*Rectangle` satisfies Shape
3. **`printArea(&r)` works** — passing a pointer gives access to all methods
4. **The `var _ Shape = ...` lines** are zero-cost compile-time checks. They're the idiomatic Go pattern for asserting interface satisfaction without any runtime overhead. Use these in your code to catch interface bugs early.
5. **`%T` in Printf** shows the concrete type stored in the interface — useful for debugging

### Key takeaway

The rule is simple: **if ANY method uses a pointer receiver, you must pass a pointer to satisfy the interface.** This is because the interface stores a copy of the value, and Go prevents pointer-receiver methods on copies to avoid silent mutation bugs.

---

> Back to main note → [[T01 Go Type System & Value Semantics]]
