---
type: quick-revision
domain: infrastructure
status: active
---

# Observability Interview Revision

## Signal model

Metrics say whether/how much; traces show where time went; logs explain what a component observed. Propagate request/trace context through HTTP and message metadata. Telemetry failure must not block product traffic.

## Pipeline

Go OTel SDK → Collector batch/memory limit/redaction/sampling → Prometheus/Datadog/CloudWatch/ELK/tracing backend → dashboard/alert. Prometheus scrapes and evaluates rules; Grafana visualizes; ELK parses JSON logs; managed APM reduces operations at cost/coupling.

## SLO and alerts

SLI = good eligible events / eligible events (or latency distribution); SLO = agreed target/window; budget = allowed bad. Multi-window burn pages on urgent user impact. Page needs owner, action, context, runbook and recovery signal.

## Cardinality and cost

Never metric-label user/request IDs. Use bounded service/route/result/version; use logs/traces for individual events. Control sampling, log indexing and retention; redact before export.

## Incident order

Acknowledge → user impact/blast radius/timeline → reversible mitigation → preserve evidence → trace first failed hop → one hypothesis/change → verify SLI → communicate → prevention.

## Golden checks

Rate, errors, duration, saturation plus dependency pool/lag/queue. Histograms, not averages. Monitor collectors, scrapes, rule evaluation and alert delivery.

## Related

[[Incident Investigation]] · [[OpenTelemetry]] · [[Alert Design]]

Return: [[Infrastructure Dashboard]]
