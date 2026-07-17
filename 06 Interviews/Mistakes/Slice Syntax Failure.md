---
type: mistake
domain: go
topic: slices
status: implementation-needed
next_review: 2026-07-18
source_conversations:
  - "Golang Implementation Fluency Issues | 2026-07-15 | 6a5778fc-3758-83ee-9998-cba2bb1b0577"
---
# Slice Syntax Failure

## Observed failure

Slice construction or manipulation syntax failed during implementation.

## Correction pattern

Cold recall must include literals, `make([]T, len, cap)`, `append` with assignment, copy, two-index and full-slice expressions, deletion, insertion, and `[][]T`. Predict aliasing before mutating a subslice.

## Smallest correction drill

Complete [[Slice Creation and Modification - Drill]] from an empty file, invoke empty/single/many cases from `main()`, then produce both mutating and non-mutating delete variants.

## Re-test

| Date | Constraint | Result | Exact syntax miss | Next review |
| --- | --- | --- | --- | --- |
| 2026-07-18 | 15 minutes; compile and run | pending | record, do not infer | after attempt |

Related: [[Go Slices]], [[Go Slices - Quick Revision]].
