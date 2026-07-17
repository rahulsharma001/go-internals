---
type: canonical
domain: infrastructure
topic: pods-deployments-replicasets
status: learning
---

# Pods Deployments and ReplicaSets

## Problem and mental model

Runs one or more tightly coupled containers while maintaining a desired number and safe rollout history.

## Internal and end-to-end flow

A Pod is the scheduling/network namespace unit. A Deployment owns ReplicaSets; a ReplicaSet owns Pods through labels/owner references. Editing a Deployment template creates a new ReplicaSet; deleting a Pod causes replacement, not a configuration fix.

## Failure modes and troubleshooting

Pending: scheduling. ImagePullBackOff: registry/auth/tag. CrashLoop: process lifecycle. Terminating: finalizer/volume/grace. Use owner chain, conditions, events, current/previous logs.

## Production choices, security and trade-offs

Keep one main process per container, immutable images, graceful SIGTERM, topology spread and realistic resources. Sidecars share fate and resources; use them only for coupled lifecycle.

## Interview lens and five-minute revision

Why not deploy naked Pods? What is the difference between restart and replacement? Recall: Runs one or more tightly coupled containers while maintaining a desired number and safe rollout history.

## Related notes

[[Rolling Deployments and Rollbacks]] · [[Probes and Application Health]] · [[Requests Limits and QoS]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

