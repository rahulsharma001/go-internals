---
type: canonical
domain: infrastructure
topic: aws-cost-scaling
status: learning
---

# AWS Cost and Scaling Trade-offs

## Problem and mental model

Makes capacity and service choices economically sustainable without sacrificing protected reliability.

## End-to-end flow and internals

Model requests/connections/bytes/storage/retention/NAT/cross-AZ/logs/LCU or transitions and steady compute. Scaling frontends changes downstream connections and transfer. Unit cost plus engineering/on-call cost drives choice.

## Failure modes and diagnosis

Investigate cost anomaly by tag/service/region and usage dimension; correlate deployments/traffic. NAT, logs, idle load balancers, overprovisioned nodes and cross-AZ traffic are common hidden owners.

## Security, scaling and trade-offs

Use budgets/anomaly alerts, rightsizing, autoscaling floors/ceilings, Savings Plans for stable compute where suitable, lifecycle/retention, endpoints and architecture review. Do not optimize by removing resilience blindly.

## Interview questions and five-minute revision

Compare Lambda/API Gateway variable cost with ECS/EKS steady cost and operations. Recall the request/event path, security boundary, bottleneck, recovery and rejected alternative.

## Related notes

[[AWS Architecture Selection Guide]] · [[Autoscaling HPA VPA and Cluster Autoscaler]]

## Source metadata

Curated from the infrastructure source conversations and existing system-design canonicals. AWS feature, quota, price, region and integration details are `needs-verification` against current official documentation.
