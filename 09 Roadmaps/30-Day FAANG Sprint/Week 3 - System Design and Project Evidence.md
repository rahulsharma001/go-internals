---
type: sprint-week
domain: system-design
status: planned
sprint_week: 3
start: 2026-07-30
end: 2026-08-05
---

# Week 3 - System Design and Project Evidence

## Purpose

Turn the existing [[System Design Interview Framework]] and verified first-hand experience into interview performance. This week creates design attempts and evidence; it does not create a distributed-systems encyclopedia.

Every full system exercise must cover: requirements, scale assumptions, entities, APIs, data model, architecture, complete success flow, complete failure flow, bottlenecks, reliability/observability, security, trade-offs, technology choices, and follow-ups. Reusable ideas—cache, partitioning, replication, Kafka/messaging, idempotency, retry, circuit breaker, backpressure, rate limiting, Saga, outbox, CDC—are selected only when the requirements need them.

## Day 15 — Thu 2026-07-30 — Framework and evidence baseline

- [ ] **W3S01 — 40-minute framework-only design outline.** From a blank page, design a generic event-processing service through all required sections, spending the last ten minutes on failure flow and trade-offs. [task_id:: W3S01] [date:: 2026-07-30] [week:: 3] [area:: system-design] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::] [mock_score::]
- [ ] **W3R01 — Reusable decision retrieval.** For cache, partitioning, replication, messaging, idempotency, retry, circuit breaker, backpressure, rate limiting, Saga, outbox, CDC, observability, and security, state the trigger, failure, and trade-off in one sentence each; mark unknowns, do not author canonicals. [task_id:: W3R01] [date:: 2026-07-30] [week:: 3] [area:: system-design] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **W3E01 — Project evidence inventory.** Open the four blocked project notes, locate first-hand artefacts/resume evidence, and fill only claims you can verify; leave every unknown explicit. [task_id:: W3E01] [date:: 2026-07-30] [week:: 3] [area:: project-evidence] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **W3A01 — Secondary-role shortlist.** Verify five current roles from real JDs, record fit gaps and next action in Obsidian, and exclude roles that would require unverified resume claims. [task_id:: W3A01] [date:: 2026-07-30] [week:: 3] [area:: applications] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::] [company:: secondary-targets]

## Day 16 — Fri 2026-07-31 — Notification delivery system and NCS evidence

- [ ] **W3S02 — Design a notification delivery system in 45 minutes.** Cover channel preferences, APIs/events, storage, fan-out, retries, idempotency, rate limits, provider outage, observability, security, and delivery-status trade-offs. [task_id:: W3S02] [date:: 2026-07-31] [week:: 3] [area:: system-design] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::] [mock_score::]
- [ ] **W3F02 — Notification failure-flow challenge.** Trace duplicate event, poison message, consumer lag, and provider outage; choose retry budget, DLQ/reconciliation, and outbox/idempotency boundaries. [task_id:: W3F02] [date:: 2026-07-31] [week:: 3] [area:: system-design] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **W3E02 — Verify [[NCS Permission Versioning]].** Produce a two-minute summary only if problem, role, architecture, decision, failure, impact, and improvement are sourced; otherwise keep it `blocked`. [task_id:: W3E02] [date:: 2026-07-31] [week:: 3] [area:: project-evidence] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]

## Day 17 — Sat 2026-08-01 — Ride-hailing system and CEE evidence

- [ ] **W3S03 — Design Uber/ride hailing in 45 minutes.** Bound scope to rider request, driver location/matching, trip state, and payment handoff; cover geospatial partitioning, hot regions, consistency, and location privacy. [task_id:: W3S03] [date:: 2026-08-01] [week:: 3] [area:: system-design] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::] [mock_score::]
- [ ] **W3F03 — Ride-hailing scale/failure challenge.** Explain stale location, double assignment, regional outage, retry/idempotency, backpressure, rate limiting, and the first bottleneck from estimates. [task_id:: W3F03] [date:: 2026-08-01] [week:: 3] [area:: system-design] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **W3E03 — Verify [[CEE Conductor Migration]].** Record endpoints of the migration, ownership, rollout/rollback, failure handling, trade-offs, impact, and improvement only from evidence. [task_id:: W3E03] [date:: 2026-08-01] [week:: 3] [area:: project-evidence] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]

## Day 18 — Sun 2026-08-02 — Video platform and CoMarketer evidence

