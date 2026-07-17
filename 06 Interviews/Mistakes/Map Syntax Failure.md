---
type: mistake
domain: go
topic: maps
status: implementation-needed
next_review: 2026-07-18
source_conversations:
  - "Golang Implementation Fluency Issues | 2026-07-15 | 6a5778fc-3758-83ee-9998-cba2bb1b0577"
---
# Map Syntax Failure

## Observed failure

Map syntax failed during implementation despite stronger conceptual knowledge.

## Correction pattern

Cold recall must cover `make(map[K]V)`, literals, assignment, comma-ok lookup, `delete`, iteration, `map[K][]V`, and `map[K]map[K2]V`. A nil map can be read but not written; initialize nested maps before their first write.

## Smallest correction drill

Complete [[Map Frequency Counting - Drill]] and [[Nested Maps and Slice Values - Drill]] without reference. Modify the frequency map into grouped positions and print deterministic output by sorting keys.

## Re-test

| Date | Constraint | Result | Exact syntax miss | Next review |
| --- | --- | --- | --- | --- |
| 2026-07-18 | 15 minutes; compile and run | pending | record, do not infer | after attempt |

Related: [[Go Maps]], [[Go Maps - Quick Revision]].
