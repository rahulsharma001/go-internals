---
type: mistake
domain: go
topic: embedding-composition
status: implementation-needed
next_review: 2026-07-18
source_conversations:
  - "Golang Implementation Fluency Issues | 2026-07-15 | 6a5778fc-3758-83ee-9998-cba2bb1b0577"
---
# Embedding Correct but Construction or Invocation Wrong

## Observed failure

Embedding syntax was understood, but constructing the outer value or invoking promoted behavior from `main()` failed.

## Correct pattern

Initialize the embedded field explicitly in a keyed outer literal. Distinguish promoted selection (`outer.Method()`) from explicit delegation (`outer.Inner.Method()`) and from overriding via a wrapper method.

## Smallest correction drill

Run [[Struct Embedding and Promoted Methods - Drill]] cold. Add a name collision, resolve it explicitly, then replace embedding with a named field and state the trade-off.

## Re-test

| Date | Constraint | Result | Next review |
| --- | --- | --- | --- |
| 2026-07-18 | 15 minutes; construction plus two calls from `main()` | pending | after attempt |

Related: [[Struct Embedding and Composition]], [[Go Structs and Constructors]].
