---
type: canonical
domain: infrastructure
topic: connection-pooling
status: learning
---

# Connection Pooling

## Problem and mental model

Reuses expensive TCP/TLS/database connections while bounding concurrency and resource use.

## Packet or connection flow

Caller requests connection → pool returns idle or opens within max → request/transaction runs under context → healthy connection returns idle → idle/lifetime eviction closes it. HTTP reuse requires consuming/closing response; `database/sql` exposes open/in-use/idle/wait stats.

## Failure modes and senior diagnosis

Measure acquisition wait separately from operation latency, open/in-use/idle, reuse, connection age, server sessions, DNS endpoint/failover. Leaks exhaust FDs/pool; oversized pools overload database.

## Production security, scaling and trade-offs

Budget max connections across replicas, set acquisition deadline, idle/lifetime below infrastructure limits with jitter, validate after failover. Pools trade handshake cost for staleness and held resources.

## Interview questions and five-minute revision

Why does scaling Pods worsen DB latency even when each pool is unchanged? Recall the exact packet/connection sequence and the first diagnostic evidence at each boundary.

## Related notes

[[File Descriptors]] · [[Kubernetes Production Failures]] · [[Context Cancellation]]

## Source metadata

Curated from *Golang Interview Prep Guide* (2026-06-29, `6a420622-0d40-83ee-8a64-955c416c4a67`) for the networking-focused role, plus relevant Kubernetes/AWS extracts. Protocol and implementation details are `needs-verification` against RFC/vendor/kernel documentation.
