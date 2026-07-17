---
type: canonical
domain: system-design
topic: leader-election
status: active
last_verified: 2026-07-17
---
# Leader Election

## 1. Problem it solves

A replicated control function sometimes needs one active coordinator per scope to assign work, own a partition, or serialize metadata changes.

## 2. Simple mental model

Election chooses a leader; fencing makes leadership safe. Availability of a leader is liveness, while rejection of stale leaders is safety.

## 3. How it works

Candidates use consensus/lease store to acquire term/epoch; leader renews heartbeat; followers observe; on expiry/quorum change elect higher term. Every mutation carries term and resource rejects older term. State/checkpoints allow new leader to resume.

## 4. Concrete example

Job-scheduler shard leader term 19 assigns runs. Region partition elects term 20. Old term 19 assignments are rejected/deduplicated.

## 5. Detailed success flow

01. One leader with quorum acts, checkpoints, renews.
11. Followers do not mutate.
21. Planned handoff drains and transfers term/state.

## 6. Detailed failure flow

01. Old leader pauses and resumes after new election.
11. Fencing rejects term 19.
21. If quorum unavailable, no leader is elected and control pauses instead of split brain.

## 7. Scaling behaviour

Elect per shard/partition rather than one global leader. Election storms and synchronized timeouts need jitter. Leader workload/capacity can bottleneck.

## 8. Data consistency implications

Consensus/linearizable term store is required for safe election. Async heartbeat alone can create dual leaders. Data replication/commit semantics remain separate.

## 9. Real implementation choices

etcd/Raft, ZooKeeper, Consul, database advisory/lease for small scope, Kubernetes Lease, Kafka partition leadership. Managed primitives preferred.

## 10. Trade-offs

Single leader simplifies ordering but bottlenecks and pauses on election. Sharded leaders scale but add membership/rebalance. Longer lease reduces churn but delays failure recovery.

## 11. When not to use it

Stateless request handling, naturally partitioned work queues, or tasks already protected by database constraint/idempotency may not need explicit leader.

## 12. Common interview mistakes

Election without fencing; heartbeat service mistaken for consensus; leader state only in memory; no term on writes; global leader for all tenants; zero-downtime election claim.

## 13. How it appears inside larger systems

Schedulers, partition controllers, metadata coordinators, database/broker replicas, compaction and singleton jobs.

## 14. Likely interviewer follow-ups

Consensus? term? quorum loss? old leader? leader state recovery? per-shard? election timeout/storm? planned deploy?

## 15. Five-minute revision

Consensus/lease elects term; leader renews; all effects carry term and are fenced; checkpoint; fail closed on no quorum; shard leadership to scale.

## 16. Related notes

[[Distributed Locking]] · [[Replication]] · [[Distributed Job Scheduler]] · [[Multi-Region Design]]

## 17. Verified further reading

- [Kubernetes leases](https://kubernetes.io/docs/concepts/architecture/leases/) — official leader-election coordination primitive.
- [etcd FAQ and learning](https://etcd.io/docs/) — official Raft/consensus documentation.

