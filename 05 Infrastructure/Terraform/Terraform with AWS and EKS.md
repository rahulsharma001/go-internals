---
type: canonical
domain: infrastructure
topic: terraform-aws-eks
status: learning
---

# Terraform with AWS and EKS

## Problem and mental model

Builds AWS network/IAM/EKS infrastructure reproducibly while separating cluster bootstrap and workload delivery.

## End-to-end flow and internals

Foundation state creates VPC/subnets/endpoints/IAM → EKS state/module creates cluster/node groups/add-ons → authenticated Kubernetes/Helm layer installs controllers → GitOps/app pipeline deploys workloads. Outputs pass minimal IDs/endpoints between layers.

## Failure modes and troubleshooting

Failure order: AWS identity/region → backend/lock → VPC/IP/IAM → cluster endpoint/auth → node bootstrap/add-ons → Kubernetes provider reachability. One monolithic apply can fail because cluster does not exist when provider initializes.

## Production security, scaling and trade-offs

Split blast radii/lifecycles, pin module/provider/Kubernetes compatibility, private network access and workload identity. Avoid using Terraform for high-frequency application rollout if GitOps/Helm is the owner.

## Interview questions and five-minute revision

Where should AWS Load Balancer Controller be owned and why? Recall owner, data path, failure evidence, mitigation and trade-off.

## Related notes

[[EKS Architecture]] · [[IAM Roles and Policies]] · [[Modules]]

## Source metadata

Curated from *AWS Terraform Overview* (2025-06-09, `684734b5-7220-8013-a3a3-90bcad6c1448`) and HashiCorp official state/backend documentation. Backend/provider/version behavior is `needs-verification`.
