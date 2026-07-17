---
type: canonical
domain: infrastructure
topic: elk-kibana
status: learning
---

# ELK and Kibana

## Problem and mental model

Centralizes structured logs for search, correlation, dashboards and forensic investigation.

## End-to-end flow and internals

Application writes one JSON event → agent/Filebeat/Fluent Bit parses/enriches → optional Logstash/ingest pipeline → Elasticsearch index/data stream → Kibana query/visualization. Trace/request IDs link logs to spans.

## Failure modes and troubleshooting

Raw JSON string inside a message is not structured fields. Inspect parser errors, mapping conflicts, dropped events, ingest queue, shard health, disk/watermark and time range. Avoid mapping explosion from dynamic arbitrary keys.

## Production security, scaling and trade-offs

Define schema, severity and safe identifiers; redact tokens/payload/PII before ship; lifecycle/retention and tiering control cost. Elasticsearch is not a metrics replacement.

## Interview questions and five-minute revision

How does double-encoded JSON hurt queries? Recall owner, data path, failure evidence, mitigation and trade-off.

## Related notes

Source conversation: *Kibana Structured Logging* (2025-02-25, 67bd8e4b-4c10-8013-a4fb-761c32d6ce15) · [[05 Infrastructure/Observability/Logs Metrics and Traces|Logs Metrics and Traces]]

## Source metadata

Curated from *Logging Monitoring Alerting BFF* (2025-01-24, `6793a2b8-aacc-8013-a770-860633f9d45e`), *Kibana Structured Logging* (2025-02-25, `67bd8e4b-4c10-8013-a4fb-761c32d6ce15`), existing system-design canonicals, and OpenTelemetry official concepts. Vendor/version behavior is `needs-verification`.
