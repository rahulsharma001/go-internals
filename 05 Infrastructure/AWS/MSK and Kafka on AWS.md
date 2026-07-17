---
type: canonical
domain: infrastructure
topic: aws-msk-kafka
status: learning
---

# MSK and Kafka on AWS

## Problem and mental model

Provides managed Kafka brokers for durable partitioned logs, replay and multiple consumer groups.

## End-to-end flow and internals

Outbox/producer chooses key → MSK partition leader appends/replicates → consumer-group member owns partition → processes idempotently → commits offset. EKS/ECS workers use private network/auth and schema contracts.

## Failure modes and diagnosis

Per-partition lag/skew, ISR/replication, broker disk/network, produce/fetch errors, rebalances and handler dependency latency locate lag. Scaling consumers beyond partitions does not increase same-group parallelism.

## Security, scaling and trade-offs

MSK reduces broker provisioning work, not partition/key/schema/replay/consumer correctness. Compare provisioned/serverless offerings, networking, storage, cross-AZ transfer and operations with SQS.

## Interview questions and five-minute revision

Why is exactly-once not an end-to-end business guarantee? Recall the request/event path, security boundary, bottleneck, recovery and rejected alternative.

## Related notes

[[Kubernetes Production Failures]] · [[Queues and Pub Sub]] · [[OpenTelemetry]]

## Source metadata

Curated from the infrastructure source conversations and existing system-design canonicals. AWS feature, quota, price, region and integration details are `needs-verification` against current official documentation.
