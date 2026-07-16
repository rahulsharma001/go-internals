---
type: coding-drill
domain: go
topic: go-struct-embedding-composition
status: not-attempted
canonical: "[[Struct Embedding and Composition]]"
---

# Struct Embedding and Promoted Methods - Drill

## Problem

Create `ConsoleLogger` with `Log(string)`. Embed it in `Service` and call the promoted method from `main()`. Then add an `AuditLogger` with the same method, embed both in `ReportService`, and resolve the ambiguous call explicitly.

## Constraints and edge cases

- Show both a promoted call and an explicit field-path call.
- Keep the ambiguous short call commented with an explanation.
- Do not describe the relationship as inheritance.
- Invoke every active method from `main()`.

## Modification challenge

Replace both embedded fields with named fields and add one delegating method. Which API better communicates ownership?

## Attempt record

| Date | Time | Result | Hints | Failure category |
|---|---:|---|---|---|
| | | not attempted | | |

## Re-test history

| Date | Variant | Result | Remaining mistake |
|---|---|---|---|
| | embedding / named composition | | |

<details>
<summary>Reference solution — reveal only after an attempt</summary>

```go
package main

import "fmt"

type ConsoleLogger struct{}

func (ConsoleLogger) Log(message string) {
	fmt.Println("console:", message)
}

type AuditLogger struct{}

func (AuditLogger) Log(message string) {
	fmt.Println("audit:", message)
}

type Service struct {
	ConsoleLogger
}

type ReportService struct {
	ConsoleLogger
	AuditLogger
}

func main() {
	service := Service{ConsoleLogger: ConsoleLogger{}}
	service.Log("started")
	service.ConsoleLogger.Log("explicit")

	reports := ReportService{}
	// reports.Log("ambiguous")
	reports.ConsoleLogger.Log("report generated")
	reports.AuditLogger.Log("report generated")
}
```

</details>

Related: [[Struct Embedding and Composition]] · [[Go Method Sets]]

Index: [[Coding Drill Index]]
