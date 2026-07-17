---
type: canonical
domain: infrastructure
topic: terraform-plan-drift
status: learning
---

# Plan Apply and Drift

## Problem and mental model

Shows how desired configuration differs from refreshed remote reality before changing infrastructure.

## End-to-end flow and internals

Plan reads config/state/remote objects and proposes create/update/replace/destroy; a saved plan binds review to apply input. Drift is out-of-band difference surfaced on refresh/plan; import binds an existing object but does not author maintainable config automatically.

## Failure modes and troubleshooting

Treat replace/destroy, IAM/network and data-store changes as high risk. Investigate provider version/default/API change and out-of-band actor via audit logs. Avoid routine `-target`, which creates partial intent.

## Production security, scaling and trade-offs

CI scheduled drift detection is read-only; apply uses approvals and protected role. Reconcile emergency console fixes back into code; decide whether code or emergency state is intended.

## Interview questions and five-minute revision

Why can a plan change between review and later apply? Recall owner, data path, failure evidence, mitigation and trade-off.

## Related notes

[[Terraform Mental Model]] · [[State and Remote Backends]]

## Source metadata

Curated from *AWS Terraform Overview* (2025-06-09, `684734b5-7220-8013-a3a3-90bcad6c1448`) and HashiCorp official state/backend documentation. Backend/provider/version behavior is `needs-verification`.
