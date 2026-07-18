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
- **G03 — Map lifecycle, comma-ok, delete, deterministic output, and frequency counter.** Use [[Map Frequency Counting - Drill]] with nil/empty input and explicit missing-key behavior. _(status: `not-started`)_
- **G04 — `map[string][]T` grouping and nested-map initialization.** Combine [[Grouping and Collection Transformations - Drill]] with [[Nested Maps and Slice Values - Drill]]; print explicit keys and preserve order. _(status: `not-started`)_
- **D02 — Valid Anagram in Go (20-minute cap).** State the byte/rune assumption, test unequal lengths and repeated characters, and modify for Unicode input. _(status: `attempting`)_
- **R02 — Day 1 slice re-test.** Rebuild balanced partitioning from an empty file without links; compare only after the timer and record the exact remaining blocker. _(status: `not-started`)_
<!-- AUTO:today:end -->

## Current implementation blocker

User-reported baseline: slice/map syntax and struct/interface/embedding invocation become unreliable under pressure. The first timed attempts must identify one concrete current blocker; until then this is reported context, not an observed mistake record.

## Preparation evidence sync

Last checked 2026-07-17: `/home/rahul/go-interview-prep` contains six Arrays & Hashing implementations with runnable `main()` examples. All six current examples ran and passed `go vet`; three files still need `gofmt`, and the `neetcode/` tree is untracked in its repository. D01–D04 are now `attempting`, while completion and readiness remain gated on durable raw evidence, recorded timing/hints, required edge cases, explanation, modification, and a later re-test. Full intake: [[NeetCode 150 in Go#Preparation sync — 2026-07-17]].

## Tasks awaiting review

<!-- AUTO:reviews:start -->
- **D01 — Contains Duplicate in Go (20-minute cap).** Explain the hash-set pattern, test empty/single/duplicate cases, state O(n) time/O(n) space, and change the return to the first duplicate value. _(status: `attempting`)_
- **D02 — Valid Anagram in Go (20-minute cap).** State the byte/rune assumption, test unequal lengths and repeated characters, and modify for Unicode input. _(status: `attempting`)_
- **D03 — Two Sum in Go (20-minute cap).** Use a complement map, manually test duplicates and no-solution behavior, and modify to return an error when absent. _(status: `attempting`)_
- **D04 — Group Anagrams in Go (35-minute cap).** Use `map[key][]string`, explain the key trade-off, test empty strings, and change the output to deterministic group order. _(status: `attempting`)_
<!-- AUTO:reviews:end -->

## Re-test queue

<!-- AUTO:retests:start -->
- **R02 — Day 1 slice re-test.** Rebuild balanced partitioning from an empty file without links; compare only after the timer and record the exact remaining blocker. _(status: `not-started`)_
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

## Apple / Uber Coding Tracks

This manually maintained section sits outside the sprint automation markers.

| Track | Scope | Running/tested references | Timed-ready | Interview-ready | Reviews due | Tracker |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| DSA in Go | 75 core + 3 extensions | Existing references preserved; completion not inferred | 0 | 0 | 0 scheduled | [[DSA Practice Tracker]] |
| Backend LLD in Go | 50 | 5 enriched; final race validation pending | 0 | 0 | 0 scheduled | [[Backend LLD Practice Tracker]] |

Next: due reviews first; then [[Two Sum]] cold reconstruction; then [[Top K Frequent Elements]]; then [[Thread-Safe Bounded Queue]] from a blank editor; finish the week with one [[DSA Mock Interview Template|timed coding mock]] or [[LLD Machine Coding Mock Template|machine-coding mock]].

Dashboards: [[DSA Dashboard]] · [[Backend LLD Dashboard]] · schedule: [[Apple Uber SDE2 - 75 DSA Plan]].

## Application pipeline

<!-- AUTO:applications:start -->
**Pipeline tasks:** `not-started` 12.
- Next scheduled: 2026-07-23 (referral-pipeline) — **W2A01 — Go map syntax review plus referral pipeline seed.** Rebuild set/frequency/grouping snippets in 20 minutes, then record five real referral/recruiter leads with next actions; do not maintain the spreadsheet.
<!-- AUTO:applications:end -->

## Next five actions

<!-- AUTO:next-actions:start -->
- **R02 — Day 1 slice re-test.** Rebuild balanced partitioning from an empty file without links; compare only after the timer and record the exact remaining blocker. _(status: `not-started`)_
- **D01 — Contains Duplicate in Go (20-minute cap).** Explain the hash-set pattern, test empty/single/duplicate cases, state O(n) time/O(n) space, and change the return to the first duplicate value. _(status: `attempting`)_
- **D02 — Valid Anagram in Go (20-minute cap).** State the byte/rune assumption, test unequal lengths and repeated characters, and modify for Unicode input. _(status: `attempting`)_
- **D03 — Two Sum in Go (20-minute cap).** Use a complement map, manually test duplicates and no-solution behavior, and modify to return an error when absent. _(status: `attempting`)_
- **D04 — Group Anagrams in Go (35-minute cap).** Use `map[key][]string`, explain the key trade-off, test empty strings, and change the output to deterministic group order. _(status: `attempting`)_
<!-- AUTO:next-actions:end -->

## Deferred topics

Keep advanced Go internals, broad DSA coverage, infrastructure encyclopedias, and optional projects outside the active queue: [[Deferred Backlog]].
