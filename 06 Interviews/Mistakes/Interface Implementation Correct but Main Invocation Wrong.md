---
type: mistake
domain: go
topic: interfaces
status: implementation-needed
next_review: 2026-07-18
related_mistakes: []
source_conversations:
  - "Golang Implementation Fluency Issues | 2026-07-15 | 6a5778fc-3758-83ee-9998-cba2bb1b0577"
---
# Interface Implementation Correct but Main Invocation Wrong

## Observed failure

The implementation satisfied the interface, but construction and invocation from `main()` were wrong. This is a confirmed implementation gap, not a generic trap; no success is recorded yet.

## Correct pattern

Construct the concrete value, pass it where the consumer interface is required, then invoke the consumer through a complete executable path. Check whether pointer-receiver methods mean `*T`, rather than `T`, satisfies the interface.

## Smallest correction drill

Complete [[Correct Interface Invocation from Main - Drill]] from a blank editor. Run both implementations, then change one receiver from value to pointer and explain the method-set effect.

## Re-test

| Date | Constraint | Result | Next review |
| --- | --- | --- | --- |
| 2026-07-18 | 15 minutes; no reference; complete `main()` | pending | after attempt |

Related: [[Go Interfaces]], [[Go Method Sets]], [[Complete Go Programs]].
