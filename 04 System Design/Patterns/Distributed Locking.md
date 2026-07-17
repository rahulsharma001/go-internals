---
type: canonical
domain: system-design
topic: distributed-locking
status: active
last_verified: 2026-07-17
---
# Distributed Locking

## 1. Problem it solves

Rare workflows need mutual exclusion across processes when database constraints, idempotency, partition ownership, or single-writer design cannot enforce the action.

## 2. Simple mental model

A distributed lock is a lease that may expire while the old holder still runs. Correctness requires a monotonically increasing fencing token that the protected resource rejects when stale.

## 3. How it works

Acquire lease with owner ID, expiry, and fencing token; renew within deadline; perform work sending token to resource; resource accepts only token ≥ last seen; release best effort. Treat pause/network uncertainty as loss.

## 4. Concrete example

Scheduler grants worker token 43 for a shard. Lease expires and worker B gets 44. Paused A resumes; database update with 43 is rejected.

## 5. Detailed success flow

01. Contender acquires a time-bounded lease and receives a monotonically increasing fencing token.
11. Before work, it verifies enough lease budget remains and sends the token with every protected-resource mutation.
21. The resource records the highest accepted token and rejects any older writer, then the owner completes bounded work.
31. Renewal is conditional on the same lease identity
41. release removes only that owner's lease.

## 6. Detailed failure flow

01. Owner pauses beyond expiry.
11. New owner proceeds with higher token.
21. Old owner cannot corrupt state because resource fences it.
31. Without fencing, both execute despite “correct” lease store.

## 7. Scaling behaviour

Lock key granularity determines contention; hot global locks serialize throughput. Shard ownership/queues often scale better. Monitor wait, hold, renewal, expiry, stale rejection.

## 8. Data consistency implications

Lease service must provide suitable conditional/linearizable operations. Clock assumptions and network delay matter. Lock does not make multi-resource work atomic.

## 9. Real implementation choices

Database row/advisory lock, etcd/Consul/ZooKeeper lease, Redis lock only with understood failure model, DynamoDB conditional lease. Protected resource must support token.

## 10. Trade-offs

Simple exclusion versus availability, latency, deadlock/expiry, and operational dependency. Short leases fail under pauses; long leases slow recovery.

## 11. When not to use it

Prefer unique constraints, compare-and-set, idempotency, partition leader, or work queue. Never use lock merely to serialize all traffic.

## 12. Common interview mistakes

Lease without fencing; wall-clock trust; release another owner’s lock; no renewal bound; work outlives lease; lock store available but resource partitioned; Redlock name as proof.

## 13. How it appears inside larger systems

Schedulers, singleton maintenance, shard movement, rare cross-process coordination. Not usually payments/seat uniqueness where DB constraints fit.

## 14. Likely interviewer follow-ups

Why lock? lease duration? pause? fencing resource? stale release? lock-service partition? deadlock? throughput?

## 15. Five-minute revision

First avoid lock. If needed: conditional lease + owner + expiry + monotonic fencing token; bounded renewal; resource rejects stale token; observe contention/expiry.

## 16. Related notes

[[Leader Election]] · [[Idempotency Pattern]] · [[Distributed Job Scheduler]]

## 17. Verified further reading

- [Redis distributed locks](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/) — official algorithm and safety discussion.
- [Kubernetes leases](https://kubernetes.io/docs/concepts/architecture/leases/) — official lease usage for coordination.
