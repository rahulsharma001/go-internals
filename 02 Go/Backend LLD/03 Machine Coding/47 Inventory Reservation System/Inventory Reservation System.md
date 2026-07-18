---
type: backend-lld
language: go
category: machine-coding
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

# Inventory Reservation System

## Interview Prompt

Design and implement an interview-sized Inventory Reservation System in Go. Define a small public API, validate invalid operations, preserve the core invariants, and demonstrate behavior with deterministic tests.

## Why This Problem Matters

- Go skills: atomic state transitions, idempotency, expiry, concurrency.
- Backend skills: API contracts, failure behavior, testability, and production-minded trade-offs.

## Functional Requirements

- Support the minimal operations implied by Inventory Reservation System; make success and failure results explicit.
- Preserve deterministic observable behavior and reject invalid inputs without corrupting state.
- Provide a reconstruction-friendly API that can be implemented and tested within 60–90 minutes.

## Non-Functional Requirements

- Thread-safe public methods with bounded internal state.
- Graceful shutdown or cancellation for blocking work; no callback executes while an internal lock is held.

## Out of Scope

Distributed coordination, external persistence, authentication, multi-region behavior, and production telemetry backends unless the prompt explicitly requires a simulation.

## Example Usage

~~~go
// Expected shape; finalize exact names during the design stage.
component, err := New(/* interview-sized options */)
if err != nil { /* handle invalid configuration */ }
_ = component
~~~

## Core Invariants

- Every accepted operation produces one documented state transition or no state change on error.
- Capacity, ordering, lifecycle, and identity rules remain true across every public method.

## Design

### Entities

Component configuration, owned state, operation input/output, and explicit domain errors.

### Interfaces

Introduce an interface only for a real substitution boundary such as a clock, callback, persistence adapter, or policy.

### Data Structures

Choose from atomic state transitions, idempotency, expiry, concurrency; justify each structure against an invariant rather than familiarity.

### Concurrency Ownership

- Map/channel owner: the implementation owns internal state; each concrete channel owner must be named during implementation.
- Channel closer: only the goroutine or component that creates and sends on a channel may close it.
- Concurrent methods: assume all exported methods may overlap unless the API documents otherwise.
- Callbacks under locks: no.
- Shutdown: reject new work, unblock waiters through context/lifecycle signaling, then wait for owned goroutines.

### ASCII Diagram

~~~text
caller(s) -> validated public API -> owned state / worker -> result or explicit error
                         |-> cancellation / shutdown signal
~~~

## Implementation Plan

1. Lock requirements, exclusions, API, and errors.
2. Implement the single-threaded core invariant.
3. Add synchronization and lifecycle ownership where relevant.
4. Add happy-path, boundary, failure, concurrency, and shutdown tests.
5. Run package tests and the race detector when concurrent.

## Implementation Workspace

- [[02 Go/Backend LLD/03 Machine Coding/47 Inventory Reservation System/README|Package README]]
- [[02 Go/Backend LLD/03 Machine Coding/47 Inventory Reservation System/implementation.go|Implementation]]
- [[02 Go/Backend LLD/03 Machine Coding/47 Inventory Reservation System/implementation_test.go|Tests]]

## Test Plan

- Happy path and representative multi-operation flow
- Empty, full, duplicate, invalid, and boundary cases as applicable
- Failure leaves state unchanged
- Concurrent callers and cancellation/shutdown waiters
- go test -race ./...

## Complexity

State time and space per public operation after choosing the final structures.

## Trade-offs

Decision → smallest explicit API; Reason → interview clarity; Cost → fewer features; Alternative → policy interfaces added only when a follow-up requires them.

## Senior Follow-Ups

- How would bounded memory, fairness, observability, persistence, or partial failure change the ownership model?
- Which contract would you change first for production, and what new failure mode appears?

## Mistakes I Made

Record only mistakes observed during an actual design or implementation attempt.

## Review History

| Date | Attempt | Design min | Running-code min | Tests | Race | Next review |
| --- | ---: | ---: | ---: | --- | --- | --- |

