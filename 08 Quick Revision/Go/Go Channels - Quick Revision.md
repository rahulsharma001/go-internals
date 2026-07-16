---
type: quick-revision
domain: go
topic: channels
canonical: "[[Go Channels]]"
---

# Go Channels - Quick Revision

## 30-second definition and mental model

Channels communicate values and synchronize goroutines. Unbuffered is a handoff; buffered is a bounded queue that absorbs bursts but eventually applies backpressure.

```go
ch := make(chan int, 4)
ch <- 1
value, ok := <-ch
close(ch)
```

Five facts: nil channels block; closed receives drain then return zero/false; send to closed panics; sender normally owns close; capacity does not fix sustained overload.

Common trap: closing a channel from the receiver.

Interview answer: “I choose capacity from burst and service-rate reasoning, make ownership explicit, and provide cancellation for every potentially blocking operation.”

Production example: a bounded job queue limits memory and exposes queue-depth/wait-time signals.

Active recall: build producer → workers → closer; then make the consumer exit early and repair the leak.

Canonical: [[Go Channels]] · Related: [[Select in Go]], [[Worker Pool]]

Index: [[Quick Revision Index]]
