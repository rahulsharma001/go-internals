---
type: canonical
domain: infrastructure
topic: network-policies
status: learning
---

# Network Policies

## Problem and mental model

Restricts Pod ingress/egress so a compromised workload cannot freely reach every cluster or external endpoint.

## Internal and end-to-end flow

Policies select Pods and allow traffic; behavior only exists if the installed CNI enforces NetworkPolicy. Default deny plus explicit DNS, service and external dependency egress is clearer than ad hoc blocks.

## Failure modes and troubleshooting

Check selector/namespace labels, port/protocol, both source egress and destination ingress, DNS allowance and CNI enforcement/logs. Test from an ephemeral debug Pod before/after policy.

## Production choices, security and trade-offs

Layer NetworkPolicy with security groups, IAM and application auth. L3/L4 policy does not understand all L7 identities; meshes/gateways may add L7/mTLS at operational cost.

## Interview lens and five-minute revision

Why might a valid NetworkPolicy have no effect? Recall: Restricts Pod ingress/egress so a compromised workload cannot freely reach every cluster or external endpoint.

## Related notes

[[Kubernetes Networking CNI and kube-proxy]] · [[VPC Subnets Routing and Security Groups]] · [[TLS and mTLS]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

