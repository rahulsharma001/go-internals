---
type: quick-revision
domain: go
topic: defer-panic-recover
canonical: "[[Defer Panic and Recover]]"
---

# Defer, Panic and Recover - Quick Revision

## 30-second definition and mental model

`defer` registers cleanup for function exit and executes registrations LIFO. Panic unwinds the current goroutine and runs defers. A deferred function in that goroutine can recover at a deliberate boundary.

```go
resource, err := acquire()
if err != nil { return err }
defer resource.Close()
```

## Five facts

1. Deferred arguments are evaluated at registration.
2. Deferred closures read captures when they execute.
3. Defers run on return and panic, not `os.Exit`.
4. Recover belongs inside a deferred call during unwinding.
5. Panics do not jump across goroutines for recovery.

Common trap: recovering and silently returning success.

Production example: an HTTP boundary records the panic and stack, emits a metric, and returns a generic 500 only when continuing is safe.

Interview answer: “Errors represent expected failures; panic is exceptional. I recover only at owned boundaries and preserve observability.”

Active recall: predict argument snapshot versus closure capture, then place recovery around a job goroutine.

Canonical: [[Defer Panic and Recover]] · Related: [[Go Error Handling]]

Index: [[Quick Revision Index]]
