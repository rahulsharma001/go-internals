# 30-Day FAANG Sprint Audit Plan

> Created: 2026-07-16  
> Scope: focused interview-preparation operating system for 2026-07-16 through 2026-08-14  
> Change rule: preserve sources, activate one dashboard and one Go recovery tracker, and make no readiness claim without dated execution evidence.

## Source ledger

| Source group | Evidence found | Planned treatment |
|---|---|---|
| `AGENTS.md` and `MIGRATION_PLAN.md` | Canonical-note, preservation, implementation-gate, and staged-change rules | Enforce throughout; do not expand technical canonicals during this sprint build |
| Migration reports | Stage 1 created 12 foundation canonicals, 12 revisions, and 10 drills; cleanup increased the active drill set to 13 | Reuse active canonicals and drills; do not duplicate their explanations |
| Current Go recovery notes | `Current Week`, the Stage 1 gate, Engineering Dashboard, and a historical Day 1 plan | Preserve but mark overlapping active surfaces inactive/superseded and point them to the new dashboard |
| Recovery spreadsheet | 51 tasks dated 2026-07-16–2026-07-22; all `Not Started`; no attempt result, rewrite, confidence, blocker, notes, or mistake entry | Move the unmodified workbook to `99 Archive/External Trackers`; create a readable disposition ledger; merge to 28 active Week 1 tasks |
| Coding drills | 13 prompt-first drills; every attempt table is empty and status is `not-attempted` | Link from Sprint v2; preserve raw future attempts in `practice/30-day-sprint` |
| DSA notes | No problem attempts, pattern canonicals, timed mocks, or mistakes exist | Select a small Week 2 problem set; create attempt records only when work is performed |
| Mistake notes | No Go, DSA, or interview mistake record exists | Keep reported blockers separate from observed mistake evidence; let future failures create notes |
| Google roadmap | Long-term evidence dashboard with no attempts or mock scores | Preserve as long-term reference; make it inactive during this sprint |
| System design | One interview framework plus MongoDB and Go-local reliability material; no full system reps | Schedule four interview exercises without creating an encyclopedia |
| Project evidence | Named project folders are empty; behavioural compilation contains unverified claims | Create claim-free evidence-intake shells for the four user-named projects; keep readiness blocked until verified |

## Change set

1. Archive the original spreadsheet unchanged and add a source/disposition note.
2. Create the requested 30-day roadmap files with no more than four primary tasks on any date.
3. Make `Week 1 - Go Recovery.md` the only active seven-day recovery tracker, with exactly 28 high-value tasks.
4. Create one active dashboard and mark overlapping dashboards/current-focus trackers inactive without deleting them.
5. Create four practice-week directories with attempt-preservation and review rules.
6. Create a small idempotent updater that reads inline task properties, validates metadata, and rewrites only marked dashboard sections.
7. Validate dates, task counts, daily limits, status vocabulary, links, archive preservation, updater idempotence, and readiness invariants.

## Explicit non-changes

- Do not rewrite Go canonicals or reveal new solutions.
- Do not claim historical Java problem completion.
- Do not convert the unverified behavioural compilation into project facts.
- Do not activate advanced runtime internals, advanced generics, or a lifetime curriculum.
- Do not create completion, mock, application, or interview history.

## Acceptance evidence

- Original workbook checksum and Git blob remain recoverable.
- Exactly one note has `type: sprint-dashboard` and `status: active`.
- Exactly one note has `type: go-recovery-tracker` and `status: active`.
- Week 1 has 25–30 tasks and every date has at most four primary tasks.
- All new tasks use only the approved status vocabulary and begin `not-started` unless explicitly deferred.
- Running `tools/30_day_sprint/update` twice produces no second dashboard change.
- Invalid sample metadata is rejected without rewriting the dashboard.

