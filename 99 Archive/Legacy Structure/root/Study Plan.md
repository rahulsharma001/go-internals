> This note has been superseded by [[Engineering Study Plan]] and [[Google Engineering Roadmap]].

# Study Plan — 80/20 Senior Go Track

> **Purpose:** Front-load the small set of topics that account for most senior Go interview signal, then apply while you finish the long tail. This file is the single source of truth for **what "done enough" means** and **what to revise each morning** in [[Daily Revision]].
>
> **Companion files:** [[Roadmap]] (full dependency order + SKIP markers) · [[Daily Revision]] (active recall) · [[INTERVIEW_PREP_STATUS]] · [[Application Targets]] (phased employer examples — verify jobs yourself)

---

## 1. The 80/20 contract (how this plan stays honest)

Senior Go loops rarely reward uniform coverage. Signal clusters into a few areas ([[Roadmap]] "Quick Reference" weights):

| Interview band | Typical weight | Your notes (primary homes) |
|----------------|----------------|----------------------------|
| **Concurrency** (goroutines, scheduler, channels, `select`, mutex, `context`) | ~30–40% | T13–T19, T20–T23, P03, P07, P08 |
| **Memory + GC** (escape ideas, GC behavior, tuning knobs) | ~15–20% | T02, P09, T24, T25 |
| **Interfaces** (nil interface, `iface`/`eface`, design) | ~10–15% | P05, T11, T12 |
| **Errors + control flow** | ~10% | T09, T10, P07 |
| **Core value semantics + DS** (types, pointers, slices, maps, strings) | ~10–15% | T01, T07, T03, T04, T08 |
| **Production bridge** (HTTP/gRPC/DB/observability) | ~15–20% in many loops | T26–T29 |

**Definition used in this plan:** The **80% pack** is *not* "80% of all roadmap topics". It is **the smallest topic set that covers ~80% of what repeats across senior Go interviews**, aligned with the bands above.

**Definition of "done enough" for first-wave applications:** You can **explain trade-offs out loud**, **predict tricky outputs**, and **sketch a correct concurrent design** (shutdown, bounded workers, fan-in) without reading the note.

---

## 2. The 80% pack — explicit topic list (wikilinks)

These are the **high-ROI spine**. Order respects dependencies from [[Roadmap]]; within a wave you may parallelize read-only review, but **do not skip prerequisites** when learning net-new material.

### Wave A — Language core (already strong for you; keep in daily maintenance)

- [[Go Types and Value Semantics]]
- [[T02 Go Memory Allocation & Value Semantics]]
- [[T07 Pointers & Pointer Semantics]]
- [[T03 Strings, Runes & UTF-8 Internals]]
- [[Go Slices]]
- [[Go Maps]]

### Wave B — Errors, closures, defer/panic (high frequency, medium depth)

- [[prerequisites/P07 Functions, Closures & Variable Capture]]
- [[Go Error Handling]]
- [[T10 Defer, Panic & Recover Internals]]

### Wave C — Interfaces (the other big "Go senior" differentiator besides concurrency)

- [[Go Interfaces]]
- [[T11 Interface Internals (iface & eface)]]
- [[Interface Design in Go]]

### Wave D — Concurrency primitives (the largest single band)

Prereqs:

- [[prerequisites/P03 Mutex & Concurrency Safety Basics]]
- [[prerequisites/P08 OS Threads vs Green Threads]]

Core T-notes (do **not** reorder blindly — follow [[Roadmap]] Phase 4):

- [[T13 Goroutine Internals]]
- [[T14 GMP Scheduler]]
- [[T15 Channel Internals]]
- [[T16 Buffered vs Unbuffered Channels]]
- [[T17 Select Statement Internals]]
- [[T18 Mutex & RWMutex Internals]]
- [[T19 Context Package Internals]]

### Wave E — GC depth (pairs with memory band)

- [[prerequisites/P09 GC Basics & Why It Matters]]
- [[T24 Garbage Collector Deep Dive]]
- [[T25 GC Tuning (GOGC & GOMEMLIMIT)]]

