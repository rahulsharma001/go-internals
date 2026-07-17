---
type: quick-revision
domain: system-design
review_time: 3-minutes
---
# Requirements Checklist

## Ask

- Who are the primary users and trusted actors?
- What is the single critical journey?
- Which three features are in scope? Which tempting features are not?
- What is average and peak traffic? Read/write mix? object/event size? retention?
- What latency percentile matters?
- What availability and durability are required?
- Which state must be strongly consistent? What may be stale, reordered, or delayed?
- Is the system regional or global? Any residency requirement?
- What is sensitive or abuse-prone?

## Confirm before drawing

- selected scope and non-goals
- labelled interview assumptions
- strict invariant and relaxed guarantees
- likely interviewer deep dive

Do not ask twenty questions. Offer a reasonable assumption, explain why it matters, and let the interviewer redirect. See [[Requirements Clarification Framework]].
