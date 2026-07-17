---
type: canonical
domain: infrastructure
topic: kubernetes-networking
status: learning
---

# Kubernetes Networking CNI and kube-proxy

## Problem and mental model

Provides routable Pod addresses and stable Service virtual endpoints across nodes.

## Internal and end-to-end flow

CNI configures Pod interfaces, IPAM and routes/policies; it runs at Pod setup, while packets use the installed data path. kube-proxy watches Services/EndpointSlices and programs node forwarding; some eBPF CNIs replace that logic. VPC CNI makes EKS Pod addressing integrate with VPC constructs.

## Failure modes and troubleshooting

Test same-Pod, same-node, cross-node, ClusterIP and external paths separately. Inspect IP exhaustion, routes, policy drops, conntrack and node-specific failures. Do not begin with packet capture before checking endpoints and ports.

## Production choices, security and trade-offs

Choose CNI for address scale, policy, observability and operational skill. eBPF can reduce translation hops but creates platform-specific diagnostics. Plan VPC/subnet IP capacity.

## Interview lens and five-minute revision

What is configured by CNI versus kube-proxy? Why can direct Pod IP work while Service IP fails? Recall: Provides routable Pod addresses and stable Service virtual endpoints across nodes.

## Related notes

[[Client to Pod Request Flow]] · [[Network Policies]] · [[VPC Subnets Routing and Security Groups]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

