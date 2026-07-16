---
type: sprint-dashboard
domain: interview-preparation
status: active
sprint_start: 2026-07-16
sprint_end: 2026-08-14
source: "[[30-Day Sprint Overview]]"
---

# 30-Day FAANG Preparation Dashboard

> This is the only active dashboard. Update task properties in the weekly notes, then run `tools/30_day_sprint/update`. Text outside `AUTO` markers is preserved.

## Current phase

<!-- AUTO:phase:start -->
**Week 1 — Go implementation recovery (2026-07-16–2026-07-22).** Work from [[Week 1 - Go Recovery|Go Recovery Sprint v2]] and preserve evidence in `practice/30-day-sprint/week-01-go-recovery`.
<!-- AUTO:phase:end -->

Future weeks: [[Week 2 - DSA in Go]] · [[Week 3 - System Design and Project Evidence]] · [[Week 4 - Mocks Revision and Applications]]

## Today’s four tasks

<!-- AUTO:today:start -->
- **G01 — Slice construction, append, copy, sub-slicing, and alias proof.** Use [[Slice Creation and Modification - Drill]]; print len/cap and caller/result ownership from a complete `main()`. _(status: `not-started`)_
- **G02 — Insert, delete, and balanced contiguous partitioning.** Implement insert/delete helpers, then [[Balanced Slice Groups - Drill]] including `k <= 0`, empty input, and `k > len`. _(status: `not-started`)_
- **D01 — Contains Duplicate in Go (20-minute cap).** Explain the hash-set pattern, test empty/single/duplicate cases, state O(n) time/O(n) space, and change the return to the first duplicate value. _(status: `not-started`)_
- **R01 — Cold slice recall and review request.** After a break, explain header/backing-array ownership, rewrite the weaker helper without hints, run the review commands, and set `review:: pending` only when raw evidence exists. _(status: `not-started`)_
<!-- AUTO:today:end -->

## Current implementation blocker

User-reported baseline: slice/map syntax and struct/interface/embedding invocation become unreliable under pressure. The first timed attempts must identify one concrete current blocker; until then this is reported context, not an observed mistake record.

## Tasks awaiting review

<!-- AUTO:reviews:start -->
No task is awaiting review. Set `review:: pending` only after preserving a raw attempt.
<!-- AUTO:reviews:end -->

## Re-test queue

<!-- AUTO:retests:start -->
No re-test is due today.
<!-- AUTO:retests:end -->

## Repeated mistakes

<!-- AUTO:mistakes:start -->
No repeated observed mistake is recorded. The reported baseline remains in **Current implementation blocker** until attempts produce evidence.
<!-- AUTO:mistakes:end -->

## Coding readiness

<!-- AUTO:readiness-coding:start -->
**0/31 evidence gates (0%).** No interview-ready evidence is recorded yet.
<!-- AUTO:readiness-coding:end -->

## Go implementation readiness

<!-- AUTO:readiness-go:start -->
**0/29 evidence gates (0%).** No interview-ready evidence is recorded yet.
<!-- AUTO:readiness-go:end -->

## System-design readiness

<!-- AUTO:readiness-system-design:start -->
**0/14 evidence gates (0%).** No interview-ready evidence is recorded yet.
<!-- AUTO:readiness-system-design:end -->

## Behavioural readiness

<!-- AUTO:readiness-behavioural:start -->
**0/4 evidence gates (0%).** No interview-ready evidence is recorded yet.
<!-- AUTO:readiness-behavioural:end -->

## Current mock scores

<!-- AUTO:mocks:start -->
No mock score is recorded.
<!-- AUTO:mocks:end -->

## Application pipeline

<!-- AUTO:applications:start -->
**Pipeline tasks:** `not-started` 12.
- 2026-07-23 (referral-pipeline) — **W2A01 — Go map syntax review plus referral pipeline seed.** Rebuild set/frequency/grouping snippets in 20 minutes, then record five real referral/recruiter leads with next actions; do not maintain the spreadsheet.
- 2026-07-25 (recruiter-outreach) — **W2A02 — Window/map syntax review plus recruiter outreach.** Recreate last-seen and count-window snippets, then send or prepare evidence-based outreach to the recorded leads.
- 2026-07-28 (referral-follow-up) — **W2A03 — Queue/heap syntax review plus referral follow-up.** Rebuild the minimal Go heap and queue, then update next actions for every active lead.
- 2026-07-30 (secondary-targets) — **W3A01 — Secondary-role shortlist.** Verify five current roles from real JDs, record fit gaps and next action in Obsidian, and exclude roles that would require unverified resume claims.
- 2026-08-03 (secondary-targets) — **W3A02 — Apply to secondary targets.** Submit only role-appropriate, truthful applications; record company, role, source, stage, date, and next action in Obsidian.
<!-- AUTO:applications:end -->

## Next five actions

<!-- AUTO:next-actions:start -->
- **G01 — Slice construction, append, copy, sub-slicing, and alias proof.** Use [[Slice Creation and Modification - Drill]]; print len/cap and caller/result ownership from a complete `main()`. _(status: `not-started`)_
- **G02 — Insert, delete, and balanced contiguous partitioning.** Implement insert/delete helpers, then [[Balanced Slice Groups - Drill]] including `k <= 0`, empty input, and `k > len`. _(status: `not-started`)_
- **D01 — Contains Duplicate in Go (20-minute cap).** Explain the hash-set pattern, test empty/single/duplicate cases, state O(n) time/O(n) space, and change the return to the first duplicate value. _(status: `not-started`)_
- **R01 — Cold slice recall and review request.** After a break, explain header/backing-array ownership, rewrite the weaker helper without hints, run the review commands, and set `review:: pending` only when raw evidence exists. _(status: `not-started`)_
- **G03 — Map lifecycle, comma-ok, delete, deterministic output, and frequency counter.** Use [[Map Frequency Counting - Drill]] with nil/empty input and explicit missing-key behavior. _(status: `not-started`)_
<!-- AUTO:next-actions:end -->

## Deferred topics

Keep advanced Go internals, broad DSA coverage, infrastructure encyclopedias, and optional projects outside the active queue: [[Deferred Backlog]].
