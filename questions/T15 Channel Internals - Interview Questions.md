# T15 Channel Internals - Interview Questions

> Comprehensive interview Q&A bank for [[T15 Channel Internals]].
> Sorted by frequency for senior Go interviews.

---

## Q1: How does unbuffered channel send/receive work internally? [COMMON]

**Answer:**  
Unbuffered channel requires sender and receiver rendezvous.  
If one side is missing, current goroutine parks in wait queue.

---

## Q2: What changes internally for buffered channels? [COMMON]

**Answer:**  
Buffered channels add circular buffer fields (`qcount`, `sendx`, `recvx`, `dataqsiz`) and use queue semantics before parking.

---

## Q3: What is the role of `sendq` and `recvq`? [COMMON]

**Answer:**  
They store parked goroutines waiting to send/receive when operation cannot proceed immediately.

---

## Q4: What happens on `close(ch)`? [COMMON]

**Answer:**  
Channel marked closed, receivers can drain remaining buffered values, later receives return zero+`ok=false`, sends panic.

---

## Q5: Why does sending to closed channel panic? [COMMON]

**Answer:**  
Runtime enforces channel safety contract: once closed, no new messages are allowed.

---

## Q6: Why does nil channel block forever? [COMMON]

**Answer:**  
Nil channel has no backing `hchan` state; send/receive has no progress path so goroutine parks forever.

---

## Q7: Is channel always better than mutex? [COMMON]

**Answer:**  
No. Channels are great for communication and coordination. For simple shared mutable counters/maps, mutex/atomic may be simpler and faster.

---

## Q8: Explain ring-buffer indexing in channels. [ADVANCED]

**Answer:**  
Buffered channel uses circular indexing for send/receive pointers (`sendx`, `recvx`) wrapping at capacity to avoid element shifting.

---

## Q9: How can channel bugs cause goroutine leaks? [COMMON]

**Answer:**  
Forgotten close/drain paths or unmatched send/receive can park goroutines forever.

---

## Q10: How do you debug channel deadlocks in production? [ADVANCED]

**Answer:**  
Use goroutine dumps, block profile, and `runtime/trace` to identify parked send/receive call sites.

---

## Q11: Who should close the channel? [COMMON]

**Answer:**  
Typically sender/producer side, because it knows when no more values will be sent.

---

## Q12: What is interview-safe one-line difference: buffered vs unbuffered? [TRICKY]

**Answer:**  
Unbuffered is immediate handshake; buffered is bounded mailbox with delayed handshake.

---
