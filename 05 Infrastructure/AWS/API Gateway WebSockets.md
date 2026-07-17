---
type: canonical
domain: infrastructure
topic: aws-apigateway-websocket
status: learning
---

# API Gateway WebSockets

## Problem and mental model

Hosts managed bidirectional connections and routes connect/message/disconnect events to backends.

## End-to-end flow and internals

Client upgrade → `$connect` auth/integration → connection ID stored with TTL → message route invokes Lambda/service → async work via SQS → worker calls management `postToConnection` → Gone response removes stale mapping. `$disconnect` is best-effort.

## Failure modes and diagnosis

Diagnose connect status, route selection expression, integration logs, connection mapping/TTL, management endpoint/permissions, Gone errors and client close reason. Durable messages require cursor catch-up.

## Security, scaling and trade-offs

Scope management permissions, rate/frame limits, TTL, jittered reconnect and secret-free logs. Managed connection operations simplify infrastructure but have quotas/charges/behavior to verify.

## Interview questions and five-minute revision

Why not treat Redis connection mapping as message durability? Recall the request/event path, security boundary, bottleneck, recovery and rejected alternative.

## Related notes

[[WebSocket Polling Webhook and SSE]] · [[ElastiCache Redis]] · [[SQS SNS and EventBridge]]

## Source metadata

Curated from the infrastructure source conversations and existing system-design canonicals. AWS feature, quota, price, region and integration details are `needs-verification` against current official documentation.
