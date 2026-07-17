---
type: quick-revision
domain: infrastructure
status: active
---

# AWS Interview Revision

## Choose from workload, not catalogue

EKS for Kubernetes ecosystem/platform needs; ECS/Fargate for AWS-native containers with less orchestration work; Lambda for short bursty event/request handlers; Step Functions for durable orchestration.

## REST flow

Route 53 → optional CloudFront/WAF → ALB or API Gateway → EKS/ECS/Lambda → Redis/RDS or DynamoDB → response. Protect private workloads with SGs, scoped runtime roles, deadlines/pools, Multi-AZ and correlated telemetry.

## Async flow

API → DB transaction/outbox → SQS/MSK/EventBridge → idempotent worker → downstream → ack/reconciliation. SQS dispatches work, MSK supplies Kafka partition log/replay/groups, EventBridge routes integrations. Monitor oldest age/lag, retries/DLQ and business completion.

## WebSocket flow

API Gateway WebSocket → connect/message integration → Redis/DynamoDB mapping with TTL → SQS worker → management `postToConnection`. Disconnect is best effort; durable messages/cursors handle reconnect.

## Data and edge

RDS/Aurora for relational transactions; DynamoDB for defined key access; Redis is an acceleration/coordination layer with explicit fail-open/closed; S3 stores objects; CloudFront caches delivery.

## Senior trade-offs

State target security boundary, bottleneck, failure and unit/operational cost. Multi-AZ is not multi-region; scaling compute can exhaust DB connections; NAT/log/cross-AZ charges matter. Verify current quotas/prices.

## Related

[[AWS Architecture Selection Guide]]

Return: [[Infrastructure Dashboard]]
