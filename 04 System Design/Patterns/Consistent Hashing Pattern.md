---
type: canonical
domain: system-design
topic: consistent-hashing-pattern
status: active
last_verified: 2026-07-17
---
# Consistent Hashing Pattern

## 1. Problem it solves

Apply stable key placement and membership changes in a distributed cache/router while making movement, failure, replicas, and stale membership explicit.

## 2. Simple mental model

The foundation [[Consistent Hashing]] explains the algorithm; this pattern is the operational recipe: versioned membership, weighted owners, replica placement, handoff, and failure behavior.

## 3. How it works

Hash key to ring/rendezvous owner set; choose distinct failure domains; owner verifies membership epoch. On add/remove, copy only moved ranges/keys, optionally dual-read, switch routing version, then retire old owner. Cache misses refill; durable stores need logged handoff.

## 4. Concrete example

Distributed cache uses rendezvous hash to choose primary+replica. Node addition receives selected keys lazily; source DB remains truth, so stale routing becomes miss rather than data loss.

## 5. Detailed success flow

Client has current membership, selects healthy owner, reads/writes cache; on rebalance movement is bounded and hit ratio recovers progressively.

## 6. Detailed failure flow

Node dies; client selects next replica and source fallback. Stale client reaches removed node and gets redirect/miss. One hot key still overloads owner, so replicate/coalesce separately.

## 7. Scaling behaviour

Weights reflect capacity; virtual nodes improve balance; membership propagation and key movement consume network. Track load variance, movement, hit rate, and rebalance time.

## 8. Data consistency implications

For cache, eventual membership and disposable values are fine. For authoritative data, hashing needs consensus/epochs, replication, quorum/conflict/repair; never infer these from placement.

## 9. Real implementation choices

Rendezvous hashing library, ring with virtual nodes, proxy layer, client-side routing, service discovery/health. Pick from rollout and hop cost.

## 10. Trade-offs

Client routing lower latency but harder membership rollout; proxy simpler clients but extra hop/bottleneck. Eager transfer preserves hits but costs bandwidth; lazy warm causes misses.

## 11. When not to use it

Fixed small set, range queries, explicit directory assignment, or hot-key problem. Use ordinary load balancing for stateless requests without key affinity.

## 12. Common interview mistakes

Duplicating [[Consistent Hashing]] definitions without handoff; no membership version/replicas; hash treated as data consistency; modulo; hot key assumed solved.

## 13. How it appears inside larger systems

Distributed Cache System, object placement, rate limit shards, gateway affinity, partition routers.

## 14. Likely interviewer follow-ups

Ring vs rendezvous? weights? replicas/failure domain? stale clients? transfer? hot key? durable writes? flapping membership?

## 15. Five-minute revision

Stable owner set + versioned membership + weights/replicas + safe handoff. Cache can miss/refill; durable state needs epochs/log/repair. Hot key is separate.

## 16. Related notes

[[Consistent Hashing]] · [[Distributed Cache System]] · [[Partitioning and Sharding]]

## 17. Verified further reading

- [Redis Cluster specification](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/) — official ownership/redirection/failover example.\n- [Kubernetes EndpointSlice](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/) — official dynamic endpoint membership.

