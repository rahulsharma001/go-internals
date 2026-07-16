---
type: quick-revision
domain: go
topic: select
canonical: "[[Select in Go]]"
---

# Select in Go - Quick Revision

## 30-second definition and mental model

`select` chooses one ready channel operation. If none is ready it waits, unless `default` exists. A nil channel disables a case; a closed receive stays ready.

Five facts: selection is not deterministic round-robin; default can busy-spin; check `ok` for closure; select does not cancel losing work; context cancellation is just another ready channel case.

Common trap: reading endless zero values from a closed input.

Production example: a service loop handles input, shutdown, and timer events without a separate goroutine for each signal.

Interview answer: “I use select to make all blocking exits visible and nil out drained inputs in multiplexing loops.”

Active recall: merge two inputs until both close, then add cancellation.

Canonical: [[Select in Go]] · Related: [[Go Channels]]

Index: [[Quick Revision Index]]
