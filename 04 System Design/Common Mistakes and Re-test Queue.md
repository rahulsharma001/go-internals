---
type: mistake-log
domain: system-design
status: active
---
# Common Mistakes and Re-test Queue

Record only mistakes observed in an actual reconstruction, mock, or feedback session. A generic risk below is **not** evidence that you personally made it.

## Observed mistake queue

| Date | System/attempt | Exact observed mistake | Why it matters | Correction in your words | Re-test prompt | Due | Result/evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Allowed status here: `open`, `scheduled`, `passed-once`, `closed-after-retest`.

## Diagnostic catalog for mock review

| Signal to look for | Strong correction | Focused re-test |
| --- | --- | --- |
| Scope expands for ten minutes | state one critical journey and explicit non-goals | finish requirements plus NFRs in seven minutes |
| Numbers never affect architecture | calculate the dominant rate/capacity/skew, then name the forced component | explain why a queue/partition/cache is needed from one estimate |
| Diagram starts at Version 3 | draw client → owner service → source of truth first | trace the smallest success path before scaling |
| Source of truth is unclear | label the owner and distinguish derived cache/index/queue | identify authority for every mutable entity |
| “Exactly once” is asserted casually | locate transaction boundary; use idempotency/reconciliation elsewhere | handle crash after effect but before acknowledgement |
| Retry is the only failure answer | add deadline, cap, jitter, retry budget, idempotency, and recovery | downstream times out with an ambiguous outcome |
| “Scale horizontally” replaces analysis | name partition key, router, skew, movement, and hotspot strategy | a celebrity/tenant/region owns 40% of traffic |
| Consistency is discussed abstractly | tie strict or eventual behavior to an invariant and user journey | interviewer makes one read-after-write guarantee stricter |
| Technology choice is brand-driven | state access pattern, guarantee, alternative, operational cost, reversal condition | replace chosen managed service with a relational option |
| Failure path omits the user | include immediate response, retry/recovery, and visible degraded state | one dependency is down for 20 minutes |
| Security is a closing checklist | identify trust boundary and abuse path during requirements/HLD | attacker controls URL, payload, token, or request rate |
| No final summary | restate critical flow, owner, guarantees, trade-offs, and remaining risk | deliver a two-minute summary from a blank page |

## Closure rule

A mistake closes only after a fresh attempt, without viewing the answer, demonstrates the correction. “Read the note again” is not a passing result.

Related: [[System Design Practice Tracker]] · [[System Design Mock Rubric]] · [[README - How to Learn System Design]].
