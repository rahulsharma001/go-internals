---
type: canonical
domain: system-design
topic: caching-pattern
status: active
last_verified: 2026-07-17
---
# Caching Pattern

## 1. Problem it solves

Reduce repeated read latency and origin load by storing a disposable copy while retaining a clear source of truth.

## 2. Simple mental model

For every cache answer seven nouns: object, key, value, source, TTL/freshness, invalidation, miss/failure. “Redis” answers none of them.

## 3. How it works

Cache-aside reads cache then source and populates after miss; writes update truth then invalidate/version. Read-through hides fetch behind cache library. Write-through updates cache and source in one path but still needs atomicity/failure semantics. Write-behind is asynchronous and risky for authoritative state.

## 4. Concrete example

URL redirect cache key `alias:v3` maps to `{target,status,expiresAt,version}` for 10 minutes. Link DB is truth. Disable commits DB then publishes invalidation; short TTL bounds lost invalidation.

## 5. Detailed success flow

Request hits fresh entry; on miss one loader reads truth, populates with TTL+jitter, and returns. Metrics record hit/miss, load latency, and age.

## 6. Detailed failure flow

Cache times out. Caller uses a short cache deadline and bounded source fallback; admission protects source. If truth is unavailable, product policy decides stale serve or fail. Cache recovery warms gradually.

## 7. Scaling behaviour

Tier local/distributed/edge; size hot set; replicate hot reads; shard by key; request-coalesce misses; limit value/key cardinality and memory; watch eviction/churn.

## 8. Data consistency implications

Cache-aside can return stale after write or replica lag. Invalidate only after source commit, include versions, and define allowed staleness. Never let cache overwrite newer truth.

## 9. Real implementation choices

Redis/Memcached, in-process LRU, CDN/edge KV. Use TTL, max memory/eviction, serialization/version, and observability. Select product only after semantics.

## 10. Trade-offs

Lower latency/origin load versus staleness, invalidation, cold start, memory, hot keys, and another dependency. Long TTL improves hits but delays changes.

## 11. When not to use it

Correctness-critical high-churn low-reuse state; unbounded personalized keys; data whose safe fallback is undefined.

## 12. Common interview mistakes

“Use Redis for speed”; no source/key/value; caching before source commit; same TTL herd; no negative-cache policy; fail-open with sensitive data; cache as durability.

## 13. How it appears inside larger systems

URL redirects, feed pages, profiles, autocomplete, video metadata/segments, API gateway, and database query results.

## 14. Likely interviewer follow-ups

Key/value? hit ratio? TTL/invalidation? write race? cache down? source down? hot key? stampede? eviction? tenant isolation?

## 15. Five-minute revision

Name object/key/value/source/freshness/invalidation/miss/failure. Truth first, version/invalidate after commit, coalesce+jitter, bound fallback and memory.

## 16. Related notes

[[Caching and CDN Fundamentals]] · [[Cache Invalidation and Stampede]] · [[Distributed Cache System]]

## 17. Verified further reading

- [Redis client-side caching](https://redis.io/docs/latest/develop/reference/client-side-caching/) — invalidation, disconnect, and candidate guidance.\n- [Redis caching use cases](https://redis.io/docs/latest/develop/use-cases/) — official cache-aside and prefetch examples.

