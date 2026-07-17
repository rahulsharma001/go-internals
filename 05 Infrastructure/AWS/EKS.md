---
type: canonical
domain: infrastructure
topic: aws-eks
status: learning
---

# EKS

## Problem and mental model

Runs Kubernetes when its API/ecosystem and portability justify a platform layer.

## End-to-end flow and internals

Route 53/ALB → AWS Load Balancer Controller → Service/EndpointSlice → EKS Pod; Pod uses workload identity for S3/SQS and private routes to RDS. AWS manages control-plane availability; customer owns node/Fargate capacity, add-ons, CNI IPs, workloads, versions and security.

## Failure modes and diagnosis

Separate control plane, nodes, add-ons, network and app. Common failures: subnet IP exhaustion, incompatible add-on/upgrade, Pending capacity, unhealthy targets, IAM/RBAC mismatch.

## Security, scaling and trade-offs

Choose ECS for simpler container scheduling; EKS for Kubernetes ecosystem/multi-service platform. Budget cluster, load balancer, NAT, logs and team/on-call cost.

## Interview questions and five-minute revision

When is EKS excessive? What remains customer responsibility? Recall the request/event path, security boundary, bottleneck, recovery and rejected alternative.

## Related notes

[[EKS Architecture]] · [[Terraform with AWS and EKS]] · [[AWS Reliability and Multi AZ]]

## Source metadata

Curated from the infrastructure source conversations and existing system-design canonicals. AWS feature, quota, price, region and integration details are `needs-verification` against current official documentation.
