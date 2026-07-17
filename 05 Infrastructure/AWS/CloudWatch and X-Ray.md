---
type: canonical
domain: infrastructure
topic: aws-observability
status: learning
---

# CloudWatch and X-Ray

## Problem and mental model

Collects AWS-native logs, metrics, alarms and traces for managed-service and workload diagnosis.

## End-to-end flow and internals

AWS service emits metrics/logs → CloudWatch stores/queries → alarm routes action; application trace segments/spans correlate through X-Ray or OpenTelemetry integration. CloudTrail is API audit history, not application tracing.

## Failure modes and diagnosis

Start from SLO, split gateway/LB/compute/dependency, correlate request/trace ID and deploy. Watch log delivery/retention and missing data. High-cardinality dimensions and verbose logs increase cost.

## Security, scaling and trade-offs

Use structured redacted logs, metric filters sparingly, dashboards, composite/actionable alarms and OTel where portability matters. Sampling saves cost but must preserve errors.

## Interview questions and five-minute revision

CloudWatch versus CloudTrail versus trace? Recall the request/event path, security boundary, bottleneck, recovery and rejected alternative.

## Related notes

[[05 Infrastructure/Observability/Logs Metrics and Traces|Logs Metrics and Traces]] · [[OpenTelemetry]] · [[Alert Design]]

## Source metadata

Curated from the infrastructure source conversations and existing system-design canonicals. AWS feature, quota, price, region and integration details are `needs-verification` against current official documentation.
