> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Caching Pattern]].

---
type: canonical
domain: system-design
topic: caching
status: learning
source_conversations:
  - "System Design Patterns | 2026-07-05 | 6a4aa703-f2d8-83ee-aac3-020aa67e9afb"
---
# Caching Pattern

## Problem it solves

Caching reduces latency and source load by serving reusable data from a faster, bounded layer.

## Mental model and how it works

A cache is a disposable derived view with an explicit key, value, freshness, eviction, invalidation, and miss path. Cache-aside reads cache then source and fills; write-through updates cache with source; write-behind defers source writes and risks durability. Multi-level caches may include client/CDN, local memory, and distributed cache.

## Concrete example and dry run

`GET /orders/o1`: key `order:v3:o1`. Miss → single-flight lock → read authoritative order DB → cache serialized version for 30 seconds with jitter → return. An order event invalidates or writes version v4. If invalidation is delayed, TTL bounds staleness; the detail API may bypass cache for read-your-writes.

## Success and failure scenarios

Success: hit returns quickly and source load falls. Failure: hot-key expiry creates a stampede; cache outage sends all traffic to DB; stale price/authorization causes harm. Use request coalescing, TTL jitter, stale-while-revalidate where safe, negative caching, admission control, and bypass for correctness-critical data.

## Scaling and production choices

CDN for public immutable content; local LRU for tiny hot data; Redis/Memcached for shared cache. Observe hit ratio by endpoint, load latency, eviction, memory, hot keys, stale serves, source fallback, and stampede lock contention.

## Trade-offs and when not to use

Freshness and invalidation complexity are the cost. Caches can hide slow queries and add another outage mode. Do not cache high-cardinality rarely reused data, secrets without controls, or authorization decisions without a safe revocation model.

## Interview mistakes and follow-ups

“Add Redis” with no key/TTL/invalidation; cache as source of truth; no outage path. Follow-ups: stampede? hot key? deletion? version race? multi-region cache?

## Five-minute recall

What/why → key → pattern → TTL/invalidation → miss/stampede → outage/degrade → consistency → metrics.

Related: [[Consistency Models]], [[Rate Limiting Pattern]], [[YouTube System Design]].

## Source metadata

Sanitized source above; Redis/product specifics require current verification.
