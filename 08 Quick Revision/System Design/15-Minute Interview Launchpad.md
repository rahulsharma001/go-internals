---
type: quick-revision
domain: system-design
review_time: 15-minutes
---
# 15-Minute Interview Launchpad

## Minutes 0–3 — reset the reasoning loop

Say aloud:

`user → critical journey → invariant → scale → API/state → owner → working flow → bottleneck → failure → trade-off`

Choose one system from [[System Coverage Matrix]]. Hide its canonical HLD.

## Minutes 3–7 — prepare the page

Write only:

- primary user and one journey
- three functional requirements and three non-functional targets
- two non-goals
- dominant scale assumption and peak multiplier
- strict invariant and relaxed consistency

## Minutes 7–11 — prepare the design spine

- two or three APIs, including authentication and idempotency
- core entities with source-of-truth owner
- Version 1: client → owner service → authoritative store
- critical flow with the commit point marked
- likely first bottleneck

## Minutes 11–15 — prepare for pressure

Pick one of each:

- duplicate or ambiguous outcome
- dependency timeout or overload
- hot key/partition or region failure
- selected trade-off and rejected alternative

Open [[45-Minute Timeline Cheatsheet]], start a timer, speak aloud, and draw incrementally. Afterward score with [[System Design Mock Rubric]]; do not read the canonical answer until the attempt is preserved.
