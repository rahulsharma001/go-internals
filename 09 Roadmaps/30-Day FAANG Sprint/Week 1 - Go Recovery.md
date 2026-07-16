---
type: go-recovery-tracker
domain: go
status: active
version: 2
sprint_week: 1
start: 2026-07-16
end: 2026-07-22
source_tracker: "[[Go 7-Day Implementation Recovery Tracker - Archive Notes]]"
---

# Go Recovery Sprint v2

## Purpose and rules

Fix the implementation failures named in the sprint request: slice/map syntax under pressure, struct/interface/embedding wiring from `main()`, Java-to-Go DSA translation, and weak later recall. These 28 tasks replace the 51-checkbox spreadsheet as the only active seven-day recovery tracker.

- Two Go implementations, one DSA-in-Go problem, and one review/re-test per day.
- Work from a blank editor before opening linked solutions.
- Reading never changes a status to `interview-ready`.
- Preserve raw code under `practice/30-day-sprint/week-01-go-recovery`.
- If the same failure recurs, schedule its correction drill before any new topic.

## Day 1 — Thu 2026-07-16 — Slices and backing arrays

- [ ] **G01 — Slice construction, append, copy, sub-slicing, and alias proof.** Use [[Slice Creation and Modification - Drill]]; print len/cap and caller/result ownership from a complete `main()`. [task_id:: G01] [date:: 2026-07-16] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **G02 — Insert, delete, and balanced contiguous partitioning.** Implement insert/delete helpers, then [[Balanced Slice Groups - Drill]] including `k <= 0`, empty input, and `k > len`. [task_id:: G02] [date:: 2026-07-16] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **D01 — Contains Duplicate in Go (20-minute cap).** Explain the hash-set pattern, test empty/single/duplicate cases, state O(n) time/O(n) space, and change the return to the first duplicate value. [task_id:: D01] [date:: 2026-07-16] [week:: 1] [area:: dsa] [status:: not-started] [primary:: true] [new_concepts:: 1] [review:: none] [retest::] [mistake::]
- [ ] **R01 — Cold slice recall and review request.** After a break, explain header/backing-array ownership, rewrite the weaker helper without hints, run the review commands, and set `review:: pending` only when raw evidence exists. [task_id:: R01] [date:: 2026-07-16] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]

## Day 2 — Fri 2026-07-17 — Maps and grouping

- [ ] **G03 — Map lifecycle, comma-ok, delete, deterministic output, and frequency counter.** Use [[Map Frequency Counting - Drill]] with nil/empty input and explicit missing-key behavior. [task_id:: G03] [date:: 2026-07-17] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **G04 — `map[string][]T` grouping and nested-map initialization.** Combine [[Grouping and Collection Transformations - Drill]] with [[Nested Maps and Slice Values - Drill]]; print explicit keys and preserve order. [task_id:: G04] [date:: 2026-07-17] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **D02 — Valid Anagram in Go (20-minute cap).** State the byte/rune assumption, test unequal lengths and repeated characters, and modify for Unicode input. [task_id:: D02] [date:: 2026-07-17] [week:: 1] [area:: dsa] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **R02 — Day 1 slice re-test.** Rebuild balanced partitioning from an empty file without links; compare only after the timer and record the exact remaining blocker. [task_id:: R02] [date:: 2026-07-17] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest:: 2026-07-17] [mistake::]

## Day 3 — Sat 2026-07-18 — Structs, constructors, and receivers

- [ ] **G05 — Keyed struct construction and validating constructor.** Use [[Struct Creation and Constructors - Drill]]; invoke valid/invalid construction from `main()` and keep zero-state decisions explicit. [task_id:: G05] [date:: 2026-07-18] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **G06 — Pointer and value receiver behavior.** Use [[Pointer and Value Receivers - Drill]]; predict mutation before running and complete the receiver-conversion modification. [task_id:: G06] [date:: 2026-07-18] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **D03 — Two Sum in Go (20-minute cap).** Use a complement map, manually test duplicates and no-solution behavior, and modify to return an error when absent. [task_id:: D03] [date:: 2026-07-18] [week:: 1] [area:: dsa] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **R03 — Map frequency and grouping re-test.** Rewrite both core functions without hints, then explain zero values, comma-ok, nested initialization, and deterministic output in 90 seconds. [task_id:: R03] [date:: 2026-07-18] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest:: 2026-07-18] [mistake::]

## Day 4 — Sun 2026-07-19 — Interfaces, method sets, and embedding

