---
type: canonical
domain: system-design
topic: consistency-models
status: active
last_verified: 2026-07-17
---
# Consistency Models

## 1. Problem it solves

Concurrent and replicated systems need an explicit contract for what reads and writes may observe. “Consistent” alone does not specify ordering, visibility, or anomalies.

## 2. Simple mental model

A consistency model is a promise about observable histories. Stronger models make reasoning simpler but require coordination; weaker models improve locality/availability while moving conflict and staleness handling to the application.

## 3. How it works

Linearizable operations appear atomic in real-time order; serializable transactions behave like some serial execution; snapshot/repeatable-read constrains transaction views; read-your-writes and monotonic reads are session guarantees; eventual consistency promises convergence if writes stop. Causal consistency preserves cause-before-effect.

## 4. Concrete example

Seat confirmation uses a serializable/conditional transaction on `(event,seat)`; the search index is eventual. A user profile may need read-your-writes after edit without globally linearizable reads.

## 5. Detailed success flow

01. A booking compare-and-set changes `AVAILABLE→HELD` once.
11. Replicas and search catch up later.
21. API responses expose authoritative confirmation versus derived availability.

## 6. Detailed failure flow

01. A stale search read shows an available seat already held.
11. Final hold rechecks truth and returns conflict.
21. If two regions accept writes without an owner/conflict rule, both may confirm—an invariant violation, not mere staleness.

## 7. Scaling behaviour

Coordination scope is key. Per-key leader/partition consistency scales better than global ordering. Quorum reads/writes add network and repair costs; session routing can provide local guarantees.

## 8. Data consistency implications

This is the topic itself: state ordering scope, freshness bound, conflict rule, and convergence/repair. Separate storage isolation from application-level cross-service consistency.

## 9. Real implementation choices

PostgreSQL offers transactional isolation including serializable; DynamoDB conditional writes support per-item guards; Kafka partitions preserve record order within a partition; caches/search indexes are usually derived/eventual.

## 10. Trade-offs

Stronger guarantees reduce anomalies but add latency, contention, or partition unavailability. Weaker guarantees need versions, merge/reconciliation, and UX that exposes pending/conflict state.

## 11. When not to use it

Do not demand global linearizability for analytics, presence, counters, or search merely for simplicity. Do not accept eventual consistency for irreversible invariant-breaking actions.

## 12. Common interview mistakes

CAP used outside partitions; database “ACID” assumed to cover services; replica reads called current; global order when per-key suffices; no user-visible semantics.

## 13. How it appears inside larger systems

Payments/bookings need strict transitions; chat uses per-conversation order; feeds/search/analytics accept lag; file sync needs version/conflict rules.

## 14. Likely interviewer follow-ups

What anomaly is harmful? What is the scope—row, key, conversation, region? Can the UI show pending? How are conflicts reconciled? What happens after failover?

## 15. Five-minute revision

Name the observation promise, scope, and anomaly. Strict at the invariant boundary; derived views may lag. Define version/conflict/repair and user-visible state.

## 16. Related notes

[[CAP and PACELC]] · [[Replication]] · [[Multi-Region Design]] · [[Invariants and Critical Paths]]

## 17. Verified further reading

- [PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html) — official isolation levels and anomalies.
- [PostgreSQL SET TRANSACTION](https://www.postgresql.org/docs/current/sql-set-transaction.html) — concrete configuration and behavior.

