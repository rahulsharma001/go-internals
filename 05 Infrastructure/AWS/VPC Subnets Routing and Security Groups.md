---
type: canonical
domain: infrastructure
topic: aws-vpc
status: learning
---

# VPC Subnets Routing and Security Groups

## Problem and mental model

A VPC creates a private routing and security boundary for workloads.

## End-to-end flow and internals

Internet client → IGW → public ALB subnet → target in private app subnet → RDS private DB subnet. Route tables choose next hop; NAT Gateway enables initiated outbound IPv4 from private subnets but does not accept unsolicited inbound. Security groups are stateful allow rules; NACLs are stateless subnet rules.

## Failure modes and diagnosis

Check DNS/IP → route table/longest prefix → SG on each ENI → NACL → NAT/IGW/endpoints → return route. Overlapping CIDRs break peering/VPN/container routes. Use VPC Flow Logs as evidence, not proof of application success.

## Security, scaling and trade-offs

Use multiple AZ subnets, private endpoints to reduce NAT exposure/cost, least-privilege SG references, and IP capacity for EKS Pods. NAT per AZ improves fault isolation at cost.

## Interview questions and five-minute revision

Why does a private subnet need neither nor always need a NAT? Explain return traffic and stateful SG. Recall the request/event path, security boundary, bottleneck, recovery and rejected alternative.

## Related notes

[[EKS Architecture]] · [[Proxies Load Balancers and NAT]] · [[IPsec and VTI]]

## Source metadata

Curated from the infrastructure source conversations and existing system-design canonicals. AWS feature, quota, price, region and integration details are `needs-verification` against current official documentation.
