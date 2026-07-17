---
type: canonical
domain: infrastructure
topic: datadog-apm
status: learning
---

# Datadog and APM

## Problem and mental model

Provides managed unified infrastructure, log, metric, trace and profile analysis with less backend operation.

## End-to-end flow and internals

Host/cluster agents plus application tracer → Datadog intake → service map/APM traces/log correlation → monitors/dashboards. Kubernetes admission/injection and unified service/env/version tags improve cross-signal navigation.

## Failure modes and troubleshooting

Check agent status, admission injection, tracer endpoint, sampling, tag mismatch and intake/network. Cost spikes often come from custom metric cardinality, log volume/indexing or trace retention.

## Production security, scaling and trade-offs

Managed speed and integrations trade vendor coupling and usage cost. Redact at source, restrict agent/API keys, sample intentionally and export SLO-critical metrics independently if portability demands.

## Interview questions and five-minute revision

When prefer managed APM over assembling Prometheus/ELK/Tempo? Recall owner, data path, failure evidence, mitigation and trade-off.

## Related notes

[[OpenTelemetry]] · [[Logs Metrics and Traces]]

## Source metadata

Curated from *Logging Monitoring Alerting BFF* (2025-01-24, `6793a2b8-aacc-8013-a770-860633f9d45e`), *Kibana Structured Logging* (2025-02-25, `67bd8e4b-4c10-8013-a4fb-761c32d6ce15`), existing system-design canonicals, and OpenTelemetry official concepts. Vendor/version behavior is `needs-verification`.
