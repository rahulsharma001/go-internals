---
type: learning-guide
domain: system-design
status: active
---
# README - How to Learn System Design

This section trains a repeatable interview skill: derive, communicate, challenge, and revise a design in about 45 minutes. A finished architecture is reference material, not evidence of readiness. The target loop is:

`Scope → critical journey → scale → invariants → APIs/state → ownership → basic design → first bottleneck → scale → failures → consistency/trade-offs → summary`

Start from [[45-Minute System Design Playbook]]. Use [[System Design Dashboard]] to select one system, [[System Design Practice Tracker]] to record evidence, and [[Common Mistakes and Re-test Queue]] only for failures actually observed during practice.

## The eight-question mental loop

1. **Who is using the system?** Name actors, trust boundaries, and the highest-value action.
2. **What is the critical journey?** State one end-to-end success path before listing features.
3. **What state must never be lost?** Identify durable facts and the moment the user may trust success.
4. **What can be eventually consistent?** Separate correctness state from derived views, caches, search, analytics, presence, or counters.
5. **Who owns each piece of state?** Give every authoritative record one writer or explicit conflict rule.
6. **What is the first bottleneck at the stated scale?** Use estimates and skew, not generic “horizontal scaling.”
7. **What happens when each dependency fails?** Trace timeout, unknown outcome, retry, duplicate, recovery, and user-visible state.
8. **Which trade-off am I deliberately making?** Name the chosen option, rejected alternative, cost, containment, and signal.

## Level 1 — Understand

- Read only the classification, requirements, mental model, invariants, and first working design.
- Fold or hide sections 11 onward before reading. Predict the next component and say what requirement forces it.
- For every box ask: “Which state or failure boundary does this own?” Delete boxes that have no answer.
- Walk the critical flow and explain why each synchronous or asynchronous boundary exists.
- Finish by explaining one relaxed guarantee and one strict invariant in plain language.

Exit evidence: a five-minute explanation without reading the final architecture. Reading alone never changes tracker readiness.

## Level 2 — Reconstruct

1. Open [[System Design Blank Interview Template]] or a blank page.
2. Write actors, one critical journey, non-goals, and three non-functional priorities.
3. Derive APIs, entities, state ownership, key schema, and the smallest HLD.
4. Trace one success flow and one partial failure before opening the canonical note.
5. Compare against the canonical design. Record differences as decisions: missing invariant, unnecessary component, unclear owner, wrong partition key, weak recovery, or simply a valid alternative.
6. Schedule a later blank-page redraw; do not overwrite the raw attempt.

Exit evidence: the design works at the initial scale, has a source of truth, and survives one concrete failure.

## Level 3 — Timed interview

- Use exactly 45 minutes and speak aloud. Draw incrementally; never reveal a memorized final diagram.
- Make every assumption explicit and invite correction: “I’ll assume 10M daily writes and a 5× peak only to size the write path.”
- Follow [[45-Minute Timeline Cheatsheet]]. At minute 22, ask which branch the interviewer wants to deepen.
- Keep a visible “parking lot” for optional features so scope does not expand silently.
- Score immediately with [[System Design Mock Rubric]]. Preserve the raw diagram and notes.

Exit evidence: a completed mock, rubric scores, one correction, and a dated re-test.

## Level 4 — Adversarial practice

After a coherent baseline, apply one change at a time:

- traffic or data grows 100×;
- one dependency or an entire region fails;
- a formerly eventual view becomes correctness-critical;
- traffic becomes geographically or tenant-skewed;
- cost becomes a hard constraint;
- multi-region support is added.

Do not redraw from scratch immediately. State which assumption changed, locate the affected invariant/flow, change the fewest components, and name the new downside. This tests transfer rather than memory.

## Level 5 — Revision

Review after **1, 3, 7, and 14 days**:

- redraw the HLD from memory;
- explain one major trade-off;
- answer one failure scenario end to end;
- perform a five-minute verbal summary;
- compare only after the attempt and update the tracker.

A failed review creates the smallest correction in [[Common Mistakes and Re-test Queue]]. It does not create a claim about a personal weakness beyond the observed attempt.

## Practising alone

Use a timer and screen recording or voice memo. Ask candidate questions aloud, then choose plausible interviewer answers and label them assumptions. At minute 22 randomly select one deep dive from the system note. At minute 32 draw a failure card: timeout, duplicate, partial write, hot partition, backlog, or region loss. Score communication as well as architecture.

## Practising with a mock interviewer

Give the interviewer only [[System Design Mock Interviewer Guide]] and the blank-page prompt. Ask them to answer scope questions, choose one deep dive, introduce one adversarial variation, and interrupt vague claims. They should not steer toward the canonical architecture. Link the result to the existing [[Mock Interview Plan]] without modifying that interview tracker.

## Using canonical notes without memorising them

Canonical notes are comparison keys. Read the approach and requirements first; hide the HLD. Reconstruct, then compare ownership, invariants, flows, bottleneck order, and trade-offs. A different technology or topology is valid when its semantics are explicit. Memorising product diagrams is actively harmful because interview constraints change.

## Recognising transferable patterns

Tag the challenge, not the product name:

- duplicate command → [[Idempotency Pattern]] and possibly [[Deduplication and Inbox Pattern]];
- database write plus event → [[Transactional Outbox Pattern]] and [[Change Data Capture]];
- high read reuse → [[Caching Pattern]] plus [[Cache Invalidation and Stampede]];
- producer outruns consumer → [[Backpressure and Load Shedding]];
- per-key ordering → partition ownership in [[Queues Streams and Pub Sub]];
- cross-service workflow → [[Saga Pattern]];
- large audience distribution → [[Fan-out on Write vs Fan-out on Read]].

Use [[System Coverage Matrix]] to choose a second system exercising the same pattern under different constraints.

## Mistake log discipline

Record: date, system, exact quote/diagram error, rubric dimension, consequence, corrected principle, smallest drill, and 1/3/7/14-day result. Never write generic entries such as “bad at scaling.” A useful entry is: “In the 2026-07-20 feed mock, I partitioned inbox rows by post ID, so a home-feed query required fan-out; redraw schema by user ID.”

## Interview-ready gate

A system is `interview-ready` only when all are true:

- one untimed reconstruction and one 45-minute mock are preserved;
- requirements, estimation, API/data, HLD, deep dive, reliability, trade-offs, and communication each score at least 3/4 on the rubric;
- the critical invariant and ownership boundaries are explicit;
- three failure flows have detection, retry/deduplication, recovery, user impact, and signals;
- one adversarial follow-up succeeds;
- a later seven- or fourteen-day reconstruction succeeds without the canonical note;
- no unresolved repeated high-severity mistake remains.

Note completeness is curriculum coverage, not personal readiness.

## Daily use

1. Launch: [[15-Minute Interview Launchpad]].
2. Select a system from [[System Coverage Matrix]].
3. Reconstruct with [[System Design Blank Interview Template]].
4. Score with [[System Design Mock Rubric]].
5. Record in [[System Design Practice Tracker]].
6. Schedule only observed corrections in [[Common Mistakes and Re-test Queue]].

