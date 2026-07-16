---
type: coding-drill
domain: go
topic: go-interfaces
status: not-attempted
canonical: "[[Go Interfaces]]"
---

# Interfaces with Two Implementations - Drill

## Problem

Define a consumer interface `Notifier` with `Notify(message string) string`. Implement it with `EmailNotifier` and `SMSNotifier`. Write `sendAlert(Notifier, string)` and invoke both implementations from `main()`.

Add compile-time assertions for both implementations.

## Constraints and edge cases

- The implementations must produce observably different strings.
- The consumer accepts the interface; constructors are not required for empty implementations.
- Do not use `any` or type switches.
- `main()` must call through the interface-typed parameter, not call implementation methods only.

## Modification challenge

Make `SMSNotifier.Notify` a pointer receiver and repair its assertion and `main()` call. Then add a recording fake without changing `sendAlert`.

## Attempt record

| Date | Time | Result | Hints | Failure category |
|---|---:|---|---|---|
| | | not attempted | | |

## Re-test history

| Date | Variant | Result | Remaining mistake |
|---|---|---|---|
| | value / pointer implementation | | |

<details>
<summary>Reference solution — reveal only after an attempt</summary>

```go
package main

import "fmt"

type Notifier interface {
	Notify(string) string
}

type EmailNotifier struct{}

func (EmailNotifier) Notify(message string) string {
	return "email: " + message
}

type SMSNotifier struct{}

func (SMSNotifier) Notify(message string) string {
	return "sms: " + message
}

var _ Notifier = EmailNotifier{}
var _ Notifier = SMSNotifier{}

func sendAlert(notifier Notifier, message string) {
	fmt.Println(notifier.Notify(message))
}

func main() {
	sendAlert(EmailNotifier{}, "deploy complete")
	sendAlert(SMSNotifier{}, "deploy complete")
}
```

</details>

Related: [[Go Interfaces]] · [[Interface Design in Go]]

