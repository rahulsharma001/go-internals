---
status: learning
type: canonical
area: system-design
sources:
  - "Curated system-design synthesis; status: needs-verification for chosen coordination service"
---

# Leader Election

## Problem it solves

A replicated group needs one active coordinator for work such as scheduling, partition assignment, or metadata updates, while surviving process failure.

## Mental model

Leadership is a renewable term recognized by a quorum. A leader from an older term must be unable to act.

## How it works

Candidates campaign through a consensus-backed coordination service. The winner receives a term/epoch and lease or session. Followers monitor the session; after expiry/quorum confirmation they elect a new leader. Every authoritative write carries the term so downstream state can reject an old leader.

## Concrete example and detailed dry run

Scheduler A is leader in epoch 8 and assigns job `j-4`. A loses quorum. Scheduler B wins epoch 9 and reassigns unfinished work. A later reconnects and sends an epoch-8 assignment; the job store rejects it because epoch 9 is current. Job execution is still idempotent because leadership alone cannot prevent every duplicate around failover.

## Success scenario

One quorum-recognized leader coordinates work, followers take over after a bounded failure-detection interval, and epochs fence stale commands.

## Failure scenario

A network partition leaves the old leader alive but separated from quorum. It must stop authoritative work. If it continues without downstream epoch checks, split-brain writes can occur.

## Scaling considerations

Do not route all data through the leader unnecessarily. Elect per shard/partition, keep the coordination state small, and monitor election frequency, term changes, quorum health, and time without a leader.

## Production technology choices

etcd/Consul/ZooKeeper sessions, Kubernetes Lease objects, or a database advisory lock can coordinate modest workloads. Raft-based services expose terms and quorum behavior; verify exact session semantics.

## Trade-offs

Election enables automatic failover and ordered coordination but introduces temporary unavailability, quorum dependency, and split-brain/fencing complexity.

## When not to use it

Avoid election when work can be safely parallel and idempotent, partition ownership is broker-managed, or a database constraint already serializes the critical update.

## Common interview mistakes

- Saying “only one leader” without explaining partitions.
- Omitting epochs/fencing and idempotent execution.
- Assuming immediate failure detection.
- Making a global leader the data-plane bottleneck.

## Interview questions and follow-ups

- What constitutes quorum?
- What can the old leader do during a partition?
- How long is the system unavailable during election?

## Five-minute recall

Quorum elects; term identifies authority; lease/session expires; epoch fences old leader; idempotency handles failover duplicates.

## Related notes

[[Distributed Locking]] · [[Replication]] · [[Consistency Models]] · [[Failure Handling Strategy]]

## Source metadata

Curated synthesis. Product-specific election and lease guarantees remain `status: needs-verification` until checked for the chosen technology/version.
