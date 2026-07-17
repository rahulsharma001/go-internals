> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Consistency Models]].

---
type: canonical
domain: system-design
topic: consistency-models
status: learning
---
# Consistency Models

## Problem it solves

Consistency defines what values concurrent readers may observe and how quickly replicas/views converge.

## Mental model and how it works

Do not say “consistent” without a guarantee. Linearizable operations appear atomic in real-time order. Sequential consistency preserves a single order but not necessarily wall-clock order. Causal consistency preserves cause-before-effect. Eventual consistency promises convergence after writes stop. Session guarantees such as read-your-writes and monotonic reads often match product needs better than global linearizability.

## Concrete example and dry run

An order transitions `PENDING → CONFIRMED`. The write owner uses a conditional version update, giving one authoritative transition. A search index and user cache update asynchronously. Immediately after confirmation, search may still show `PENDING`; the order-detail API routes to the authoritative store or overlays the session’s new version, providing read-your-writes.

## Success and failure scenarios

Success: each field/operation has an explicit guarantee and UI exposes intermediate states. Failure: replica lag allows inventory oversell or a stale authorization decision. Keep invariants on an authoritative transaction/conditional write path; treat caches and materialized views as derived.

## Scaling and production choices

Relational transactions/consensus-backed stores can enforce strong ownership; replicas, caches, Kafka consumers, and search indexes commonly expose lag. Include version numbers, event ordering, idempotency, reconciliation, and staleness metrics.

## Trade-offs and when not to use

Stronger consistency raises coordination latency and reduces availability during partitions. Eventual consistency improves locality/availability but shifts complexity to states, deduplication, conflict resolution, and user communication. Do not pay for global strong consistency on presence, analytics, or recommendations.

## Interview mistakes and follow-ups

Confusing ACID with replica consistency; saying eventual means random; assuming Kafka order across partitions; not defining conflict policy. Follow-ups: stale for how long? read-your-writes? concurrent update? partition behavior? reconciliation?

## Five-minute recall

Invariant → owner → required observation guarantee → acceptable staleness → conflict/version rule → derived-view repair.

Related: [[CAP and PACELC]], [[Replication]], [[CQRS]], [[Idempotency Pattern]].

## Source metadata

Curated from distributed-system extracts (`System Design Patterns`, `6a4aa703…`) and stable distributed-systems principles.
