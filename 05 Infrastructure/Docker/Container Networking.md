---
type: canonical
domain: infrastructure
topic: docker-networking
status: learning
---

# Container Networking

## Problem and mental model

Connects isolated container network namespaces to peers, host and external networks.

## Internal/end-to-end flow

Bridge mode creates veth pair/bridge, container IP and host NAT; published port installs host forwarding. User-defined bridge provides DNS by container name. Host mode removes namespace boundary; overlay spans hosts through an orchestrator.

## Failure modes and troubleshooting

`docker network inspect`; `ip addr`; `ip route`; `ss -lnt`; resolve/curl from both host and container. Overlapping VPN/Docker CIDRs cause longest-prefix/policy route conflict; DNS settings do not fix routing.

## Production security, scaling and trade-offs

Choose non-overlapping address pools, publish only needed ports, bind app to `0.0.0.0`, and use host firewall/security. NAT hides source and adds conntrack state.

## Interview questions and five-minute revision

Why can host reach Internet while container cannot after VPN connects? Recall the layer, evidence, mitigation and permanent fix.

## Related notes

[[Proxies Load Balancers and NAT]] · [[Network Troubleshooting]]

## Source metadata

Curated from *Docker VPN Subnet Conflict* (2025-01-27, `6797b48a-68b4-8013-a35d-bcc3ed7e533c`) plus Docker official documentation. Runtime/version behavior is `needs-verification`.
