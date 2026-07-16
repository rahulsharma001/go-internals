---
type: sprint-roadmap
domain: interview-preparation
status: active
sprint_start: 2026-07-16
sprint_end: 2026-08-14
active_dashboard: "[[30-Day FAANG Preparation Dashboard]]"
---

# 30-Day Sprint Overview

## Mission

Use one month to turn existing knowledge into interview execution. The sprint is deliberately narrower than the vault: implement Go foundations, transfer selected DSA patterns to Go, rehearse four system designs, verify project/behavioural evidence, then run mocks and applications.

One active dashboard: [[30-Day FAANG Preparation Dashboard]]. One active recovery tracker: [[Week 1 - Go Recovery|Go Recovery Sprint v2]]. The archived spreadsheet is source material, not a second tracker.

## Four phases

| Dates | Phase | Exit proof |
|---|---|---|
| 2026-07-16–2026-07-22 | [[Week 1 - Go Recovery]] | Foundation programs run, change correctly, and survive later hint-free rewrites |
| 2026-07-23–2026-07-29 | [[Week 2 - DSA in Go]] | Timed Go solves across core patterns with explanation, edge cases, and re-attempts |
| 2026-07-30–2026-08-05 | [[Week 3 - System Design and Project Evidence]] | Four design reps, verified project evidence, and behavioural answers under mock conditions |
| 2026-08-06–2026-08-14 | [[Week 4 - Mocks Revision and Applications]] | Mock-derived readiness, weak-topic re-tests, and evidence-gated applications |

Full gate: [[Sprint Exit Criteria]] · Non-urgent work: [[Deferred Backlog]].

## Daily operating model

Target six focused hours, excluding breaks:

1. **Block 1 — 90 min:** timed DSA or Go implementation.
2. **Block 2 — 90 min:** second implementation, re-test, or review.
3. **Block 3 — 90 min:** current-phase deep work.
4. **Block 4 — 60 min:** retrieval, explanation, edge cases, and modification.
5. **Block 5 — 30 min:** mistake log, dashboard update, applications when scheduled, and next-day plan.

Week 1 and Week 2 use four primary tasks per day. Week 3 uses three. Week 4 uses two larger mock/application cycles. No day exceeds four primary tasks or two new concepts, and every day contains implementation or active recall.

## Status contract

Use only:

- `not-started`
- `attempting`
- `needs-fix`
- `re-test-due`
- `interview-ready`
- `blocked`
- `deferred`

`interview-ready` is not a synonym for finished. A coding task reaches it only after a correct raw attempt is preserved, tests pass, explanation and complexity are clear, important edge cases pass, a modification succeeds, and a later hint-free rewrite succeeds.

## Task metadata contract

Tracked task lines use Obsidian inline properties:

```text
- [ ] Task [task_id:: G01] [date:: 2026-07-16] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 1] [review:: none] [retest::] [mistake::]
```

The updater validates IDs, dates, weeks, areas, statuses, daily task limits, and daily new-concept limits. Update `status`, `review`, `retest`, `mistake`, and optional `mock_score` only from actual evidence; then run:

```bash
tools/30_day_sprint/update
```

## Attempt and Codex review contract

Put implementations under the matching `practice/30-day-sprint/week-*` directory. Preserve the first raw attempt; fixes go in a later commit/file. For submitted Go code, Codex must run `gofmt -d`, `go test ./...`, and `go vet ./...`; concurrency work also requires `go test -race ./...`. Review correctness, Go fluency, `main()` wiring, edge cases, complexity, explanation, modification, and later rewrite. Record one focused correction drill—never replace a foundational attempt with an advanced rewrite.

## Expansion guardrail

Do not add a new active topic because it is interesting. A new subject enters only when a mock exposes a critical gap and an existing task can be deferred in exchange. Repeated failure causes re-testing before expansion.

