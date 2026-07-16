---
type: coding-drill
domain: go
topic: complete-go-programs
status: not-attempted
canonical: "[[Complete Go Programs]]"
---

# Complete Small Executable Programs - Drill

## Problem

From a blank file, build a complete repository → service → `main()` program:

- `Repository` stores names in a map and returns sentinel `ErrNotFound`;
- `Service` depends on a consumer interface with `Find(int) (string, error)`;
- `Greeting` wraps repository failure with `%w`;
- `main()` wires the concrete repository, invokes success and failure, and classifies failure with `errors.Is`.

## Completion contract

The file must include package, imports, sentinel, interface, concrete type, constructor or literal wiring, methods/functions, complete `main()`, expected output, and handled errors. No pseudocode or undeclared helper is allowed.

Expected output:

```text
Hello, Rahul
not found
```

## Modification challenge

Add a second repository implementation without changing `Service`. Then add a custom validation error and map it separately in `main()`.

## Attempt record

| Date | Time | Result | Hints | Failure category |
|---|---:|---|---|---|
| | | not attempted | | |

## Re-test history

| Date | Variant | Result | Remaining mistake |
|---|---|---|---|
| | second implementation / validation | | |

<details>
<summary>Reference solution — reveal only after an attempt</summary>

```go
package main

import (
	"errors"
	"fmt"
)

var ErrNotFound = errors.New("not found")

type UserFinder interface {
	Find(int) (string, error)
}

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
	users UserFinder
}

func NewService(users UserFinder) *Service {
	return &Service{users: users}
}

func (s *Service) Greeting(id int) (string, error) {
	name, err := s.users.Find(id)
	if err != nil {
		return "", fmt.Errorf("greeting for %d: %w", id, err)
	}
	return "Hello, " + name, nil
}

func main() {
	repo := Repository{users: map[int]string{7: "Rahul"}}
	service := NewService(repo)

	message, err := service.Greeting(7)
	if err != nil {
		fmt.Println("unexpected:", err)
	} else {
		fmt.Println(message)
	}

	_, err = service.Greeting(99)
	if errors.Is(err, ErrNotFound) {
		fmt.Println("not found")
	} else if err != nil {
		fmt.Println("unexpected:", err)
	}
}
```

</details>

Related: [[Complete Go Programs]] · [[Go Error Handling]] · [[Go Interfaces]]

