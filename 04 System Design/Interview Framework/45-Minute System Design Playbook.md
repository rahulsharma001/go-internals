---
type: canonical
domain: system-design
topic: interview-playbook
status: active
---
# 45-Minute System Design Playbook

The interview is a sequence of decisions, not a race to draw a large architecture. Keep one critical journey visible throughout. At every phase connect requirements to state, ownership, flow, and trade-off.

## 0–3 minutes — Frame the problem

**Think:** Who are the primary actors? What single user journey defines success? Which adjacent features can wait?

**Say:** “I’ll restate the goal, confirm the two or three core actions, and explicitly park recommendations/admin/reporting unless you want them.”

**Draw:** Title, actors, critical journey, and a small in-scope/out-of-scope box—no services yet.

**Ask:** Primary user? Critical action? Existing dependencies? What is explicitly out of scope?

**Signals:** prioritisation, listening, controlled scope, ability to simplify.

**Time-wasters:** reciting every feature, guessing company internals, drawing before agreement.

## 3–7 minutes — Requirements, targets, and scale

**Think:** Functional requirements; latency, availability, durability, consistency, geography, security; which dimension changes the design?

**Say:** “These are interview assumptions, not product facts. I’ll use them to find the first bottleneck.”

**Draw:** requirement table and three calculations: peak QPS/event rate, storage/bandwidth, and concurrency/fan-out if relevant.

**Ask:** peak or average traffic? payload and retention? read/write ratio? acceptable staleness? region failure expectations?

**Signals:** units, order-of-magnitude reasoning, ranked NFRs, no false precision.

**Time-wasters:** ten calculations with no architectural consequence; “highly available” without a target or failure scope.

## 7–12 minutes — Contracts, state, and invariants

**Think:** What facts are durable? Who owns them? Which transitions must be atomic? Which views are derived?

**Say:** “The strict invariant is __. Store __ is authoritative; cache/search/analytics is rebuildable and may lag by __.”

**Draw:** three to five entities, two to four APIs/events, keys/indexes, state machine, and source-of-truth marker.

**Ask:** duplicate-client semantics? ordering scope? pagination? delete/retention? authorization boundary?

**Signals:** concrete schemas, idempotency, ownership, consistency aligned with business correctness.

**Time-wasters:** entity lists without lifecycle, vague JSON, database choice before access paths, shared writable database.

## 12–22 minutes — First working design

**Think:** What is the smallest design that completes the critical journey? Where is the durable commit? Which side effects must be async?

**Say:** Build aloud: “Client calls X over HTTPS. X validates and commits Y. The response means Z. After commit, event A triggers B asynchronously.”

**Draw:** client, edge, named service owners, authoritative stores, caches, queues/streams, workers, external dependencies. Label sync/async and protocol; number the flow.

**Ask:** “Would you like me to validate this end-to-end flow before we choose a deep dive?”

**Signals:** coherent ownership, meaningful arrows, completion semantics, ability to stop at sufficient complexity.

**Time-wasters:** cloud-logo soup, queue without producer/consumer or delivery contract, cache without truth, skipping the flow.

## 22–32 minutes — Interviewer-selected deep dive

**Think:** What invariant or scale bottleneck makes this branch hard? Compare two alternatives before selecting.

**Say:** “The core challenge here is __. Option A optimises __ but costs __; I choose B because our stated priority is __.”

**Draw:** enlarge only the branch: storage/partitioning, matching, feeds, media, transactions, realtime, scheduling, search, or reservation. Add key, owner, and failure boundary.

**Ask:** “Which branch should I deepen?” Then ask one constraint question specific to it.

**Signals:** depth, trade-off reasoning, concurrency/failure awareness, responsive collaboration.

**Time-wasters:** deepening every subsystem, changing requirements silently, defending a technology rather than semantics.

## 32–39 minutes — Scale and failure

**Think:** first bottleneck, skew, cache behavior, async backlog, consistency, and recovery after unknown outcome.

**Say:** “At the assumed peak, __ fails first because __. I introduce __, partition by __, and contain the new risk __ with __.”

**Draw:** version 2 change, partition routing, cache/invalidation, bounded queue/backpressure, replica/failover, and observability points. Trace one failure in red/dashed notation.

**Ask:** expected behavior during overload? stale vs unavailable? duplicate semantics? region scope?

**Signals:** causal scaling, bounded retries, idempotency, graceful degradation, SLO-linked metrics.

**Time-wasters:** “scale horizontally,” infinite queues, retrying all errors, declaring exactly once, ignoring hot keys.

## 39–43 minutes — Deliberate compromises

**Think:** eight major decisions, rejected alternatives, multi-region/DR only if relevant, security/abuse risks.

**Say:** Use: “I choose X because requirement Y needs semantic Z. It costs C; I contain it with M and observe N. A wins instead when condition W holds.”

**Draw:** trade-off annotations, region authority/RPO-RTO if in scope, trust boundaries and rate limits.

**Ask:** “Is there a changed constraint you want me to apply before I summarize?”

**Signals:** explicit judgment, reversibility, cost/operations, security and privacy proportional to risk.

**Time-wasters:** generic pros/cons, multi-region decoration, naming compliance regimes not established by requirements.

## 43–45 minutes — Close strongly

**Think:** Can a listener recover requirements, critical invariant, architecture, main failure, bottleneck, and trade-off in one minute?

**Say:** “The system accepts __, commits __ in __, and completes __ via __. It guarantees __ while allowing __ to lag. It scales by __. The highest residual risks are __ and __; next I would validate __.”

**Draw:** circle the source of truth and critical path; write three guarantees and two risks. Do not add boxes.

**Ask:** none unless the interviewer invites questions.

**Signals:** synthesis, honest uncertainty, ownership of decisions, time management.

**Time-wasters:** reopening scope, adding features, claiming readiness without remaining risks.

## Recovery when behind

- At minute 12 with no design: state one invariant, choose a source of truth, draw the basic request flow.
- At minute 25 with a giant diagram: stop, number the critical path, delete optional components.
- At minute 35 with no failure analysis: pick dependency timeout after possible commit; cover deadline, idempotency, reconciliation, user state, and metric.
- At minute 43: summarize instead of starting multi-region.

Companions: [[Requirements Clarification Framework]] · [[Back-of-the-Envelope Estimation]] · [[System Design Evaluation Rubric]] · [[45-Minute Timeline Cheatsheet]].

