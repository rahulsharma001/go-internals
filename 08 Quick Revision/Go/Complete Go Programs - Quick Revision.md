---
type: quick-revision
domain: go
topic: complete-go-programs
canonical: "[[Complete Go Programs]]"
---

# Complete Go Programs - Quick Revision

## Can I run it?

```text
package → imports → types → functions/methods → main → output/error check
```

`main()` is the composition root: select concrete implementations, construct dependencies, invoke the use case, handle errors, and make results observable. Keep business logic outside `main()`.

## Checklist

- `package main` and `func main()` exist.
- Imports are complete and used.
- Every referenced type/helper is defined.
- Values and dependencies are constructed.
- The target function or interface method is invoked.
- Return values and `error` are handled.
- Expected output or assertions prove behavior.
- One edge/failure case is exercised.
- `go run file.go` or `go test` succeeds.
- One requirement-change variant is attempted.

## Common mistake

The code defines an interface and implementations but never assigns a concrete value to the interface or calls it from `main()`. Other frequent failures are unused imports, hidden pseudocode helpers, ignored errors, and an `append` result that is discarded.

## Production example

A service `main()` loads config, creates clients/repositories/services, registers handlers, starts the process, and owns lifecycle errors. The same principle scales down to a 30-line interview program.

## 30-second answer

A complete Go example is a closed executable loop, not a snippet. `main` wires concrete dependencies and invokes the behavior; logic stays in testable functions. I prove the happy path and one failure or edge case, run the code, then modify a requirement to show the wiring is understood.

## Recall challenge

Create a runnable file with a struct, constructor, method, interface, two implementations, and handled error—without looking at another note.

Canonical: [[Complete Go Programs]] · Drill: [[Complete Small Executable Programs - Drill]]

Index: [[Quick Revision Index]]