### Wave F — Applied concurrency (what coding rounds actually ask you to build)

- [[T20 Worker Pool Pattern]]
- [[T21 Fan-Out / Fan-In Pattern]]
- [[T22 Graceful Shutdown]]
- [[T23 Goroutine Leak Prevention]]

### Wave G — Production bridge (system-design + "real Go" signal)

- [[T26 net/http Internals]]
- [[T27 gRPC with Go]]
- [[T28 database/sql & Connection Pooling]]
- [[T29 Observability (Logging, Metrics, Tracing)]]

**Everything else** in [[Roadmap]] marked SKIP or optional is **intentionally not part of the 80% pack** unless an interview log proves otherwise.

---

## 2.5 DSA Track (Parallel, Daily)

> **DSA is the first filter in many loops — not optional** if you want consistent pass rates on coding rounds.

| Rule | Detail |
|------|--------|
| **Daily time** | **45–60 min** dedicated block — use the **full 60 min** when following the **§5** schedule end-to-end |
| **Pattern progression** | **Week 1:** Arrays, Hashing, Two Pointers · **Week 2:** Sliding Window, Stack, Heap · **Week 3:** Graphs (BFS / DFS) · *(extend with DP / advanced patterns only after Week 3 is stable)* |
| **Each session** | **Max 2 problems** · **~30 min per problem** (timed) · **Re-code** the solution once without peeking (same session or next morning) |
| **Language** | Default **Go**; production-ish style (clear names, edge cases, no globals) |

Log misses in §9 Interview log — weak patterns feed **next week's DSA theme** and optionally [[Daily Revision]] Focus band.

---

## 2.6 Execution layer (Go waves)

**Rule:** *If you are not coding, you are not preparing.*

A wave topic counts as **done** only when you have **both**:

1. **One implementation** — working artifact (`main`, `_test.go`, or tiny service patch).
2. **One failure / debug scenario** — e.g. `go test -race`, intentional bug → fix, trace deadlock or leak, or “what breaks if…” verbal with code proof.

| Wave | Implementation anchor | Failure / debug anchor |
|------|-------------------------|-------------------------|
| **D** (e.g. channels, `select`, mutex, `context`) | Worker pool; `select` + `ctx`; bounded producer/consumer | Race or leak under `-race`; hang with wrong close / missing `Done()` |
| **F** (patterns) | Fan-out/fan-in; graceful shutdown skeleton | Goroutine leak in pprof; shutdown timeout exceeded |
| **G** (HTTP / gRPC / DB / observability) | `http.Server` + `Shutdown`; DB query with `context`; basic metrics hook | Stolen conn / pool exhaustion story; handler panic without recover |

Vault **Interview Mode** implementation task = minimum implementation bar; extend only if time allows. Skim-reading **without** the pair above = **no progress** toward gates (§7).

---

## 2.7 Internals discipline

Deep **runtime** internals (scheduler structs, `hchan` layouts, etc.) are **optional** unless:

- an interview **explicitly** goes there, or  
- you need them to explain **observable behavior** or **debug** (races, GC stalls, scheduling surprises).

Default depth: **behavior → tradeoffs → application**. Prefer traces only where they change how you **code or fix bugs**.

---

## 3. Calendar: aggressive track (≈2 weeks to "80% pack first pass")

Use this when your goal is **start applying soon** and you can sustain **§5** most days (≈**2.5–3 h** including DSA + Go execution layer).

| Day block | Focus | Outcome |
|-----------|------|---------|
| **Days 1–3** | Close Wave B + Wave C gaps **with §2.6 artifacts** | Errors + interfaces + **code + debug reps** |
| **Days 4–10** | Wave D — **implementation + failure scenarios first**; §2.7 keeps theory thin | Concurrency you can **build and fix** under time |
| **Days 11–14** | Wave E (verbal + one GC debug story) + Wave F (**two** of T20–T23) | GC story + **two** live-coding patterns |

