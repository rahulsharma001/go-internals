---
type: canonical
domain: infrastructure
topic: kubernetes-probes
status: learning
---

# Probes and Application Health

## Problem and mental model

Distinguishes startup, traffic eligibility and process recovery.

## Internal and end-to-end flow

Startup gates liveness/readiness during slow initialization. Readiness removes a Pod from new Service traffic. Liveness asks kubelet to restart a stuck container; it must not be a general dependency check. Probe HTTP/TCP/gRPC/exec semantics depend on configuration/version.

## Failure modes and troubleshooting

Run the exact probe locally in the Pod, inspect events, latency, CPU throttling and dependency/pool waits. A wrong liveness probe causes restart storms; an over-broad readiness probe turns a shared dependency outage into zero endpoints.

## Production choices, security and trade-offs

Keep handlers cheap, bounded and unauthenticated only on an internal port/path; expose no secrets. Use reason metrics internally. Align termination readiness and external LB drain.

## Interview lens and five-minute revision

Give one condition that should fail readiness but not liveness. Recall: Distinguishes startup, traffic eligibility and process recovery.

## Related notes

[[Client to Pod Request Flow]] · [[Kubernetes Production Failures]] · [[Rolling Deployments and Rollbacks]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

