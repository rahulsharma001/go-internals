---
type: quick-revision
domain: system-design
review_time: 3-minutes
---
# 45-Minute Timeline Cheatsheet

| Time | Deliverable | Say/draw |
| --- | --- | --- |
| 0–3 | shared scope | users, one critical journey, non-goals |
| 3–7 | requirements and targets | functional/NFRs, latency, availability, durability, consistency |
| 7–12 | state and scale | assumptions/calculation, entities, APIs, keys, invariants |
| 12–22 | first working design | client, owner, source of truth, sync/async critical flow |
| 22–32 | selected deep dive | problem, alternatives, selected flow, failure, cost |
| 32–39 | causal scale and recovery | first bottleneck, partition/routing, cache/queue, overload, recovery |
| 39–43 | decisions | explicit trade-offs, rejected option, region/security where relevant |
| 43–45 | senior summary | journey, owner, guarantees, relaxed state, biggest risk |

## Recovery if behind

- At minute 12 with no HLD: freeze scope and draw Version 1.
- At minute 25 with no flow: stop adding boxes and trace one request.
- At minute 35 with no failures: cover timeout, duplicate, partial/region failure.
- At minute 43: summarize; do not introduce a new subsystem.

Canonical detail: [[45-Minute System Design Playbook]].
