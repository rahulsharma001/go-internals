---
type: canonical
domain: infrastructure
topic: kubernetes-observability
status: learning
---

# Kubernetes Observability

## Problem and mental model

Combines cluster state, node/container resources and application telemetry to explain user impact.

## Internal and end-to-end flow

Collect control/add-on events and metrics, kube-state object status, node/cAdvisor/cgroup signals, container stdout/stderr, and application OpenTelemetry. Correlate deploy version, namespace, Pod and trace without making Pod UID a high-cardinality business metric.

## Failure modes and troubleshooting

Start with SLO symptom → trace hop → application log → Pod/Node/event → CNI/controller only at the narrowed boundary. Events expire; centralize important logs. Monitor the collector so telemetry loss is visible but does not block product traffic.

## Production choices, security and trade-offs

Prometheus/Grafana plus Alertmanager is common; CloudWatch Container Insights or Datadog can reduce assembly work; OpenTelemetry keeps application instrumentation portable. Control retention/cardinality and redact.

## Interview lens and five-minute revision

Which signal distinguishes app 500 from ingress 502 and node loss? Recall: Combines cluster state, node/container resources and application telemetry to explain user impact.

## Related notes

[[Logs Metrics and Traces]] · [[Prometheus and Grafana]] · [[Incident Investigation]] · [[Kubernetes Production Failures]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

