---
type: implementation-guide
domain: infrastructure
topic: infra-signals
status: learning
canonical_owner: "[[04 System Design/Observability/Logs Metrics and Traces]]"
---

# Logs Metrics and Traces

## Problem and mental model

Implements the existing system-design signal model in infrastructure stacks without duplicating its theory.

## End-to-end flow and internals

Go OTel SDK emits traces/metrics/log context → local/DaemonSet/sidecar or gateway Collector batches/redacts → Prometheus/Datadog/CloudWatch/Elasticsearch backends → dashboard/alert links exemplar/trace ID. Kubernetes metadata enriches with bounded labels.

## Failure modes and troubleshooting

If telemetry missing: SDK/exporter → network/TLS/auth → collector receiver/queue/drop → backend ingest/index/query. Product traffic must not block on exporter. Control cardinality, sampling and retention.

## Production security, scaling and trade-offs

This note owns infrastructure implementation; conceptual canonical is [[04 System Design/Observability/Logs Metrics and Traces|System Design Logs Metrics and Traces]].

## Interview questions and five-minute revision

What signal detects, localizes and explains? Recall owner, data path, failure evidence, mitigation and trade-off.

## Related notes

[[OpenTelemetry]] · [[Kubernetes Observability]] · [[CloudWatch and X-Ray]]

## Source metadata

Curated from *Logging Monitoring Alerting BFF* (2025-01-24, `6793a2b8-aacc-8013-a770-860633f9d45e`), *Kibana Structured Logging* (2025-02-25, `67bd8e4b-4c10-8013-a4fb-761c32d6ce15`), existing system-design canonicals, and OpenTelemetry official concepts. Vendor/version behavior is `needs-verification`.
