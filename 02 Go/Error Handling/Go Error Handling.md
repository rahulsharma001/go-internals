---
type: canonical
domain: go
topic: go-error-handling
status: implementation-needed
aliases:
  - T09 Error Handling Patterns
source_notes:
  - "[[99 Archive/Superseded Originals/root/T09 Error Handling Patterns]]"
  - "[[99 Archive/Superseded Originals/prerequisites/P05 Interfaces Basics]]"
  - "[[99 Archive/Superseded Originals/simplified/T09 Error Handling Patterns - Simplified]]"
  - "[[99 Archive/Superseded Originals/revision/T09 Error Handling Patterns - Revision]]"
---

# Go Error Handling

## Problem and mental model

An error is a returned value describing why an operation could not complete. The success path should stay direct; each caller checks failure, adds useful abstraction context, or translates the error at a boundary.

Wrapping with `%w` preserves the underlying error chain. Use `errors.Is` to ask whether a chain represents a target error and `errors.As` to extract a particular error type. String matching and equality after wrapping are fragile.

## Core choices

- Sentinel error: a stable condition callers may test with `errors.Is`.
- Custom error type: structured fields callers may extract with `errors.As`.
- Wrapped error: adds operation context while preserving the cause.
- Plain error: sufficient when callers only need a message and no classification.

Do not expose internal infrastructure errors directly across an API boundary. Translate them to a domain or transport response at the edge. Distributed retry policy is a later system-design concern; this note only preserves error classification needed by Go code.

## Minimum executable example

```go
package main

import (
	"errors"
	"fmt"
)

var ErrNotFound = errors.New("user not found")

type Repository struct {
	users map[int]string
}

func (r Repository) Find(id int) (string, error) {
	name, ok := r.users[id]
	if !ok {
		return "", ErrNotFound
	}
	return name, nil
}

type Service struct {
	repo Repository
}

func (s Service) Greeting(id int) (string, error) {
	name, err := s.repo.Find(id)
	if err != nil {
		return "", fmt.Errorf("load greeting user %d: %w", id, err)
	}
	return "Hello, " + name, nil
}

func main() {
	service := Service{repo: Repository{users: map[int]string{7: "Rahul"}}}

	message, err := service.Greeting(7)
	fmt.Println(message, err)

	_, err = service.Greeting(99)
	if errors.Is(err, ErrNotFound) {
		fmt.Println("not found")
	} else if err != nil {
		fmt.Println("internal error")
	}
}
```

## Dry run

ID `7` returns a name and nil error. ID `99` returns the sentinel; the service adds operation and ID context with `%w`. `errors.Is` walks the chain and still recognizes `ErrNotFound`, allowing the outer boundary to choose a stable response without parsing the message.

## Custom error example

```go
type ValidationError struct {
	Field string
}

func (e *ValidationError) Error() string {
	return "invalid " + e.Field
}

var validation *ValidationError
if errors.As(err, &validation) {
	fmt.Println(validation.Field)
}
```

Pass a pointer to a variable of the target type to `errors.As`. If an error type has pointer-receiver methods, return its pointer form consistently.

## Boundary policy

Repository: return a meaningful domain condition or wrap infrastructure failure with operation context. Service: add use-case context without duplicating the same phrase. Handler/CLI edge: map known errors to a stable response and log unexpected failures once with request context. Avoid logging the same error at every layer.

Return untyped `nil` for success. A typed nil pointer returned through `error` creates a non-nil interface; [[Go Interfaces]] owns the full explanation.

## Production use and trade-offs

Wrapping improves diagnosis and retains machine-readable identity, but excessive context makes messages noisy. Sentinels provide simple classification but can expand a public API. Custom types carry structured context but couple callers to a type. Decide which facts callers truly need.

Success path: normal output is used only when `err == nil`, context is added once per abstraction boundary, and the edge classifies with `Is` or `As`. Failure path: `%v` destroys the chain, `==` misses a wrapped sentinel, secrets appear in returned messages, or every layer logs the same event.

## Common mistakes

- Ignoring `err` and using a partial result.
- Wrapping with `%v` when the chain must be preserved.
- Comparing wrapped errors with `==`.
- Matching `err.Error()` text.
- Returning typed nil through `error`.
- Mapping transport status inside the repository.
- Logging and returning at every layer.

## Interview questions

1. When do you use `errors.Is` versus `errors.As`?
2. What does `%w` preserve that `%v` does not?
3. Where should repository errors become HTTP or CLI responses?
4. How can a returned `error` be non-nil when its concrete pointer is nil?

## Active-recall drill

Build repository → service → boundary functions with a sentinel, a custom validation error, one `%w` wrap, and complete success/failure invocation from `main()`. Then replace `%w` with `%v`, observe classification failure, and repair it.

## Related notes

- [[Go Interfaces]]
- [[Complete Go Programs]]
- [[Go Error Handling - Quick Revision]]
- [[Complete Small Executable Programs - Drill]]

