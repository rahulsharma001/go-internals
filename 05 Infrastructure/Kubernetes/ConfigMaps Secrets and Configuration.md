---
type: canonical
domain: infrastructure
topic: kubernetes-config
status: learning
---

# ConfigMaps Secrets and Configuration

## Problem and mental model

Separates deployable image from environment-specific non-secret and secret configuration.

## Internal and end-to-end flow

ConfigMaps/Secrets can project as environment variables or files. Environment values are captured at process start; mounted projections may update eventually, but the application must reload safely. Kubernetes Secret data is encoded, not automatically a complete secret-management solution.

## Failure modes and troubleshooting

Missing key prevents start; stale env requires rollout; invalid config can crash all replicas. Validate schema before activation, version configuration, expose safe config version, and roll back. Never log values.

## Production choices, security and trade-offs

Use workload identity and an approved secret manager/CSI integration for credentials; encrypt at rest, restrict RBAC, rotate, audit, and avoid Git/plain manifests. Decide restart versus dynamic reload explicitly.

## Interview lens and five-minute revision

Why is base64 not encryption? How do you roll out a breaking config safely? Recall: Separates deployable image from environment-specific non-secret and secret configuration.

## Related notes

[[IAM Roles and Policies]] · [[RBAC and Service Accounts]] · [[Rolling Deployments and Rollbacks]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

