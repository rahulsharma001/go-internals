---
type: quick-revision
domain: go
topic: go-interface-design
canonical: "[[Interface Design in Go]]"
---

# Interface Design in Go - Quick Revision

## Default design

Start concrete. Add an interface where a real consumer needs substitution or isolation. Define it near that consumer and include only the methods the consumer calls.

```go
type UserFinder interface {
	FindName(int) (string, bool)
}

func NewService(users UserFinder) *Service { ... }
```

“Accept interfaces, return structs” means behavior-using parameters can be narrow contracts while constructors normally return useful concrete types. It is a guideline, not a ban on public producer-owned interfaces.

## Composition

Keep `Reader` and `Writer` separate when consumers need only one. Compose them into `ReadWriter` only for consumers needing both. One concrete type can satisfy all three without declarations.

## Common mistake

Interface pollution: a producer-owned `Repository` exposes many unrelated methods, every fake implements all of them, and adding one method breaks unrelated consumers. Another mistake is creating `IService` for a single concrete service only to imitate class-based design.

## Production example

A billing use case depends on one `Charge` method. `main` passes the real gateway; tests pass a recording fake. The interface is owned by billing, not copied from the vendor SDK.

## 30-second answer

I define interfaces around consumer capabilities, keep them small, and add them when a real substitution seam exists. Constructors generally return concrete types for discoverability. Small interfaces reduce coupling and test burden; fat or premature interfaces freeze unstable APIs and spread unrelated dependencies.

## Recall challenge

Given a ten-method repository, design the smallest interface for one handler. Which package owns it, and what happens when the repository adds an unrelated method?

Canonical: [[Interface Design in Go]] · Drill: [[Interfaces with Two Implementations - Drill]]

