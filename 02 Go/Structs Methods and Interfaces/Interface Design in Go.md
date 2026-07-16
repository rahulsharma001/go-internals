---
type: canonical
domain: go
topic: go-interface-design
status: implementation-needed
aliases:
  - T12 Interface Design Principles
source_notes:
  - "[[99 Archive/Superseded Originals/root/T12 Interface Design Principles]]"
  - "[[99 Archive/Superseded Originals/prerequisites/P05 Interfaces Basics]]"
---

# Interface Design in Go

## Problem and mental model

Interfaces are most useful when they describe what a consumer needs, not everything a producer can do. A small contract lowers coupling, makes substitutions simple, and lets one concrete type satisfy several role-specific interfaces.

Start concrete. Introduce an interface at the point where a real consumer needs alternate behavior, isolation from an external dependency, or a stable capability boundary.

## Core rules

1. Define the interface near the consumer in most application code.
2. Require the smallest behavior that completes the use case.
3. Accept an interface when substitution is useful; normally return a concrete type from constructors.
4. Compose small interfaces when a consumer genuinely needs the combined capability.
5. Do not create an interface merely to imitate class-based design or for a hypothetical second implementation.

Producer-owned interfaces can be correct when the interface itself is the public product boundary, as with many standard-library abstractions. “Consumer-defined” is a default, not an absolute law.

## Minimum executable example

```go
package main

import "fmt"

type UserFinder interface {
	FindName(int) (string, bool)
}

type GreetingService struct {
	users UserFinder
}

func NewGreetingService(users UserFinder) *GreetingService {
	return &GreetingService{users: users}
}

func (s *GreetingService) Greeting(id int) string {
	name, ok := s.users.FindName(id)
	if !ok {
		return "user not found"
	}
	return "Hello, " + name
}

type MemoryUsers map[int]string

func (m MemoryUsers) FindName(id int) (string, bool) {
	name, ok := m[id]
	return name, ok
}

func main() {
	users := MemoryUsers{7: "Rahul"}
	service := NewGreetingService(users)
	fmt.Println(service.Greeting(7))
	fmt.Println(service.Greeting(99))
}
```

## Dry run

`GreetingService` consumes only `FindName`; it does not depend on the rest of a database or SDK. `MemoryUsers` satisfies that role naturally. A SQL-backed type could satisfy the same interface without changing the service. The constructor returns the useful concrete service type.

## Composition

Prefer separate roles such as `Reader` and `Writer`. Combine them only where both are required:

```go
type Reader interface { Read([]byte) (int, error) }
type Writer interface { Write([]byte) (int, error) }
type ReadWriter interface {
	Reader
	Writer
}
```

## Production use and trade-offs

Small interfaces make fakes and adapters cheap. Too many tiny interfaces can obscure a simple design, while a fat interface makes every implementation and test depend on unrelated methods. Returning interfaces from constructors can hide concrete capabilities and complicate evolution; use it only when hiding implementations is part of the actual boundary.

Success path: a consumer depends on exactly what it calls, production and test implementations are wired at the composition root, and concrete types stay discoverable. Failure path: a shared `Repository` interface grows with every method, all fakes break on unrelated changes, or an interface is extracted before behavior stabilizes.

## Common mistakes

- Prefixing every concrete type with a matching `IType` interface.
- Copying an entire client/SDK surface into an application interface.
- Returning an interface only “for testability.”
- Defining a contract in the implementation package when only one consumer needs it.
- Replacing clear typed behavior with `any`.

## Interview questions

1. Why define interfaces where they are consumed?
2. What does “accept interfaces, return structs” optimize for?
3. When is a producer-owned interface appropriate?
4. What are the symptoms of interface pollution?

## Active-recall drill

Take a five-method repository and write a one- or two-method interface for a single consumer. Wire a real and an in-memory implementation from `main()`, then add an unrelated repository method without changing the consumer interface.

## Related notes

- [[Go Interfaces]]
- [[Interfaces with Two Implementations - Drill]]
- [[Correct Interface Invocation from Main - Drill]]
- [[Interface Design in Go - Quick Revision]]

