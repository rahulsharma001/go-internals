---
status: learning
type: system-design
area: system-design
sources:
  - "Curated system-design interview synthesis"
---

# URL Shortener

## 1. Problem statement

Design a service that creates short aliases for validated long URLs and redirects readers with low latency, while supporting expiration, custom aliases, abuse controls, and asynchronous analytics.

## 2. Functional requirements

Create generated/custom links; redirect; optionally expire/disable; inspect owner metadata; collect click analytics. Link previews, ad interstitials, and recommendation are out of scope.

## 3. Non-functional requirements

Redirects are read-heavy and highly available; alias uniqueness is strict; accepted links are durable; analytics must not block redirects; abuse and malicious destinations are controlled.

## 4. Scale assumptions

Ask for create/redirect ratio, peak reads, retention, URL length, custom-alias share, latency, and regions. Derive storage from created links × record bytes and cache needs from hot-key distribution; numeric targets require verification.

## 5. Core entities

`ShortLink`, `Owner`, `AliasReservation`, `RedirectPolicy`, `ClickEvent`, and `AbuseDecision`.

## 6. API design

```text
POST /v1/links
Idempotency-Key: create-session
{longUrl, customAlias?, expiresAt?}
→ 201 {alias, shortUrl}

GET /{alias} → 302/307 Location: longUrl
DELETE /v1/links/{alias}
GET /v1/links/{alias}/stats
```

## 7. Data model

`short_links(alias PK, long_url, owner_id, created_at, expires_at, status, version)`. A unique constraint arbitrates custom aliases. Generated aliases can encode a unique numeric ID or use random base62 with collision retry. Click events contain alias, coarse time/region/referrer data subject to privacy policy.

## 8. High-level architecture

```text
Creator → API Gateway → Link Service → primary link store
Reader  → edge/LB → Redirect Service → cache → link store
                              └→ non-blocking click stream → analytics
Admin/abuse pipeline → status update + cache invalidation
```

## 9. Component responsibilities

Link service validates schemes, reserves aliases, and persists metadata. Redirect service serves cached/authoritative mappings. Cache holds hot positive results plus short-lived negative entries. Analytics consumers aggregate clicks. Abuse service scans destinations and disables links.

## 10. Complete request or event flow

Create: authenticate/rate-limit → validate/canonicalize URL → reserve/allocate alias → persist → return. Redirect: validate alias → cache lookup → store on miss → verify active/not expired → return redirect → publish best-effort/durable click event asynchronously.

## 11. Detailed success path

Custom alias creation wins the unique constraint and cache is warmed after commit. A reader gets a cache hit and immediate redirect. Click publication happens after the response path and is duplicate-tolerant; aggregated stats become eventually consistent.

## 12. At least one detailed failure path

Two users request the same custom alias; one insert commits, the other receives conflict—never last-write-wins. If cache is unavailable, bounded requests fall back to replicated storage with admission/rate limits; analytics is shed before redirects. If a link is disabled, update authoritative state and invalidate cache; short TTL bounds stale redirects if invalidation is lost.

## 13. Bottlenecks

Viral aliases, cache stampedes, sequential-ID generator dependency, database read fan-out, abusive creation, analytics volume, and global invalidation.

## 14. Scaling strategy

Cache hot mappings at edge/region; request-collapse misses; shard storage by alias hash; replicate reads; allocate ID ranges or random IDs to remove a central generator; partition analytics separately; use [[Rate Limiting Pattern]].

## 15. Reliability and disaster recovery

Replicate durable mappings, back up/restore tested metadata, define home-region writes for alias uniqueness, use read failover, and prefer stale-but-valid redirects only if product/security policy permits. Analytics loss must not affect redirects.

## 16. Observability

Measure create/redirect rates and latency, cache hit/miss/stampede, store errors, conflicts/collisions, hot keys, disabled-link access, analytics lag/drop, and abuse decisions. Separate 404, expired, disabled, and backend failures.

## 17. Security

Allow only approved URL schemes; prevent open internal-network fetches in scanners; rate-limit and authenticate creators; scan/report malicious links; protect custom aliases; minimize click PII; sign admin changes; do not reflect unsafe input.

## 18. Concrete technology choices

PostgreSQL/DynamoDB/Cassandra-like mapping store according to region and consistency needs; Redis/CDN/edge KV cache; Kafka/Kinesis-like click stream; base62 alias codec. Product guarantees require verification.

## 19. Trade-offs

Sequential IDs are compact and collision-free but guessable and generator-dependent. Random IDs obscure volume and decentralize creation but need enough entropy and collision handling. Longer cache TTL reduces load but delays disable/expiry. `301` caches strongly; `302/307` provides more operational control.

## 20. Interview follow-up questions

How many characters are required? How is custom alias uniqueness global? What happens to a viral link? How are malicious links disabled quickly? Why should analytics be off the redirect path?

## 21. Five-minute revision

Strict unique alias; generated base62 via unique IDs or random+retry; cache read-heavy redirects; hash-shard durable mappings; async duplicate-tolerant analytics; explicit expiry/disable invalidation; protect creation and destination safety.

## Related notes

[[Caching Pattern]] · [[Partitioning and Sharding]] · [[Replication]] · [[Rate Limiting Pattern]] · [[API Security]]

## Source metadata

Curated interview synthesis. No external product scale or personal production claim is included; concrete operational targets remain `status: needs-verification`.
