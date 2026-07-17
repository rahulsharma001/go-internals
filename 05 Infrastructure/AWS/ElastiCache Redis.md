---
type: canonical
domain: infrastructure
topic: aws-elasticache
status: learning
---

# ElastiCache Redis

## Problem and mental model

Adds low-latency ephemeral data structures for cache, sessions, rate limits or coordination.

## End-to-end flow and internals

Go client pool → cluster endpoint → shard/primary/replica → command; miss loads source of truth then fills with TTL. Locks require token ownership and failure semantics; Redis is not automatically authoritative.

## Failure modes and diagnosis

Measure client pool wait/network/server command separately; inspect hot keys, large values, CPU, evictions, memory, failover/reconnect and stampede. Never run broad scans casually.

## Security, scaling and trade-offs

Use TLS/auth, private SGs, bounded TTL/value, jitter/singleflight, fail-open/closed decision. Caching improves latency/load but creates stale data and failover complexity.

## Interview questions and five-minute revision

What happens to RDS when Redis fails? Recall the request/event path, security boundary, bottleneck, recovery and rejected alternative.

## Related notes

[[Kubernetes Production Failures]] · [[Caching Pattern]] · [[Connection Pooling]]

## Source metadata

Curated from the infrastructure source conversations and existing system-design canonicals. AWS feature, quota, price, region and integration details are `needs-verification` against current official documentation.
