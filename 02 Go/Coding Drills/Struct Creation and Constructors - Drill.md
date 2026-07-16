---
type: coding-drill
domain: go
topic: go-structs-constructors
status: not-attempted
canonical: "[[Go Structs and Constructors]]"
---

# Struct Creation and Constructors - Drill

## Problem

Define a `Product` with unexported `name` and `priceCents` fields. Write `NewProduct(name string, priceCents int) (*Product, error)` that trims the name, rejects an empty name, and rejects negative price. Add a `Label()` method and invoke valid and invalid creation from `main()`.

## Constraints and edge cases

- Zero price is valid.
- Whitespace-only name is invalid.
- Invalid construction returns `nil` plus an error.
- `main()` must not access unexported fields directly.

## Modification challenge

Add an optional SKU without breaking existing callers. Then decide whether a useful zero-value `Product` would be better and defend the choice.

## Attempt record

| Date | Time | Result | Hints | Failure category |
|---|---:|---|---|---|
| | | not attempted | | |

## Re-test history

| Date | Variant | Result | Remaining mistake |
|---|---|---|---|
| | validation / optional field | | |

<details>
<summary>Reference solution — reveal only after an attempt</summary>

```go
package main

import (
	"errors"
	"fmt"
	"strings"
)

type Product struct {
	name       string
	priceCents int
}

func NewProduct(name string, priceCents int) (*Product, error) {
	name = strings.TrimSpace(name)
	if name == "" {
		return nil, errors.New("name is required")
	}
	if priceCents < 0 {
		return nil, errors.New("price cannot be negative")
	}
	return &Product{name: name, priceCents: priceCents}, nil
}

func (p Product) Label() string {
	return fmt.Sprintf("%s: %d cents", p.name, p.priceCents)
}

func main() {
	product, err := NewProduct("Book", 1299)
	if err != nil {
		fmt.Println("create product:", err)
		return
	}
	fmt.Println(product.Label())

	_, err = NewProduct("   ", -1)
	fmt.Println("invalid:", err)
}
```

</details>

Related: [[Go Structs and Constructors]] · [[Go Error Handling]]

