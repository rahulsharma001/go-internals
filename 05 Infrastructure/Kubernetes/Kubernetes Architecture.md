---
type: canonical
domain: infrastructure
topic: kubernetes-architecture
status: learning
---

# Kubernetes Architecture

## Problem and mental model

Separates cluster decision-making from node execution so workloads can be scheduled, healed and exposed across machines.

## Internal and end-to-end flow

API server is the authenticated API boundary; etcd stores cluster state; controllers reconcile; scheduler chooses a node. Kubelet drives Pod lifecycle; CRI runtime runs containers; CNI supplies networking; kube-proxy/eBPF implements Services; CoreDNS provides discovery.

## Failure modes and troubleshooting

`kubectl apply` failing points to auth/admission/API; Pending points to scheduling/capacity; ContainerCreating points to image/volume/CNI; Running-but-unreachable points to readiness/Service/network/app.

## Production choices, security and trade-offs

EKS manages control-plane components, not application correctness, worker capacity, CNI address supply, add-ons, or workload security. Test API and data-plane failure separately.

## Interview lens and five-minute revision

Name each component by responsibility and state whether it participates in every user request. Recall: Separates cluster decision-making from node execution so workloads can be scheduled, healed and exposed across machines.

## Related notes

[[Kubernetes Mental Model]] · [[EKS Architecture]] · [[Kubernetes Networking CNI and kube-proxy]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

