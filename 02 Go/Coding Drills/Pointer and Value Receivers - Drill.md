---
type: coding-drill
domain: go
topic: go-methods-receivers
status: not-attempted
canonical: "[[Go Methods and Receivers]]"
---

# Pointer and Value Receivers - Drill

## Problem

Create a `Wallet` with an integer `balance`. Implement:

- `Balance() int` with a value receiver;
- `Deposit(amount int) error` with a pointer receiver, rejecting non-positive amounts;
- `WithBonus(amount int) Wallet` with a value receiver that returns a modified copy.

From `main()`, show that `Deposit` changes the original and `WithBonus` does not unless its returned value is assigned.

## Constraints and edge cases

- A failed deposit leaves the balance unchanged.
- Handle the returned error.
- Do not use global state.
- Explain why direct pointer-method call shorthand works on an addressable variable.

## Modification challenge

Change `Deposit` to a value receiver, observe the behavioral failure, and repair it. Then explain the method-set impact of each receiver choice.

## Attempt record

| Date | Time | Result | Hints | Failure category |
|---|---:|---|---|---|
| | | not attempted | | |

## Re-test history

| Date | Variant | Result | Remaining mistake |
|---|---|---|---|
| | receiver conversion | | |

<details>
<summary>Reference solution — reveal only after an attempt</summary>

```go
package main

import (
	"errors"
	"fmt"
)

type Wallet struct {
	balance int
}

func (w Wallet) Balance() int {
	return w.balance
}

func (w *Wallet) Deposit(amount int) error {
	if amount <= 0 {
		return errors.New("deposit must be positive")
	}
	w.balance += amount
	return nil
}

func (w Wallet) WithBonus(amount int) Wallet {
	w.balance += amount
	return w
}

func main() {
	wallet := Wallet{}
	if err := wallet.Deposit(100); err != nil {
		fmt.Println("deposit:", err)
	}
	bonusCopy := wallet.WithBonus(25)
	fmt.Println(wallet.Balance())    // 100
	fmt.Println(bonusCopy.Balance()) // 125
	fmt.Println(wallet.Deposit(0))   // deposit must be positive
}
```

</details>

Related: [[Go Methods and Receivers]] · [[Go Method Sets]]

