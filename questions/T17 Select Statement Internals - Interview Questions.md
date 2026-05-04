# T17 Select Statement Internals — Interview Questions

> Comprehensive interview Q&A bank for [[T17 Select Statement Internals]].
> Sorted by frequency at top companies. Tags: `[COMMON]` `[ADVANCED]` `[TRICKY]`

---

## Q1: What happens when multiple `select` cases are ready at once? [COMMON]

**Answer:**

**In one line:** The runtime **randomly permutes case order** (`pollorder`), locks channels safely, then picks the **first ready case** in that shuffled walk — **not** “first branch in source.”

**Visualize it:**
```
Source cases:   [work] [cancel]

pollorder A:    cancel, work   → if BOTH ready, cancel checked first this round
pollorder B:    work, cancel     → work might win same instant different shuffle

Winner = first ready along THAT pollorder — uniform among simultaneous readiness.
```

**Key facts:**
- Fairness targets **inspection order**, not throughput quotas.
- **Pass 1** completes immediately when first readiness hits.
- Combined with locks sorted by **`hchan` address** — deadlock-safe.

**Interview tip:** They want **pseudo-random fairness** + awareness **source order is not priority**.

> [!example]- Full Story: Multiple readiness
>
> **The problem:** Without randomization, always scanning source order starves later cases.
>
> **How it works:** `cheaprandn` builds random permutation; locked scan walks permuted indices until success.
>
> **What to watch out for:** Need strict priority? **`select` alone is wrong tool**.

---

## Q2: Why does the runtime sort channel locks by address in `select`? [COMMON]

**Answer:**

**In one line:** **Total lock ordering** — every goroutine grabs **`hchan.lock`** in **increasing channel pointer order**, preventing classic **AB/BA deadlock**.

**Visualize it:**
```
Goroutine X:   locks chA(0x100) then chB(0x200)
Goroutine Y:   locks chB(0x200) then chA(0x100)   ← dangerous pattern

select fixes Y order → always 0x100 before 0x200 — cycle impossible.
```

**Key facts:**
- **`sellock`** walks **`lockorder`** sorted ascending.
- **`selunlock`** reverses walk.
- Same technique as transferring multiple mutexes safely.

**Interview tip:** Tests whether you connect **`select` internals** to **lock discipline**.

> [!example]- Full Story: Lock inversion
>
> **The problem:** Two goroutines; overlapping channels; opposite acquisition orders ⇒ deadlock.
>
> **How it works:** Heap-sort cases by channel identity — canonical global order.
>
> **What to watch out for:** Mixing manual mutex + channel locks elsewhere — still need discipline outside `select`.

---

## Q3: What does `default` actually do inside `runtime.selectgo`? [COMMON]

**Answer:**

**In one line:** It compiles to **`block=false`** — after pass 1 finds nothing ready, **`selectgo` unlocks all channels and returns `-1`** without enqueueing waiters.

**Visualize it:**
```
pass1: nothing ready?
  block=true  → pass2 sudogs + gopark (sleep)
  block=false → selunlock + return default index
```

**Key facts:**
- **No `sudog`** allocation when default wins without waiting.
- Enables **non-blocking** channel ops pattern.
- Misuse ⇒ **busy spin** if loop body never blocks elsewhere.

**Interview tip:** Distinguish **`default`** from **timeout** (`time.After` allocates unless handled carefully).

> [!example]- Full Story: Non-blocking send
>
> **The problem:** Try enqueue without stalling producer when queue saturated.
>
> **How it works:** `select { case ch<-x: default: backoff }`.
>
> **What to watch out for:** Hot loops — add sleep/backpressure.

---

## Q4: Explain `scase` and what lives on the stack during `select`. [ADVANCED]

**Answer:**

**In one line:** Each arm becomes **`scase{c, elem}`** — channel pointer + unsafe pointer to send payload / recv destination scratch — arrays **`cas`**, **`pollorder`**, **`lockorder`** allocated **on the goroutine stack**.

**Visualize it:**
```
stack frame:
  scase[0]: c→hchan jobs, elem→&payload
  scase[1]: c→hchan done, elem→nil or &recvslot
  pollorder[], lockorder[]
```

**Key facts:**
- **`elem`** carries address for typed copy (`typedmemmove`).
- **`ncases ≤ 65536`** guard in runtime.
- Compiler + runtime must agree on layout (`scasetype`).

**Interview tip:** Shows you read **`runtime/select.go`** structure literally.

> [!example]- Full Story: Compiler lowering
>
> **The problem:** High-level `select` must become concrete runtime call.
>
> **How it works:** Compiler emits **`selectgo`** with counts of sends vs recvs for indexing rules.
>
> **What to watch out for:** Tiny selects rewritten to simpler constructs — large nilled-out selects still hit general path.

---

## Q5: How are nil channel cases handled? [COMMON]

**Answer:**

**In one line:** **`c == nil` cases are skipped** — they never appear in `pollorder`; behave like **receive/send forever blocked** unless **`default`** exists.

**Visualize it:**
```
cases: recv nilAlerts, recv heartbeat
              ↑ dropped              ↑ participates

only heartbeat path remains
```

**Key facts:**
- Used intentionally to **disable** branches (`ch = nil`).
- **All nil + no default** ⇒ **deadlock** (empty effective select).

**Interview tip:** Classic **feature-flag channel** pattern vs bug.

> [!example]- Full Story: Nil as off-switch
>
> **The problem:** Stop reading from one input after close without leaving select.
>
> **How it works:** On close `ok==false`, set handle `nil`.
>
> **What to watch out for:** Hidden **`default` spin** when channel uninitialized.

---

## Q6: What is `selectgo` pass 2 / pass 3 in plain language? [ADVANCED]

**Answer:**

