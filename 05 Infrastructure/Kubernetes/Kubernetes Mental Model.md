---
type: canonical
domain: infrastructure
topic: kubernetes-mental-model
status: learning
---

# Kubernetes Mental Model

## Problem and mental model

Kubernetes continuously reconciles declared desired state with observed state; it is not a script runner and does not make an unhealthy application correct.

## Internal and end-to-end flow

Write objects to the API → API server validates/persists → controllers create dependent objects → scheduler binds Pods → kubelet/runtime/CNI make them run → status flows back. A Service/Ingress separately exposes eligible endpoints.

## Failure modes and troubleshooting

Failure comes from intent/status/data-plane disagreement. Compare spec, status, events, controller logs and an actual request. `kubectl get -o yaml`, `describe`, events, and EndpointSlices reveal different layers.

## Production choices, security and trade-offs

Use Deployments for stateless replicas, StatefulSets only for stable identity/storage, Jobs for finite work. Prefer managed state outside the cluster unless operational requirements justify owning it.

## Interview lens and five-minute revision

Explain reconciliation, control versus data plane, and why deleting a broken Pod rarely fixes a bad desired state. Recall: Kubernetes continuously reconciles declared desired state with observed state; it is not a script runner and does not make an unhealthy application correct.

## Related notes

[[Kubernetes Architecture]] · [[Client to Pod Request Flow]] · [[Pods Deployments and ReplicaSets]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

