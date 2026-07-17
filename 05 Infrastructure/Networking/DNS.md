---
type: canonical
domain: infrastructure
topic: dns-flow
status: learning
---

# DNS

## Problem and mental model

Translates service names to addresses while enabling indirection, caching and service discovery.

## Packet or connection flow

Stub resolver → recursive resolver cache → root/TLD/authoritative lookup → record/CNAME chain → cached answer by TTL. Kubernetes Pod → CoreDNS → Service ClusterIP or headless endpoint records. Negative results can cache too.

## Failure modes and senior diagnosis

`dig +trace`, `dig @resolver`, `getent hosts`, Pod `/etc/resolv.conf`, CoreDNS metrics/logs. Distinguish NXDOMAIN, SERVFAIL, timeout and stale answer. Search domains/`ndots` can multiply queries.

## Production security, scaling and trade-offs

Use TTL aligned with failover/change, health-aware routing where supported, DNSSEC where threat/model fits, and redundant resolvers. DNS changes do not terminate existing connections.

## Interview questions and five-minute revision

What happens after DNS changes while a Go pool retains connections? Recall the exact packet/connection sequence and the first diagnostic evidence at each boundary.

## Related notes

[[Services and Service Discovery]] · [[Network Troubleshooting]]

## Source metadata

Curated from *Golang Interview Prep Guide* (2026-06-29, `6a420622-0d40-83ee-8a64-955c416c4a67`) for the networking-focused role, plus relevant Kubernetes/AWS extracts. Protocol and implementation details are `needs-verification` against RFC/vendor/kernel documentation.
