---
type: canonical
domain: infrastructure
topic: aws-iam
status: learning
---

# IAM Roles and Policies

## Problem and mental model

IAM authorizes AWS API actions without embedding long-lived credentials.

## End-to-end flow and internals

Principal assumes a role through STS → receives short-lived credentials → signs request → identity policy, resource policy, permissions boundary, SCP and explicit denies are evaluated. EKS workload identity, ECS task role and Lambda execution role place identity at workload boundary.

## Failure modes and diagnosis

403 diagnosis: identify principal/account/region/action/resource, inspect CloudTrail decision context, policy conditions and KMS/resource policy. Never solve by attaching administrator access.

## Security, scaling and trade-offs

Separate human federation, deployment and runtime roles; least privilege, session limits, MFA where relevant, Access Analyzer and rotation. IAM controls AWS APIs; Kubernetes RBAC controls Kubernetes API.

## Interview questions and five-minute revision

Trace an EKS Pod reading one S3 prefix. Which role, trust and resource permissions are evaluated? Recall the request/event path, security boundary, bottleneck, recovery and rejected alternative.

## Related notes

[[RBAC and Service Accounts]] · [[ConfigMaps Secrets and Configuration]] · [[CloudWatch and X-Ray]]

## Source metadata

Curated from the infrastructure source conversations and existing system-design canonicals. AWS feature, quota, price, region and integration details are `needs-verification` against current official documentation.
