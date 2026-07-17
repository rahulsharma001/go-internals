---
type: canonical
domain: system-design
topic: cap-and-pacelc
status: active
last_verified: 2026-07-17
---
# CAP and PACELC

## 1. Problem it solves

Network partitions and normal replication latency force choices that cannot be hidden behind “use distributed database.” CAP frames partition-time behavior; PACELC adds the normal-time latency/consistency choice.

## 2. Simple mental model

When replicas cannot communicate (P), choose whether an operation preserves availability (A) or consistency (C) for that invariant. Else (E), systems still trade latency (L) against consistency (C). CAP is per operation and guarantee, not a database label.

## 3. How it works

Define a partition and authority. A CP booking path rejects writes without quorum/leader to prevent double booking. An AP presence system accepts local updates and later reconciles. Under normal operation, quorum reads may improve freshness at network latency cost.

## 4. Concrete example

During a region partition, payment intent writes remain with the home-region epoch; the isolated region returns unavailable/pending rather than create a second charge. Feed likes may accept locally and merge by event ID.

## 5. Detailed success flow

01. The client sends an operation to the current authority and includes the observed version or epoch.
11. The authority confirms it still has quorum before accepting an invariant-changing write.
21. During a partition, the unavailable side rejects or limits the operation according to the stated policy while safe reads may continue.
31. After connectivity returns, replicas catch up and reconciliation verifies that no accepted state violated the invariant.

## 6. Detailed failure flow

01. A naïve active-active design lets both sides allocate the same seat.
11. DNS failover restores traffic but not correctness.
21. Recovery finds conflicting confirmations requiring manual repair.

## 7. Scaling behaviour

Quorum size, replica placement, cross-region RTT, and conflict rate affect throughput/latency. Per-key ownership narrows coordination; global consensus becomes expensive.

## 8. Data consistency implications

CP sacrifices write availability during partition for a consistent order. AP requires conflict-free operations or a deterministic merge; “last write wins” can lose intent. PACELC makes the everyday price visible.

## 9. Real implementation choices

Leader-based PostgreSQL/distributed SQL for strict transactions; quorum key-value stores for tunable reads/writes; CRDT/event-set designs for mergeable state; explicit home regions and fencing epochs.

## 10. Trade-offs

CP can reject users during isolation; AP can surface stale/conflicting state; cross-region quorum increases tail latency; async replication increases RPO and failover ambiguity.

## 11. When not to use it

Do not cite CAP for a single-node cache miss or routine slow request. Do not classify an entire product without naming the operation and failure.

## 12. Common interview mistakes

“Pick two of three”; ignoring partitions; availability confused with uptime; AP with no merge; CP with no failure UX; PACELC omitted while latency drives the design.

## 13. How it appears inside larger systems

Multi-region payments/bookings, chat ordering, driver assignment, cache replication, metadata conflict resolution, and monitoring ingestion.

## 14. Likely interviewer follow-ups

What exactly is unavailable? How is partition detected? What is the conflict rule? Who has the epoch? What does failback do? What is the normal RTT cost?

## 15. Five-minute revision

CAP: during partition, per operation choose availability or consistency. PACELC: otherwise latency versus consistency. State authority, conflict/repair, UX, and failback.

## 16. Related notes

[[Consistency Models]] · [[Replication]] · [[Multi-Region Design]] · [[Leader Election]]

## 17. Verified further reading

- [Google Cloud reliability framework](https://cloud.google.com/architecture/framework/reliability) — official guidance on designing for failures and regions.
- [PostgreSQL concurrency control](https://www.postgresql.org/docs/current/mvcc.html) — primary documentation for transaction/concurrency semantics.
