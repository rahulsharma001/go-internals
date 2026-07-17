---
type: canonical
domain: infrastructure
topic: infra-slo-implementation
status: learning
---

# SLI SLO and Error Budgets

## Problem and mental model

Implements user-journey SLIs and burn alerts in metric backends; the system-design note owns definitions/policy.

## End-to-end flow and internals

Instrument eligible/good counters or latency histograms → recording rules compute ratios over windows → dashboard shows target/budget → multi-window burn alerts → release/incident policy. Missing telemetry must not silently count healthy.

## Failure modes and troubleshooting

Backtest denominator/exclusions against known events. Low traffic needs appropriate windows/synthetics. Avoid averaging percentiles or summing precomputed percentages.

## Production security, scaling and trade-offs

Start with critical journeys and supporting dependency indicators. Actual targets require business agreement and are `needs-verification`. Canonical theory: [[04 System Design/Observability/SLI SLO and Error Budgets|System Design SLI SLO and Error Budgets]].

## Interview questions and five-minute revision

Write availability and latency SLI numerator/denominator. Recall owner, data path, failure evidence, mitigation and trade-off.

## Related notes

[[Alert Design]] · [[Prometheus and Grafana]]

## Source metadata

Curated from *Logging Monitoring Alerting BFF* (2025-01-24, `6793a2b8-aacc-8013-a770-860633f9d45e`), *Kibana Structured Logging* (2025-02-25, `67bd8e4b-4c10-8013-a4fb-761c32d6ce15`), existing system-design canonicals, and OpenTelemetry official concepts. Vendor/version behavior is `needs-verification`.
