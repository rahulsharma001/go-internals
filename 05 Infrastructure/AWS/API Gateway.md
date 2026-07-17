---
type: canonical
domain: infrastructure
topic: aws-api-gateway
status: learning
---

# API Gateway

## Problem and mental model

Provides a managed public API boundary for routing, auth, throttling, validation and integrations.

## End-to-end flow and internals

Client → custom domain/TLS → stage/route → authorizer/IAM/JWT → integration (Lambda or private HTTP through supported VPC linkage) → mapped response. It is a gateway, not the business authorization/source of truth.

## Failure modes and diagnosis

Split gateway 4xx/5xx from integration 5xx/timeouts; inspect execution/access logs, authorizer latency, integration latency, quotas and trace. Avoid retrying non-idempotent requests at multiple layers.

## Security, scaling and trade-offs

Good for serverless/managed API controls; ALB is simpler for direct container HTTP. Account for payload/timeout/quota/cost and validate current API type capabilities.

## Interview questions and five-minute revision

API Gateway versus ALB, and where does authorization belong? Recall the request/event path, security boundary, bottleneck, recovery and rejected alternative.

## Related notes

[[API Gateway WebSockets]] · [[AWS Architecture Selection Guide]] · [[HTTP 1 2 and 3]]

## Source metadata

Curated from the infrastructure source conversations and existing system-design canonicals. AWS feature, quota, price, region and integration details are `needs-verification` against current official documentation.
