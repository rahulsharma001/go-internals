---
type: canonical
domain: infrastructure
topic: pod-disruption-budgets
status: learning
---

# Pod Disruption Budgets

## Problem and mental model

Limits simultaneous voluntary disruption of replicas during drain, upgrade or autoscaler action.

## Internal and end-to-end flow

A PDB selects Pods and specifies `minAvailable` or `maxUnavailable`; eviction-aware operations respect it. It does not prevent crashes, node loss or all direct deletes, and cannot create capacity.

## Failure modes and troubleshooting

Drain blocked means compare selector, expected/allowed disruptions, replica readiness and other constraints. An impossible PDB can halt maintenance; an absent PDB can remove too many replicas.

## Production choices, security and trade-offs

Choose availability with replica count and topology. Single-replica workloads cannot have both uninterrupted voluntary maintenance and zero spare capacity. Test node upgrades.

## Interview lens and five-minute revision

What does a PDB protect, and what failures bypass it? Recall: Limits simultaneous voluntary disruption of replicas during drain, upgrade or autoscaler action.

## Related notes

[[Rolling Deployments and Rollbacks]] · [[AWS Reliability and Multi AZ]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

