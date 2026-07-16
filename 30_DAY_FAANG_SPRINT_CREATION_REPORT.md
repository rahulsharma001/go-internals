# 30-Day FAANG Sprint Creation Report

> Created and validated: 2026-07-16  
> Sprint window: 2026-07-16 through 2026-08-14  
> Audit plan: [[30_DAY_FAANG_SPRINT_AUDIT_PLAN]]

## Outcome

The vault now has one focused 30-day execution system, one active dashboard, and one active seven-day Go recovery tracker. It contains 97 tracked tasks across 30 dates: 28 in Week 1, 28 in Week 2, 23 in Week 3, and 18 larger Week 4 mock/application cycles. Every task starts `not-started`; no completion or readiness was inferred.

## Source baseline

Read and used:

- `AGENTS.md`, `MIGRATION_PLAN.md`, both migration reports, and the preceding audit/inventory findings.
- Existing current-focus/recovery surfaces, the historical Day 1 plan, all 13 active Go coding drills, DSA/Mistake/Interview indexes, the two Google roadmap notes, the system-design framework/MOC, application snapshots, and the unverified behavioural compilation.
- All four sheets of the recovery workbook.
- Git history for Go attempts, recovery trackers, DSA attempts, mistakes, and reviews.

Findings: no `.go` attempt files or Codex reviews existed; all coding-drill attempt tables were empty; DSA and mistake folders had no evidence notes; all 51 workbook tasks were `Not Started`, every rewrite flag was `No`, and attempt/result/blocker fields plus the workbook mistake log were empty.

## Old tracker tasks retained

The original workbook is preserved unchanged at [[Go_7_Day_Implementation_Recovery_Tracker.xlsx]]. Its SHA-256 matches the Git checkpoint: `559725e8bf27017620aae377252693326195a3b10dbe446830c21ac61d53d972`.

Of 51 source rows, 43 intents were retained, merged into stronger executable tasks, or moved to the appropriate sprint week. Retained clusters include:

- slice construction/copy/insert/delete/partition and two slice/hash DSA drills;
- map lifecycle/frequency/grouping/nesting plus selected DSA;
- structs, constructors, receivers, store/CRUD, and full service integration;
- two implementations, interface parameter invocation, embedding, and promotion;
- stack/queue basics through selected Week 2 problems;
- one bounded worker-pool/cancellation integration;
- all five Go mock intents, Merge Intervals, Number of Islands, and five-weakest re-testing.

The exact row-by-row mapping is in [[Go 7-Day Implementation Recovery Tracker - Archive Notes]].

## Tasks removed or deferred

No source task was deleted. Eight lower-priority rows were wholly deferred from the active month:

1. Merge two maps.
2. Product of Array Except Self.
3. Longest Consecutive Sequence.
4. Slice of interfaces.
5. Type assertion/type switch.
6. Min Stack.
7. Top K Frequent Elements.
8. Concurrent frequency counter.

Generic/reduce expansion from the filter-map-reduce row was also deferred while its filtering/grouping intent remains in G04. Optional runtime internals, advanced generics, broad standard-library/framework work, exhaustive DSA, and infrastructure encyclopedias are isolated in [[Deferred Backlog]].

## Revised Week 1 tasks

[[Week 1 - Go Recovery|Go Recovery Sprint v2]] contains exactly 28 primary tasks:

| Day | Two Go implementation tasks | DSA in Go | Review/re-test |
|---|---|---|---|
| 1 | Slice ownership; insert/delete/balanced groups | Contains Duplicate | Slice recall and review request |
| 2 | Map lifecycle/frequency; grouping/nested maps | Valid Anagram | Balanced partition re-test |
| 3 | Struct/constructor; pointer/value receivers | Two Sum | Frequency/grouping re-test |
| 4 | Interfaces/main invocation; embedding/promotion | Group Anagrams | Struct/receiver re-test |
| 5 | Errors/boundary mapping; complete program/table tests | Binary Search | Interface/embedding re-test |
| 6 | Map-backed CRUD; bounded cancellation integration | Valid Parentheses | Error/program rewrite and Codex review |
| 7 | Collections mock; service/main mock | Merge Intervals | Five-weakest re-test and gate |

The active tracker links to existing canonicals and drills rather than duplicating their teaching content.

## DSA problems selected

Week 1 uses seven problems to keep daily Go syntax active. Week 2 selects 13 core problems plus one 3Sum re-attempt:

