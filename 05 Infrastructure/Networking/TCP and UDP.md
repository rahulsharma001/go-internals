---
type: canonical
domain: infrastructure
topic: tcp-udp
status: learning
---

# TCP and UDP

## Problem and mental model

Chooses reliable ordered byte streams or message-oriented best-effort datagrams.

## Packet or connection flow

TCP socket → three-way handshake → sequence/ACK windows → retransmission/congestion control → ordered bytes; UDP sends independent datagrams without connection recovery. Applications add message framing above TCP and reliability above UDP when needed.

## Failure modes and senior diagnosis

Use `ss`, `tcpdump` flags/sequence, retransmits, resets, receive/send queues and application timeout. TCP success does not prove HTTP correctness; UDP loss may be network or application buffer.

## Production security, scaling and trade-offs

TCP suits HTTP/DB; UDP suits DNS, telemetry or real-time cases that tolerate/design loss. QUIC builds reliable encrypted streams over UDP. Security needs TLS/DTLS/protocol auth.

## Interview questions and five-minute revision

Why is TCP a byte stream, and how does head-of-line behavior differ from UDP/QUIC? Recall the exact packet/connection sequence and the first diagnostic evidence at each boundary.

## Related notes

[[TCP Connection Lifecycle]] · [[HTTP 1 2 and 3]]

## Source metadata

Curated from *Golang Interview Prep Guide* (2026-06-29, `6a420622-0d40-83ee-8a64-955c416c4a67`) for the networking-focused role, plus relevant Kubernetes/AWS extracts. Protocol and implementation details are `needs-verification` against RFC/vendor/kernel documentation.
