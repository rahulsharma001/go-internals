---
status: learning
type: canonical
area: system-design
sources:
  - "ChatGPT: Logging Monitoring Alerting BFF (2025-01-24, 6793a2b8-aacc-8013-a770-860633f9d45e)"
  - "OpenTelemetry documentation"
---

# Logs Metrics and Traces

## Problem it solves

Distributed systems need evidence to detect user impact, localize faults, understand causality, and verify recovery without guessing.

## Mental model

Metrics tell **whether/how much**, traces tell **where the request spent time**, and logs tell **what a component observed**. Correlation turns three stores into one investigation.

## How it works

Instrument service boundaries with stable service/operation names, trace/span IDs, result/error class, duration, and business identifiers that are safe to record. Export through an agent/collector that batches, samples, retries with bounds, and redacts. Keep telemetry asynchronous so an observability outage cannot block the product.

## Concrete example and detailed dry run

An order times out. The SLO alert shows elevated checkout error ratio. A trace reveals most time in payment; the payment span links `order_id=o-42` and an error class. Structured logs with the trace ID show a provider timeout and idempotency lookup. A dashboard confirms one provider/region, guiding circuit/failover action.

## Success scenario

Operators move from symptom to affected dependency/tenant/version, verify mitigation in the same signals, and retain enough evidence for follow-up.

## Failure scenario

High-cardinality user IDs in metric labels explode cost and impair queries. Correct design keeps metrics bounded, uses exemplars/traces for individual examples, samples verbose success telemetry, and never drops the error-budget signals needed to alert.

## Scaling considerations

Control cardinality, event size, sampling, retention tiers, tenant budgets, batch sizes, collector queues, and query concurrency. Tail sampling preserves interesting traces but needs buffering and coordination.

## Production technology choices

OpenTelemetry SDK/Collector; Prometheus-compatible metrics; structured logs to Loki/Elasticsearch/cloud logging; traces in Tempo/Jaeger/vendor backend; dashboards in Grafana-like tools.

## Trade-offs

More detail improves diagnosis but raises cost/privacy and ingestion load. Head sampling is cheap but may miss rare faults; tail sampling captures outcomes but costs state and delay.

## When not to use it

Do not log entire payloads, secrets, tokens, or sensitive identifiers. Do not turn every value into a metric label or synchronously export on the request path.

## Common interview mistakes

“Add logging” without signals; no propagation; confusing monitoring with observability; alerting on logs alone; ignoring telemetry failure/backpressure/privacy.

## Interview questions and follow-ups

Which golden signals apply? How are IDs propagated across Kafka? What is sampled? How are secrets/cardinality controlled? What happens when the collector fails?

## Five-minute recall

Metrics detect, traces localize, logs explain. Use consistent context, bounded cardinality, async collectors, sampling/retention tiers, redaction, and product-independent failure handling.

## Related notes

[[SLI SLO and Error Budgets]] · [[Alerting Strategy]] · [[Monitoring System]] · [[Backpressure Pattern]]

## Source metadata

Based on the extracted logging/monitoring conversation and official OpenTelemetry concepts. Backend-specific behavior needs verification.

