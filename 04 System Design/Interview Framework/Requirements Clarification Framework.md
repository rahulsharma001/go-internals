---
type: canonical
domain: system-design
topic: requirements
status: active
---
# Requirements Clarification Framework

## Purpose

Turn a broad prompt into a bounded contract before architecture. Requirements decide which state matters and which trade-offs are legitimate; they are not ceremony before naming technologies.

## The four-pass method

### 1. Actors and journey

Ask who creates, reads, updates, administers, and receives data. Select one critical journey in verb form: “a rider requests and gets one driver,” “a buyer reserves and pays for one seat,” or “a creator uploads and a viewer plays a video.”

### 2. Functional scope

Choose two or three operations required to complete that journey. Explicitly park optional discovery, recommendations, analytics, admin tools, billing, or ML unless central. Confirm cancellation and status lookup when the workflow is long-running.

### 3. Non-functional priorities

For each critical operation clarify:

| Dimension | Question | Design consequence |
| --- | --- | --- |
| latency | response or completion target; p50 or tail? | cache, locality, async boundary |
| availability | which operation and failure scope? | replicas, degradation, region plan |
| durability | what acknowledged state may never be lost? | commit point, replication, backup |
| consistency | what stale result is harmful? | transaction, quorum, versioning |
| scale | peak rate, data, skew, connections? | partition and capacity plan |
| geography | users, writes, residency? | placement and authority |
| security | trust, PII, abuse, compliance supplied? | authorization, minimization, rate limits |

Rank rather than demand all properties maximally.

### 4. Assumptions and non-goals

If no answer is supplied, say: “I’ll assume X for this interview and change it if you prefer.” Mark it on the board. A non-goal prevents accidental expansion and demonstrates prioritisation.

## Candidate question bank

- Which user and operation should I optimise first?
- Is this read-heavy, write-heavy, connection-heavy, or fan-out-heavy?
- Which state must be immediately consistent? Which may lag, and by how long?
- Does acceptance mean durable receipt or completed processing?
- Are we designing for one region, many read regions, or multi-region writes?
- What retention, deletion, privacy, and audit expectations matter?
- Should I cover abuse/fraud, recommendations, live media, or keep them out of scope?

Do not ask all questions mechanically. Ask the ones that choose an architecture.

## Example: ticket booking

Selected scope: search an event, hold seats for five minutes, pay, confirm booking, and inspect status. Strict invariant: one seat has at most one confirmed booking; inventory never goes below zero. Event search may lag; hold and confirmation may not. Assume a single write region initially and a burst around popular releases. Non-goals: resale, dynamic pricing, venue scanning.

That scope immediately suggests an authoritative inventory transaction, expiring holds, idempotent payment, and a derived search index. It does not yet justify Kafka, Redis, or sharding.

## Weak versus strong framing

Weak: “It should be scalable, available, and consistent.”

Strong: “Seat confirmation prioritises correctness over availability during a partition. Search may return stale availability, but final hold uses an atomic conditional write. I’ll target a two-second hold response at peak and degrade browsing before overselling.”

## Failure and follow-up prompts

Ask what the user sees when a downstream dependency times out, whether partial success is visible, and how the system recovers. Follow-ups often change one requirement: global writes, stronger freshness, lower cost, a celebrity hotspot, or a provider outage. Restate the changed assumption before changing the diagram.

## Five-minute revision

Actors → critical journey → two or three functions → ranked NFRs → strict invariant → consistency split → scale/skew → geography/security → assumptions → non-goals.

Related: [[45-Minute System Design Playbook]] · [[Invariants and Critical Paths]] · [[Back-of-the-Envelope Estimation]] · [[Requirements Checklist]].

