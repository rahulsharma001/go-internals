---
type: canonical
domain: go
topic: pointers
status: implementation-needed
aliases:
  - T07 Pointers & Pointer Semantics
source_notes:
  - "[[99 Archive/Superseded Originals/root/T07 Pointers & Pointer Semantics]]"
---

# Pointers in Go

## Why this matters

Pointers make mutation, optionality, identity, and sharing explicit. They also introduce nil handling, aliasing, escape-analysis effects, and synchronization responsibilities.

## Explain like I am 12 and mental model

A value is a document. A pointer is a note containing the document's location. Copying the note still points to the same document; copying the document creates an independent value. Go still passes the pointer value by value.

`&x` obtains an address, `*p` reads or writes the pointed value, and a pointer's zero value is `nil`. Go has no pointer arithmetic. Slices, maps, channels, functions, and interfaces already contain reference-like state; a pointer to them is rarely the default answer.

## Minimum executable example and complete main usage

```go
package main

import "fmt"

type Counter struct{ Value int }

func increment(c *Counter) error {
	if c == nil {
		return fmt.Errorf("counter is nil")
	}
	c.Value++
	return nil
}

func main() {
	c := Counter{Value: 3}
	p := &c
	if err := increment(p); err != nil {
		fmt.Println("error:", err)
		return
	}
	fmt.Println(c.Value) // 4
}
```

## Detailed dry run

`p` receives `c`'s address. Calling `increment` copies that address into the parameter. Dereferencing it reaches the same `Counter`, so the caller sees the update. The nil guard turns an otherwise possible panic into an explicit failure path.

## Core concepts and under the hood

- Returning a pointer to a local is safe; the compiler chooses storage lifetime.
- `new(T)` returns `*T` initialized to the zero value; `&T{...}` is usually clearer for structs.
- Addressability matters: map elements are not addressable because growth can relocate them; use read-modify-write or store pointers intentionally.
- Pointer receiver choice belongs with [[Go Methods and Receivers]]; interface satisfaction belongs with [[Go Method Sets]].
- Allocation location is a compiler decision, not “pointer means heap.” Inspect with compiler diagnostics and profiles instead of fixed folklore.

## Production usage, success, and failure

Use a pointer when a function must mutate caller-owned state, identity matters, copying is unsafe or meaningfully expensive, or nil has a documented meaning. Prefer values for small immutable data with useful zero values.

Success: ownership and nil behavior are explicit. Failure: multiple goroutines mutate the same pointee without synchronization, an API uses nil ambiguously, or a pointer is used solely from habit and creates unnecessary sharing.

## Common mistakes and trade-offs

- Saying Go is pass-by-reference.
- Dereferencing without defining nil behavior.
- Taking a pointer to an interface.
- Copying a value containing `sync.Mutex`.
- Using a pointer receiver to solve an interface method-set mismatch without understanding why.
- Assuming a returned pointer is invalid or always forces a particular allocation in every build.

Pointers reduce copying and enable mutation, but add aliasing, nil states, GC scanning, and race risk. Measure large-value copying before optimizing.

## Google / Senior Interview Lens

The minimum answer is “everything is passed by value, including pointers.” Follow-ups include receiver method sets, map element addressability, escape analysis, nil interfaces, and concurrency ownership. In code, handle nil deliberately and explain whether shared mutation is required.

## Active recall and blank-editor challenge

Implement a validated constructor, a mutating pointer method, and a non-mutating value method. Change the design to a value-only type and explain the method-set and ownership differences.

## Related notes

- [[Go Methods and Receivers]]
- [[Go Method Sets]]
- [[Go Memory Allocation and Escape Analysis]]
- [[Pointers in Go - Quick Revision]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
