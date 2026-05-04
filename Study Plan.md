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

- [[T01 Go Type System & Value Semantics]]
- [[T02 Go Memory Allocation & Value Semantics]]
- [[T07 Pointers & Pointer Semantics]]
- [[T03 Strings, Runes & UTF-8 Internals]]
- [[T04 Arrays & Slice Internals]]
- [[T08 Map Internals]]

### Wave B — Errors, closures, defer/panic (high frequency, medium depth)

- [[prerequisites/P07 Functions, Closures & Variable Capture]]
- [[T09 Error Handling Patterns]]
- [[T10 Defer, Panic & Recover Internals]]

### Wave C — Interfaces (the other big "Go senior" differentiator besides concurrency)

- [[prerequisites/P05 Interfaces Basics]]
- [[T11 Interface Internals (iface & eface)]]
- [[T12 Interface Design Principles]]

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

## 3. Calendar: aggressive track (≈2 weeks to "80% pack first pass")

Use this when your goal is **start applying soon** and you can sustain **~2 h/day deep work** + **20–30 min/day** [[Daily Revision]].

| Day block | Focus | Outcome |
|-----------|------|---------|
| **Days 1–3** | Close Wave B + Wave C gaps (T09, T10, T11, T12; P05/P07 if rusty) | You can answer interface nil traps + error wrapping cold |
| **Days 4–10** | Wave D (T13→T19) as the main job | Concurrency band covered end-to-end once |
| **Days 11–14** | Wave E (P09, T24, T25) + start Wave F (pick **two** of T20–T23 first) | GC story + at least two coding-round patterns solid |

**Parallel rule (applications):** Starting **Day 4–7** is reasonable **if** Wave A is already comfortable and you have **T15 + P03 + T18** at least read once (you can explain blocking, close rules, and mutex vs channel trade-offs). Use early applications as **calibration**, not as your only shot at dream companies.

**Honest ceiling:** A *first pass* through the 80% pack in ~2 weeks is viable for strong engineers; *fluency* (mock-level smoothness) usually needs **repetition + mocks** across **another 2–3 weeks**. Treat Week 3–4 as **retrieval + mocks**, not as "learn new theory."

---

## 4. Calendar: balanced track (≈4 weeks to fluency on the 80% pack)

Use this if you want **higher confidence per topic** or you are limited to **~45–60 min/day**.

| Week | Focus |
|------|--------|
| **Week 1** | Wave B + Wave C |
| **Week 2** | Wave D (T13–T16) |
| **Week 3** | Wave D (T17–T19) + Wave E |
| **Week 4** | Wave F + start Wave G (HTTP + one of gRPC/DB/observability) |

**Application rule:** Begin **end of Week 2** to **mid Week 3** depending on mock performance.

---

## 5. Daily rhythm (must match the 80/20 spine)

### Morning — [[Daily Revision]] (20–30 min)

Split topics into two bands (update the bands weekly — see §6):

1. **Focus band (this week):** Full blurt. No peeking until you have an answer shape.
2. **Maintenance band (everything behind you):** **5-second answer** or skim-only for topics you rate 3/3 confidence.

This is the same 80/20 idea as the roadmap: **most minutes on the few things that are hot in interviews right now**, not equal time on every historical topic.

### Deep work block (45–120 min)

Rotation:

1. **One** net-new section from the current wave (concept-first, then code — your SKILL pattern).
2. **Two** retrieval items from Section 6 of that note: **Predict the output** or **trick question** (not MCQ volume).
3. **One** verbal question (Section 12 / "Interview Gold") answered out loud with a 60–90 s cap.

### Evening (15–20 min)

- One **timed** explanation: pick "channel close rules", "context cancellation", or "nil interface" — rotate.
- If you have energy: **one** small LeetCode medium in Go (implementation, not math trivia) **or** 30 min system-design whiteboard on a service you've shipped.

### Weekly (non-negotiable for interview readiness)

- **≥2 mock sessions** (behavioral + technical or pure technical). Notes-only prep does not simulate pressure.

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

- [ ] [[T09 Error Handling Patterns]]
- [ ] [[T10 Defer, Panic & Recover Internals]]
- [x] [[prerequisites/P07 Functions, Closures & Variable Capture]]

### 8.2 Wave C — Interfaces

- [x] [[prerequisites/P05 Interfaces Basics]]
- [ ] [[T11 Interface Internals (iface & eface)]]
- [ ] [[T12 Interface Design Principles]]

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

- **No high-volume MCQ blocks** as a primary study mode — use **predict-output + verbal gold + mocks**.
- **No equal-time revision** — maintenance stays thin; focus stays thick.
- **No pretending two weeks equals two months of fluency** — parallelize **applications + repetition**, not **applications + brand-new theory mountains**.

---

## 11. Legacy 8-week outline (optional backdrop)

If you prefer a longer horizon, keep using [[Roadmap]] phases as the dependency skeleton. The **80% pack** in §2 is what you must not defer; everything SKIP-marked there stays SKIP unless your interview log contradicts it.

---

**Self-audit (internal):** This plan (a) names the 80% set explicitly, (b) orders waves by interview ROI × dependencies, (c) ties [[Daily Revision]] to Focus/Maintenance bands, (d) separates **first-pass** from **fluency**, and (e) gives application gates that do not require finishing the entire vault.
