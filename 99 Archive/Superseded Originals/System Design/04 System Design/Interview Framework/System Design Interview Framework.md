> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[45-Minute System Design Playbook]].

---
type: canonical
domain: system-design
topic: interview-framework
status: implementation-needed
source_notes:
  - "[[Day 1 — Interview Preparation Plan]]"
  - "[[Engineering Study Plan]]"
source_conversations:
  - "System Design Practice Tips | 2025-05-04 | 681749e6-1698-8013-bb4c-22bcf122748c"
  - "System Design Prep Hub | 2026-05-30 | 6a1ae0f4-402c-8324-b49e-754f47133b80"
---

# System Design Interview Framework

## Problem and mental model

A system-design interview is a structured decision conversation under uncertainty. The goal is not to guess the interviewer's architecture; it is to turn requirements into a coherent design, follow success and failure flows, quantify bottlenecks, and defend trade-offs.

## 1. Requirements

Clarify actors, core actions, read/write paths, latency and availability expectations, consistency, geography, retention, privacy, and explicit non-goals. State assumptions rather than silently inventing them.

## 2. Scale assumptions

Estimate active users, requests or events per second, payload size, storage growth, read/write ratio, peak factor, and bandwidth. Use round numbers and say which estimate actually changes the design.

## 3–5. Entities, APIs, and data model

Name durable entities and their identifiers. Define a small set of APIs or events with request, response, idempotency, pagination, and error behavior. Choose data models from access patterns, invariants, transaction boundaries, and growth—not from technology preference.

## 6. High-level architecture

Draw clients, edge, stateless services, storage, cache, queue/stream, workers, and external systems only when needed. Mark synchronous versus asynchronous boundaries and ownership of state.

```text
Client -> API -> Service -> Primary store
                  |
                  +-> durable event/queue -> Worker -> downstream
```

## 7. Complete success flow

Trace one request or event end to end: validation, authentication, idempotency, data read/write, cache behavior, enqueue/ack, response, and observable signals. Specify when the user considers the operation complete.

## 8. Complete failure flow

Choose the most important failure and trace timeout, partial write, retry, duplicate, poison message, dependency outage, consumer lag, and recovery. State retry budget, backoff, idempotency boundary, dead-letter/reconciliation behavior, and what the user sees.

## 9–11. Bottlenecks, reliability, observability, and security

Identify the first likely bottleneck from estimates. Discuss partition keys, hot keys, connection limits, queue growth, storage write rate, and fan-out. Define service-level signals: traffic, errors, latency, saturation, queue age/depth, replication lag, cache hit rate, and business correctness. Cover authentication, authorization, encryption, secrets, abuse, data minimization, audit, and tenant isolation.

## 12–13. Trade-offs and technology choices

For each major choice state the requirement it serves, alternative, cost, and reversal path. Name a real technology only after the required semantics are clear. Separate what is guaranteed from what is an operational target.

## 14. Interview follow-ups

Expect: 10× scale, multi-region, hot partition, downstream outage, duplicate events, data migration, schema evolution, cost reduction, and observability of silent correctness failures.

## 15. Five-minute revision and practice

Requirements → estimates → entities/APIs/data → architecture → success flow → failure flow → bottleneck → reliability/observability/security → trade-offs.

Blank-design challenge: outline an event-processing system in 35 minutes. Spend the last ten minutes on failure flow and trade-offs, not extra boxes.

## Related notes

- [[System Design Map of Content]]
- [[System Design Interview Framework - Quick Revision]]
- [[Requirements and Scope]] · [[Capacity Estimation]]
- [[Core Entities APIs and Data Model]] · [[Architecture Presentation Strategy]]
- [[Trade-off Communication]] · [[System Design Interview Checklist]]

Mistakes and re-tests: [[Mistake Index]]

## Interview scoring rubric

Score each dimension 0–2 after a timed attempt: requirement clarity, useful estimates, coherent data/API model, readable architecture, complete success flow, complete failure flow, scaling depth, reliability/observability, security, and trade-off communication. A note existing is not a passing mock. Record the lowest two dimensions as the next drill.

## Source metadata

Curated from the existing vault framework and the two sanitized conversations listed in frontmatter. Technology selections in system notes are illustrative production choices, not claims about personal use. Version-sensitive product behavior must be checked against current official documentation before implementation.
