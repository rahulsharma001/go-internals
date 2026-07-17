---
type: canonical
domain: infrastructure
topic: aws-s3-cloudfront
status: learning
---

# S3 and CloudFront

## Problem and mental model

Stores durable objects and serves/cache-distributes content near clients.

## End-to-end flow and internals

Client uploads via authenticated API/presigned URL → S3 object/version → event may enqueue processing → CloudFront fetches origin on miss and caches by key/TTL → signed URL/cookie controls private delivery.

## Failure modes and diagnosis

Check DNS/TLS, CloudFront result/cache key/origin status, S3 policy/KMS/object key, range requests and invalidation. Avoid making buckets public.

## Security, scaling and trade-offs

Use origin access controls, encryption, versioning/lifecycle and least privilege. CDN lowers latency/origin load but invalidation and transfer/request costs require immutable object names where possible.

## Interview questions and five-minute revision

Why prefer versioned object keys over frequent invalidation? Recall the request/event path, security boundary, bottleneck, recovery and rejected alternative.

## Related notes

[[AWS Architecture Selection Guide]] · [[TLS and mTLS]] · [[SQS SNS and EventBridge]]

## Source metadata

Curated from the infrastructure source conversations and existing system-design canonicals. AWS feature, quota, price, region and integration details are `needs-verification` against current official documentation.
