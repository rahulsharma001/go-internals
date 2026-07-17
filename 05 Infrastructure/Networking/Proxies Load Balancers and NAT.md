---
type: canonical
domain: infrastructure
topic: proxies-lb-nat
status: learning
---

# Proxies Load Balancers and NAT

## Problem and mental model

Routes traffic across boundaries, balances healthy capacity and translates addresses.

## Packet or connection flow

Forward proxy acts for client; reverse proxy/LB acts for server. L4 selects connection; L7 parses protocol/routes/terminates TLS. NAT rewrites address/port and maintains state; return traffic must traverse compatible state. Long-lived connections balance only at connect.

## Failure modes and senior diagnosis

Inspect DNS → listener → SG/firewall → target health → upstream connect → application. NAT port/conntrack exhaustion causes intermittent connects; X-Forwarded-For trust must be configured only for known proxies.

## Production security, scaling and trade-offs

Use connection draining, health/readiness, timeout hierarchy, proxy protocol/header trust and source-IP requirements. Each proxy adds buffering/retry/TLS/cost/failure.

## Interview questions and five-minute revision

ALB versus NLB; SNAT versus DNAT; why round-robin connections may not balance work? Recall the exact packet/connection sequence and the first diagnostic evidence at each boundary.

## Related notes

[[Ingress and AWS Load Balancers]] · [[VPC Subnets Routing and Security Groups]]

## Source metadata

Curated from *Golang Interview Prep Guide* (2026-06-29, `6a420622-0d40-83ee-8a64-955c416c4a67`) for the networking-focused role, plus relevant Kubernetes/AWS extracts. Protocol and implementation details are `needs-verification` against RFC/vendor/kernel documentation.
