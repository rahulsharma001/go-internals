---
type: canonical
domain: system-design
topic: cache-invalidation-and-stampede
status: active
last_verified: 2026-07-17
---
# Cache Invalidation and Stampede

## 1. Problem it solves

Cached copies outlive changes, and synchronized misses can overload the source precisely when a hot key expires or a cache fleet restarts.

## 2. Simple mental model

Invalidation controls correctness; stampede control protects capacity. Use versions/immutable keys when possible, and let only one loader refresh a key.

## 3. How it works

TTL bounds time, explicit invalidation accelerates change, versioned keys make old values unreachable, and CDC can refresh. Stampede controls include request coalescing/singleflight, soft TTL with stale-while-revalidate, jitter, probabilistic early refresh, prewarming, and origin admission.

## 4. Concrete example

Viral video manifest uses immutable `video/42/generation/7/manifest`. Metadata pointer has short TTL. One regional loader refreshes pointer before expiry; other requests use still-safe old pointer briefly.

## 5. Detailed success flow

Truth commits version 8, invalidation publishes, caches evict/update; misses coalesce and populate version 8. Old immutable objects remain safe until lifecycle cleanup.

## 6. Detailed failure flow

Invalidation event is lost. TTL/version read bounds staleness. When many entries expire, jitter and per-key coalescing prevent an origin wave; overload sheds optional reads.

## 7. Scaling behaviour

Hot-key replication and tiered caches reduce load. Invalidation fan-out itself can be high; version keys trade messages for storage. Prewarm only known hot working sets.

## 8. Data consistency implications

Immediate revocation may require short credentials, purge, or truth recheck; TTL alone is insufficient. For ordinary metadata, bounded stale may be acceptable.

## 9. Real implementation choices

Redis locks only as refresh coordination (not truth), local singleflight, CDN stale-while-revalidate/purge, CDC invalidation, version columns/content hashes.

## 10. Trade-offs

Short TTL improves freshness but increases misses; explicit invalidation reduces stale time but can be lost/expensive; stale-while-refresh improves availability but serves old data.

## 11. When not to use it

Do not serve stale for authorization, revoked private content, inventory confirmation, or other unsafe state unless revalidated.

## 12. Common interview mistakes

Identical TTLs; distributed lock with no expiry/fencing; cache purge assumed instant; no negative-cache bound; thundering herd after outage; stale authorization.

## 13. How it appears inside larger systems

CDN media, URL disable, feeds, configuration, product metadata, search results, and distributed cache recovery.

## 14. Likely interviewer follow-ups

Lost invalidation? hot key? cache restart? negative entry? revocation? loader crash? origin unavailable? how measure staleness/stampede?

## 15. Five-minute revision

Truth version → invalidate/versioned key → TTL+jitter safety net → one loader → stale policy → origin admission → staleness/miss metrics.

## 16. Related notes

[[Caching Pattern]] · [[Caching and CDN Fundamentals]] · [[Backpressure and Load Shedding]]

## 17. Verified further reading

- [Redis client-side caching](https://redis.io/docs/latest/develop/reference/client-side-caching/) — official invalidation race/disconnect behavior.\n- [Amazon CloudFront expiration](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html) — official TTL/stale cache behavior.

