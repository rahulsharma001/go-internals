---
type: canonical
domain: infrastructure
topic: ipsec-vti
status: learning
---

# IPsec and VTI

## Problem and mental model

Encrypts site-to-site IP traffic and exposes a route-based tunnel interface suitable for dynamic routing.

## Packet or connection flow

IKE authenticates peers/negotiates Security Associations → routes send packet to VTI/XFRM interface → IPsec ESP encrypts/authenticates and encapsulates → peer decrypts → routes inner packet. NAT traversal commonly uses UDP encapsulation; exact modes depend on deployment.

## Failure modes and senior diagnosis

Check underlay reachability/UDP ports → time/cert/PSK identity → IKE logs and SAs → XFRM policy/state counters → VTI up/address/routes → OSPF → firewall/return path → MTU/MSS when small packets work but large fail.

## Production security, scaling and trade-offs

Use modern approved algorithms, key rotation, anti-replay, least-privilege management and audited config. Route-based VPN scales routing better; policy-based can be simpler for fixed selectors. Encryption does not create routes.

## Interview questions and five-minute revision

IKE versus ESP; tunnel versus transport; why MTU shrinks? Recall the exact packet/connection sequence and the first diagnostic evidence at each boundary.

## Related notes

[[OSPF Fundamentals]] · [[TLS and mTLS]] · [[VPC Subnets Routing and Security Groups]]

## Source metadata

Curated from *Golang Interview Prep Guide* (2026-06-29, `6a420622-0d40-83ee-8a64-955c416c4a67`) for the networking-focused role, plus relevant Kubernetes/AWS extracts. Protocol and implementation details are `needs-verification` against RFC/vendor/kernel documentation.
