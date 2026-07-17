---
type: canonical
domain: infrastructure
topic: aws-architecture-selection
status: learning
source_conversations:
  - "AWS EKS App Deployment | 2026-06-25 | 6a3ce123-1794-83e8-83ea-0c20e4b4424c"
  - "AWS WebSocket Architecture Overview | 2025-06-09 | 6846e928-6bfc-8013-8fb6-6961d4da1540"
  - "AWS ECS Overview | 2025-06-13 | 684bbc35-a624-8013-8c48-46c325fbfbf8"
---

# AWS Architecture Selection Guide

## Selection principle

Choose the smallest operational model that satisfies workload shape, latency, protocol, state, isolation, scaling and team constraints. Do not start from a service catalogue. Place every service on a request/event path, define its failure ownership, and price both AWS spend and engineering/on-call work.

## Compute decision

| Need | Default candidate | Why / caution |
| --- | --- | --- |
| Kubernetes APIs/ecosystem, many services, platform team | EKS | Flexible; highest cluster/add-on/network/upgrade responsibility |
| Containers without Kubernetes | ECS on Fargate | Simpler AWS-native scheduler; less portability/control than EKS |
| Short stateless event/request handler with bursty or low duty cycle | Lambda | Scale-to-zero and managed runtime; limits, cold start, concurrency and database connections matter |
| Stable long-lived HTTP/WebSocket/background process | ECS/EKS | Connection lifecycle and predictable process model; pay for provisioned capacity |
| Workflow state, retries and waits | Step Functions | Durable orchestration visibility; transition cost and AWS coupling |

Use RDS/Aurora for relational transactions/joins, DynamoDB for known key-access patterns and horizontal managed scale, ElastiCache for ephemeral acceleration/coordination with explicit failure semantics, S3 for durable objects, SQS for work queues, SNS for fan-out notification, EventBridge for event routing/integration, and MSK when Kafka semantics/ecosystem/replay justify its operational and cost profile.

## Connected architecture 1: REST request

Route 53 → optional CloudFront/WAF → ALB or API Gateway → EKS Ingress / ECS Service / Lambda → RDS and/or ElastiCache → response.

### Responsibilities and flow

1. Route 53 resolves the public name. CloudFront caches safe content and reduces origin load; WAF filters defined threats.
2. API Gateway is useful for managed API auth, quotas, request routing and serverless integrations. ALB is a direct L7 entry for container services and EKS Ingress. Avoid stacking both without a concrete boundary.
3. Compute authenticates/authorizes business actions, propagates a deadline and trace ID, and uses bounded connection pools.
4. Redis serves only data whose staleness/failure policy is explicit. RDS commits authoritative relational state; DynamoDB may own key-value state instead.
5. Response and telemetry return along the same request context; do not synchronously wait for optional analytics/notifications.

### Security boundary

Public edge accepts TLS; WAF and rate limits reduce abuse. ALB/API Gateway integrate with private VPC targets as supported. Workloads run in private subnets, use security-group least privilege and workload/task/Lambda roles, and fetch secrets through an approved service. Database is not public. Authorization remains in the application even when the gateway authenticates.

### Scaling, failure and observability

Scale edge and stateless compute independently, but budget RDS/Redis connections and downstream rate. Use Multi-AZ, health/readiness, timeouts, circuit/bulkhead, load shedding and idempotency. Observe Route 53/edge errors, ALB/API Gateway status/latency, compute saturation, traces, pool wait, RDS/Redis latency and business outcome.

### Cost/operations

CloudFront/API Gateway/Lambda can be economical for bursty traffic but request/transfer/transition charges grow. ALB plus ECS/EKS suits steady traffic; EKS adds cluster/platform work. Cache lowers origin load but adds invalidation and failure complexity.

## Connected architecture 2: asynchronous state change

API → database transaction → outbox/event → SQS, MSK/Kafka or EventBridge → worker → downstream service → inbox/idempotency → outcome/reconciliation.

### Responsibilities and flow

