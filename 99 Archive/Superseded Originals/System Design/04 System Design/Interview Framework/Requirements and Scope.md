> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Requirements Clarification Framework]].

---
type: canonical
domain: system-design
topic: requirements-scope
status: learning
source_conversations:
  - "System Design Practice Tips | 2025-05-04 | 681749e6-1698-8013-bb4c-22bcf122748c"
---
# Requirements and Scope

## Problem it solves

Ambiguous prompts cause candidates to design different systems from the interviewer. Scope converts “design YouTube” into a bounded contract that can be tested.

## Mental model and method

Start with actors and their top actions. Separate functional requirements—what users do—from non-functional requirements—how well and under what failures. Ask for the top two or three flows, consistency-sensitive operations, geography, retention, privacy, and explicit non-goals. If the interviewer does not provide numbers, state labeled assumptions.

## Concrete example and dry run

For ride hailing: actors are rider and driver. In scope: driver location updates, nearby matching, offer acceptance, trip states, pricing/payment handoff. Out of scope initially: maps rendering, driver onboarding, support, and fraud models. The critical invariant is one active ride per accepted driver; location display may be eventually consistent.

Dry run the prompt before architecture: “A rider requests a nearby driver; the driver accepts once; both see trip changes; payment begins after completion.” Each sentence later maps to an API, state transition, data owner, and failure path.

## Success and failure scenarios

Success: interviewer confirms scope and the remaining design time deepens the critical flow. Failure: candidate silently assumes global strong consistency, uploads, analytics, recommendations, and billing, then never completes one path. Recover by restating priorities and cutting non-goals.

## Scaling, technology, and trade-offs

Requirements determine technology; they are not a prelude to naming Kafka or Redis. Availability, latency, durability, consistency, cost, privacy, and operability conflict. Rank them. A chat system may favor low latency and eventual presence, while payment ownership needs durable idempotent state transitions.

## When not to expand scope

Do not add features because a famous reference architecture has them. Do not invent contractual SLOs, regulatory obligations, or scale as facts.

## Interview mistakes and follow-ups

Common misses: no non-goals; confusing throughput with latency; saying “highly available” without user impact; never identifying the invariant. Follow-ups: What changes at 10×? What data may be stale? What must survive a region loss? Which action defines user-visible completion?

## Five-minute recall

Actors → top flows → NFR ranking → invariant → consistency → geography/retention/security → non-goals → labeled assumptions.

Related: [[System Design Interview Framework]], [[Capacity Estimation]], [[Trade-off Communication]].

## Source metadata

Existing vault framework plus the sanitized conversation listed in frontmatter; no personal system claim used.
