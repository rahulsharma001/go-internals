---
type: canonical
domain: infrastructure
topic: kubernetes-rollouts
status: learning
---

# Rolling Deployments and Rollbacks

## Problem and mental model

Changes application versions while controlling unavailable and surge capacity and retaining rollback history.

## Internal and end-to-end flow

Deployment creates a new ReplicaSet, waits for readiness and scales old replicas down using surge/unavailable policy. Termination removes eligibility, sends SIGTERM and enforces grace. Rollback selects an older template, not a database undo.

## Failure modes and troubleshooting

Watch errors by version, ready endpoints, target deregistration and termination duration. Pause first when uncertain. `kubectl rollout status|history|pause|undo deploy/<name>`. Schema/config compatibility and long-lived sockets commonly break otherwise healthy rollouts.

## Production choices, security and trade-offs

Use canary for high-risk changes, immutable digests, graceful Go shutdown and expand-migrate-contract data changes. Keep rollback possible and automate SLO gates.

## Interview lens and five-minute revision

Why can maxUnavailable=0 still produce errors? How does readiness differ from drain? Recall: Changes application versions while controlling unavailable and surge capacity and retaining rollback history.

## Related notes

[[Client to Pod Request Flow]] · [[Pod Disruption Budgets]] · [[Kubernetes Production Failures]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