1. API validates and commits business state plus outbox in one local transaction.
2. Relay/CDC publishes stable event ID. SQS dispatches work; Kafka/MSK retains ordered partition logs for multiple consumer groups/replay; EventBridge routes events to AWS/SaaS targets.
3. Worker acknowledges only after durable side effect. It uses inbox/idempotency, bounded retries/backoff and DLQ/quarantine.
4. A reconciler finds stuck outbox rows, old messages and unknown downstream outcomes.

### Security, scaling and failure

Use producer/consumer IAM permissions, encryption and private endpoints/network paths; validate schema and never place secrets in payloads. Scale SQS workers from oldest-message age, Kafka consumers up to partition concurrency, and protect downstreams with backpressure. Broker publish/consume is normally at-least-once at the business boundary; design duplicates and poison messages.

### Observability and trade-offs

Track oldest outbox/message age, publish error, per-partition lag/skew, retries/DLQ, processing duration and business completion. SQS is operationally simple but offers queue semantics; MSK gives Kafka compatibility/replay/order per partition at greater steady cost/operations; EventBridge provides rich routing but not a general high-throughput log replacement.

Related canonical: [[Transactional Outbox Pattern]].

## Connected architecture 3: WebSocket

Client → API Gateway WebSocket → `$connect`/message/`$disconnect` integration (Lambda or service) → Redis/DynamoDB connection mapping → SQS asynchronous/delayed work → worker → API Gateway Management `postToConnection` → client.

### Responsibilities and flow

1. `$connect` authenticates and records connection ID/user/expiry after successful handshake.
2. Message route validates authorization and enqueues durable/long work; it does not hold the route open unnecessarily.
3. A worker finds current connection IDs and calls the management endpoint. Gone connections cause mapping cleanup.
4. `$disconnect` is best-effort cleanup; TTL/reconciliation handles missed disconnects. Durable application messages live in a database/log, not only the socket.

### Security, scaling and failure

Authorize connect and every action; scope management API permissions; never log tokens. Partition mappings, cap per-user connections/frame/rate, and use TTL. Clients reconnect with jitter and an application cursor. SQS absorbs bursts and retries; delivery to a connection can still fail after dequeue, so durable sequence/catch-up is required.

### Observability and cost

Measure active connections, message rate/size, connect/auth failures, management API failures, stale mappings, queue age and end-to-end delivery. Managed WebSocket reduces gateway operations but charges by connection/message and imposes documented behavior/limits. ECS/EKS-hosted WebSockets offer protocol/process control but require load balancing, draining, registry and capacity engineering.

## Reliability and regional choices

Start Multi-AZ inside one region. Define RTO/RPO and data consistency before multi-region. Route 53/CloudFront global routing does not replicate database state. Active-passive is simpler; active-active needs conflict/ownership rules, regional idempotency and tested failover. See [[AWS Reliability and Multi AZ]].

## Senior interview checklist

- State workload shape and the rejected alternative.
- Draw synchronous and asynchronous boundaries and the source of truth.
- Give IAM/network/data security at each boundary.
- Explain overload, partial failure, duplicate, timeout and recovery.
- Name user and saturation signals.
- Discuss steady and variable costs plus on-call complexity.

## Five-minute revision

REST: DNS/edge → gateway/LB → compute → cache/database. Async: transaction/outbox → SQS/Kafka/EventBridge → idempotent worker/reconciliation. WebSocket: managed connection → route integration → TTL mapping → queue/worker → management API → cursor recovery. Select EKS/ECS/Lambda by workload and team, and select RDS/DynamoDB/S3/Redis/messaging by access and failure semantics.

## Related notes

[[EKS]] · [[ECS and Fargate]] · [[Lambda]] · [[API Gateway]] · [[API Gateway WebSockets]] · [[SQS SNS and EventBridge]] · [[MSK and Kafka on AWS]] · [[RDS Aurora and DynamoDB]] · [[ElastiCache Redis]] · [[AWS Cost and Scaling Trade-offs]]

## Source metadata

Curated from the extracted conversations listed in frontmatter, existing system-design canonicals and AWS official documentation. Pricing, quotas, feature availability, regional behavior and integration details are `needs-verification` for the chosen region/date.
