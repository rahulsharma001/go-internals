---
type: canonical
domain: infrastructure
topic: ospf
status: learning
---

# OSPF Fundamentals

## Problem and mental model

Dynamically exchanges internal routes and reconverges after topology changes for networking-focused backend roles.

## Packet or connection flow

Routers discover neighbors with Hello packets → form adjacency when parameters match → flood link-state advertisements → build link-state database → run shortest-path calculation → install best routes by cost. Areas limit flooding; OSPF runs directly over IP protocol 89, not TCP/UDP.

## Failure modes and senior diagnosis

If neighbor down: interface/VTI/IP → IPsec → protocol 89/firewall → area, authentication, hello/dead timers, MTU and router IDs → LSDB/routes. Separate tunnel UP from routing UP.

## Production security, scaling and trade-offs

Backend control plane should store desired config, roll out idempotently and reconcile actual neighbor/route state. Static routes are simpler for tiny stable topologies; OSPF adds convergence and operational complexity.

## Interview questions and five-minute revision

Why can IPsec/VTI be up while traffic has no route? Recall the exact packet/connection sequence and the first diagnostic evidence at each boundary.

## Related notes

[[IPsec and VTI]] · [[SNMP and Traps]] · [[Linux Networking Tools]]

## Source metadata

Curated from *Golang Interview Prep Guide* (2026-06-29, `6a420622-0d40-83ee-8a64-955c416c4a67`) for the networking-focused role, plus relevant Kubernetes/AWS extracts. Protocol and implementation details are `needs-verification` against RFC/vendor/kernel documentation.