**Parallel rule (applications):** Starting **Day 4–7** is reasonable **if** Wave A is already comfortable and you have **T15 + P03 + T18** at least read once (you can explain blocking, close rules, and mutex vs channel trade-offs). Use early applications as **calibration**, not as your only shot at dream companies.

**Honest ceiling:** A *first pass* through the 80% pack in ~2 weeks is viable for strong engineers; *fluency* (mock-level smoothness) usually needs **repetition + mocks** across **another 2–3 weeks**. Treat Week 3–4 as **retrieval + mocks**, not as "learn new theory mountains."

---

## 4. Calendar: balanced track (≈4 weeks to fluency on the 80% pack)

Use this if you want **higher confidence per topic** or you are limited to **~45–60 min/day**.

If using this track, treat **§2.5 DSA** as **≥30 min/day** minimum (even when vault minutes shrink); reduce **Section 4 internals reading**, not builds.

| Week | Focus |
|------|--------|
| **Week 1** | Wave B + Wave C |
| **Week 2** | Wave D (T13–T16) |
| **Week 3** | Wave D (T17–T19) + Wave E |
| **Week 4** | Wave F + start Wave G (HTTP + one of gRPC/DB/observability) |

**Application rule:** Begin **end of Week 2** to **mid Week 3** depending on mock performance.

---

## 5. Daily Execution Model (~2.5–3 hrs)

Designed for **timed coding + execution**, not passive reading. Swap **Verbal** vs **System design** by day (see block 4).

| Block | Time | What |
|-------|------|------|
| **1. Morning** | **20–30 min** | [[Daily Revision]] — Focus band (full blurt) + Maintenance band (5-second / skim). Same split as §6. |
| **2. Deep work** | **60–90 min** | **One** topic from your **current wave** (§2) — **implementation-first**: ship artifact + failure/debug from §2.6 before deep Section 4 reading. Two retrieval drills (predict output / trick) from that note if time remains. One **60–90 s** verbal from Interview Mode or Section 12. |
| **3. DSA** | **60 min** | §2.5 — **2 problems**, **~30 min each**, timed; **re-code** before closing the session. |
| **4. Verbal + System design** | **20–30 min** | **Alternate days:** e.g. Mon/Wed/Fri **verbal** tradeoffs (channels vs mutex, shutdown, errors); Tue/Thu/Sat **15–20 min SD sketch** (API + storage + failure). |

**Optional overflow (≤15 min):** missed timer pressure from earlier blocks — **not** extra theory.

### Weekly requirements (non-negotiable)

| Requirement | Notes |
|-------------|--------|
| **≥2 mock interviews** | Behavioral + technical and/or pure coding — notes ≠ readiness |
| **1× cold build** | **No vault notes** — one **§2.6** implementation + failure scenario (or SD-sized toy) under timer; log gaps to §9 |
| **Weak-area loop** | Mocks + §9 log + DSA misses → **next week's Focus band** (§6) and DSA Week **n** theme |

---

## 6. Weekly Focus / Maintenance bands (copy/paste into [[Daily Revision]] top each Monday)

Template:

```markdown
> **This week's Focus band (full blurt):** T15, T16, T17 (example)
> **This week's Maintenance band (5-sec / skim):** T01, T02, T04, T08 (example)
```

**Rule:** Focus band = whatever you are *actively learning or freshly finished* (usually **Wave D** topics while in that phase). Maintenance band = **Wave A** topics + completed waves.

---

## 7. Application gates (aligned with 80/20, not with "I read everything")

| Gate | Minimum evidence | Where to apply |
|------|------------------|----------------|
| **Gate 0 — Practice employers** | Wave A solid + T09/T10 + can implement `WaitGroup` / mutex fix under time | High-volume, lower-stakes companies, referrals you use for calibration |
| **Gate 1 — Serious loops** | Wave D first pass done + can explain T15/T19 cold + 2 mocks ≥ 3/5 quality | Target employers |
| **Gate 2 — Top of funnel / bar-raising teams** | Wave D fluency + Wave E + most of Wave F + Wave G started + mock streak | Dream employers |

