---
type: canonical
domain: infrastructure
topic: services-discovery
status: learning
---

# Services and Service Discovery

## Problem and mental model

Gives a stable virtual identity and port for ephemeral ready Pod backends.

## Internal and end-to-end flow

Service selector → EndpointSlice addresses/conditions → CoreDNS Service record → kube-proxy/eBPF virtual-IP translation. ClusterIP is internal; NodePort exposes a node port; LoadBalancer asks a cloud controller/controller to provision external L4 reachability; headless returns endpoints.

## Failure modes and troubleshooting

`kubectl get svc,endpointslice`; compare selector/labels, `port`/`targetPort`, readiness, DNS result and direct calls. A Service with no endpoints cannot route. `ExternalName` is DNS indirection, not a proxy.

## Production choices, security and trade-offs

Use named ports and FQDN across namespaces. Watch endpoint count/health. Session affinity reduces mobility; headless discovery shifts balancing and failure handling to the client.

## Interview lens and five-minute revision

Explain why Service IP does not belong to one interface and how readiness removes backends. Recall: Gives a stable virtual identity and port for ephemeral ready Pod backends.

## Related notes

[[Client to Pod Request Flow]] · [[Service to Service Communication]] · [[DNS]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

