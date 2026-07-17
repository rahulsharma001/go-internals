---
type: canonical
domain: system-design
topic: stateless-and-stateful-services
status: active
last_verified: 2026-07-17
---
# Stateless and Stateful Services

## 1. Problem it solves

Compute that silently owns session or workflow state cannot be safely rescheduled, scaled, or failed over. Yet some workloads—connections, partitions, caches—necessarily have local state.

## 2. Simple mental model

Stateless means any instance can handle the next request using external authoritative state. Stateful means instance identity/local state affects correctness or performance. Statefulness is not bad; hidden or unfenced state is.

## 3. How it works

Externalize durable session/workflow state; route through stable IDs; make handlers idempotent. For necessary local state, define ownership, replication/checkpoint, lease/epoch, rebalancing, and recovery. Connection gateways hold sockets but not message truth.

## 4. Concrete example

A chat gateway owns live sockets and bounded send buffers. The message store and delivery cursor are durable elsewhere. On gateway loss clients reconnect and catch up by cursor.

## 5. Detailed success flow

01. Load balancing sends an API request to any instance
11. it reads authoritative state and performs a versioned/idempotent update.
21. A stateful worker holds a partition lease and checkpoints progress.

## 6. Detailed failure flow

01. A stateful worker is duplicated after pause
11. the old worker resumes.
21. A fencing epoch on writes rejects the stale owner.
31. Without it, both mutate state despite a lease.

## 7. Scaling behaviour

Stateless replicas scale easily until shared stores saturate. Stateful partitions scale by rebalancing and may pause/move large state. Sticky sessions improve locality but reduce balance/failover.

## 8. Data consistency implications

External state centralizes consistency; local replicated state introduces lag. Define which local state is cache/soft and which must be checkpointed before acknowledgement.

## 9. Real implementation choices

Stateless HTTP/RPC services behind a load balancer; Redis/database for sessions where needed; Kafka consumer partition ownership; Kubernetes StatefulSet only when stable identity/storage is required.

## 10. Trade-offs

Externalization adds network latency/dependency. Locality improves performance but complicates failover. Stickiness reduces cache misses but concentrates load. Replicated state costs bandwidth/storage.

## 11. When not to use it

Do not call a service stateless because it runs in containers. Do not externalize every byte if reconstructible local caches are cheaper.

## 12. Common interview mistakes

In-memory idempotency; sticky sessions as durability; WebSocket gateway as message truth; no rebalance/drain; lease without fencing; stateful store scaled like stateless compute.

## 13. How it appears inside larger systems

API tiers, WebSocket gateways, schedulers, cache nodes, stream processors, and search shards.

## 14. Likely interviewer follow-ups

What survives restart? How does ownership move? What happens to in-flight requests? Is local state rebuildable? How does a stale owner get rejected?

## 15. Five-minute revision

Any instance for stateless; identity matters for stateful. Name durable owner, soft/local state, checkpoint, routing, rebalance, and fencing.

## 16. Related notes

[[Load Balancing]] · [[Leader Election]] · [[Distributed Locking]] · [[WebSocket Chat or Realtime System]]

## 17. Verified further reading

- [Kubernetes Service](https://kubernetes.io/docs/concepts/services-networking/service/) — stable routing to changing stateless endpoints.
- [Kubernetes StatefulSet](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) — official stable identity/storage behavior.

