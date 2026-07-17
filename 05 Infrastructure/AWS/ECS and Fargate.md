---
type: canonical
domain: infrastructure
topic: aws-ecs-fargate
status: learning
---

# ECS and Fargate

## Problem and mental model

Runs containers with AWS-native orchestration without operating Kubernetes.

## End-to-end flow and internals

ECR image → task definition (image, CPU/memory, ports, roles, secrets) → ECS Service maintains tasks → ALB/NLB target group routes to healthy task ENIs. Fargate supplies compute isolation; EC2 launch type gives host control and bin packing.

## Failure modes and diagnosis

Inspect service events, task stop reason, container logs, target health, ENI/SG, task execution role versus task role, and deployment circuit breaker. Long-lived WebSockets need drain/idle design.

## Security, scaling and trade-offs

Fargate reduces host work but charges per task resources and limits host-level control. ECS/EC2 can be cheaper at steady scale but owns instances. Use task role, private subnets and immutable definitions.

## Interview questions and five-minute revision

Task role versus execution role? ECS Service versus one-off task? Recall the request/event path, security boundary, bottleneck, recovery and rejected alternative.

## Related notes

[[AWS Architecture Selection Guide]] · [[Containers and Images]] · [[Ingress and AWS Load Balancers]]

## Source metadata

Curated from the infrastructure source conversations and existing system-design canonicals. AWS feature, quota, price, region and integration details are `needs-verification` against current official documentation.
