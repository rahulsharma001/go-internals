# T14 GMP Scheduler - Interview Questions

> Comprehensive interview Q&A bank for [[T14 GMP Scheduler]].
> Sorted by frequency for senior Go interviews.

---

## Q1: Explain G, M, and P in one minute. [COMMON]

**Answer:**  
G is the goroutine (work).  
M is the OS thread that runs code.  
P is runtime scheduling context with local run queue.  
M needs P to run Go user code.

---

## Q2: Why does Go need P? Why not only G and M? [COMMON]

**Answer:**  
P decouples execution context from thread identity.  
When an M blocks in syscall, P can be detached and attached to another M.  
Without P, syscall blocking would hurt scheduler flexibility and throughput.

---

## Q3: What does `GOMAXPROCS` control? [COMMON]

**Answer:**  
It controls number of Ps, which is the number of parallel Go execution lanes.  
It does not cap goroutine count.

---

## Q4: What happens when a goroutine performs a blocking syscall? [COMMON]

**Answer:**  
Running M may block in kernel. Runtime detaches P and reassigns it to another M.  
Other runnable Gs continue while blocked call waits.

---

## Q5: Local run queue vs global run queue? [COMMON]

**Answer:**  
Local per-P queues reduce contention and improve cache locality.  
Global queue provides fairness and overflow fallback.

---

## Q6: What is work stealing in GMP? [COMMON]

**Answer:**  
Idle P steals runnable goroutines from busy P.  
This balances load and improves CPU utilization.

---

## Q7: How does preemption affect scheduler fairness? [ADVANCED]

**Answer:**  
Long-running goroutines can be preempted to let others run.  
Modern async preemption reduces starvation and improves tail latency.

---

## Q8: Is P a CPU core? [TRICKY]

**Answer:**  
No. P is runtime scheduling abstraction.  
It often maps in count to logical cores via `GOMAXPROCS`, but it is not hardware itself.

---

## Q9: How would you debug scheduler issues in production? [ADVANCED]

**Answer:**  
Use `GODEBUG=schedtrace=1000,scheddetail=1`, goroutine/block profiles, and `runtime/trace`.  
Look for run queue growth, blocked goroutines, and CPU saturation patterns.

---

## Q10: Can 100k goroutines run with `GOMAXPROCS=4`? [COMMON]

**Answer:**  
Yes. They can exist.  
Only around 4 Go execution lanes run in parallel; others wait/park.

---

## Q11: Why is GMP strong for I/O-heavy services? [COMMON]

**Answer:**  
Waiting goroutines park cheaply, and Ms are reused to run other goroutines.  
This allows high concurrency without one thread per request.

---

## Q12: Give one production anti-pattern tied to scheduler misunderstanding. [TRICKY]

**Answer:**  
Unbounded CPU goroutine fan-out expecting linear speedup.  
Result: huge runnable queues, scheduler overhead, latency spikes.  
Fix: bound concurrency and profile before scaling workers.

---
