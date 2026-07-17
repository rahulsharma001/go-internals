---
type: canonical
domain: system-design
topic: observability-and-slos
status: active
last_verified: 2026-07-17
---
# Observability and SLOs

## 1. Problem it solves

A distributed design is not operable if teams cannot detect user impact, locate the failing path, distinguish overload from correctness failure, and verify recovery.

## 2. Simple mental model

Metrics show rates/distributions, logs explain discrete events, traces connect a request across components, and profiles locate resource use. An SLI measures a user-relevant outcome; an SLO sets its target; alerts spend attention on actionable burn.

## 3. How it works

Define traffic/error/latency/saturation plus domain signals. Propagate trace/request/event IDs. Use structured logs without secrets. Measure queue age/lag, cache hit/staleness, replica lag, stuck workflows, and business invariants. Alert on multi-window error-budget burn with owner/runbook.

## 4. Concrete example

Order SLI is durable acceptance success and latency, not API host uptime. Dashboard also shows oldest outbox age, saga time by state, compensation pending, duplicate rate, and payment unknown outcomes.

## 5. Detailed success flow

01. Trace follows client→service→DB/outbox→consumer
11. metrics show SLO and dependency saturation
21. logs identify state transition/version.
31. Alert contains scope, impact, links, owner, and safe action.

## 6. Detailed failure flow

01. Consumer silently stops but API stays green.
11. Oldest-event age and end-to-end completion SLI breach, page the owner, and reconciliation confirms recovery.
21. CPU alone would miss it.

## 7. Scaling behaviour

Control metric label cardinality, trace/log sampling, retention/tiering, and query fairness. Preserve unsampled errors/rare correctness events. Observability pipeline failure must not overload production.

## 8. Data consistency implications

Telemetry can be delayed/duplicated; alert state needs deduplication. Business audit data may require stronger durability than diagnostic logs. Missing data is not healthy.

## 9. Real implementation choices

OpenTelemetry SDK/Collector; Prometheus-compatible metrics; Grafana; Loki/ELK/OpenSearch logs; Jaeger/Tempo traces; PagerDuty-like paging. These are examples.

## 10. Trade-offs

High-cardinality detail versus cost; sampling versus rare-event visibility; short alerts versus detection delay; centralized convenience versus blast radius/privacy.

## 11. When not to use it

Do not instrument every field blindly or page on every component anomaly. Monitoring is not a substitute for business audit/state.

## 12. Common interview mistakes

CPU-only dashboards; averages; queue depth without age; no business correctness signal; high-cardinality user IDs; secrets in logs; alerts with no owner/action; missing data treated healthy.

## 13. How it appears inside larger systems

All systems. Each system note should name SLI/SLO candidates, technical saturation, business outcome, dashboard, alerts, and trace keys.

## 14. Likely interviewer follow-ups

What user outcome? p99? missing data? cardinality? sampling? queue lag? silent correctness? monitor the monitor? alert owner/runbook? retention/privacy?

## 15. Five-minute revision

SLI=user outcome, SLO=target, error budget=decision signal. Metrics+logs+traces, plus domain invariants. Control cardinality/sampling, alert actionable burn, detect missing data.

## 16. Related notes

[[System Design Mock Rubric]] · [[Reliability and Failure Analysis]] · [[Monitoring System]] · [[Logging and Metrics Pipeline]]

## 17. Verified further reading

- [OpenTelemetry observability primer](https://opentelemetry.io/docs/concepts/observability-primer/) — official signals and instrumentation concepts.
- [Google Cloud: observability for reliability](https://cloud.google.com/architecture/framework/reliability/slo-and-alerts) — official SLI/SLO and alerting guidance.

