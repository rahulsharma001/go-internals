---
type: canonical
domain: system-design
topic: consistent-hashing
status: active
last_verified: 2026-07-17
---
# Consistent Hashing

## 1. Problem it solves

Modulo hashing remaps most keys when node count changes. Consistent and rendezvous hashing reduce movement and enable weighted ownership for caches and partition routers.

## 2. Simple mental model

Place keys and virtual node tokens on a ring; a key belongs to the next token clockwise. Or score every node with key+node in rendezvous hashing and choose the top score. Movement should be proportional to capacity change.

## 3. How it works

Use many virtual nodes or weighted rendezvous scores to smooth ownership. Maintain a versioned membership view. Replicate to distinct failure domains and handle transition with dual lookup/copy or handoff.

## 4. Concrete example

A cache cluster adds one node. Only a share of keys move; misses refill from source of truth. For durable storage, background transfer and routing epochs prevent lost writes during ownership change.

## 5. Detailed success flow

01. Client/router reads membership version and hashes the qualified key to a virtual shard.
11. It selects the current primary and failure-domain-aware replicas, then sends the request with that epoch.
21. During rebalance, the new owner copies still-valid keys and catches up changes while the old owner continues serving.
31. Control plane switches the shard only after validation, and the old replicas drain after the grace period.

## 6. Detailed failure flow

01. Clients use stale rings and send writes to old owners.
11. Old owner must redirect/reject by epoch
21. otherwise divergent writes occur.
31. Node flapping causes churn, so membership changes are damped.

## 7. Scaling behaviour

Virtual-node count, weight, replication factor, and membership distribution affect balance. Consistent hashing balances many keys, not a single hot key. Rendezvous hashing can simplify top-N replica selection.

## 8. Data consistency implications

For caches, misses/stale movement are tolerable. Durable stores require write authority, handoff, read repair, quorum/conflict rules, and fencing beyond the hash algorithm.

## 9. Real implementation choices

Client-side hashing libraries, proxy/router layer, Redis/Memcached-style sharding, Cassandra/Dynamo-style token rings, rendezvous hashing for gateways.

## 10. Trade-offs

More virtual nodes improve balance but enlarge metadata/rebalance work. Client-side routing removes hop but complicates rollout; proxy routing centralizes membership but adds latency/failure point.

## 11. When not to use it

Do not use when a fixed small node set or directory/range routing is simpler, or when the core need is one hot-key mitigation.

## 12. Common interview mistakes

“Consistent” confused with data consistency; no replication/failure domains; no membership version; ring alone claimed to prevent split brain; no key movement plan.

## 13. How it appears inside larger systems

Distributed caches, object placement, partition routers, service affinity, and sharded rate-limit state.

## 14. Likely interviewer follow-ups

How many virtual nodes? How are weights/failure domains handled? What happens to in-flight writes? How do clients update membership? How address a hot key?

## 15. Five-minute revision

Hash key to stable owner set; minimal movement on membership change. Add virtual nodes/weights, versioned membership, handoff, replicas, and fencing. It does not solve hot keys.

## 16. Related notes

[[Consistent Hashing Pattern]] · [[Partitioning and Sharding]] · [[Distributed Cache System]] · [[Replication]]

## 17. Verified further reading

- [Redis Cluster specification](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/) — official slot ownership, redirection, and failover behavior.
- [Kubernetes EndpointSlice](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/) — official dynamic endpoint membership context.
