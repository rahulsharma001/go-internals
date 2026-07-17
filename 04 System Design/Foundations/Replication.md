---
type: canonical
domain: system-design
topic: replication
status: active
last_verified: 2026-07-17
---
# Replication

## 1. Problem it solves

A single copy is a durability, availability, and read-capacity risk. Replication maintains copies, but introduces lag, coordination, failover, and conflict questions.

## 2. Simple mental model

Ask who may write, when a write is acknowledged, which replica a read uses, and how a failed/recovered replica catches up. Copies are not backups against logical deletion.

## 3. How it works

Leader-follower serializes writes at a leader and streams a log; synchronous replicas join acknowledgement, asynchronous replicas lag. Leaderless/quorum systems accept at multiple replicas and use versions, repair, and conflict resolution. Multi-leader improves locality but exposes conflicts.

## 4. Concrete example

Order writes commit on a leader plus synchronous standby before acknowledgement; read replicas serve non-critical history. Search/index replicas are derived and can rebuild. Backups retain older recoverable versions.

## 5. Detailed success flow

01. Leader assigns log order, quorum/synchronous policy commits, followers apply, client receives success.
11. Reads choose leader/current replica according to freshness.
21. Failover elects/fences a new leader.

## 6. Detailed failure flow

01. Old leader is isolated and continues accepting writes after failover.
11. Epoch/fencing rejects stale leadership.
21. On recovery it discards/catches up divergent state
31. asynchronous failover may lose acknowledged writes unless policy prevented that.

## 7. Scaling behaviour

Read replicas scale reads; they do not scale the single write leader. Replication multiplies storage/network and repair work. Cross-region sync raises latency; async lowers it but increases RPO/staleness.

## 8. Data consistency implications

Read-after-write, monotonic reads, quorum formulas, conflict detection, and replica lag must be explicit. Quorum overlap alone needs correct version/repair semantics.

## 9. Real implementation choices

PostgreSQL streaming replication; Kafka replication/ISR; Cassandra/Dynamo-style quorum; object storage native durability/replication; CDN replicas for immutable bytes.

## 10. Trade-offs

Synchronous durability versus write latency/availability; asynchronous locality versus data loss/staleness; more replicas versus cost/repair; multi-leader versus conflict complexity.

## 11. When not to use it

Do not add read replicas to solve write contention, or call three copies a backup/DR plan.

## 12. Common interview mistakes

No write authority; instant failover assumption; stale reads ignored; split brain without fencing; replication factor treated as durability proof; no repair/backfill.

## 13. How it appears inside larger systems

Databases, brokers, object metadata, caches, search shards, multi-region read paths, and schedulers.

## 14. Likely interviewer follow-ups

When is write acknowledged? Can an acknowledged write be lost? How detect/fence old leader? What do reads observe? How repair a lagged replica? What about logical corruption?

## 15. Five-minute revision

Writer → ack rule → read rule → lag → failover election/fence → catch-up/repair → backup. Replicas scale reads/faults, not automatically writes.

## 16. Related notes

[[Consistency Models]] · [[Leader Election]] · [[Multi-Region Design]] · [[Observability and SLOs]]

## 17. Verified further reading

- [PostgreSQL high availability and replication](https://www.postgresql.org/docs/current/high-availability.html) — official replication/failover concepts.
- [Amazon S3 consistency model](https://docs.aws.amazon.com/AmazonS3/latest/userguide/) — official object-store consistency and durability context.