- Arrays/hash maps: Two Sum, Group Anagrams.
- Two pointers: 3Sum, Container With Most Water.
- Sliding window: Longest Substring Without Repeating Characters.
- Stack: Valid Parentheses, Daily Temperatures.
- Binary search: Binary Search.
- Linked lists: Reverse Linked List.
- Trees/queues: Binary Tree Level Order Traversal.
- Heaps: Kth Largest Element.
- Intervals: Merge Intervals.
- Graphs: Number of Islands.

These are practice prompts, not pre-created solution notes. Historical Java completion was not claimed because no attempt evidence exists in the vault.

## System-design exercises selected

[[Week 3 - System Design and Project Evidence]] uses the existing [[System Design Interview Framework]] for four complete designs:

1. Notification delivery system.
2. Uber/ride-hailing system.
3. YouTube-like video platform.
4. Uptime-monitoring system.

Each has a separate failure/scale challenge. Reusable patterns are retrieval prompts selected by requirements; no new pattern encyclopedia was created.

## Project notes linked

Created one evidence-intake canonical for each user-named project:

- [[NCS Permission Versioning]]
- [[CEE Conductor Migration]]
- [[CoMarketer WebSocket Architecture]]
- [[PulseCheck Monitoring System]]

All four are `blocked`, contain no invented facts, and require verification of problem, role, architecture, decisions, failures, impact, improvement, and disclosure boundary before an interview answer is allowed. The behavioural compilation remains an unverified candidate source and was not mapped to a project by assumption.

## Dashboards created or retired

- Created the only active dashboard: [[30-Day FAANG Preparation Dashboard]].
- Marked the old `Engineering Dashboard`, `Current Week`, and Stage 1 gate inactive/superseded while preserving their content.
- Marked the Google roadmap and long-term study plan inactive during this sprint.
- The dashboard expands only the current phase and today’s work; future weeks remain short links.

## Practice and scripts created

Created four practice directories under `practice/30-day-sprint/`, each with raw-attempt preservation and review instructions.

Created executable `tools/30_day_sprint/update`. It:

- scans inline task properties under the sprint roadmap/practice directories;
- validates unique IDs, date/week/status/review fields, readiness evidence, maximum four primary tasks/day, maximum two new concepts/day, and the Week 1 task-count range;
- computes current phase, today’s tasks, review queue, re-tests, repeated mistakes, four readiness areas, mock scores, application pipeline, and next five actions;
- changes only `AUTO` dashboard sections;
- rejects invalid metadata before writing;
- is idempotent.

## Unresolved decisions

1. No implementation attempt exists yet, so the exact current syntax/root-cause blocker remains unobserved.
2. No historical Java attempt list exists; the Week 2 set is high-value and source-informed, not a claim of prior completion.
3. All four project stories need user-provided first-hand evidence; the Week 3 three-project exit gate may remain blocked.
4. Behavioural employers, metrics, scale, ownership, and outcomes remain unverified.
5. Real application companies/roles must be entered from current JDs during the scheduled outreach blocks; time-sensitive roles were not invented.

## Validation results

- Original workbook: archived, unchanged, checksum matched; old Inbox path absent.
- Active recovery trackers: exactly 1.
- Active dashboards: exactly 1.
- Week 1 tasks: 28; all source statuses preserved as no evidence/`not-started`.
- Total: 97 tasks across 30 dates; daily primary-task range 2–4; maximum new concepts/day 2.
- Status vocabulary: 97/97 task statuses valid; 97/97 currently `not-started`.
- Dashboard on 2026-07-16: exactly four primary tasks.
- Updater check: 97 tasks and 30 days valid.
- Idempotence: consecutive updates produced the same dashboard SHA-256.
- Manual dashboard preservation: checksum outside `AUTO` blocks remained identical across Week 1/Week 2 updates.
- Invalid metadata: an isolated invalid-status fixture exited 2 and did not change the fixture dashboard checksum.
- Links: 275 wikilinks across the new and directly affected surfaces scanned; 0 unresolved.
- No completed attempt history was lost because none existed; the untouched workbook remains the authoritative source snapshot.
- No giant Go curriculum, advanced runtime internals, or optional material was activated.

## Recommended first task

Start with **G01 — Slice construction, append, copy, sub-slicing, and alias proof** in [[Week 1 - Go Recovery]]. Work from a blank editor, preserve `attempt-01-raw`, invoke normal and empty cases from `main()`, and do not open the reference solution until the timed attempt is preserved.
