---
type: rubric
domain: system-design
status: active
---
# System Design Evaluation Rubric

Use the 100-point implementation in [[System Design Mock Rubric]]. This note explains interviewer signals.

| Dimension | Weak signal | Senior signal | Staff-leaning signal |
| --- | --- | --- | --- |
| scope | feature dump | bounded journey/non-goals | reframes ambiguity and priority |
| estimation | absent/false precision | units, peak, consequence | skew/amplification and cost sensitivity |
| invariants | “consistent data” | testable invariant and owner | narrows strong consistency deliberately |
| API/data | vague boxes | concrete commands, keys, indexes | evolution, lifecycle, deletion, conflicts |
| HLD | logo soup | incremental, labelled critical flow | clear control/data and sync/async boundaries |
| deep dive | shallow breadth | one branch with alternatives | concurrency/failure/operability depth |
| scale | “horizontal” | first bottleneck and partition unit | skew, rebalancing, saturation, economics |
| reliability | retries/DLQ | unknown outcomes and recovery | overload, reconciliation, DR/failback |
| security | “JWT/TLS” | resource auth, privacy, abuse | trust boundaries and operational controls |
| trade-offs | generic pros/cons | decision with cost/alternative | switch condition and reversibility |
| communication | monologue | signposting and time control | collaborates, adapts, synthesizes |

## Red flags

No source of truth, two uncontrolled writers, success before durable commit, unbounded queue/buffer, retry without identity/deadline, cache without invalidation, sharding without key, multi-region without authority, external provider exactly-once claim, or unsupported private-company facts.

## Interview-ready threshold

The note is not the candidate. Personal `interview-ready` requires a 45-minute score of at least 80, no dimension below the rubric’s strong threshold, one successful follow-up, and a later hint-free reconstruction. Record evidence in [[System Design Practice Tracker]].

## Feedback format

1. Strongest decision and why.
2. Highest-risk gap with exact quote/diagram point.
3. Smallest correction drill.
4. One adversarial re-test and date.

Related: [[System Design Mock Rubric]] · [[Common Mistakes and Re-test Queue]].

