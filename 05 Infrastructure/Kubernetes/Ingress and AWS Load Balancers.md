---
type: canonical
domain: infrastructure
topic: ingress-aws-load-balancers
status: learning
---

# Ingress and AWS Load Balancers

## Problem and mental model

Publishes HTTP routes or L4 services without exposing every Pod directly.

## Internal and end-to-end flow

Ingress declares L7 host/path/TLS intent; a controller implements it. On EKS, AWS Load Balancer Controller can create ALB for Ingress and NLB for LoadBalancer Service. ALB IP target can reach Pod IP; instance target goes through nodes/Service. Gateway API is an evolving alternative; verify support.

## Failure modes and troubleshooting

Separate controller reconciliation from request path. Inspect Ingress events/controller logs, AWS listener/rules/security groups/target health, EndpointSlices and application timings. 502 is often upstream connection/response; 504 is usually timeout.

## Production choices, security and trade-offs

ALB suits HTTP routing/WAF integration; NLB suits TCP/UDP, static IP/source-IP needs. Align TLS termination, health checks, idle timeout and graceful target deregistration.

## Interview lens and five-minute revision

Draw IP versus instance target modes and explain controller absence: the Ingress object alone does nothing. Recall: Publishes HTTP routes or L4 services without exposing every Pod directly.

## Related notes

[[Client to Pod Request Flow]] · [[EKS Architecture]] · [[Proxies Load Balancers and NAT]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

