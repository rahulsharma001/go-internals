---
type: canonical
domain: infrastructure
topic: http-versions
status: learning
---

# HTTP 1 2 and 3

## Problem and mental model

Maps application requests onto connections with different multiplexing and transport trade-offs.

## Packet or connection flow

HTTP/1.1 reuses/pipelines carefully but commonly one in-flight request per connection; HTTP/2 multiplexes streams over one TCP connection with HPACK and flow control; HTTP/3 uses QUIC over UDP with TLS 1.3 integration and independent transport streams. Semantics remain HTTP.

## Failure modes and senior diagnosis

Capture protocol negotiation/ALPN, connection reuse, stream limits, resets, queueing and server/gateway support. One H2 TCP loss can still affect connection congestion; H3 can be blocked by UDP networks and fall back.

## Production security, scaling and trade-offs

Choose by client/edge support and operational evidence. Configure Go server header/body/idle/write policy and client pools; proxy buffering/timeouts may dominate.

## Interview questions and five-minute revision

Why can HTTP/2 reduce connections yet create a single-connection blast radius? Recall the exact packet/connection sequence and the first diagnostic evidence at each boundary.

## Related notes

[[TCP Connection Lifecycle]] · [[TLS and mTLS]] · [[API Gateway]]

## Source metadata

Curated from *Golang Interview Prep Guide* (2026-06-29, `6a420622-0d40-83ee-8a64-955c416c4a67`) for the networking-focused role, plus relevant Kubernetes/AWS extracts. Protocol and implementation details are `needs-verification` against RFC/vendor/kernel documentation.
