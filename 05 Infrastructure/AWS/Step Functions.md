---
type: canonical
domain: infrastructure
topic: aws-step-functions
status: learning
---

# Step Functions

## Problem and mental model

Coordinates multi-step workflows, waits, branches and retries with durable execution state.

## End-to-end flow and internals

API/event starts execution → state machine invokes Lambda/ECS/AWS services → Choice/Wait/Retry/Catch controls progress → result/event updates source of truth. Business idempotency remains required.

## Failure modes and diagnosis

Inspect execution history, failed state input/output with data controls, retry policy, service quota and downstream state. A workflow retry can duplicate a side effect if task is not idempotent.

## Security, scaling and trade-offs

Use for visible orchestration and long waits; avoid for a simple in-process sequence or ultra-high-transition path without cost analysis. Redact/scope payload and execution IAM.

## Interview questions and five-minute revision

When use Saga state machine versus Kafka choreography? Recall the request/event path, security boundary, bottleneck, recovery and rejected alternative.

## Related notes

[[Saga Pattern]] · [[Lambda]] · [[SQS SNS and EventBridge]]

## Source metadata

Curated from the infrastructure source conversations and existing system-design canonicals. AWS feature, quota, price, region and integration details are `needs-verification` against current official documentation.
