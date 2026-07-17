---
type: canonical
domain: infrastructure
topic: snmp-traps
status: learning
---

# SNMP and Traps

## Problem and mental model

Monitors and manages network-device state; traps provide fast event notification for networking-focused Go roles.

## Packet or connection flow

Manager polls agent OIDs for reconciled state; agent emits trap/inform on event such as interface/tunnel down → receiver decodes MIB identity → normalizes/deduplicates → alert/state pipeline. Traps are often UDP and can be lost; informs acknowledge but still need policy.

## Failure modes and senior diagnosis

If missing: device generated? destination/route/ACL/UDP 162? version and SNMPv3 user/auth/privacy? receiver listener? MIB/OID parsing? queue/alert? Use packet capture narrowly and compare periodic poll.

## Production security, scaling and trade-offs

Prefer SNMPv3 auth/privacy, isolate management network, rotate credentials, rate-limit/dedupe traps. Treat trap as signal and polling/heartbeat as reconciliation; never claim trap-only state correctness.

## Interview questions and five-minute revision

Trap versus polling versus inform, and how does a Go receiver handle backpressure? Recall the exact packet/connection sequence and the first diagnostic evidence at each boundary.

## Related notes

[[OSPF Fundamentals]] · [[Incident Investigation]] · [[Worker Pool]]

## Source metadata

Curated from *Golang Interview Prep Guide* (2026-06-29, `6a420622-0d40-83ee-8a64-955c416c4a67`) for the networking-focused role, plus relevant Kubernetes/AWS extracts. Protocol and implementation details are `needs-verification` against RFC/vendor/kernel documentation.
