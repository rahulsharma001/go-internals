---
type: canonical
domain: system-design
topic: caching-and-cdn-fundamentals
status: active
last_verified: 2026-07-17
---
# Caching and CDN Fundamentals

## 1. Problem it solves

Repeatedly computing or fetching the same data wastes latency and origin capacity. Caches and CDNs place reusable values closer to consumers while preserving an authoritative source.

## 2. Simple mental model

A cache is a disposable copy with a key, value, freshness rule, capacity rule, and fallback. A CDN is a geographically distributed HTTP/content cache. Neither is automatically the source of truth.

## 3. How it works

Define what is cached, key and tenant/version dimensions, value, TTL, invalidation, source, consistency tolerance, eviction, miss path, negative caching, and failure behavior. CDNs use cache-control, immutable URLs, purge, and origin shielding.

## 4. Concrete example

Video segments use immutable content-addressed/versioned URLs and long CDN TTLs. Private playback uses short-lived signed authorization; metadata cache key includes `video_id:version`. A visibility change updates truth and purges/shortens token exposure.

## 5. Detailed success flow

Request hits a fresh edge entry and avoids origin. On miss, one request fetches truth while others wait; response populates bounded cache with jittered TTL. Metrics record hit, origin latency, and staleness.

## 6. Detailed failure flow

A viral key expires everywhere, causing a stampede. Request coalescing, soft TTL/background refresh, jitter, and origin admission protect the store. If cache is down, fallback is bounded; optional reads may serve stale or fail rather than overwhelm truth.

## 7. Scaling behaviour

Tier browser/edge/regional/local caches; size the hot working set and replication. Hot keys need replication/coalescing; high-churn/low-reuse data is a bad cache candidate. CDN reduces origin bandwidth and geographic latency.

## 8. Data consistency implications

TTL bounds staleness only if truth does not require immediate revocation. Write-through still has dual-write failure unless one system owns commit. Cache-aside can serve stale after write; invalidate/version after source commit.

## 9. Real implementation choices

Redis/Memcached for application cache; in-process LRU for tiny hot data; CloudFront/Fastly/Cloudflare-like CDN; object storage as origin; Cache-Control/ETag for HTTP.

## 10. Trade-offs

Latency/origin relief versus stale data, memory cost, invalidation complexity, cold misses, and privacy. Long TTL improves hit rate but delays changes; versioned immutable keys simplify correctness but accumulate objects.

## 11. When not to use it

Do not cache correctness-critical mutable state unless stale behavior is safe. Do not cache data with low reuse, unbounded keys, or secrets without isolation.

## 12. Common interview mistakes

“Use Redis for speed”; no key/value/TTL/source; cache as truth; no stampede; negative cache too long; tenant omitted from key; CDN private content without authorization; hot key ignored.

## 13. How it appears inside larger systems

URL redirects, feeds, video/file delivery, autocomplete prefixes, product metadata, API gateway responses, and search results.

## 14. Likely interviewer follow-ups

What is the key/value? How invalidate? What if cache is lost? Can stale be served? How handle hot keys/revocation? What eviction and memory policy?

## 15. Five-minute revision

Cache only useful reusable data. Define key/value/source/TTL/invalidation/miss/eviction/failure. Coalesce+jitter hot misses. CDN for cacheable bytes; authorization and purge remain.

## 16. Related notes

[[Caching Pattern]] · [[Cache Invalidation and Stampede]] · [[Distributed Cache System]] · [[Blob Object and File Storage]]

## 17. Verified further reading

- [Redis client-side caching](https://redis.io/docs/latest/develop/reference/client-side-caching/) — official invalidation, disconnect, and cache-candidate guidance.\n- [Amazon CloudFront caching](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html) — official TTL and expiration behavior.

