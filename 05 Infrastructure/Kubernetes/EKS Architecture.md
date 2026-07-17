---
type: canonical
domain: infrastructure
topic: eks-architecture
status: learning
---

# EKS Architecture

## Problem and mental model

Provides a managed Kubernetes control plane integrated with AWS networking, identity, load balancing and managed worker options.

## Internal and end-to-end flow

AWS operates regional control-plane endpoints; workloads run on managed/self-managed nodes or supported serverless compute. VPC CNI assigns Pod networking; CoreDNS/kube-proxy and controllers remain add-ons to manage. AWS Load Balancer Controller reconciles Ingress/Services; workload identity authorizes AWS calls.

## Failure modes and troubleshooting

Separate control-plane health, node group/AMI/capacity, subnet IPs, CNI, add-on versions, IAM/RBAC and application. Multi-AZ control plane does not make single-AZ Pods or state resilient.

## Production choices, security and trade-offs

Use private subnets/nodes, multi-AZ node groups, endpoint access controls, least-privilege workload identity, upgrade/add-on compatibility testing, topology spread and spare capacity. Managed service reduces control-plane toil, not platform ownership.

## Interview lens and five-minute revision

Which responsibilities remain with the customer on EKS? Recall: Provides a managed Kubernetes control plane integrated with AWS networking, identity, load balancing and managed worker options.

## Related notes

[[AWS Architecture Selection Guide]] · [[Ingress and AWS Load Balancers]] · [[Terraform with AWS and EKS]] · [[AWS Reliability and Multi AZ]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

