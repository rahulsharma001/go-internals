---
type: canonical
domain: infrastructure
topic: network-troubleshooting
status: learning
---

# Network Troubleshooting

## Problem and mental model

Finds the first failed hop without random configuration changes.

## Packet or connection flow

Define source/destination/protocol/time → DNS → route/namespace → local listener → firewall/SG/policy → TCP handshake → TLS → proxy/LB target → HTTP/app → return path. Compare affected and healthy source/node/version.

## Failure modes and senior diagnosis

Commands: `dig/getent`, `ip route get`, `ss`, `curl -v`, `openssl s_client`, `tracepath`, `tcpdump` with filters, VPC Flow Logs, EndpointSlices. Timeout usually means drop/no route/slow; refusal means reachable host with no accepting listener/reset, but proxies can alter symptoms.

## Production security, scaling and trade-offs

Preserve packet metadata securely, avoid broad captures, record exact timestamps. Mitigate at narrowed layer; permanent fix includes monitoring and topology/timeout/address plans.

## Interview questions and five-minute revision

Small ping works but large HTTPS fails: consider MTU, TLS record, fragmentation/path MTU. Recall the exact packet/connection sequence and the first diagnostic evidence at each boundary.

## Related notes

[[Linux Networking Tools]] · [[Client to Pod Request Flow]] · [[Docker Production Failures]]

## Source metadata

Curated from *Golang Interview Prep Guide* (2026-06-29, `6a420622-0d40-83ee-8a64-955c416c4a67`) for the networking-focused role, plus relevant Kubernetes/AWS extracts. Protocol and implementation details are `needs-verification` against RFC/vendor/kernel documentation.
