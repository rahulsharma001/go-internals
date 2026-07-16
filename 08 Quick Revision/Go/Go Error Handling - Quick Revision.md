---
type: quick-revision
domain: go
topic: go-error-handling
canonical: "[[Go Error Handling]]"
---

# Go Error Handling - Quick Revision

## Mental model

Errors are returned values. Check failure before using the result. Add useful context at abstraction boundaries while preserving machine-readable causes.

```go
value, err := repo.Find(id)
if err != nil {
	return "", fmt.Errorf("find user %d: %w", id, err)
}
```

Use `errors.Is(err, target)` for sentinel/identity classification and `errors.As(err, &target)` to extract a custom error type. `%w` preserves a chain; `%v` only formats text.

## Boundary flow

Repository returns a meaningful condition or contextual infrastructure error. Service adds use-case context. Handler/CLI edge maps known conditions to a stable response and logs unexpected errors once with request context.

Return untyped `nil` on success. A nil concrete pointer returned as `error` is non-nil when the dynamic type remains present.

## Common mistakes

- Ignoring `err` and using the result.
- Comparing a wrapped sentinel with `==`.
- Matching `err.Error()` strings.
- Using `%v` when callers need the chain.
- Logging the same error at every layer.
- Returning typed nil through `error`.
- Translating to HTTP inside the repository.

## Production example

A not-found sentinel is wrapped by the service with operation context. The transport edge recognizes it using `errors.Is` and returns a stable not-found response; unexpected failures are logged once and sanitized.

## 30-second answer

Go errors are values returned explicitly. I check them immediately, wrap with `%w` when adding abstraction context, classify sentinels with `Is`, and extract structured types with `As`. I translate at the outer boundary, avoid duplicate logs, and return true nil on success.

## Recall challenge

Build repo → service → edge flow with a sentinel and custom validation error. Replace `%w` with `%v`; which checks stop working?

Canonical: [[Go Error Handling]] · Drill: [[Complete Small Executable Programs - Drill]]

