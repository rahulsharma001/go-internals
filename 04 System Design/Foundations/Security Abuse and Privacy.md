---
type: canonical
domain: system-design
topic: security-abuse-and-privacy
status: active
last_verified: 2026-07-17
---
# Security Abuse and Privacy

## 1. Problem it solves

A functional design can leak data, authorize the wrong object, enable fraud/spam, or exhaust shared capacity. Security follows trust boundaries, assets, actors, and abuse incentives.

## 2. Simple mental model

Authenticate who, authorize this action on this resource, minimize sensitive data, protect it in transit/at rest, and make abusive cost visible/bounded. TLS/JWT are mechanisms, not the whole design.

## 3. How it works

At edge validate protocol/size/rate; establish user/workload identity; resource owner enforces authorization and state transition; encrypt and rotate secrets/keys; tokenize payment data; audit privileged changes; detect abuse with limits and risk signals.

## 4. Concrete example

File download checks user/device membership against metadata, returns a short-lived object-scoped signed URL, and logs access without the URL token. Object origin is private; tenant ID is in cache/storage keys.

## 5. Detailed success flow

Authenticated principal requests allowed object; owner evaluates policy; scoped credential grants least privilege; sensitive fields remain minimized; audit/metrics record decision.

## 6. Detailed failure flow

Stolen token scrapes locations/files. Audience/expiry checks, object authorization, rate/concurrency limits, anomaly detection, revocation/short lifetime, and incident audit bound exposure.

## 7. Scaling behaviour

Authorization caches need safe invalidation; rate limits partition by identity/tenant; abuse detection pipelines are async but enforcement has low-latency rules. High-cardinality security logs need retention and access control.

## 8. Data consistency implications

Authorization and revocation freshness may be stricter than ordinary cache. Signed URLs remain valid until expiry unless provider purge/revocation exists. Audit events need durable ordering/identity appropriate to policy.

## 9. Real implementation choices

OIDC/OAuth provider; mTLS/workload identity; KMS/secret manager; WAF/API gateway; signed URLs; tokenization; policy engine; immutable audit store. Exact compliance depends on supplied requirements.

## 10. Trade-offs

Short tokens improve revocation but increase refresh dependency; strong authorization freshness adds latency; aggressive abuse limits create false positives; detailed logs aid investigation but raise privacy/cost.

## 11. When not to use it

Do not invent PCI/HIPAA/GDPR requirements. State general controls and ask. Do not build custom crypto/auth protocols.

## 12. Common interview mistakes

“Use JWT”; authentication without object authorization; PII/secrets in logs/events/cache keys/URLs; tenant missing from partition/key; public object origin; rate limit only by IP; no operator audit.

## 13. How it appears inside larger systems

Every external system; especially payments, files/media, ride location, chat, notifications, API gateway, crawler egress, and monitoring tenants.

## 14. Likely interviewer follow-ups

Trust boundaries? resource authorization? tenant isolation? revocation? signed URL? abuse/fraud/spam? deletion/retention? secrets? audit? data residency?

## 15. Five-minute revision

Asset/actor/trust → authN → resource authZ → minimize/encrypt → secret/key lifecycle → limits/abuse → audit/alerts → privacy/delete. Name user-visible false-positive trade-off.

## 16. Related notes

[[Rate Limiting Pattern]] · [[API Gateway System]] · [[Observability and SLOs]] · [[Caching and CDN Fundamentals]]

## 17. Verified further reading

- [OAuth 2.0 Security Best Current Practice, RFC 9700](https://www.rfc-editor.org/rfc/rfc9700) — current standards security guidance.\n- [OWASP API Security Top 10](https://owasp.org/API-Security/) — reputable API-specific threat checklist.

