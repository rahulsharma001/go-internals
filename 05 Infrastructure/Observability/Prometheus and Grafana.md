---
type: canonical
domain: infrastructure
topic: prometheus-grafana
status: learning
---

# Prometheus and Grafana

## Problem and mental model

Collects dimensional time-series metrics, evaluates rules and visualizes operational state.

## End-to-end flow and internals

Targets expose `/metrics` → Prometheus service discovery selects/scrapes → TSDB stores samples → recording/alerting rules evaluate → Alertmanager routes → Grafana queries dashboards. Remote write adds durable/managed backend paths.

## Failure modes and troubleshooting

Check target discovery/labels, scrape error, sample/cardinality limits, rule evaluation and query range. Missing metric can be absent target or absent series; stale does not mean zero.

## Production security, scaling and trade-offs

Use counters/histograms/gauges correctly, bounded labels, recording rules, HA pairs with dedupe where required, retention/capacity and secured endpoints. Prometheus pull is not a durable event store.

## Interview questions and five-minute revision

Why histogram over average? Why never label by user ID? Recall owner, data path, failure evidence, mitigation and trade-off.

## Related notes

[[Alert Design]] · [[05 Infrastructure/Observability/SLI SLO and Error Budgets|SLI SLO and Error Budgets]]

## Source metadata

Curated from *Logging Monitoring Alerting BFF* (2025-01-24, `6793a2b8-aacc-8013-a770-860633f9d45e`), *Kibana Structured Logging* (2025-02-25, `67bd8e4b-4c10-8013-a4fb-761c32d6ce15`), existing system-design canonicals, and OpenTelemetry official concepts. Vendor/version behavior is `needs-verification`.
