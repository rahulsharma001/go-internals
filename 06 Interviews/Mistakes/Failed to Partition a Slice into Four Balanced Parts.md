---
type: mistake
domain: go
topic: slices
status: implementation-needed
next_review: 2026-07-18
source_conversations:
  - "Golang Implementation Fluency Issues | 2026-07-15 | 6a5778fc-3758-83ee-9998-cba2bb1b0577"
---
# Failed to Partition a Slice into Four Balanced Parts

## Observed failure

A slice could not be partitioned into four balanced groups under interview conditions.

## Root cause to test

Do not infer whether the cause was syntax, quotient/remainder reasoning, bounds, or pressure. The re-test must record the actual failure category. For `n` items and `k=4`, use `base=n/k`, `extra=n%k`; group `i` receives `base+1` items while `i < extra`. Advance one `start` index and slice `[start:end]`.

## Smallest correction drill

Complete [[Balanced Slice Groups - Drill]] for lengths `0, 1, 3, 4, 5, 10`, then generalize from four groups to `k` and reject invalid `k`.

## Re-test

| Date | Constraint | Result | Actual failure category | Next review |
| --- | --- | --- | --- | --- |
| 2026-07-18 | 20 minutes; no reference; full `main()` | pending | pending observation | after attempt |

Related: [[Go Slices]], [[Collection Transformations in Go]].
