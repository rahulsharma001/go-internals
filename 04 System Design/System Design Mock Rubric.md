---
type: practice-rubric
domain: system-design
status: active
---
# System Design Mock Rubric

Score only what the candidate made visible in 45 minutes. The total is 100. Give one evidence sentence and one next action for every category below 70% of its maximum.

## Scorecard

| Dimension | Points | Strong performance | Common evidence gap |
| --- | ---: | --- | --- |
| Requirements and prioritisation | 12 | clarifies users, critical journey, non-goals, NFR targets, and asks the interviewer to confirm scope | collects a feature list without choosing a critical path |
| Estimation and scale | 10 | labels assumptions, computes average/peak and the dimension that changes architecture, then uses the result | arithmetic is disconnected from design decisions |
| APIs, entities, and data ownership | 12 | shows interview-sized APIs, idempotency/error behavior, concrete keys/indexes, lifecycle, and one source of truth per state | names tables/services without access patterns or owners |
| Incremental HLD and critical flow | 18 | draws a working Version 1, labels sync/async paths and protocols, traces one end-to-end flow, then evolves causally | jumps to a giant diagram or cannot trace a commit |
| Deep dive | 12 | identifies alternatives, selects one under stated constraints, explains detailed state transitions and failure behavior | repeats the HLD at greater word count |
| Reliability, consistency, and recovery | 14 | distinguishes strict/relaxed guarantees; covers timeout, duplicate, partial failure, overload, recovery, and user outcome | says retry/replicate without budgets or reconciliation |
| Trade-offs and technology judgment | 12 | makes explicit decisions, rejected alternatives, weaknesses, and conditions that reverse the choice | gives generic pros/cons or brand-driven choices |
| Communication and interview control | 10 | signposts phases, makes assumptions explicit, checks alignment, responds to hints, and ends with guarantees/risks | silent diagramming, jargon, or no summary |
| **Total** | **100** |  |  |

## Performance bands

| Score | Interpretation | Required next step |
| --- | --- | --- |
| 90–100 | exceptional senior signal; coherent under follow-ups | adversarial variation and spaced re-test |
| 80–89 | strong interview performance with bounded gaps | repair the lowest category, then another mock |
| 70–79 | plausible but inconsistent senior signal | targeted reconstruction and follow-up round |
| 60–69 | incomplete derivation or weak defense | untimed rebuild before another mock |
| below 60 | foundations and critical flow are not yet reliable | return to playbook plus one Tier 1A system |

No total can produce `interview-ready` if any category is below 70% of that category's maximum, no complete success flow was traced, or the candidate asserted an impossible guarantee such as exactly-once external effects without a shared transaction boundary.

## Interviewer evidence sheet

| Phase | Timestamp | What the candidate made visible | Follow-up or hint | Candidate response |
| --- | --- | --- | --- | --- |
| Scope and scale | 0–12 |  |  |  |
| Working HLD and flow | 12–22 |  |  |  |
| Deep dive | 22–32 |  |  |  |
| Scale and failures | 32–39 |  |  |  |
| Trade-offs and summary | 39–45 |  |  |  |

## Feedback format

- **Strongest observable signal:**
- **Highest-risk gap:**
- **One repeated mistake actually observed:**
- **One blank-page re-test:**
- **One adversarial variation:**
- **Re-test date:**

Related: [[45-Minute System Design Playbook]] · [[System Design Evaluation Rubric]] · [[System Design Practice Tracker]].
