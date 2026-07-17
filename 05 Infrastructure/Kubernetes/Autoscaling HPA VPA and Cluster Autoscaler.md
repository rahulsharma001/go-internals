---
type: canonical
domain: infrastructure
topic: kubernetes-autoscaling
status: learning
---

# Autoscaling HPA VPA and Cluster Autoscaler

## Problem and mental model

Matches workload replicas, per-Pod resources and node capacity to changing demand.

## Internal and end-to-end flow

HPA changes replica count from resource/custom/external signals; VPA recommends or changes requests and can restart Pods depending on mode; node autoscaling provisions/removes nodes for unschedulable/underused capacity. The loops have different delays and can interact.

## Failure modes and troubleshooting

CPU HPA fails when requests are absent/wrong; queue workers should often scale on backlog age/processing capacity; new Pods may overload DB pools; node provisioning lags. Inspect desired/current metrics, stabilization, Pending reasons and dependency headroom.

## Production choices, security and trade-offs

Scale the bottleneck, not merely frontends. Bound maximum replicas by downstream budgets. Avoid HPA and VPA fighting over the same CPU request without a reviewed design.

## Interview lens and five-minute revision

Why does HPA not solve a slow database? What occurs before a new node is ready? Recall: Matches workload replicas, per-Pod resources and node capacity to changing demand.

## Related notes

[[Requests Limits and QoS]] · [[AWS Cost and Scaling Trade-offs]] · [[Backpressure Pattern]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

