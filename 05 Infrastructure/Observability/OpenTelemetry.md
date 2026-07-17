---
type: canonical
domain: infrastructure
topic: opentelemetry
status: learning
---

# OpenTelemetry

## Problem and mental model

Standardizes vendor-neutral telemetry APIs, semantic context and collection pipelines.

## End-to-end flow and internals

Go instrumentation creates spans/metrics and propagates W3C trace context → OTLP exporter → Collector receivers/processors (batch, memory limiter, sampling, redaction) → one or more backends. Messaging propagation uses record headers.

## Failure modes and troubleshooting

Check sampling/propagation first, then exporter endpoint/TLS, collector queue/drop and backend. Tail sampling preserves interesting outcomes but buffers state; head sampling is cheaper but can miss rare failures.

## Production security, scaling and trade-offs

OTel is not a storage/query UI. Keep SDK overhead bounded, collector failure non-blocking, attributes low-cardinality and secrets excluded. Version semantic conventions deliberately.

## Interview questions and five-minute revision

What happens to trace continuity across SQS/Kafka async work? Recall owner, data path, failure evidence, mitigation and trade-off.

## Related notes

[[05 Infrastructure/Observability/Logs Metrics and Traces|Logs Metrics and Traces]] · [[CloudWatch and X-Ray]]

## Source metadata

Curated from *Logging Monitoring Alerting BFF* (2025-01-24, `6793a2b8-aacc-8013-a770-860633f9d45e`), *Kibana Structured Logging* (2025-02-25, `67bd8e4b-4c10-8013-a4fb-761c32d6ce15`), existing system-design canonicals, and OpenTelemetry official concepts. Vendor/version behavior is `needs-verification`.
