> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Distributed Locking]].

---
status: learning
type: canonical
area: system-design
sources:
  - "Curated system-design synthesis; status: needs-verification for chosen lock service"
---

# Distributed Locking

## Problem it solves

Multiple processes must avoid concurrently performing a narrowly defined action for the same resource.

## Mental model

A lock is a time-bounded lease, not proof that an old holder has stopped. A monotonically increasing fencing token protects the resource from stale holders.

## How it works

A client atomically acquires a lease for key `inventory:sku-7`, receives token `41`, renews only while healthy, and releases conditionally using its owner ID. The protected storage accepts writes only when their fencing token is newer than the last accepted token. Correctness comes from the resource enforcing fencing, not wall-clock confidence.

## Concrete example and detailed dry run

Worker A obtains token 41, pauses beyond the lease, and worker B obtains token 42. A resumes and tries to write. The inventory database has already seen token 42, so it rejects A's token 41. Without fencing, both workers could believe they own the lock.

## Success scenario

Only the current lease holder performs the action; renewal is bounded; conditional release cannot delete another owner's lease.

## Failure scenario

Network pause separates the client from the lock service. The lease expires and another holder starts. The original client's stale write is rejected by fencing. If the resource cannot enforce fencing, the design cannot claim strong mutual exclusion under pauses.

## Scaling considerations

Use fine-grained keys, short critical sections, bounded wait queues, jittered retries, and contention metrics. A hot global lock serializes throughput and is an architectural smell.

## Production technology choices

Database row locks/advisory locks are simplest when work shares that database transaction. etcd or ZooKeeper provide lease/session primitives. Redis may coordinate best-effort work, but safety assumptions must be explicit and verified.

## Trade-offs

Locks simplify exclusion but reduce availability and throughput, add lease-expiry edge cases, and can hide a poor ownership model.

## When not to use it

Prefer unique constraints, optimistic concurrency, idempotency, queues partitioned by key, or single-writer ownership when these express the invariant directly.

## Common interview mistakes

- Believing TTL alone prevents stale writes.
- Omitting fencing tokens and conditional release.
- Locking globally or holding locks across slow network calls.
- Calling a lock service failure-proof.

## Interview questions and follow-ups

- What happens during a long GC pause?
- Can the protected resource enforce fencing?
- Could a database constraint replace the lock?

## Five-minute recall

Lease + owner identity + renewal + fencing token + resource validation. Prefer constraints/idempotency when possible; measure contention.

## Related notes

[[Leader Election]] · [[Idempotency Pattern]] · [[Consistency Models]] · [[Partitioning and Sharding]]

## Source metadata

Curated from standard distributed-systems principles. Specific product guarantees are `status: needs-verification` against current official documentation.

