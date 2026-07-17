---
type: canonical
domain: infrastructure
topic: aws-lambda
status: learning
---

# Lambda

## Problem and mental model

Executes event-driven code without managing servers and can scale from low/bursty utilization.

## End-to-end flow and internals

API Gateway/SQS/EventBridge invokes a version/alias → runtime environment initializes/reuses → handler uses role and VPC/network as configured → result/ack. SQS event source mapping batches and retries; failed batches need partial-response/idempotency policy.

## Failure modes and diagnosis

Inspect invocation errors, duration, throttles/concurrency, init duration, DLQ/destination and downstream pool/connections. VPC/DNS and reserved concurrency can be the bottleneck.

## Security, scaling and trade-offs

Use deadlines, idempotency, small packages, bounded concurrency, secrets manager, and RDS Proxy where connection bursts justify it. ECS/EKS suits long-lived/high-control steady services.

## Interview questions and five-minute revision

Why can scaling Lambda overload RDS? Reserved versus provisioned concurrency? Recall the request/event path, security boundary, bottleneck, recovery and rejected alternative.

## Related notes

[[API Gateway]] · [[SQS SNS and EventBridge]] · [[Step Functions]]

## Source metadata

Curated from the infrastructure source conversations and existing system-design canonicals. AWS feature, quota, price, region and integration details are `needs-verification` against current official documentation.
