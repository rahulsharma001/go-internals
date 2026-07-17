---
type: canonical
domain: infrastructure
topic: kubernetes-rbac
status: learning
---

# RBAC and Service Accounts

## Problem and mental model

Controls who can perform which Kubernetes API actions and supplies workload identity.

## Internal and end-to-end flow

Authentication establishes identity; authorization evaluates verb/resource/namespace; admission applies policy. Role/ClusterRole define permission; bindings attach subjects. ServiceAccount identifies a Pod to Kubernetes; on EKS a workload-identity mechanism can map it to scoped AWS permissions.

## Failure modes and troubleshooting

Use `kubectl auth can-i --as=...`; inspect binding subjects and token audience. Avoid `cluster-admin`, wildcard resources/verbs and long-lived static tokens. A 403 differs from network/API unavailability.

## Production choices, security and trade-offs

Separate deployer, operator and workload roles. Use least privilege, short-lived identity, audit logs and namespace boundaries; Kubernetes RBAC does not replace AWS IAM.

## Interview lens and five-minute revision

Trace a Pod calling S3 and name both authorization systems. Recall: Controls who can perform which Kubernetes API actions and supplies workload identity.

## Related notes

[[IAM Roles and Policies]] · [[ConfigMaps Secrets and Configuration]] · [[EKS Architecture]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

