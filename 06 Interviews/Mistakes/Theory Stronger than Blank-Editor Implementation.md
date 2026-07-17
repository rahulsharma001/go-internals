---
type: mistake
domain: interview-preparation
topic: implementation-fluency
status: implementation-needed
next_review: 2026-07-18
source_conversations:
  - "Golang Implementation Fluency Issues | 2026-07-15 | 6a5778fc-3758-83ee-9998-cba2bb1b0577"
---
# Theory Stronger than Blank-Editor Implementation

## Observed failure

Explanations and solution recognition are stronger than producing a complete working Go program from a blank editor.

## Correction system

Use the lifecycle: prompt → raw timed attempt → compile/run → classify the exact failure → smallest correction → requirement modification → scheduled re-test. Reading or editing a canonical does not update readiness. Every attempt must preserve the raw version and a complete executable invocation.

## Smallest correction drill

Start with [[Complete Small Executable Programs - Drill]]. Use one concept only, normal and failure inputs, and no reference for 20 minutes. Request review only after preserving the raw attempt.

## Re-test

| Date | Constraint | Result | Evidence link | Next review |
| --- | --- | --- | --- | --- |
| 2026-07-18 | one complete program plus one live modification | pending | pending | after attempt |

Related: [[Stage 1 Go Foundation Implementation Gate]], [[30-Day FAANG Preparation Dashboard]].
