# T16 Buffered vs Unbuffered Channels — Interview Questions

> Comprehensive Q&A for [[T16 Buffered vs Unbuffered Channels]].
> Sorted rough frequency for senior Go interviews.

---

## Q1: What is the difference between buffered and unbuffered channels? [COMMON]

**Answer:** Both use an `hchan`. **Unbuffered** has `dataqsiz == 0` and `buf == nil` — send blocks until a receive is ready and vice versa (rendezvous). **Buffered** has `dataqsiz == k` — values sit in a ring buffer; send blocks only when `qcount == k`, receive blocks only when empty (until closed and drained).

---

## Q2: When would you choose unbuffered? [COMMON]

**Answer:** When you want **explicit synchronization** — the sender shouldn’t proceed until someone takes the value, or you want a strict **signal handoff**. Examples: **`done`** channel signaling completion, pairwise coordination, guarding ordering stories.

---

## Q3: When would you choose buffered? [COMMON]

**Answer:** When you need **bounded slack** — producer spikes, worker pools with a job queue, **semaphore limiting concurrency**, absorbing short bursts **without coupling every send to an immediate receive**. Always pair with metrics because buffers hide consumer lag until they fill.

---

## Q4: Does `make(chan int)` allocate a buffer? [COMMON]

**Answer:** It allocates an `hchan`, but **`dataqsiz` is 0** — no ring buffer array. Default capacity is **zero**, not one.

---

## Q5: How do you implement a semaphore with channels? [COMMON]

**Answer:** `sem := make(chan struct{}, N)` — **acquire** with `sem <- struct{}{}` (blocks when N holders haven’t released), **release** with `<-sem` in `defer`. Leak releases on panic paths causes permanent capacity loss.

---

## Q6: Can a buffered channel deadlock where unbuffered would not? [TRICK]

**Answer:** Patterns differ — deadlock is pairing logic, not “buffered safer.” Classic: **wrong order** launching receiver vs sender hurts both. Buffered helps only when backlog fits in capacity.

---

## Q7: What does `cap(ch)` tell you? [COMMON]

**Answer:** **`dataqsiz`** — maximum slots in buffer. **Does not** report current backlog (no built-in live `len` for channels).

---

## Q8: Is a larger channel always faster? [COMMON]

**Answer:** No — large buffers consume **memory**, add **scheduling wakeups**, and **delay** back-pressure signals. Micro-benchmarks sometimes favor tiny buffers or mutexes for hot counters.

---

## Q9: How does close interact with buffered data? [COMMON]

**Answer:** Receivers **drain** remaining buffer first. After `qcount == 0` and `closed == 1`, receives return zero value and `ok == false` without blocking. Sends always panic after close.

---

## Q10: Channel vs mutex for a shared map? [COMMON]

**Answer:** Protect the map with **mutex** (or `sync.Map` in specific cases). Channels move **ownership** or **stage work**; they’re the wrong default for arbitrary shared map mutation.

---

## Q11: What’s wrong with an enormous buffer “so we never block”? [COMMON]

**Answer:** You still block when full; you increase **memory**, hide **consumer death**, and push **tail latency** risk to the moment the buffer saturates.

---

## Q12: Explain back-pressure with channels. [ADVANCED]

**Answer:** A finite buffer **is** back-pressure — producers slow when it fills. For cross-service load, you often need **external queues** or **explicit reject** policies (HTTP 503, `select` default) rather than an unbounded goroutine fan-out.

---

> See [[T16 Buffered vs Unbuffered Channels]] Section 6 for active recall drills.
