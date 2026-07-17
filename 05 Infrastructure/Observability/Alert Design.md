---
type: canonical
domain: infrastructure
topic: infra-alert-design
status: learning
---

# Alert Design

## Problem and mental model

Implements actionable symptom and burn-rate alerts while reusing the system-design alert policy.

## End-to-end flow and internals

SLI/recording rule → multi-window evaluation → grouping/inhibition/dedupe → route to owner → runbook/dashboard/trace → resolution condition → review. Capacity alerts page only when impact/imminent action is clear.

## Failure modes and troubleshooting

Validate expression with history, no-data semantics, labels and notification route. Alert storms require grouping/inhibition and root-symptom preference. Monitor the alert pipeline with dead-man/external checks.

## Production security, scaling and trade-offs

Page for urgent action, ticket for slow risk, dashboard for diagnosis. This implementation note links [[04 System Design/Observability/Alerting Strategy|Alerting Strategy]] as policy owner.

## Interview questions and five-minute revision

What action and user objective justify this page? Recall owner, data path, failure evidence, mitigation and trade-off.

## Related notes

[[Prometheus and Grafana]] · [[Incident Investigation]]

## Source metadata

Curated from *Logging Monitoring Alerting BFF* (2025-01-24, `6793a2b8-aacc-8013-a770-860633f9d45e`), *Kibana Structured Logging* (2025-02-25, `67bd8e4b-4c10-8013-a4fb-761c32d6ce15`), existing system-design canonicals, and OpenTelemetry official concepts. Vendor/version behavior is `needs-verification`.