- [ ] **G07 — Interface with two implementations and correct `main()` invocation.** Complete [[Interfaces with Two Implementations - Drill]] and [[Correct Interface Invocation from Main - Drill]], including the pointer-receiver modification. [task_id:: G07] [date:: 2026-07-19] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **G08 — Embedding, promoted methods, ambiguity, and named composition.** Complete [[Struct Embedding and Promoted Methods - Drill]] with every active method invoked from `main()`. [task_id:: G08] [date:: 2026-07-19] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **D04 — Group Anagrams in Go (35-minute cap).** Use `map[key][]string`, explain the key trade-off, test empty strings, and change the output to deterministic group order. [task_id:: D04] [date:: 2026-07-19] [week:: 1] [area:: dsa] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **R04 — Struct and receiver re-test.** Recreate a constructor plus one mutating and one non-mutating method, invoke all paths, and explain method-set impact without notes. [task_id:: R04] [date:: 2026-07-19] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest:: 2026-07-19] [mistake::]

## Day 5 — Mon 2026-07-20 — Errors, tests, and complete programs

- [ ] **G09 — Sentinel/custom/wrapped errors and boundary mapping.** Complete [[Errors and Validation - Drill]] with success and two failures invoked from `main()`. [task_id:: G09] [date:: 2026-07-20] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **G10 — Complete executable plus table tests.** Use [[Complete Small Executable Programs - Drill]]; add table tests for success, not-found, and validation, then run format/test/vet. [task_id:: G10] [date:: 2026-07-20] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 1] [review:: none] [retest::] [mistake::]
- [ ] **D05 — Binary Search in Go (20-minute cap).** State the invariant, test empty/one/missing/boundaries, and modify to return the first occurrence among duplicates. [task_id:: D05] [date:: 2026-07-20] [week:: 1] [area:: dsa] [status:: not-started] [primary:: true] [new_concepts:: 1] [review:: none] [retest::] [mistake::]
- [ ] **R05 — Interface and embedding re-test.** Write two implementations, pointer/value assertions, promoted and explicit calls, and a complete `main()` in 25 minutes without hints. [task_id:: R05] [date:: 2026-07-20] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest:: 2026-07-20] [mistake::]

## Day 6 — Tue 2026-07-21 — Integrated service and basic concurrency

- [ ] **G11 — Small map-backed CRUD service.** Build constructor, Add/Get/Update/Delete/List, sentinel errors, deterministic list order, complete `main()`, and table tests. [task_id:: G11] [date:: 2026-07-21] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **G12 — One bounded concurrency integration.** Attempt [[Worker Pool with Cancellation - Drill]] only at basic usage depth; preserve raw code and require a clean race test. [task_id:: G12] [date:: 2026-07-21] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 1] [review:: none] [retest::] [mistake::]
- [ ] **D06 — Valid Parentheses in Go (20-minute cap).** Implement a slice-backed stack, test invalid early close and leftovers, and modify to return the first error index. [task_id:: D06] [date:: 2026-07-21] [week:: 1] [area:: dsa] [status:: not-started] [primary:: true] [new_concepts:: 1] [review:: none] [retest::] [mistake::]
- [ ] **R06 — Error/program rewrite and Codex review.** Rewrite the service boundary without hints, run required commands, request review, and create one correction drill only for an observed miss. [task_id:: R06] [date:: 2026-07-21] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest:: 2026-07-21] [mistake::]

## Day 7 — Wed 2026-07-22 — Timed mock and weakness assessment

- [ ] **M01 — 35-minute Go collections mock.** From a blank file: balanced groups plus active-user grouping; include edge cases, complexity, and a changed ordering requirement. [task_id:: M01] [date:: 2026-07-22] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::] [mock_score::]
- [ ] **M02 — 45-minute Go service mock.** Build a map store behind an interface with two implementations, errors, constructor, methods, embedding/composition choice, tests, and complete `main()`. [task_id:: M02] [date:: 2026-07-22] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::] [mock_score::]
- [ ] **D07 — Merge Intervals in Go (40-minute cap).** Sort, merge, test touching/nested/empty cases, state complexity, and modify to avoid mutating caller input. [task_id:: D07] [date:: 2026-07-22] [week:: 1] [area:: dsa] [status:: not-started] [primary:: true] [new_concepts:: 1] [review:: none] [retest::] [mistake::]
- [ ] **R07 — Re-test queue and Week 1 gate.** Rewrite the five weakest functions without hints, update statuses from evidence, schedule exact re-test dates, and name the single implementation blocker for Week 2. [task_id:: R07] [date:: 2026-07-22] [week:: 1] [area:: go] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest:: 2026-07-22] [mistake::]

## Week 1 exit gate

The required outputs are listed in [[Sprint Exit Criteria]]. If any core task remains `needs-fix`, it becomes an early Week 2 re-test and displaces a second problem; it does not create a fifth daily task.

Source canonicals: [[Go Slices]] · [[Go Maps]] · [[Go Structs and Constructors]] · [[Go Methods and Receivers]] · [[Go Interfaces]] · [[Struct Embedding and Composition]] · [[Go Error Handling]] · [[Complete Go Programs]]

