---
type: canonical
domain: infrastructure
topic: aws-messaging
status: learning
---

# SQS SNS and EventBridge

## Problem and mental model

Provides managed work queues, fan-out and event routing without operating brokers.

## End-to-end flow and internals

API/outbox → SQS for one competing worker group; SNS topic → multiple subscriptions; EventBridge event bus/rules → filtered targets. Worker processes idempotently then deletes/acks; visibility timeout, retry and DLQ bound failure.

## Failure modes and diagnosis

Track oldest age, in-flight, receives, deletes, retries/DLQ and target failures. Visibility too short duplicates concurrent work; too long delays retry. Poison messages need quarantine.

## Security, scaling and trade-offs

Use least-privilege producer/consumer roles, encryption and schema validation. SQS is simple work dispatch; SNS fan-out; EventBridge integration/routing. Kafka/MSK fits replayable partition log/consumer groups.

## Interview questions and five-minute revision

Compare delivery, ordering, replay and scaling—not service names. Recall the request/event path, security boundary, bottleneck, recovery and rejected alternative.

## Related notes

[[Queues and Pub Sub]] · [[Transactional Outbox Pattern]] · [[MSK and Kafka on AWS]]

## Source metadata

Curated from the infrastructure source conversations and existing system-design canonicals. AWS feature, quota, price, region and integration details are `needs-verification` against current official documentation.
