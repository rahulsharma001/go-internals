---
type: coding-drill
domain: go
topic: interface-main-invocation
status: not-attempted
canonical: "[[Go Method Sets]]"
---

# Correct Interface Invocation from Main - Drill

## Problem

Define `Runner` with `Run() string`. Implement it on `*Job` with a pointer receiver that increments a run counter. Write `execute(Runner)` and wire a `Job` correctly from `main()`.

Before compiling, explain why `job.Run()` can work while `execute(job)` does not.

## Constraints and edge cases

- Add `var _ Runner = (*Job)(nil)`.
- Invoke twice and prove state changes.
- Keep `execute` unaware of `Job`.
- Include the invalid value assignment as a comment, not broken active code.

## Modification challenge

Change `Run` to a value receiver. Predict interface satisfaction and state behavior separately; they are different questions.

## Attempt record

| Date | Time | Result | Hints | Failure category |
|---|---:|---|---|---|
| | | not attempted | | |

## Re-test history

| Date | Variant | Result | Remaining mistake |
|---|---|---|---|
| | pointer / value receiver | | |

<details>
<summary>Reference solution — reveal only after an attempt</summary>

```go
package main

import "fmt"

type Runner interface {
	Run() string
}

type Job struct {
	runs int
}

func (j *Job) Run() string {
	j.runs++
	return fmt.Sprintf("run %d", j.runs)
}

var _ Runner = (*Job)(nil)

func execute(runner Runner) {
	fmt.Println(runner.Run())
}

func main() {
	job := Job{}
	job.Run()    // direct call can take &job; result intentionally ignored
	// execute(job) // Job lacks the pointer-receiver method in its method set
	execute(&job)
	fmt.Println("total:", job.runs)
}
```

</details>

Related: [[Go Method Sets]] · [[Go Interfaces]] · [[Complete Go Programs]]

