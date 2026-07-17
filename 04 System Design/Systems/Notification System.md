---
status: learning
type: system-design
area: system-design
sources:
  - "ChatGPT: System Design Patterns (2026-07-05, 6a4aa703-f2d8-83ee-aac3-020aa67e9afb)"
---

# Notification System

## 1. Problem statement

Design a multi-channel notification platform for transactional email, SMS, push, and in-app delivery with preferences, templates, provider failover, deduplication, and auditable outcomes.

## 2. Functional requirements

Accept notification requests/events; resolve recipients and preferences; render versioned templates; schedule/immediately dispatch; select channel/provider; record attempts and callbacks; expose status; support cancellation before dispatch. Marketing campaign authoring is out of scope unless requested.

## 3. Non-functional requirements

Durable acceptance, bounded dispatch delay by priority, no duplicate user-visible message from platform retries where preventable, provider isolation, privacy, and graceful degradation.

## 4. Scale assumptions

Ask for events/second by channel and priority, fan-out size, payload size, latency target, provider quotas, and retention. Model `accepted × average recipients × selected channels`; all concrete targets need verification.

## 5. Core entities

`NotificationRequest`, `Recipient`, `Preference`, `TemplateVersion`, `Delivery`, `Attempt`, `ProviderCallback`, and `Suppression`.

## 6. API design

```text
POST /v1/notifications
Idempotency-Key: order-confirmed-o-42
{type, recipientId, templateId, variables, channels, priority}
→ 202 {notificationId, state:"ACCEPTED"}

GET /v1/notifications/{id}
POST /v1/providers/{provider}/callbacks  (signed callback)
```

## 7. Data model

The request stores a dedupe key and normalized payload hash. A delivery is unique by notification/channel/recipient. Attempts append provider ID, state, timestamp, and error class. Templates are immutable versions. PII is referenced or encrypted rather than copied broadly into queues.

## 8. High-level architecture

```text
Producer → API/Event Consumer → request DB/outbox → priority topics
                                                 → preference/template worker
                                                 → channel queues
                                                 → provider adapters → providers
Provider callbacks → callback API → delivery state → status/analytics
```

## 9. Component responsibilities

Ingestion authenticates and deduplicates; policy resolves consent/preferences; renderer creates channel content; scheduler enforces send time; dispatcher rate-limits by provider/tenant; adapters normalize provider APIs; callback processor advances delivery state.

## 10. Complete request or event flow

Accept request → commit request/outbox → policy and template resolution → create channel delivery → enqueue → acquire quota → provider send with stable idempotency/reference → persist response → consume signed callback → mark delivered/bounced/failed.

## 11. Detailed success path

An `OrderConfirmed` event creates one notification by event ID. Email is allowed, template `order-confirmed:v3` renders, and the adapter sends with `delivery_id`. Provider acceptance records `SENT`; a verified callback later records `DELIVERED`. Duplicate input returns the existing notification.

## 12. At least one detailed failure path

Provider times out after possibly accepting. The attempt becomes `UNKNOWN`, not immediately retried blindly. Query/provider idempotency reconciles it; only then retry or fail over. When a provider rate limit rises, its circuit opens, queue consumption slows via [[Backpressure Pattern]], urgent traffic uses reserved capacity, and optional traffic is delayed. Poison templates go to quarantine.

## 13. Bottlenecks

Large fan-out, template rendering, recipient preference lookups, provider quotas, callback bursts, hot tenants, and retry storms.

## 14. Scaling strategy

Partition by recipient/tenant where ordering matters; separate priority/channel topics; bulk provider calls only when semantics allow; cache immutable templates/preferences with invalidation; apply per-provider/token-bucket limits; scale adapters independently.

## 15. Reliability and disaster recovery

Use durable request/outbox state, replicated queues, replayable delivery records, provider fallback by channel and policy, backups, and reconciliation for unknown attempts. Do not fail over if it risks duplicate high-impact messages without an explicit business decision.

## 16. Observability

Measure acceptance and dispatch latency, queue age by priority, suppression rate, render errors, provider latency/errors/throttles, attempts per delivery, unknown outcomes, callback lag, bounce rate, and delivered rate. Correlate request, delivery, attempt, and provider IDs.

## 17. Security

Authorize producers; minimize/encrypt contact data; sanitize template variables; sign and replay-protect callbacks; isolate tenants; manage consent and unsubscribe; redact message bodies from logs; restrict operator access.

## 18. Concrete technology choices

PostgreSQL for request/delivery audit; Kafka/SQS-like queues; Redis token buckets; provider-specific email/SMS/push adapters; object storage for large campaign artifacts if later required.

## 19. Trade-offs

Exactly-once visible delivery is generally impossible across external providers; choose idempotency and reconciliation. Multi-provider improves resilience but makes status normalization and duplicate risk harder. Per-recipient ordering costs parallelism.

## 20. Interview follow-up questions

How do preferences race with queued sends? How are urgent and bulk traffic isolated? What is `SENT` versus `DELIVERED`? How is provider failover made safe? How are templates rolled back?

## 21. Five-minute revision

Durably accept and dedupe; resolve preference + versioned template; queue by channel/priority; rate-limit isolated adapters; store attempts; verify callbacks; reconcile unknown outcomes; never promise end-to-end exactly-once.

## Related notes

[[Transactional Outbox Pattern]] · [[Idempotency Pattern]] · [[Rate Limiting Pattern]] · [[Circuit Breaker Pattern]] · [[Queues and Pub Sub]]

## Source metadata

Curated from the extracted patterns conversation above. Provider contracts, quotas, and delivery semantics are `status: needs-verification`.

