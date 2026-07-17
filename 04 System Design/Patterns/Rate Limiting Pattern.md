---
type: canonical
domain: system-design
topic: rate-limiting-pattern
status: active
last_verified: 2026-07-17
---
# Rate Limiting Pattern

## 1. Problem it solves

Protect finite capacity, enforce fair usage, and slow abuse by bounding requests/work per identity and interval.

## 2. Simple mental model

Choose who is limited, what resource, where enforced, algorithm, distributed state consistency, and rejection/degradation semantics.

## 3. How it works

Fixed window is simple/bursty; sliding log/window smoother/costlier; token bucket allows controlled bursts with refill; leaky bucket smooths output. Hierarchical limits combine global, tenant, user, IP, endpoint, and expensive-resource quotas.

## 4. Concrete example

API gateway token bucket per tenant+route allows 100/s with burst 200, plus global backend cap. Payment creation also has per-account concurrency/fraud limits. Response uses 429 and retry-after without consuming downstream.

## 5. Detailed success flow

Request atomically consumes token under correct key; accepted proceeds; headers expose policy; metrics track allowed/rejected and saturation.

## 6. Detailed failure flow

Limiter store is unavailable. Security/cost-sensitive mutation fails closed or uses conservative local quota; public read may fail open with global admission. Local caches reconcile carefully to avoid unlimited overshoot.

## 7. Scaling behaviour

Shard by limit key; hot global counters need hierarchical/local token allocation; approximate distributed limits may overshoot. TTL expires buckets; time source/skew and region budgets matter.

## 8. Data consistency implications

Strict global rate requires coordination and latency; local limits are available but overshoot. Define acceptable overshoot and whether quota is fairness, billing, or safety.

## 9. Real implementation choices

Redis atomic script/module, Envoy/API gateway, in-process token bucket, DynamoDB conditional counters, dedicated quota service.

## 10. Trade-offs

Accuracy versus latency/availability; burst allowance versus smooth protection; global fairness versus regional autonomy; fail-open availability versus abuse/cost.

## 11. When not to use it

Do not use rate limits as the only authorization/fraud control or substitute for backend capacity/admission. Static limit may harm variable-cost endpoints.

## 12. Common interview mistakes

Only IP; no resource/key; per-instance limit multiplied by replicas; limiter after expensive work; no fail mode; 429 retries create herd; one tenant starves global capacity.

## 13. How it appears inside larger systems

API gateways, login, URL creation, notifications/provider quotas, crawler politeness, chat sends, upload bandwidth, search queries.

## 14. Likely interviewer follow-ups

Key/scope? algorithm/burst? distributed accuracy? multi-region? fail open/closed? headers/retry? dynamic cost? hot key? config rollout?

## 15. Five-minute revision

Resource + identity + scope → token/window algorithm → atomic state → hierarchy/global cap → fail behavior → 429/degrade → metrics. State acceptable overshoot.

## 16. Related notes

[[Rate Limiter System]] · [[Backpressure and Load Shedding]] · [[Security Abuse and Privacy]]

## 17. Verified further reading

- [Redis rate limiting use case](https://redis.io/docs/latest/develop/use-cases/) — official token-bucket example catalog.\n- [RFC 6585, 429 Too Many Requests](https://www.rfc-editor.org/rfc/rfc6585) — authoritative HTTP status semantics.