- [ ] **W3S04 — Design a YouTube-like video platform in 45 minutes.** Scope upload, transcode, metadata, playback, and popular-content delivery; cover object storage, queues, CDN/cache, partitioning, and access control. [task_id:: W3S04] [date:: 2026-08-02] [week:: 3] [area:: system-design] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::] [mock_score::]
- [ ] **W3F04 — Video success/failure challenge.** Trace upload through playable renditions, then partial upload, failed transcode, hot video, regional CDN failure, retry/reconciliation, and observability. [task_id:: W3F04] [date:: 2026-08-02] [week:: 3] [area:: system-design] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **W3E04 — Verify [[CoMarketer WebSocket Architecture]].** Do not assume the unverified behavioural WebSocket story refers to this project; establish identity, actual architecture, decisions, incidents, and supported impact first. [task_id:: W3E04] [date:: 2026-08-02] [week:: 3] [area:: project-evidence] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]

## Day 19 — Mon 2026-08-03 — Uptime monitoring and PulseCheck evidence

- [ ] **W3S05 — Design an uptime-monitoring system in 45 minutes.** Cover monitor configuration, distributed probes, scheduling, result ingestion, state transitions, alerting, history, multi-region checks, and tenant isolation. [task_id:: W3S05] [date:: 2026-08-03] [week:: 3] [area:: system-design] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::] [mock_score::]
- [ ] **W3F05 — Monitoring failure challenge plus [[PulseCheck Monitoring System]] verification.** Trace probe outage, false alert, queue backlog, duplicate alert, retry/backpressure/circuit breaker, and then fill project facts only where evidence confirms them. [task_id:: W3F05] [date:: 2026-08-03] [week:: 3] [area:: project-evidence] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **W3R05 — Four-system retrieval.** Explain each system’s core invariant, first bottleneck, primary failure, and decisive trade-off without notes. [task_id:: W3R05] [date:: 2026-08-03] [week:: 3] [area:: system-design] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **W3A02 — Apply to secondary targets.** Submit only role-appropriate, truthful applications; record company, role, source, stage, date, and next action in Obsidian. [task_id:: W3A02] [date:: 2026-08-03] [week:: 3] [area:: applications] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::] [company:: secondary-targets]

## Day 20 — Tue 2026-08-04 — Project and behavioural execution

- [ ] **W3T01 — Re-test the weakest system in 40 minutes.** Use a blank page and a changed requirement; compare failure-flow and trade-off quality with the first attempt. [task_id:: W3T01] [date:: 2026-08-04] [week:: 3] [area:: system-design] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest:: 2026-08-04] [mistake::] [mock_score::]
- [ ] **W3E06 — Project-story mock.** Deliver two-minute summaries for every evidence-backed project, then answer architecture, difficult decision, failure, impact, improvement, and follow-ups; do not force three if evidence supports fewer. [task_id:: W3E06] [date:: 2026-08-04] [week:: 3] [area:: project-evidence] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]
- [ ] **W3B01 — Behavioural answer set.** Verify and rehearse “tell me about yourself,” challenging project, one failure, and one disagreement from first-hand facts; flag every unsupported statement in [[Behavioural Interview Compilation - Needs Verification]]. [task_id:: W3B01] [date:: 2026-08-04] [week:: 3] [area:: behavioural] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::]

## Day 21 — Wed 2026-08-05 — Week 3 mocks and gate

- [ ] **W3M01 — Full 45-minute system-design mock.** Record section scores, omissions, root causes, one correction drill, and a re-test date. [task_id:: W3M01] [date:: 2026-08-05] [week:: 3] [area:: system-design] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::] [mock_score::]
- [ ] **W3M02 — Three-project evidence gate.** Demonstrate three verified project stories or explicitly record the evidence blocker; unsupported confidence does not pass. [task_id:: W3M02] [date:: 2026-08-05] [week:: 3] [area:: project-evidence] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::] [mock_score::]
- [ ] **W3M03 — Behavioural mock.** Answer introduction, challenge, failure, and disagreement with follow-ups; record score, root causes, correction drills, and re-test dates. [task_id:: W3M03] [date:: 2026-08-05] [week:: 3] [area:: behavioural] [status:: not-started] [primary:: true] [new_concepts:: 0] [review:: none] [retest::] [mistake::] [mock_score::]

## Week 3 exit gate

Use [[Sprint Exit Criteria]]. Project notes remain `blocked` until actual evidence is entered; creating the shell is not project readiness.

