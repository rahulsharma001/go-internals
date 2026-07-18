---
type: backend-lld
language: go
category: foundation
priority: P0
company_focus:
  - apple
  - uber
status: not-started
first_attempt_date:
last_attempt_date:
next_review_date:
attempt_count: 0
best_running_code_time_minutes:
tests_passing: false
race_test_passing: false
needs_revisit: true
---

# {{title}}

## Interview Prompt

Write a concise original prompt with an interview-sized contract.

## Why This Problem Matters

- Go skills:
- Backend skills:

## Functional Requirements

## Non-Functional Requirements

Include only relevant constraints: thread safety, latency, bounded memory, graceful shutdown, fairness, idempotency, and extensibility.

## Out of Scope

## Example Usage

```go
// Show the expected public API and a complete invocation.
```

## Core Invariants

## Design

### Entities

### Interfaces

### Data Structures

### Concurrency Ownership

- Map/channel owner:
- Channel closer:
- Concurrent methods:
- Callbacks under locks: never, unless explicitly justified.
- Shutdown behavior:

### ASCII Diagram

```text
caller -> public API -> owned state/worker -> result
```

## Implementation Plan

1. Define contracts and errors.
2. Implement the single-threaded invariant.
3. Add synchronization/lifecycle where required.
4. Add happy-path, boundary, failure, shutdown, and concurrency tests.
5. Run `go test ./...` and, where concurrent, `go test -race ./...`.

## Implementation Workspace

Package files: `README.md`, `types.go`, optional `interfaces.go`, `implementation.go`, `implementation_test.go`, and optional `main.go`.

## Test Plan

- Happy path
- Boundary cases
- Failure cases
- Concurrency tests where applicable
- Shutdown tests where applicable
- Race detector where applicable

## Complexity

## Trade-offs

Decision → Reason → Cost → Alternative

## Senior Follow-Ups

## Mistakes I Made

Record only observed mistakes from an actual attempt.

## Review History

| Date | Attempt | Design min | Running-code min | Tests | Race | Next review |
| --- | ---: | ---: | ---: | --- | --- | --- |

