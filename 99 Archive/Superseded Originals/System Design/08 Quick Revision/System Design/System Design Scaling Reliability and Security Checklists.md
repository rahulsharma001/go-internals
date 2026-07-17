> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Reliability Checklist]].

---
type: quick-revision
domain: system-design
---

# System Design Scaling Reliability and Security Checklists

## Scaling

- Peak traffic and skew, not only average.
- First bottleneck: CPU, memory, connection, disk, DB lock, broker, dependency.
- Partition key, hot key/region/tenant, rebalancing, cross-partition work.
- Cache key/TTL/invalidation/stampede and CDN/origin shielding.
- Queue capacity, age, consumer lag, backpressure, expiry, poison work.
- Load test assumption and autoscaling signal; reserve critical capacity.

## Reliability

- End-to-end deadline and cancellation.
- Retry safety, idempotency, jitter, cap, budget; unknown outcome reconciliation.
- Circuit/bulkhead/admission control; graceful shed order.
- Durable state and source of truth; duplicates/order/concurrency.
- Success, partial failure, compensation/manual repair, terminal state.
- Multi-zone/region authority, replication lag, fencing, RPO/RTO, restore/failback drill.
- SLI/SLO, backlog/stuck-work signals, alerts with owner/action/runbook.

## Security

- Authenticate users/workloads; authorize action and object at owner.
- Validate schema, size, state transition, upload/content, outbound URLs.
- Rate/concurrency limits by IP/user/tenant/resource.
- TLS/mTLS as appropriate; encrypt storage; rotate keys/certs/tokens.
- Minimize PII; no secrets/tokens in logs, events, URLs, or traces.
- SSRF/egress, injection, webhook signature/replay, abuse/fraud controls.
- Least privilege, tenant isolation, audit sensitive/operator changes.

If a checklist item does not apply, say why; do not add a component reflexively.

