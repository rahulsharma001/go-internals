---
type: quick-revision
domain: go
topic: context-cancellation
canonical: "[[Context Cancellation]]"
---

# Context Cancellation - Quick Revision

## 30-second definition and mental model

Context carries request-scoped deadline, cancellation, and limited metadata through a call tree. Cancellation is cooperative: each blocking operation must observe it.

Five facts: context is the first parameter; derived cancel functions must be called; children inherit parent cancellation; values are not optional arguments; canceled context does not automatically roll back remote side effects.

Common trap: replacing the incoming context with `context.Background()` in a repository call.

Production example: one request budget propagates through HTTP, service, database, and worker operations; metrics distinguish deadline from other failures.

Interview answer: “I propagate one budget, make sends and I/O cancellation-aware, clean up derived contexts, and design downstream side effects for timeout ambiguity.”

Active recall: add cancellation to a blocked result send.

Canonical: [[Context Cancellation]] · Related: [[Select in Go]]

Index: [[Quick Revision Index]]
