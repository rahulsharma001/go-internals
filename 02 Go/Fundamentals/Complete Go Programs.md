---
type: canonical
domain: go
topic: complete-go-programs
status: implementation-needed
source_notes:
  - "[[99 Archive/Superseded Originals/exercises/T01 Go Type System - Exercises]]"
  - "[[99 Archive/Superseded Originals/exercises/T04 Arrays & Slice Internals - Exercises]]"
  - "[[99 Archive/Superseded Originals/exercises/T08 Map Internals - Exercises]]"
  - "[[99 Archive/Superseded Originals/exercises/T09 Error Handling Patterns - Exercises]]"
  - "[[99 Archive/Superseded Originals/exercises/T12 Interface Design Principles - Exercises]]"
---

# Complete Go Programs

## Problem and mental model

A snippet can demonstrate syntax while hiding whether the code can actually be invoked. Interview implementation requires a closed loop: declare the package, import only what is used, define data and behavior, construct values, call the behavior from `main`, observe output, and exercise at least one failure or edge case.

Treat `main()` as the composition root. It selects concrete implementations, creates dependencies, invokes the use case, handles returned errors, and makes behavior observable. Business logic should remain in functions or methods rather than being buried inside `main`.

## Minimum executable shape

```go
package main

import "fmt"

func double(values []int) []int {
	out := make([]int, len(values))
	for i, value := range values {
		out[i] = value * 2
	}
	return out
}

func main() {
	input := []int{2, 4, 6}
	result := double(input)
	fmt.Println(result) // [4 8 12]
}
```

## Execution checklist

1. `package main` is present.
2. Imports match actual use; no unused imports remain.
3. Types, constructors, functions, and methods have complete signatures.
4. `main()` constructs the required values and dependencies.
5. The target function or method is actually called.
6. Returned values and errors are handled.
7. Expected output is stated or assertions are present.
8. Empty, missing, invalid, or boundary input is exercised.
9. The file runs with `go run file.go` or tests with `go test`.
10. A requirement-change variant is attempted after the first success.

## Success and failure paths

Success path: construction is explicit, the call graph is visible, normal input produces the expected output, and the result is checked. Failure path: code exists only as disconnected types and functions; an interface implementation is never assigned or called; `main()` ignores `err`; or the solution depends on undeclared helpers.

## Production use and trade-offs

Real services usually keep `main()` small: load configuration, create infrastructure clients, construct application services, register handlers, start the process, and handle shutdown. A small composition root makes dependency choices visible. Packing logic into `main()` may feel faster for a tiny exercise, but it makes testing and modification harder.

For interview programs, printed output is acceptable when it proves behavior. For reusable code, prefer table-driven tests. The key is not the mechanism; it is having executable evidence rather than mentally completing missing wiring.

## Common mistakes

- Defining an interface and two structs but never assigning a concrete value to the interface.
- Calling a pointer-receiver implementation with a non-addressable value.
- Ignoring returned `append` results or errors.
- Leaving pseudocode, omitted helpers, or unused imports.
- Testing only the happy path.

## Interview questions

1. What belongs in `main()` and what should stay outside it?
2. How do you prove an interface-based example is correctly wired?
3. What is the smallest useful failure-path check for this program?

## Active-recall drill

Open a blank file and build a runnable program containing one struct, one constructor, one method, one interface, two implementations, and one handled error. Run it, then change one method signature and repair every call site.

## Related notes

- [[Complete Small Executable Programs - Drill]]
- [[Correct Interface Invocation from Main - Drill]]
- [[Complete Go Programs - Quick Revision]]

