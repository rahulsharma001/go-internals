---
type: canonical
domain: infrastructure
topic: service-to-service-communication
status: learning
---

# Service to Service Communication

## Problem and mental model

Allows changing Pod replicas/IPs to communicate through a stable name and virtual service endpoint.

## Internal and end-to-end flow

`orders` resolves `payments.<ns>.svc.cluster.local` through CoreDNS → gets ClusterIP → opens/reuses TCP → NetworkPolicy allows flow → kube-proxy/eBPF selects a ready EndpointSlice address → CNI routes to Pod IP. A headless Service returns endpoint records and leaves client-side selection.

## Failure modes and troubleshooting

Check FQDN resolution, Service selector/ports, ready EndpointSlices, policy, and direct Pod call in that order. Propagate deadlines, trace context and idempotency keys; close HTTP response bodies so Go can reuse connections.

## Production choices, security and trade-offs

ClusterIP is the default internal boundary. A mesh adds mTLS/retries/telemetry but also proxies, policy and failure modes. Avoid routing ordinary internal calls through public Ingress.

## Interview lens and five-minute revision

Describe both DNS and packet flow, then explain what changes when no endpoint is ready. Recall: Allows changing Pod replicas/IPs to communicate through a stable name and virtual service endpoint.

## Related notes

[[Client to Pod Request Flow]] · [[Services and Service Discovery]] · [[Connection Pooling]] · [[Context Cancellation]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