If you apply earlier than Gate 1, do it **deliberately** as data collection — log questions in the Interview Log below.

---

## 8. Checklists — track first-pass completion (edit checkboxes as you go)

### 8.1 Wave B — Errors & control flow

- [ ] [[Go Error Handling]]
- [ ] [[T10 Defer, Panic & Recover Internals]]
- [x] [[prerequisites/P07 Functions, Closures & Variable Capture]]

### 8.2 Wave C — Interfaces

- [ ] [[Go Interfaces]]
- [ ] [[T11 Interface Internals (iface & eface)]]
- [ ] [[Interface Design in Go]]

### 8.3 Wave D — Concurrency primitives

- [x] [[prerequisites/P03 Mutex & Concurrency Safety Basics]]
- [x] [[prerequisites/P08 OS Threads vs Green Threads]]
- [x] [[T13 Goroutine Internals]]
- [x] [[T14 GMP Scheduler]]
- [x] [[T15 Channel Internals]]
- [x] [[T16 Buffered vs Unbuffered Channels]]
- [ ] [[T17 Select Statement Internals]]
- [ ] [[T18 Mutex & RWMutex Internals]]
- [ ] [[T19 Context Package Internals]]

### 8.4 Wave E — GC

- [x] [[prerequisites/P09 GC Basics & Why It Matters]]
- [ ] [[T24 Garbage Collector Deep Dive]]
- [ ] [[T25 GC Tuning (GOGC & GOMEMLIMIT)]]

### 8.5 Wave F — Patterns

- [ ] [[T20 Worker Pool Pattern]]
- [ ] [[T21 Fan-Out / Fan-In Pattern]]
- [ ] [[T22 Graceful Shutdown]]
- [ ] [[T23 Goroutine Leak Prevention]]

### 8.6 Wave G — Production bridge

- [ ] [[T26 net/http Internals]]
- [ ] [[T27 gRPC with Go]]
- [ ] [[T28 database/sql & Connection Pooling]]
- [ ] [[T29 Observability (Logging, Metrics, Tracing)]]

> **Note:** Checkboxes above are **reset to a honest default** (based on files you had marked done in the vault). Fix them to match *your* Obsidian reality — the structure matters more than the default ticks.

---

## 9. Interview log (keep forever — this beats generic research)

| Date | Company | Round | Go topics tested | Self-score (1–3) | Gap to patch |
|------|---------|-------|------------------|------------------|--------------|
| | | | | | |
| | | | | | |

**After every three interviews:** If the same theme appears twice (e.g., `context`, channel close, GC pacing), promote that theme into **next week's Focus band** in [[Daily Revision]] even if it feels "already done."

---

## 10. What we deliberately stopped doing (quality bar)

- **No default deep-dive on runtime internals** — follow §2.7 unless behavior/debug demands it.
- **No high-volume MCQ blocks** as a primary study mode — use **predict-output + verbal gold + mocks**.
- **No equal-time revision** — maintenance stays thin; focus stays thick.
- **No pretending two weeks equals two months of fluency** — parallelize **applications + repetition**, not **applications + brand-new theory mountains**.

---

## 11. Legacy 8-week outline (optional backdrop)

If you prefer a longer horizon, keep using [[Roadmap]] phases as the dependency skeleton. The **80% pack** in §2 is what you must not defer; everything SKIP-marked there stays SKIP unless your interview log contradicts it.

---

**Self-audit (internal):** This plan (a) names the 80% set explicitly, (b) orders waves by interview ROI × dependencies, (c) ties [[Daily Revision]] to Focus/Maintenance bands, (d) separates **first-pass** from **fluency**, (e) gives application gates that do not require finishing the entire vault, (f) makes **DSA + timed execution** non-optional, (g) enforces **§2.6** (code + debug) and **§5** daily structure, (h) keeps **§2.7** from over-investing in theory.
