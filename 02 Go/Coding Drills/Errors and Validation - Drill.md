---
type: coding-drill
domain: go
topic: errors-validation
status: not-attempted
canonical: "[[Go Error Handling]]"
---

# Errors and Validation - Drill

## Problem

Implement `Register(name string, age int) (User, error)`. Empty names return a sentinel `ErrNameRequired`. Ages outside 18–120 return a custom `ValidationError` containing field and reason. Wrap errors in a service function while preserving `errors.Is`/`errors.As` behavior.

Expected cases: valid input returns a user; empty name matches `ErrNameRequired`; age 17 can be extracted as `*ValidationError` after wrapping.

## Starter signatures and constraints

```go
func Register(name string, age int) (User, error)
func CreateUser(name string, age int) (User, error)
```

- Use `%w` exactly where the caller must inspect the cause.
- Return the zero `User` on failure.
- Do not log inside both functions.
- Provide complete `main()` usage for success and both failures.

## Edge cases and checklist

- Whitespace-only name; ages 18 and 120; unexpected wrapped error.
- `ValidationError.Error()` has a pointer or value receiver chosen deliberately.
- `errors.Is` handles the sentinel; `errors.As` handles the custom type.
- The user-facing boundary does not leak internal details accidentally.

## Modification challenge

Add a repository `ErrConflict`, map each error to an HTTP-like status in a separate boundary function, and keep retryability separate from status mapping.

## Attempt record and re-test history

| Date | Time | Result | Hints | Failure category |
|---|---:|---|---|---|
| | | not attempted | | |

| Re-test date | Variant | Result | Remaining mistake |
|---|---|---|---|
| | conflict / boundary mapping | | |

Related: [[Go Error Handling]] · [[Complete Go Programs]]

Index: [[Coding Drill Index]]

