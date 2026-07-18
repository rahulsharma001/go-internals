---
type: quick-revision
domain: backend-lld
topic: go-interface-design
review_time: under-5-minutes
---

# Go Interface Design — Quick Revision

## Mental Model

Define interfaces at the consumer boundary and keep them as small as the behavior a caller actually needs. Concrete types own implementation detail; constructors may return concrete pointers even when callers depend on an interface. A useful interface represents substitution that tests or production policies need now: a Clock, Store, Sender, or RetryPolicy. Avoid one interface per struct, broad service bags, and getters that merely expose fields. Method names and error contracts matter more than type count. Value versus pointer receiver method sets can change whether T or *T satisfies an interface, so verify the intended assignment at compile time.

## Go / Design Checklist

For machine coding, start with concrete entities and one public API. Add a Clock when deterministic time tests require it, or a callback interface when two real strategies exist. Keep domain errors comparable with errors.Is. Never accept context only to store it in a struct; pass it to blocking operations. Do not return an interface solely to hide a type. In tests, use a tiny fake that records calls and controls results. Explain the dependency direction: policy depends on abstraction, implementation satisfies it implicitly.

## Explain Aloud

In 60–90 seconds: state the contract, name the invariant and owner, describe success and failure flow, identify cancellation/shutdown behavior, give complexity, and make one Decision → Reason → Cost → Alternative trade-off.

## Reconstruction Drill

Close this note. Sketch the public API and ownership diagram from memory, implement the smallest success path, add one boundary/failure test, then run go test and go test -race where concurrent. Record only observed mistakes and schedule the re-test in [[Backend LLD Practice Tracker]].

## Practice Links

[[Go Interfaces]], [[Interface Design in Go]], [[Middleware Chain]], [[Retry Executor]], [[Notification Service]], [[Splitwise Expense Manager]]