**In one line:** **Pass 2** queues **`sudog`** on **every** participating channel and **`gopark`** once; **pass 3** after wakeup **removes loser sudogs** so you do not leak waiters.

**Visualize it:**
```
pass2:  GP.waiting → sudog₁ → sudog₂ → sudog₃   (isSelect=true)
wake:   winner marks gp.param → winning sudog
pass3:  dequeue self from every OTHER channel queue
```

**Key facts:**
- Single goroutine — **not** per-case threads.
- **`selparkcommit`** interacts with stack shrinking safety.

**Interview tip:** Shows understanding **`sudog`** lifetime beyond single-channel ops.

> [!example]- Full Story: Why cleanup matters
>
> **The problem:** Without dequeuing losers, silent buildup on idle channels.
>
> **How it works:** Walk **`lockorder`** matching winner vs **`gp.waiting`** chain.
>
> **What to watch out for:** Rare runtime bugs historically — trust current implementation cleans queues.

---

## Q7: Does `select` guarantee balanced consumption from two busy channels? [TRICKY]

**Answer:**

**In one line:** **No** — random inspection gives **fair chance each invocation**, not equal **long-run counts** if producers differ.

**Visualize it:**
```
High-rate chan A vs idle chan B — A wins readiness almost always.
Random order rarely saves you from physics.
```

**Key facts:**
- Fair among **simultaneous readiness**.
- Throughput skew needs **application-level metering**.

**Interview tip:** Nuanced statistical vs algorithmic fairness.

> [!example]- Full Story: Producer imbalance
>
> **The problem:** Metrics show branch B rarely runs — not necessarily `select` bug.
>
> **How it works:** Only ready cases compete.
>
> **What to watch out for:** Measure **readiness**, not fairness assumptions.

---

## Q8: What does `select {}` compile to? [TRICKY]

**Answer:**

**In one line:** Blocks forever — **`runtime.block()` → `gopark`** with **no wake condition**.

**Visualize it:**
```
select with 0 cases → permanent sleep (until whole process stops)
```

**Key facts:**
- Distinct from **all-nil channel cases** — similar symptom, different construction.

**Interview tip:** Edge trivia — shows careful reading of spec/runtime.

> [!example]- Full Story: Empty select
>
> **The problem:** Accidentally generated zero-case select in codegen experiments.
>
> **How it works:** Immediate park forever.
>
> **What to watch out for:** Dead goroutines in dumps.

---

## Q9: How does receive from a closed channel interact with `select` readiness? [COMMON]

**Answer:**

**In one line:** **Receive from closed empty channel is always ready** — yields zero value + **`recvOK=false`** immediately.

**Visualize it:**
```
closed && drained buffer → recv ready each time (zero value stream)
```

**Key facts:**
- Competes with other ready branches via randomized walk.
- Send on closed **panics** if selected — still “ready” for wrong reasons.

**Interview tip:** Pair with **channel close semantics** from [[T15 Channel Internals]].

> [!example]- Full Story: Shutdown broadcast
>
> **The problem:** Signal termination alongside work loop.
>
> **How it works:** Close `done` — receives become ready.
>
> **What to watch out for:** Mixing **send** on closed still catastrophic.

---

## Q10: Performance-wise, when does a large `select` hurt? [COMMON]

**Answer:**

**In one line:** Each execution **heap-sorts lock order** + **locks `O(n)` channels** — hurts tail latency when **`n` explodes** (generated fan-in anti-pattern).

**Visualize it:**
```
n cases → sort + loop cost grows linearly
Hot path handler + huge n → selectgo shows in profiles
```

**Key facts:**
- Prefer **aggregator goroutine** / **fewer channels**.
- Profile **`runtime.selectgo`** + **`sellock`**.

**Interview tip:** Bridge primitives knowledge to **service architecture**.

> [!example]- Full Story: Sidecar explosion
>
> **The problem:** Thousands of upstream subscriptions modeled as distinct channel arms.
>
> **How it works:** Collapse events into **shared queue** or shard workers.
>
> **What to watch out for:** Macro micro benchmarks hide coordination costs.

---

## Q11: Can you rely on case order for “cancel supersedes work”? [TRICKY]

**Answer:**

**In one line:** **No** — if **both** `ctx.Done()` and `jobs` ready same instant, **either** may run first.

**Visualize it:**
```
both ready → pollorder decides — not textual case ordering
```

**Key facts:**
- Use **separate goroutine** draining cancel exclusively, or **nonblocking** status checks after batching, or **priority structures** outside naive `select`.

**Interview tip:** Tests whether candidate knows **`select` non-priority semantics**.

> [!example]- Full Story: Shutdown races
>
> **The problem:** Process extra job after cancellation observed logically.
>
> **How it works:** Cancellation and job both became ready — job branch won randomized sweep.
>
> **What to watch out for:** Idempotent handlers + post-select cancel checks.

---

## Q12: Single-case `select` with `default` vs bare channel op — difference? [ADVANCED]

**Answer:**

**In one line:** Semantically similar for try-send/recv — compiler often lowers simpler patterns; still conceptual **`selectgo`** path with **`block=false`**.

**Visualize it:**
```
single case + default  ⇐⇒  try op semantics (implementation may optimize)
```

**Key facts:**
- Compiler may rewrite tiny selects.
- Read **`walk/select.go`** for transformations.

**Interview tip:** Shows awareness **compile pipeline optimizes** common shapes.

> [!example]- Full Story: Optimization reality
>
> **The problem:** Micro-benchmark differences noise level.
>
> **How it works:** Treat them **behaviorally same** unless profiling proves edge.
>
> **What to watch out for:** Premature worry — clarity beats nanoseconds.

---

> Full notes → [[T17 Select Statement Internals]]
