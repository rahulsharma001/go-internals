---
type: canonical
domain: infrastructure
topic: tcp-lifecycle
status: learning
---

# TCP Connection Lifecycle

## Problem and mental model

Explains connection establishment, reuse, failure and cleanup that drive latency and FD/port state.

## Packet or connection flow

Client SYN → server SYN-ACK → client ACK; application data uses sequence/ACK and flow/congestion windows; graceful close uses FIN/ACK per direction; RST aborts. TIME_WAIT protects delayed segments. Keepalive/HTTP reuse amortizes handshake; retransmission backoff raises tail latency.

## Failure modes and senior diagnosis

`ss -tanpo`; `tcpdump 'tcp[tcpflags] != 0'`; SYN backlog, retransmits, resets, TIME_WAIT and conntrack. SYN timeout differs from TLS/HTTP timeout. Repeated new connections indicate pool/reuse failure.

## Production security, scaling and trade-offs

Set connect/idle/deadline hierarchy, drain on deploy, size backlog/FD/ports from measured connections. Do not globally shorten TIME_WAIT to hide a client leak.

## Interview questions and five-minute revision

Walk handshake and four-way close; who holds TIME_WAIT and why? Recall the exact packet/connection sequence and the first diagnostic evidence at each boundary.

## Related notes

[[File Descriptors]] · [[Connection Pooling]] · [[TLS and mTLS]]

## Source metadata

Curated from *Golang Interview Prep Guide* (2026-06-29, `6a420622-0d40-83ee-8a64-955c416c4a67`) for the networking-focused role, plus relevant Kubernetes/AWS extracts. Protocol and implementation details are `needs-verification` against RFC/vendor/kernel documentation.
