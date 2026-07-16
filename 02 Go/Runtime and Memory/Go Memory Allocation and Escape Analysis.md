---
type: canonical
domain: go
topic: allocation-escape-analysis
status: learning
aliases:
  - T02 Go Memory Allocation & Value Semantics
source_notes:
  - "[[99 Archive/Superseded Originals/root/T02 Go Memory Allocation & Value Semantics]]"
  - "[[99 Archive/Superseded Originals/prerequisites/P06 Function Call Stack]]"
---

# Go Memory Allocation and Escape Analysis

## Why this matters

Allocation location and object lifetime affect latency, GC work, cache behavior, and memory retention. The compiler decides placement from escape analysis; source syntax such as `new` or `&T{}` does not dictate it alone.

## Mental model and core concepts

Function frames and goroutine stacks store call-local execution state. Heap storage supports values whose lifetime or reachability cannot remain confined to a frame. Escape analysis proves what can stay local and moves what must outlive or be shared according to compiler rules.

- Go passes every argument by value.
- Returning a pointer is safe; the compiler ensures the pointee lives long enough.
- Interface boxing, closure capture, variable-size data, and sharing may influence escape, but none is a universal one-line rule.
- Slices copy a header and may share backing storage; maps and channels refer to runtime-managed state.
- Stack growth and allocation strategies are implementation details, not language contracts.

## Minimum executable example

```go
package main

import "fmt"

type User struct{ Name string }

func newUser(name string) *User { return &User{Name: name} }

func renameCopy(user User, name string) User {
	user.Name = name
	return user
}

func main() {
	original := User{Name: "A"}
	copy := renameCopy(original, "B")
	pointer := newUser("C")
	fmt.Println(original.Name, copy.Name, pointer.Name)
}
```

The semantic result is defined by value copying and pointer access, regardless of a particular compiler's placement decision.

## Under the hood and tooling

Use compiler escape diagnostics to form a hypothesis, benchmarks with allocation reporting to compare variants, and heap/alloc profiles under representative load to find meaningful hotspots. Treat diagnostic wording as version-specific.

Optimize allocation rate and retained live data only after measuring. A pooled object can reduce allocation but increases complexity, retention, and ownership risk. A small pointer-heavy representation may cost more GC scanning than a compact value representation.

## Production success and failure

Success: profiles identify a hot allocation path; a benchmark captures the behavior; a change reduces allocations without breaking ownership or increasing retained memory; load tests confirm latency and memory improvement.

Failure: choosing pointers everywhere to “avoid copies,” retaining a large backing array through a tiny slice, pooling without resetting data, or applying a fixed size threshold as universal receiver guidance.

## Common mistakes and trade-offs

- “Pointers always allocate on heap.”
- “Maps are passed by reference.”
- Confusing allocation count with live heap size.
- Optimizing compiler output instead of the end-to-end bottleneck.
- Ignoring the GC scanning cost of pointer-rich structures.

## Google / Senior Interview Lens

Start with semantics: value passing and compiler-chosen placement. Then discuss lifetime, escape causes, profiling, and a measured optimization workflow. Connect memory choices to caches, request buffers, queues, and GC rather than quoting unstable nanosecond claims.

## Active recall and challenge

Predict which values may escape in a closure, returned pointer, and interface conversion; compile with diagnostics; then explain why the semantic code must not depend on the result.

## Related notes

- [[Pointers in Go]]
- [[Go Garbage Collector]]
- [[Go Slices]]
- [[Go Memory Model]]
- [[Go Memory Model - Quick Revision]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
